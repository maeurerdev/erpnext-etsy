from typing import Optional

import os
import base64
import secrets
import hashlib

from requests_oauthlib import OAuth2Session
from urllib.parse import urlencode, urljoin, quote_plus, unquote_plus

import pytz
import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint, cstr, get_system_timezone

from erpnext.selling.doctype.sales_order.sales_order import make_sales_invoice, close_or_unclose_sales_orders
from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

from etsy.datastruct import ListingType
from etsy.api import EtsyAPI, QP_getListingsByShop, QP_getShopReceipts, fetch_all



AUTHORIZATION_URI = "https://www.etsy.com/oauth/connect"
TOKEN_URI = "https://api.etsy.com/v3/public/oauth/token"
SCOPES = ["address_r", "email_r", "listings_r", "shops_r", "transactions_r"]
QUERY_PARAMS = {}
LISTING_STATES = ("active", "inactive", "sold_out", "draft", "expired")


if any((os.getenv("CI"), frappe.conf.developer_mode, frappe.conf.allow_tests)):
	# Disable mandatory TLS in developer mode and tests
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"


def short_title(title:str) -> str:  # TODO: move to utils
	return title.replace("&quot;", '"').split(",")[0].split(";")[0].split("|")[0].split("•")[0].split(" - ")[0].split(" – ")[0].strip()[:60]


