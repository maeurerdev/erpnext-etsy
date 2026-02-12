from __future__ import annotations
from typing import Optional, Tuple, List, Callable, Iterator, TypeVar, TYPE_CHECKING
T = TypeVar('T')

import time
import frappe
import frappe.defaults
from frappe.utils import cstr

from httpx import Response
from hishel.httpx import SyncCacheClient
from pydantic import BaseModel, field_validator
from .datastruct import Me, User, Address, ShopReceipt, Payment, LedgerEntry, Listing

if TYPE_CHECKING:
    from .etsy.doctype.etsy_shop.etsy_shop import EtsyShop



### Helper functions
def fetch_all(
        fetch_func: Callable[[int], Tuple[int, List[T]]],
        start_offset: int = 0
    ) -> Iterator[T]:
    """
    ### Usage example:
    `for x in fetch_all(lambda offset: getXYZ(offset=offset, params=...)):`
    """
    offset:int = start_offset
    total: Optional[int] = None
    seen:int = 0

    while True:
        total_count, page = fetch_func(offset)
        
        if total is None:
            total = total_count
            
        if not page:
            return
            
        for item in page:
            yield item
            seen += 1
            
        if seen >= total:
            return
            
        offset += len(page)
        time.sleep(0.25)  # limit querys/sec


### Query Parameter Classes

class QP_getShopReceipts(BaseModel):
    """
    ### Query Parameters for getShopReceipts()
    ### required params:
    - shop_id: The unique positive non-zero numeric ID for an Etsy Shop.
    ### optional params:
    - min_created: The earliest unix timestamp for when a record was created. `>= 946684800`
    - max_created: The latest unix timestamp for when a record was created. `>= 946684800`
    - min_last_modified: The earliest unix timestamp for when a record last changed. `>= 946684800`
    - max_last_modified: The latest unix timestamp for when a record last changed. `>= 946684800`
    - limit: The maximum number of results to return. `[ 1 .. 100 ]`
    - offset: The number of records to skip before selecting the first result. `>= 0`
    - sort_on: The value to sort a search result of listings on. Enum: `created` `updated` `receipt_id`
    - sort_order: The ascending(up) or descending(down) order to sort receipts by. Enum: `asc` `ascending` `desc` `descending` `up` `down`
    - was_paid: When true, returns receipts where the seller has recieved payment for the receipt. When false, returns receipts where payment has not been received. `Nullable`
    - was_shipped: When true, returns receipts where the seller shipped the product(s) in this receipt. When false, returns receipts where shipment has not been set. `Nullable`
    - was_delivered: When true, returns receipts that have been marked as delivered. When false, returns receipts where shipment has not been marked as delivered. `Nullable`
    - was_canceled: When true, the endpoint will only return the canceled receipts. When false, the endpoint will only return non-canceled receipts. `Nullable`
    """
    shop_id: int
    min_created: Optional[int] = None
    max_created: Optional[int] = None
    min_last_modified: Optional[int] = None
    max_last_modified: Optional[int] = None
    limit: int = 25
    offset: int = 0
    sort_on: str = "created"
    sort_order: str = "desc"
    was_paid: Optional[bool] = None
    was_shipped: Optional[bool] = None
    was_delivered: Optional[bool] = None
    was_canceled: Optional[bool] = None

    @field_validator(
        'min_created',
        'max_created',
        'min_last_modified',
        'max_last_modified',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, int) and v < 946684800:
            raise ValueError("Timestamp must be greater or equal to 946684800")
        return v

    @field_validator('limit')
    @classmethod
    def check_limit(cls, v):
        if isinstance(v, int) and not (1 <= v <= 100):
            raise ValueError("'limit' must be between 1 and 100")
        return v

    @field_validator('sort_on')
    @classmethod
    def check_sort_on(cls, v):
        allowed_values = ("created", "updated", "receipt_id")
        if isinstance(v, str) and v not in allowed_values:
            raise ValueError(f"'sort_on' must be one of: {allowed_values}")
        return v

    @field_validator('sort_order')
    @classmethod
    def check_sort_order(cls, v):
        allowed_values = ("asc", "ascending", "desc", "descending", "up", "down")
        if isinstance(v, str) and v not in allowed_values:
            raise ValueError(f"'sort_order' must be one of: {allowed_values}")
        return v

