# Copyright (c) 2026, Cornstarch3D and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from etsy.etsy.doctype.etsy_listing.etsy_listing import EtsyListing
from etsy.datastruct import (
	Listing,
	Inventory,
	Product,
	Offering,
	Property,
	MonetaryAmount,
	CurrencyCode,
	ListingType,
)

# Reuse helpers from etsy_shop tests
from etsy.etsy.doctype.etsy_shop.test_etsy_shop import create_etsy_shop


def make_monetary_amount(amount=1000, divisor=100, currency="EUR"):
	return MonetaryAmount(amount=amount, divisor=divisor, currency_code=currency)


def make_offering(offering_id=1, quantity=10, is_enabled=True, is_deleted=False):
	return Offering(
		offering_id=offering_id,
		quantity=quantity,
		is_enabled=is_enabled,
		is_deleted=is_deleted,
		price=make_monetary_amount(),
		readiness_state_id=None,
	)


def make_property(property_id=100, property_name="Color", values=None):
	return Property(
		property_id=property_id,
		property_name=property_name,
		scale_id=None,
		scale_name=None,
		value_ids=[1],
		values=values or ["Red"],
	)


def make_product(product_id=5001, is_deleted=False, property_values=None, offerings=None):
	return Product(
		product_id=product_id,
		sku="TEST-SKU",
		is_deleted=is_deleted,
		offerings=offerings or [make_offering()],
		property_values=property_values or [],
	)


def make_inventory(products=None):
	return Inventory(
		products=products or [make_product()],
		price_on_property=[],
		quantity_on_property=[],
		sku_on_property=[],
		readiness_state_on_property=[],
		listing=None,
	)


def make_listing(listing_id=12345, has_variations=False, state="active", products=None, images=None):
	"""Create a Listing data structure for testing."""
	if products is None:
		products = [make_product()]

	return Listing(
		listing_id=listing_id,
		user_id=1,
		shop_id=1,
		title="Test Listing Title",
		description="A test listing description",
		state=state,
		creation_timestamp=1700000000,
		created_timestamp=1700000000,
		ending_timestamp=1700000000,
		original_creation_timestamp=1700000000,
		last_modified_timestamp=1700000000,
		updated_timestamp=1700000000,
		state_timestamp=1700000000,
		quantity=10,
		shop_section_id=None,
		featured_rank=1,
		url="https://www.etsy.com/listing/12345",
		num_favorers=5,
		non_taxable=False,
		is_taxable=True,
		is_customizable=False,
		is_personalizable=False,
		personalization_is_required=False,
		personalization_char_count_max=None,
		personalization_instructions=None,
		listing_type=ListingType.PHYSICAL,
		tags=[],
		materials=[],
		shipping_profile_id=None,
		return_policy_id=None,
		processing_min=None,
		processing_max=None,
		who_made=None,
		when_made=None,
		is_supply=None,
		item_weight=None,
		item_weight_unit=None,
		item_length=None,
		item_width=None,
		item_height=None,
		item_dimensions_unit=None,
		is_private=False,
		style=[],
		file_data=None,
		has_variations=has_variations,
		should_auto_renew=False,
		language=None,
		price=make_monetary_amount(),
		taxonomy_id=None,
		readiness_state_id=None,
		suggested_title=None,
		shipping_profile=None,
		user=None,
		shop=None,
		images=images or [{"url_170x135": "https://example.com/image.jpg"}],
		videos=None,
		inventory=make_inventory(products),
		production_partners=[],
		skus=[],
		translations=None,
		views=100,
	)


def create_etsy_listing(listing_id=None, etsy_shop=None):
	"""Create an Etsy Listing document for testing."""
	if not etsy_shop:
		shop = create_etsy_shop()
		etsy_shop = shop.name

	item_group = frappe.db.get_value("Item Group", {"is_group": 0})
	uom = frappe.db.get_value("UOM", {})

	doc = frappe.get_doc({
		"doctype": "Etsy Listing",
		"listing_id": listing_id or str(frappe.generate_hash(length=8)),
		"etsy_shop": etsy_shop,
		"item_name": "Test Item",
		"item_group": item_group,
		"stock_uom": uom,
		"is_stock_item": 1,
		"title": "Test Listing",
		"status": "Active",
	})
	doc.flags.ignore_mandatory = True
	doc.insert(ignore_if_duplicate=True)
	return doc