class EtsyShop(Document):
	### hooks
	def validate(self):
		# redirect_uri
		base_url = frappe.utils.get_url()  # or e.g.: "http://localhost:8000"
		if self.use_localhost:
			splt = base_url.split(":")
			base_url = f"{splt[0]}://localhost:{splt[-1]}"
		callback_path = f"/api/method/etsy.etsy.doctype.etsy_shop.etsy_shop.callback/{quote_plus(self.name)}"
		self.redirect_uri = urljoin(base_url, callback_path)
	
	### public
	def get_auth_header(self) -> dict:
		if not self.token_exists():
			frappe.log_error("Etsy: Access token does not exist for shop {0}".format(self.name))
			return None
		
		if self.token_expired():
			oauth_session = self.get_oauth2_session()

			try:
				token = oauth_session.refresh_token(
					body=f"redirect_uri={self.redirect_uri}",
					token_url=TOKEN_URI,
				)
			except Exception:
				frappe.log_error("Etsy: Token refresh failed for shop {0}".format(self.name))
				return None

			self.token_update(token)
			
		return {
            "x-api-key": f"{self.client_id}:{self.get_password('client_secret')}",
            "Authorization": f"Bearer {self.get_password('access_token')}",
        }
	
	### private
	# Token
	def token_exists(self) -> bool:
		return bool(self.get_password("access_token", False))
	
	def token_expires_in(self) -> int:
		system_timezone = pytz.timezone(get_system_timezone())
		modified = frappe.utils.get_datetime(self.expires_in_datetime)
		modified = system_timezone.localize(modified)
		expiry_utc = modified.astimezone(pytz.utc)
		now_utc = datetime.datetime.now(pytz.utc)
		return cint((expiry_utc - now_utc).total_seconds())  # why do comp. in UTC?
	
	def token_expired(self) -> bool:
		return self.token_expires_in() < 0
	
	def update_expires_in(self, seconds:int):
		self.expires_in = seconds
		self.expires_in_datetime = frappe.utils.add_to_date(
			datetime.datetime.now(pytz.timezone(get_system_timezone())),
			seconds=seconds,
			as_string=True,
			as_datetime=True
		)
	
	def token_update(self, data:dict):
		"""
		Store data returned by authorization flow.

		Params:
		data - Dict with access_token, refresh_token, expires_in and scope.
		"""
		self.access_token = cstr(data.get("access_token", ""))
		self.refresh_token = cstr(data.get("refresh_token"))
		self.token_type = cstr(data.get("token_type", ""))
		self.update_expires_in(cint(data.get("expires_in", 0)))

		self.token_state = None
		self.save(ignore_permissions=True)
		frappe.db.commit()

		try:
			me = EtsyAPI(self).getMe()
		except Exception:
			frappe.log_error("Etsy: Failed to verify connection for shop {0}".format(self.name))
			self.status = "Disconnected"
		else:
			self.status = "Connected"
			self.user_id = cstr(me.user_id)
			self.shop_id = cstr(me.shop_id)
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	def token_json(self) -> dict:
		return {
			"access_token": self.get_password("access_token", False),
			"refresh_token": self.get_password("refresh_token", False),
			"expires_in": self.token_expires_in(),
			"token_type": self.token_type,
		}
	
	# OAuth
	def get_oauth2_session(self, init=False) -> OAuth2Session:
		"""Return an auto-refreshing OAuth2 session which is an extension of a requests.Session()"""
		token = None
		token_updater = None
		auto_refresh_kwargs = None

		if not init:
			token = self.token_json()
			token_updater = self.token_update
			auto_refresh_kwargs = {"client_id": self.client_id}
			client_secret = self.get_password("client_secret")
			if client_secret:
				auto_refresh_kwargs["client_secret"] = client_secret

		return OAuth2Session(
			client_id=self.client_id,
			token=token,
			token_updater=token_updater,
			auto_refresh_url=TOKEN_URI,
			auto_refresh_kwargs=auto_refresh_kwargs,
			redirect_uri=self.redirect_uri,
			scope=SCOPES,
		)
	
	def generate_code_verifier(self) -> str:
		self.code_verifier = secrets.token_urlsafe(48)
		self.save()
		return self.code_verifier
	
	def generate_code_challenge(self) -> str:
		m = hashlib.sha256(self.code_verifier.encode("utf-8"))
		b64_encode = base64.urlsafe_b64encode(m.digest()).decode("utf-8")
		# per https://docs.python.org/3/library/base64.html, there may be a trailing '=' - get rid of it
		return b64_encode.split("=")[0]

	@frappe.whitelist()
	def initiate_web_application_flow(self) -> str:
		if not self.client_id:
			frappe.throw(_("CLIENT_ID is mandatory!"))
		if not self.client_secret:
			frappe.throw(_("CLIENT_SECRET is mandatory!"))
		
		self.generate_code_verifier()
		code_challenge = self.generate_code_challenge()

		oauth = self.get_oauth2_session(init=True)
		authorization_url, state = oauth.authorization_url(
			AUTHORIZATION_URI,
			code_challenge=code_challenge,
			code_challenge_method="S256",
			**QUERY_PARAMS
		)

		self.token_state = state
		self.save(ignore_permissions=True)
		frappe.db.commit()

		return authorization_url

	@frappe.whitelist()
	def disconnect_etsy_shop(self):
		self.user_id = None
		self.shop_id = None
		self.access_token = None
		self.refresh_token = None
		self.expires_in = 0
		self.token_type = None
		self.token_state = None
		self.status = "Disconnected"
		self.save(ignore_permissions=True)
		frappe.db.commit()
	
	### Etsy Shop data import methods ###
	@frappe.whitelist()
	def enqueue_import_listings(self, listing_state:str="active", include_attributes:int=1, include_items:int=0):
		"""Enqueue listing import as a background job to avoid request timeouts."""
		frappe.enqueue(
			"etsy.etsy.doctype.etsy_shop.etsy_shop.run_import_listings",
			queue="long",
			timeout=3600,
			enqueue_after_commit=True,
			user=frappe.session.user,
			etsy_shop=self.name,
			listing_state=listing_state,
			include_attributes=include_attributes,
			include_items=include_items,
		)

	@frappe.whitelist()
	def enqueue_import_receipts(self, min_date:Optional[str]=None, max_date:Optional[str]=None):
		"""Enqueue receipt import as a background job to avoid request timeouts."""
		frappe.enqueue(
			"etsy.etsy.doctype.etsy_shop.etsy_shop.run_import_receipts",
			queue="long",
			timeout=3600,
			enqueue_after_commit=True,
			user=frappe.session.user,
			etsy_shop=self.name,
			min_date=min_date,
			max_date=max_date,
		)

	def import_listings(self, listing_state:str="active", include_attributes:int=1, include_items:int=0, etsy_api:Optional[EtsyAPI]=None):
		api = etsy_api or EtsyAPI(self)

		if listing_state == "all":
			for state in LISTING_STATES:
				self.import_listings(listing_state=state, include_attributes=include_attributes, include_items=include_items, etsy_api=api)
			return

		if listing_state not in LISTING_STATES:
			frappe.throw(_("'listing_state' must be one of: {0}").format(LISTING_STATES))

		for listing in fetch_all(lambda o: api.getListingsByShop(QP_getListingsByShop(
			shop_id=self.shop_id,
			state=listing_state,
			limit=100,
			offset=o,
			includes=['Inventory', 'Images'],
		))):
			try:
				### Etsy Listing
				if frappe.db.exists("Etsy Listing", cstr(listing.listing_id)):
					etsy_listing = frappe.get_doc("Etsy Listing", cstr(listing.listing_id))
				else:
					etsy_listing = frappe.new_doc("Etsy Listing")
					etsy_listing.listing_id = cstr(listing.listing_id)
					etsy_listing.etsy_shop = self.name
					# Etsy Listing Settings
					etsy_listing.item_name = short_title(listing.title)
					etsy_listing.item_group = self.item_group or frappe.defaults.get_global_default("item_group")
					etsy_listing.stock_uom = self.stock_uom or frappe.defaults.get_global_default("stock_uom")
					etsy_listing.is_stock_item = 1 - int(listing.listing_type is ListingType.DOWNLOAD)

				etsy_listing.status = listing_state.replace("_", " ").title()
				etsy_listing.views = listing.views
				etsy_listing.likes = listing.num_favorers

				etsy_listing.title = listing.title
				etsy_listing.description = listing.description
				etsy_listing.inventory = str(listing.inventory)

				if listing.images:
					etsy_listing.image = listing.images[0].get("url_170x135")

				etsy_listing.flags.ignore_mandatory = True
				etsy_listing.save()

				if int(include_items):
					etsy_listing.update_items(listing)  # create items and attributes
				elif int(include_attributes):
					etsy_listing.update_attributes(listing)  # just create attributes

				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error("Etsy: Failed to import listing {0}".format(listing.listing_id))

	def import_receipts(self, min_date:Optional[str]=None, max_date:Optional[str]=None, abort_on_exist:bool=False):
		api = EtsyAPI(self)

		for receipt in fetch_all(lambda o: api.getShopReceipts(QP_getShopReceipts(
			shop_id = self.shop_id,
			min_created=int(frappe.utils.get_datetime(f"{min_date} 00:00:00").timestamp()) if min_date else None,
			max_created=int(frappe.utils.get_datetime(f"{max_date} 23:59:59").timestamp()) if max_date else None,
			limit=100,
			offset=o,
		))):
			if frappe.db.exists("Sales Order", {"etsy_order_id": receipt.receipt_id}):
				if abort_on_exist:
					break
				else:
					continue

			try:
				### Customer
				if customer_name := frappe.db.exists("Customer", {"etsy_customer_id": receipt.buyer_user_id}):
					customer = frappe.get_doc("Customer", customer_name)
				else:
					customer = frappe.new_doc("Customer")
					if naming_series := self.customer_naming_series:
						customer.naming_series = str(naming_series).replace("{ETSY_BUYER_ID}", str(receipt.buyer_user_id))
					customer.etsy_customer_id = receipt.buyer_user_id

				customer.customer_name = receipt.name
				customer.customer_type = "Individual"
				customer.customer_group = (self.customer_group or frappe.defaults.get_global_default("customer_group"))

				customer.flags.ignore_mandatory = True
				customer.save()

				### Address
				if address_name := frappe.db.exists("Address", f"{customer.name}-Billing"):
					address = frappe.get_doc("Address", address_name)
				else:
					address = frappe.new_doc("Address")

				address.address_title = customer.name
				address.address_type = "Billing"
				address.address_line1 = receipt.first_line
				address.address_line2 = receipt.second_line
				address.city = receipt.city
				address.state = receipt.state
				address.pincode = receipt.zip
				address.country = frappe.db.get_value("Country", {"code": receipt.country_iso.lower()})
				address.email_id = receipt.buyer_email
				address.is_primary_address = 1
				address.is_shipping_address = 1

				address.append("links", {"link_doctype": "Customer", "link_name": customer.name})

				address.flags.ignore_mandatory = True
				address.save()

				### Contact - makes no sense without email address
				if receipt.buyer_email:
					if contact_name := frappe.db.exists("Contact", {"etsy_customer_id": receipt.buyer_user_id}):
						contact = frappe.get_doc("Contact", contact_name)
					else:
						contact = frappe.new_doc("Contact")
						contact.etsy_customer_id = receipt.buyer_user_id

					contact.first_name = receipt.name.split(" ", 1)[0]
					contact.last_name = receipt.name.split(" ", 1)[-1]
					contact.email_id = receipt.buyer_email
					contact.add_email(receipt.buyer_email, is_primary=1)
					contact.is_primary_contact = 1
					contact.is_billing_contact = 1

					contact.append("links", {"link_doctype": "Customer", "link_name": customer.name})

					contact.flags.ignore_mandatory = True
					contact.save()

					# update customer - only if contact is created
					customer.customer_primary_address = address.name
					customer.customer_primary_contact = contact.name
					customer.save()

				### Sales Order
				sales_order: Document = frappe.new_doc("Sales Order")
				if naming_series := self.sales_order_naming_series:
					sales_order.naming_series = str(naming_series).replace("{ETSY_ORDER_ID}", str(receipt.receipt_id))
				sales_order.etsy_order_id = sales_order.po_no = receipt.receipt_id
				sales_order.customer = customer
				sales_order.company = self.company

				sales_order.transaction_date = sales_order.po_date = receipt.created_timestamp.date()
				sales_order.delivery_date = max([t.expected_ship_date.date() for t in receipt.transactions if t.expected_ship_date] + [receipt.create_timestamp.date()])

				# Items
				for transaction in receipt.transactions:
					if item_name := frappe.db.exists("Item", {"etsy_product_id": transaction.product_id}):
						item = frappe.get_doc("Item", item_name)
					else:
						item = frappe.new_doc("Item")
						item.item_code = f"{transaction.product_id}"
						item.etsy_product_id = cstr(transaction.product_id)
						item.item_name = short_title(transaction.title)
						item.item_group = self.item_group or frappe.defaults.get_global_default("item_group")
						item.stock_uom = self.stock_uom or frappe.defaults.get_global_default("stock_uom")
						item.is_stock_item = 1 - int(transaction.is_digital)
						item.image = api.rest.getListingImage(api.client, transaction.listing_id, transaction.listing_image_id).json().get("url_170x135")
						item.flags.ignore_mandatory = True
						item.save()

					sales_order_item = {
						"item_code": item.name,
						"item_name": item.item_name,
						"delivery_date": transaction.expected_ship_date.date() if transaction.expected_ship_date else sales_order.delivery_date,
						"uom": item.stock_uom,
						"qty": transaction.quantity,
						"rate": transaction.price.as_float(),
						"description": "".join([f"<b>{v.formatted_name}:</b> {v.formatted_value}<br>" for v in transaction.variations]),
					}
					# Cost Center
					cost_center = self.cost_center_digital if transaction.is_digital else self.cost_center_physical
					if cost_center:
						sales_order_item["cost_center"] = cost_center
					
					sales_order.append("items", sales_order_item)

				# Tax and Shipping
				if receipt.total_tax_cost.as_float() > 0.0:
					sales_order.append(
						"taxes",
						{
							"charge_type": "Actual",
							"account_head": self.sales_tax_account,
							"tax_amount": receipt.total_tax_cost.as_float(),
							"description": "Sales Tax Total",
						},
					)
				sales_order.append(
					"taxes",
					{
						"charge_type": "Actual",
						"account_head": self.shipping_tax_account,
						"tax_amount": receipt.total_shipping_cost.as_float(),
						"description": "Shipping Cost Total",
					},
				)

				sales_order.flags.ignore_mandatory = True
				sales_order.insert(ignore_permissions=True)
				sales_order.submit()

				### Sales Invoice
				sales_invoice: Document = make_sales_invoice(sales_order.name)
				if naming_series := self.sales_invoice_naming_series:
					sales_invoice.naming_series = str(naming_series).replace("{ETSY_ORDER_ID}", str(receipt.receipt_id))
				sales_invoice.etsy_order_id = receipt.receipt_id
				sales_invoice.set_posting_time = 1
				sales_invoice.posting_date = receipt.created_timestamp.date()
				sales_invoice.due_date = receipt.created_timestamp.date()
				sales_invoice.insert(ignore_permissions=True)
				sales_invoice.submit()

				### Payment
				if receipt.is_paid:
					payment_entry: Document = get_payment_entry(sales_invoice.doctype, sales_invoice.name, bank_account=self.bank_account)
					payment_entry.reference_no = sales_invoice.name
					payment_entry.posting_date = receipt.created_timestamp.date()
					payment_entry.reference_date = receipt.created_timestamp.date()
					payment_entry.insert(ignore_permissions=True)
					payment_entry.submit()

					# close Sales Order if is_shipped or everything is_digital
					if receipt.is_shipped or all([t.is_digital for t in receipt.transactions]):
						close_or_unclose_sales_orders(f'["{sales_order.name}"]', "Closed")

				frappe.db.commit()
			except Exception:
				frappe.db.rollback()
				frappe.log_error("Etsy: Failed to import receipt {0}".format(receipt.receipt_id))