class QP_getShopPaymentAccountLedgerEntries(BaseModel):
    """
    ### Query Parameters for getShopPaymentAccountLedgerEntries()
    ### required params:
    - shop_id: The unique positive non-zero numeric ID for an Etsy Shop.
    - min_created: The earliest unix timestamp for when a record was created. `>= 946684800`
    - max_created: The latest unix timestamp for when a record was created. `>= 946684800`
    ### optional params:
    - limit: The maximum number of results to return. `[ 1 .. 100 ]`
    - offset: The number of records to skip before selecting the first result. `>= 0`
    """
    shop_id: int
    min_created: int
    max_created: int
    limit: int = 25
    offset: int = 0

    @field_validator(
        'min_created',
        'max_created',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, int) and v < 946684800:
            raise ValueError("Timestamp must be greater or equal to 946684800")
        return v

    @field_validator('limit')
    @classmethod
    def check_limit(cls, v):
        if isinstance(v, int) and not (1 <= v <= 100):
            raise ValueError("'limit' must be between 1 and 100")
        return v

class QP_getListingsByShop(BaseModel):
    """
    ### Query Parameters for getListingsByShop()
    ### required params:
    - shop_id: The unique positive non-zero numeric ID for an Etsy Shop.
    ### optional params:
    - state: Default: "active" Enum: "active" "inactive" "sold_out" "draft" "expired" When updating a listing, this value can be either active or inactive. Note: Setting a draft listing to active will also publish the listing on etsy.com and requires that the listing have an image set. Setting a sold_out listing to active will update the quantity to 1 and renew the listing on etsy.com.
    - limit: The maximum number of results to return. `[ 1 .. 100 ]`
    - offset: The number of records to skip before selecting the first result. `>= 0`
    - sort_on: Default: "created" Enum: "created" "price" "updated" "score" The value to sort a search result of listings on. NOTES: a) sort_on only works when combined with one of the search options (keywords, region, etc.). b) when using score the returned results will always be in descending order, regardless of the sort_order parameter.
    - sort_order: Default: "desc" Enum: "asc" "ascending" "desc" "descending" "up" "down" The ascending(up) or descending(down) order to sort listings by. NOTE: sort_order only works when combined with one of the search options (keywords, region, etc.).
    - includes: Default: null Items Enum: "Shipping" "Images" "Shop" "User" "Translations" "Inventory" "Videos" An enumerated string that attaches a valid association. Acceptable inputs are 'Shipping', 'Shop', 'Images', 'User', 'Translations' and 'Inventory'.
    """
    shop_id: int
    state: str = "active"
    limit: int = 25
    offset: int = 0
    sort_on: str = "created"
    sort_order: str = "desc"
    includes: Optional[str] = None

    @field_validator('state')
    @classmethod
    def check_state(cls, v):
        allowed_values = ("active", "inactive", "sold_out", "draft", "expired")
        if isinstance(v, str) and v not in allowed_values:
            raise ValueError(f"'state' must be one of: {allowed_values}")
        return v

    @field_validator('limit')
    @classmethod
    def check_limit(cls, v):
        if isinstance(v, int) and not (1 <= v <= 100):
            raise ValueError("'limit' must be between 1 and 100")
        return v

    @field_validator('sort_on')
    @classmethod
    def check_sort_on(cls, v):
        allowed_values = ("created", "price", "updated", "score")
        if isinstance(v, str) and v not in allowed_values:
            raise ValueError(f"'sort_on' must be one of: {allowed_values}")
        return v

    @field_validator('sort_order')
    @classmethod
    def check_sort_order(cls, v):
        allowed_values = ("asc", "ascending", "desc", "descending", "up", "down")
        if isinstance(v, str) and v not in allowed_values:
            raise ValueError(f"'sort_order' must be one of: {allowed_values}")
        return v

    @field_validator('includes', mode='before')
    @classmethod
    def check_includes(cls, v):
        allowed_values = ("Shipping", "Images", "Shop", "User", "Translations", "Inventory", "Videos")
        if isinstance(v, (Tuple, List)):
            for i in v:
                if isinstance(i, str) and i not in allowed_values:
                    raise ValueError(f"'includes' can only contain: {allowed_values}")
            return ",".join(v)
        elif isinstance(v, str) and v not in allowed_values:
            raise ValueError(f"'includes' can only contain: {allowed_values}")
        return v