class TestEtsyListing(FrappeTestCase):
	def setUp(self):
		self.shop = create_etsy_shop()
		self.listing = create_etsy_listing(etsy_shop=self.shop.name)

	def tearDown(self):
		# Clean up items created during tests
		for item in frappe.get_all("Item", filters={"etsy_listing": self.listing.name}):
			frappe.delete_doc("Item", item.name, force=True)
		for attr in frappe.get_all("Item Attribute", filters={"etsy_listing": self.listing.name}):
			frappe.delete_doc("Item Attribute", attr.name, force=True)
		frappe.delete_doc("Etsy Listing", self.listing.name, force=True)
		frappe.delete_doc("Etsy Shop", self.shop.name, force=True)
		frappe.db.commit()

	def test_creation(self):
		"""Etsy Listing can be created with required fields."""
		self.assertTrue(frappe.db.exists("Etsy Listing", self.listing.name))

	def test_listing_id_is_unique(self):
		"""Duplicate listing_id raises an error."""
		self.assertRaises(
			frappe.DuplicateEntryError,
			create_etsy_listing,
			listing_id=self.listing.listing_id,
			etsy_shop=self.shop.name,
		)

	def test_listing_linked_to_shop(self):
		"""Etsy Listing is linked to an Etsy Shop."""
		self.assertEqual(self.listing.etsy_shop, self.shop.name)

	def test_get_attribute_creates_new(self):
		"""get_attribute creates a new Item Attribute when none exists."""
		prop = make_property(property_id=999, property_name="Size")
		listing = make_listing(listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999)

		attribute = self.listing.get_attribute(prop, listing)
		self.assertTrue(attribute.is_new())
		self.assertIn("Size", attribute.attribute_name)
		self.assertEqual(attribute.etsy_property_id, 999)

	def test_get_attribute_returns_existing(self):
		"""get_attribute returns an existing Item Attribute if it matches."""
		prop = make_property(property_id=888, property_name="Material")
		listing = make_listing(listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999)

		# Create the attribute first
		attr = self.listing.get_attribute(prop, listing)
		attr.attribute_name = f"Material-{listing.listing_id}"
		attr.etsy_listing = self.listing.name
		attr.etsy_property_id = 888
		attr.save()

		# Should return the same one
		attr2 = self.listing.get_attribute(prop, listing)
		self.assertFalse(attr2.is_new())
		self.assertEqual(attr.name, attr2.name)

	def test_update_attributes(self):
		"""update_attributes creates Item Attributes from listing properties."""
		prop_color = make_property(property_id=200, property_name="Color", values=["Red"])
		product1 = make_product(product_id=6001, property_values=[prop_color])

		prop_color2 = make_property(property_id=200, property_name="Color", values=["Blue"])
		product2 = make_product(product_id=6002, property_values=[prop_color2])

		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=True,
			products=[product1, product2],
		)

		self.listing.update_attributes(listing)

		# Should have created an attribute with both values
		attrs = frappe.get_all(
			"Item Attribute",
			filters={"etsy_listing": self.listing.name, "etsy_property_id": "200"},
		)
		self.assertEqual(len(attrs), 1)

		attr = frappe.get_doc("Item Attribute", attrs[0].name)
		values = [v.attribute_value for v in attr.item_attribute_values]
		self.assertIn("Red", values)
		self.assertIn("Blue", values)

	def test_update_attributes_no_duplicates(self):
		"""update_attributes does not add duplicate attribute values."""
		prop = make_property(property_id=300, property_name="Size", values=["Large"])
		product1 = make_product(product_id=7001, property_values=[prop])
		product2 = make_product(product_id=7002, property_values=[prop])

		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=True,
			products=[product1, product2],
		)

		self.listing.update_attributes(listing)

		attrs = frappe.get_all(
			"Item Attribute",
			filters={"etsy_listing": self.listing.name, "etsy_property_id": "300"},
		)
		attr = frappe.get_doc("Item Attribute", attrs[0].name)
		values = [v.attribute_value for v in attr.item_attribute_values]
		# "Large" should appear only once despite two products having it
		self.assertEqual(values.count("Large"), 1)

	def test_update_attributes_abbreviation(self):
		"""Attribute values are abbreviated to 28 characters max."""
		long_value = "A" * 50
		prop = make_property(property_id=400, property_name="Description", values=[long_value])
		product = make_product(product_id=8001, property_values=[prop])

		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=True,
			products=[product],
		)

		self.listing.update_attributes(listing)

		attrs = frappe.get_all(
			"Item Attribute",
			filters={"etsy_listing": self.listing.name, "etsy_property_id": "400"},
		)
		attr = frappe.get_doc("Item Attribute", attrs[0].name)
		for val in attr.item_attribute_values:
			self.assertLessEqual(len(val.abbr), 28)

	def test_update_items_no_variations(self):
		"""update_items creates a single item for listings without variations."""
		product = make_product(product_id=9001)
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			products=[product],
		)

		self.listing.update_items(listing)

		item = frappe.get_doc("Item", {"etsy_product_id": "9001"})
		self.assertEqual(item.etsy_listing, self.listing.name)
		self.assertEqual(item.item_name, self.listing.item_name)
		self.assertEqual(item.item_group, self.listing.item_group)
		self.assertEqual(item.stock_uom, self.listing.stock_uom)
		self.assertEqual(item.is_stock_item, self.listing.is_stock_item)
		self.assertFalse(item.disabled)

	def test_update_items_inactive_listing_disables_item(self):
		"""Items from inactive listings should be disabled."""
		product = make_product(product_id=9002)
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			state="inactive",
			products=[product],
		)

		self.listing.update_items(listing)

		item = frappe.get_doc("Item", {"etsy_product_id": "9002"})
		self.assertTrue(item.disabled)

	def test_update_items_deleted_product_disables_item(self):
		"""Items from deleted products should be disabled."""
		product = make_product(product_id=9003, is_deleted=True)
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			state="active",
			products=[product],
		)

		self.listing.update_items(listing)

		item = frappe.get_doc("Item", {"etsy_product_id": "9003"})
		self.assertTrue(item.disabled)

	def test_update_items_deleted_offering_disables_item(self):
		"""Items with deleted offerings should be disabled."""
		offering = make_offering(is_deleted=True)
		product = make_product(product_id=9004, offerings=[offering])
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			state="active",
			products=[product],
		)

		self.listing.update_items(listing)

		item = frappe.get_doc("Item", {"etsy_product_id": "9004"})
		self.assertTrue(item.disabled)

	def test_update_items_disabled_offering_disables_item(self):
		"""Items with disabled offerings should be disabled."""
		offering = make_offering(is_enabled=False)
		product = make_product(product_id=9005, offerings=[offering])
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			state="active",
			products=[product],
		)

		self.listing.update_items(listing)

		item = frappe.get_doc("Item", {"etsy_product_id": "9005"})
		self.assertTrue(item.disabled)

	def test_update_items_sets_image(self):
		"""update_items sets the item image from listing images."""
		product = make_product(product_id=9006)
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			products=[product],
			images=[{"url_170x135": "https://example.com/test-image.jpg"}],
		)

		self.listing.update_items(listing)

		item = frappe.get_doc("Item", {"etsy_product_id": "9006"})
		self.assertEqual(item.image, "https://example.com/test-image.jpg")

	def test_update_items_with_variations_creates_template_and_variants(self):
		"""update_items creates an item template and variants for listings with variations."""
		prop_color1 = make_property(property_id=500, property_name="Color", values=["Red"])
		prop_color2 = make_property(property_id=500, property_name="Color", values=["Blue"])

		product1 = make_product(product_id=10001, property_values=[prop_color1])
		product2 = make_product(product_id=10002, property_values=[prop_color2])

		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=True,
			products=[product1, product2],
		)

		self.listing.update_items(listing)

		# Template item should exist
		template_code = f"T{listing.listing_id}"
		self.assertTrue(frappe.db.exists("Item", {"item_code": template_code}))
		template = frappe.get_doc("Item", {"item_code": template_code})
		self.assertTrue(template.has_variants)
		self.assertIn("[", template.item_name)
		self.assertIn("]", template.item_name)

		# Variant items should exist
		variant1 = frappe.get_doc("Item", {"etsy_product_id": "10001"})
		self.assertEqual(variant1.variant_of, template.name)

		variant2 = frappe.get_doc("Item", {"etsy_product_id": "10002"})
		self.assertEqual(variant2.variant_of, template.name)

	def test_update_items_no_images(self):
		"""update_items handles listings with empty images list."""
		product = make_product(product_id=9007)
		listing = make_listing(
			listing_id=int(self.listing.listing_id) if self.listing.listing_id.isdigit() else 99999,
			has_variations=False,
			products=[product],
			images=[],
		)

		# Should not raise
		self.listing.update_items(listing)
		item = frappe.get_doc("Item", {"etsy_product_id": "9007"})
		self.assertEqual(item.etsy_listing, self.listing.name)