### background job entry points for enqueued imports
def run_import_listings(user, etsy_shop, listing_state="active", include_attributes=1, include_items=0):
	shop:EtsyShop = frappe.get_doc("Etsy Shop", etsy_shop)
	shop.import_listings(listing_state=listing_state, include_attributes=include_attributes, include_items=include_items)
	frappe.publish_realtime(
		"msgprint",
		{"message": _("Etsy listing import completed for {0}.").format(etsy_shop), "indicator": "green", "alert": True},
		user=user,
	)

def run_import_receipts(user, etsy_shop, min_date=None, max_date=None):
	shop:EtsyShop = frappe.get_doc("Etsy Shop", etsy_shop)
	shop.import_receipts(min_date=min_date, max_date=max_date)
	frappe.publish_realtime(
		"msgprint",
		{"message": _("Etsy sales import completed for {0}.").format(etsy_shop), "indicator": "green", "alert": True},
		user=user,
	)


### public functions
@frappe.whitelist(methods=["GET"], allow_guest=True)
def callback(code=None, state=None):
	"""
	Handle client's code.

	Called during the oauthorization flow by the remote oAuth2 server to transmit
	a code that can be used by the local server to obtain an access token.
	"""
	if frappe.session.user == "Guest":
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = "/login?" + urlencode({"redirect-to": frappe.request.url})
		return

	path = frappe.request.path[1:].split("/")
	if len(path) != 4 or not path[3]:
		frappe.throw(_("Invalid Parameters."))

	etsy_shop:EtsyShop = frappe.get_doc("Etsy Shop", unquote_plus(path[3]))

	if state != etsy_shop.token_state:
		frappe.throw(_("Invalid token state! Check if the token has been created by the OAuth flow."))

	oauth_session = etsy_shop.get_oauth2_session(init=True)
	token = oauth_session.fetch_token(
		TOKEN_URI,
		code=code,
		client_secret=etsy_shop.get_password("client_secret"),
		include_client_id=True,
		code_verifier=etsy_shop.code_verifier,
		**QUERY_PARAMS,
	)
	etsy_shop.token_update(token)

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = etsy_shop.get_url()

@frappe.whitelist()
def has_token(etsy_shop) -> bool:
	shop:EtsyShop = frappe.get_doc("Etsy Shop", etsy_shop)
	return shop.token_exists()