### API Classes

class EtsyRESTv3:
    def __init__(self, auth_header:dict, language:str="de"):
        self.headers = auth_header
        self.language = language

    def args(self, endpoint:str, headers:Optional[dict]=None, params:Optional[dict]=None, extensions:Optional[dict]=None) -> dict:
        _url = "https://api.etsy.com/"
        _url += endpoint[1:] if endpoint.startswith("/") else endpoint

        _params = {k: v for k, v in params.items() if v is not None} if isinstance(params, dict) else {}
        _params["language"] = self.language 

        _headers = self.headers | headers if isinstance(headers, dict) else self.headers
        
        _extensions = {k: v for k, v in extensions.items() if v is not None} if isinstance(extensions, dict) else None
        
        return dict(url=_url, params=_params, headers=_headers, extensions=_extensions)
    
    def getMe(self, client:SyncCacheClient) -> Response:
        """Returns basic info for the user making the request."""
        return client.get(**self.args(
            endpoint="/v3/application/users/me"
        ))
    
    def getUser(self, client:SyncCacheClient, user_id:int) -> Response:
        """
        Retrieves a user profile based on a unique user ID.
        Access is limited to profiles of the authenticated user or linked buyers.
        For the primary_email field, specific app-based permissions are required and granted case-by-case.
        ### query params:
        - user_id: The numeric ID of a user.
        """
        return client.get(**self.args(
            endpoint=f"/v3/application/users/{user_id}"
        ))
    
    def getUserAddress(self, client:SyncCacheClient, user_address_id:int) -> Response:
        """
        Open API V3 endpoint to retrieve a UserAddress for a User.
        ### query params:
        - user_address_id: The numeric ID of the user's address.
        """
        return client.get(**self.args(
            endpoint=f"/v3/application/user/addresses/{user_address_id}"
        ))
    
    def getShopPaymentByReceiptId(self, client:SyncCacheClient, shop_id:int, receipt_id:int) -> Response:
        """
        Retrieves a payment from a specific receipt, identified by receipt_id, from a specific shop, identified by shop_id
        ### query params:
        - shop_id: The unique positive non-zero numeric ID for an Etsy Shop.
        - receipt_id: The numeric ID for the receipt associated to this transaction.
        """
        return client.get(**self.args(
            endpoint=f"/v3/application/shops/{shop_id}/receipts/{receipt_id}/payments"
        ))
    
    def getShopReceipts(self, client:SyncCacheClient, query_params:QP_getShopReceipts) -> Response:
        """Requests the Shop Receipts from a specific Shop, unfiltered or filtered by receipt id range or offset, date, paid, and/or shipped purchases."""
        return client.get(**self.args(
            endpoint=f"/v3/application/shops/{query_params.shop_id}/receipts",
            params=query_params.model_dump(exclude={"shop_id"}, exclude_unset=True)
        ))

    def getShopPaymentAccountLedgerEntries(self, client:SyncCacheClient, query_params:QP_getShopPaymentAccountLedgerEntries) -> Response:
        """Get a Shop Payment Account Ledger's Entries"""
        return client.get(**self.args(
            endpoint=f"/v3/application/shops/{query_params.shop_id}/payment-account/ledger-entries",
            params=query_params.model_dump(exclude={"shop_id"}, exclude_unset=True),
        ))
    
    def getListingsByShop(self, client:SyncCacheClient, query_params:QP_getListingsByShop) -> Response:
        """Endpoint to list Listings that belong to a Shop."""
        return client.get(**self.args(
            endpoint=f"/v3/application/shops/{query_params.shop_id}/listings",
            params=query_params.model_dump(exclude={"shop_id"}, exclude_unset=True),
        ))
    
    # utils
    def getListingImage(self, client:SyncCacheClient, listing_id:int, listing_image_id:int) -> Response:
        """
        Retrieves the references and metadata for a listing image with a specific image ID.
        ### query params:
        - listing_id: The numeric ID for the listing associated to this transaction.
        - listing_image_id: The numeric ID of the primary listing image for this transaction.
        """
        return client.get(**self.args(
            endpoint=f"/v3/application/listings/{listing_id}/images/{listing_image_id}",
            extensions={"force_cache": True},
        ))


class EtsyAPI:
    def __init__(self, etsy_shop:EtsyShop):
        language:str = (etsy_shop.language or frappe.defaults.get_global_default("language"))
        self.rest = EtsyRESTv3(etsy_shop.get_auth_header(), language=language.split("-")[0])
        self.client = SyncCacheClient()
    
    def getMe(self) -> Me:
        """Returns basic info for the user making the request."""
        resp = self.rest.getMe(self.client).json()
        return Me.model_validate(resp)
    
    def getUser(self, user_id:int) -> User:
        """
        Retrieves a user profile based on a unique user ID.
        Access is limited to profiles of the authenticated user or linked buyers.
        For the primary_email field, specific app-based permissions are required and granted case-by-case.
        ### query params:
        - user_id: The numeric ID of a user.
        """
        resp = self.rest.getUser(self.client, user_id).json()
        return User.model_validate(resp)

    def getUserAddress(self, user_address_id:int) -> Address:
        """
        Open API V3 endpoint to retrieve a UserAddress for a User.
        ### query params:
        - user_address_id: The numeric ID of the user's address.
        """
        resp = self.rest.getUserAddress(self.client, user_address_id).json()
        return Address.model_validate(resp)
    
    def getShopPaymentByReceiptId(self, shop_id:int, receipt_id:int) -> Tuple[int, List[Payment]]:
        """
        Retrieves a payment from a specific receipt, identified by receipt_id, from a specific shop, identified by shop_id
        ### query params:
        - shop_id: The unique positive non-zero numeric ID for an Etsy Shop.
        - receipt_id: The numeric ID for the receipt associated to this transaction.
        """
        resp = self.rest.getShopPaymentByReceiptId(self.client, shop_id, receipt_id).json()
        return (resp["count"], [Payment.model_validate(result) for result in resp["results"]])
    
    def getShopReceipts(self, query_params:QP_getShopReceipts) -> Tuple[int, List[ShopReceipt]]:
        """Requests the Shop Receipts from a specific Shop, unfiltered or filtered by receipt id range or offset, date, paid, and/or shipped purchases."""
        resp = self.rest.getShopReceipts(self.client, query_params).json()
        return (resp["count"], [ShopReceipt.model_validate(result) for result in resp["results"]])
    
    def getShopPaymentAccountLedgerEntries(self, query_params:QP_getShopPaymentAccountLedgerEntries) -> Tuple[int, List[LedgerEntry]]:
        """Get a Shop Payment Account Ledger's Entries"""
        resp = self.rest.getShopPaymentAccountLedgerEntries(self.client, query_params).json()
        return (resp["count"], [LedgerEntry.model_validate(result) for result in resp["results"]])
    
    def getListingsByShop(self, query_params:QP_getListingsByShop) -> Tuple[int, List[Listing]]:
        """Endpoint to list Listings that belong to a Shop."""
        resp = self.rest.getListingsByShop(self.client, query_params).json()
        return (resp["count"], [Listing.model_validate(result) for result in resp["results"]])


##########################################################################################################################################################


def synchronise_receipts():
    """This function will be regularly executed by the Scheduler to synchronise Sales Orders."""

    shop_list = frappe.get_all("Etsy Shop", fields=['name', 'status'])

    for shop in shop_list:
        if shop.status != "Connected": continue
        try:
            etsy_shop:EtsyShop = frappe.get_doc("Etsy Shop", shop.name)
            etsy_shop.import_receipts(abort_on_exist=True)
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(f"Etsy: Failed to sync receipts for shop {shop.name}")


def synchronise_listings():
    """This function will be regularly executed by the Scheduler to synchronise Items."""

    shop_list = frappe.get_all("Etsy Shop", fields=['name', 'status'])

    for shop in shop_list:
        if shop.status != "Connected": continue
        try:
            etsy_shop:EtsyShop = frappe.get_doc("Etsy Shop", shop.name)
            etsy_shop.import_listings()
            frappe.db.commit()
        except Exception:
            frappe.db.rollback()
            frappe.log_error(f"Etsy: Failed to sync listings for shop {shop.name}")