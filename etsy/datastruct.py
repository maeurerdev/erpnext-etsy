from __future__ import annotations
from typing import Optional, List, Tuple

from enum import Enum
from datetime import datetime
from pydantic import BaseModel, field_validator
from babel.numbers import format_currency



### Enums

class OrderStatus(Enum):
    PAID = "paid"
    COMPLETED = "completed"
    OPEN = "open"
    PAYMENT_PROCESSING = "payment processing"
    CANCELED = "canceled"
    FULLY_REFUNDED = "fully refunded"
    PARTIALLY_REFUNDED = "partially refunded"

class PaymentMethod(Enum):
    CC = "cc"  # credit card
    PAYPAL = "paypal"
    CHECK = "check"
    MO = "mo"  # money order
    BT = "bt"  # bank transfer
    OTHER = "other"
    IDEAL = "ideal"
    SOFORT = "sofort"
    APPLE_PAY = "apple_pay"
    GOOGLE = "google"
    ANDROID_PAY = "android_pay"
    GOOGLE_PAY = "google_pay"
    KLARNA = "klarna"
    K_PAY_IN_4 = "k_pay_in_4"
    K_PAY_IN_3 = "k_pay_in_3"
    K_FINANCING = "k_financing"

class CurrencyCode(Enum):
    EUR = "EUR"
    USD = "USD"
    GBP = "GBP"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    CHF = "CHF"
    CNY = "CNY"
    SEK = "SEK"
    NZD = "NZD"
    MXN = "MXN"
    SGD = "SGD"
    HKD = "HKD"
    NOK = "NOK"
    KRW = "KRW"

class ListingType(Enum):
    PHYSICAL = "physical"
    DOWNLOAD = "download"
    BOTH = "both"

class WhoMade(Enum):
    i_did = "i_did"
    someone_else = "someone_else"
    collective = "collective"

class WeightUnit(Enum):
    OZ = "oz"
    LB = "lb"
    G = "g"
    KG = "kg"

class DimensionsUnit(Enum):
    IN = "in"
    FT = "ft"
    MM = "mm"
    CM = "cm"
    M = "m"
    YD = "yd"
    INCHES = "inches"


### Data Classes

class Me(BaseModel):
    """
    ## Basic info for the user making the request.
    ### attributes:
    - user_id: `int >= 1` The numeric ID of a user. This number is also a valid shop ID for the user's shop.
    - shop_id: `int >= 1` The unique positive non-zero numeric ID for an Etsy Shop.
    """
    user_id: int
    shop_id: int

class User(BaseModel):
    """
    ## User Profile
    Access is limited to profiles of the authenticated user or linked buyers.
    For the `primary_email` field, specific app-based permissions are required and granted case-by-case.
    ### attributes:
    - user_id: `int >= 1` The numeric ID of a user. This number is also a valid shop ID for the user's shop.
    - primary_email: `str` An email address string for the user's primary email address.
    - first_name: `str` The user's first name.
    - last_name: `str` The user's last name.
    - image_url_75x75: `str` The user's avatar URL.
    """
    user_id: int
    primary_email: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    image_url_75x75: Optional[str]

class Address(BaseModel):
    """
    ## User Address
    Access is limited to addresses of the authenticated user or linked buyers.
    ### attributes:
    - user_address_id: `int >= 1` The numeric ID of the user's address.
    - user_id: `int >= 1` The user's numeric ID.
    - name: `str` The user's name for this address.
    - first_line: `str` The first line of the user's address.
    - second_line: `str` The second line of the user's address.
    - city: `str` The city field of the user's address.
    - state: `str` The state field of the user's address.
    - zip: `str` The zip code field of the user's address.
    - iso_country_code: `str` The ISO code of the country in this address.
    - country_name: `str` The name of the user's country.
    - is_default_shipping_address: `bool` Is this the user's default shipping address.
    """
    user_address_id: int
    user_id: int
    name: str
    first_line: str
    second_line: Optional[str]
    city: str
    state: Optional[str]
    zip: Optional[str]
    iso_country_code: Optional[str]
    country_name: Optional[str]
    is_default_shipping_address: bool

class MonetaryAmount(BaseModel):
    """
    ## Monetry amount
    ### attributes:
    - amount: `int` The amount of money represented as an integer.
    - divisor: `int` The divisor for the amount of money.
    - currency_code: `str` The ISO-4217 currency code.
    """
    amount: int
    divisor: int
    currency_code: CurrencyCode

    @field_validator('divisor')
    @classmethod
    def to_natural_number(cls, v):
        if isinstance(v, int):
            return max(1, v)
        else:
            return v
    
    @field_validator('currency_code', mode="before")
    @classmethod
    def to_upper(cls, v):
        if isinstance(v, str):
            return v.upper()
        else:
            return v
    
    @classmethod
    def zero(cls, currency_code:CurrencyCode=CurrencyCode.EUR) -> MonetaryAmount:
        return MonetaryAmount(amount=0, divisor=100, currency_code=currency_code)

    def as_float(self) -> float:
        return float(self.amount / self.divisor)
    
    def __compare(self, other:MonetaryAmount, op:str="compare") -> Tuple[int, int, int]:
        if self.currency_code != other.currency_code:
            raise ValueError(f"Cannot {op} monetary amounts with different currencies: {self.currency_code.value} and {other.currency_code.value}")
        divisor = max(self.divisor, other.divisor)
        corrected_self = self.amount * int(divisor / self.divisor)
        corrected_other = other.amount * int(divisor / other.divisor)
        return corrected_self, corrected_other, divisor
    
    def __str__(self) -> str:
        try:
            import frappe
            locale = frappe.local.lang or "en"
        except Exception:
            locale = "en"
        return format_currency(self.as_float(), self.currency_code.value, locale=locale)

    def __add__(self, other:MonetaryAmount) -> MonetaryAmount:
        corrected_self, corrected_other, divisor = self.__compare(other, "add")
        return MonetaryAmount(
            amount=corrected_self + corrected_other,
            divisor=divisor,
            currency_code=self.currency_code
        )
    
    def __sub__(self, other:MonetaryAmount) -> MonetaryAmount:
        corrected_self, corrected_other, divisor = self.__compare(other, "subtract")
        return MonetaryAmount(
            amount=corrected_self - corrected_other,
            divisor=divisor,
            currency_code=self.currency_code
        )
    
    def __mul__(self, other:int|float) -> MonetaryAmount:
        if not isinstance(other, (int, float)):
            raise TypeError("MonetaryAmount can only be multiplied by types int or float")
        return MonetaryAmount(
            amount=int(self.amount * other),
            divisor=self.divisor,
            currency_code=self.currency_code
        )

    def __rmul__(self, other:int|float) -> MonetaryAmount:
        return self.__mul__(other)
    
    def __eq__(self, other:MonetaryAmount) -> bool:
        corrected_self, corrected_other, _ = self.__compare(other)
        return corrected_self == corrected_other

    def __lt__(self, other:MonetaryAmount) -> bool:
        corrected_self, corrected_other, _ = self.__compare(other)
        return corrected_self < corrected_other
    
    def __le__(self, other:MonetaryAmount) -> bool:
        corrected_self, corrected_other, _ = self.__compare(other)
        return corrected_self <= corrected_other
    
    def __gt__(self, other:MonetaryAmount) -> bool:
        corrected_self, corrected_other, _ = self.__compare(other)
        return corrected_self > corrected_other
    
    def __ge__(self, other:MonetaryAmount) -> bool:
        corrected_self, corrected_other, _ = self.__compare(other)
        return corrected_self >= corrected_other

class ShipmentStatement(BaseModel):
    """
    ## Shipment statement for a Shop Receipt
    ### attributes:
    - receipt_shipping_id: `int` The unique numeric ID of a Shop Receipt Shipment record. `Nullable`
    - shipment_notification_timestamp: `int >= 946684800` The time at which Etsy notified the buyer of the shipment event, in epoch seconds.
    - carrier_name: `str` The name string for the carrier/company responsible for delivering the shipment.
    - tracking_code: `str` The tracking code string provided by the carrier/company for the shipment.
    """
    receipt_shipping_id: Optional[int]
    shipment_notification_timestamp: datetime
    carrier_name: str
    tracking_code: str

    @field_validator('shipment_notification_timestamp')
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v

class Variation(BaseModel):
    """
    ## Product variation for a Transaction
    ### attributes:
    - property_id: `int >= 1` The variation property ID.	
    - value_id: `int` The ID of the variation value selected. `Nullable`
    - formatted_name: `str` Formatted name of the variation.
    - formatted_value: `str` Value of the variation entered by the buyer.
    """
    property_id: int
    value_id: Optional[int]
    formatted_name: str
    formatted_value: str

class Property(BaseModel):
    """
    ## Product property value entry
    ### attributes:
    - property_id: `int >= 1` The numeric ID of the Property.	
    - property_name: `str` The name of the Property. `Nullable`
    - scale_id: `int >= 1` The numeric ID of the scale (if any). `Nullable`
    - scale_name: `str` The name of the scale (if any). `Nullable`
    - value_ids: `List[int]` The numeric IDs of the Property values
    - values: `List[str]` The Property values
    """
    property_id: int
    property_name: Optional[str]
    scale_id: Optional[int]
    scale_name: Optional[str]
    value_ids: List[int]
    values: List[str]

class Offering(BaseModel):
    """
    ## Offering for a Listing
    ### attributes:
    - offering_id: `int >= 1` The ID for the ProductOffering
    - quantity: `int >= 1` The quantity the ProductOffering
    - is_enabled: `bool` Whether or not the offering can be shown to buyers
    - is_deleted: `bool` Whether or not the offering has been deleted
    - price: `MonetaryAmount` Price data for this ProductOffering
    - readiness_state_id: `Optional[int]` Processing Profile for this ProductOffering
    """
    offering_id: int
    quantity: int
    is_enabled: bool
    is_deleted: bool
    price: MonetaryAmount
    readiness_state_id: Optional[int]

class Product(BaseModel):
    """
    ## Product for a Listing
    ### attributes:
    - product_id: `int >= 1` The numeric ID for a specific product purchased from a listing.
    - sku: `str` The SKU string for the product
    - is_deleted: `bool` When true, someone deleted this product.
    - offerings: `List[Offering]` A list of product offering entries for this product.
    - property_values: `List[Property]` A list of property value entries for this product. Note: parenthesis characters (( and )) are not allowed.
    """
    product_id: int
    sku: str
    is_deleted: bool
    offerings: List[Offering]
    property_values: List[Property]

class Transaction(BaseModel):
    """
    ## Transaction for a Shop Receipt
    ### attributes:
    - transaction_id: `int >= 1` The unique numeric ID for a transaction.	
    - title: `str` The title string of the listing purchased in this transaction. `Nullable`
    - description: `str` The description string of the listing purchased in this transaction. `Nullable`
    - seller_user_id: `int >= 1` The numeric user ID for the seller in this transaction.
    - buyer_user_id: `int >= 1` The numeric user ID for the buyer in this transaction.
    - create_timestamp: `int >= 946684800` The transaction's creation date and time, in epoch seconds.
    - created_timestamp: `int >= 946684800` The transaction's creation date and time, in epoch seconds.
    - paid_timestamp: `int >= 946684800` The transaction's paid date and time, in epoch seconds. `Nullable`
    - shipped_timestamp: `int >= 946684800` The transaction's shipping date and time, in epoch seconds. `Nullable`
    - quantity: `int >= 0` The numeric quantity of products purchased in this transaction.
    - listing_image_id: `int >= 1` The numeric ID of the primary listing image for this transaction. `Nullable`
    - receipt_id: `int >= 1` The numeric ID for the receipt associated to this transaction.
    - is_digital: `bool` When true, the transaction recorded the purchase of a digital listing.
    - file_data: `str` A string describing the files purchased in this transaction.
    - listing_id: `int >= 0` The numeric ID for the listing associated to this transaction. `Nullable`
    - transaction_type: `str` The type string for the transaction, usually "listing".
    - product_id: `int >= 1` The numeric ID for a specific product purchased from a listing. `Nullable`
    - sku: `str` The SKU string for the product. `Nullable`
    - price: `MonetaryAmount` A money object representing the price recorded the transaction.
    - shipping_cost: `MonetaryAmount` A money object representing the shipping cost for this transaction.
    - variations: `List[Variation]` A list of variations and personalizations the buyer chose.
    - product_data: `List[Property]` A list of property value entries for this product.
    - shipping_profile_id: `int >= 1` The ID of the shipping profile selected for this listing. `Nullable`
    - min_processing_days: `int >= 1` The minimum number of days for processing the listing. `Nullable`
    - max_processing_days: `int >= 1` The maximum number of days for processing the listing. `Nullable`
    - shipping_method: `str` The name of the selected shipping method. `Nullable`
    - shipping_upgrade: `str` The name of the shipping upgrade selected for this listing. `Nullable`
    - expected_ship_date: `int >= 946684800` The date & time of the expected ship date, in epoch seconds. `Nullable`
    - buyer_coupon: `float` The amount of the buyer coupon that was discounted in the shop's currency.
    - shop_coupon: `float` The amount of the shop coupon that was discounted in the shop's currency.
    """
    transaction_id: int
    title: Optional[str]
    description: Optional[str]
    seller_user_id: int
    buyer_user_id: int
    create_timestamp: datetime
    created_timestamp: datetime
    paid_timestamp: Optional[datetime]
    shipped_timestamp: Optional[datetime]
    quantity: int
    listing_image_id: Optional[int]
    receipt_id: int
    is_digital: bool
    file_data: str
    listing_id: Optional[int]
    transaction_type: str
    product_id: Optional[int]
    sku: Optional[str]
    price: MonetaryAmount
    shipping_cost: MonetaryAmount
    variations: List[Variation]
    product_data: List[Property]
    shipping_profile_id: Optional[int]
    min_processing_days: Optional[int]
    max_processing_days: Optional[int]
    shipping_method: Optional[str]
    shipping_upgrade: Optional[str]
    expected_ship_date: Optional[datetime]
    buyer_coupon: float
    shop_coupon: float

    @field_validator(
        'create_timestamp',
        'created_timestamp',
        'paid_timestamp',
        'shipped_timestamp',
        'expected_ship_date',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v

class Refund(BaseModel):
    """
    ## Refund for a Shop Receipt
    ### attributes:
    - amount: `MonetaryAmount` A number equal to the refund total.
    - created_timestamp: `int >= 946684800` The date & time of the refund, in epoch seconds.
    - reason: `str` The reason string given for the refund. `Nullable`
    - note_from_issuer: `str` The note string created by the refund issuer. `Nullable`
    - status: `str` The status indication string for the refund. `Nullable`
    """
    amount: MonetaryAmount
    created_timestamp: datetime
    reason: Optional[str]
    note_from_issuer: Optional[str]
    status: Optional[str]

    @field_validator('created_timestamp')
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v

class ShopReceipt(BaseModel):
    """
    ## Receipt from an Etsy shop
    ### attributes:
    - receipt_id: `int >= 1` The numeric ID for the receipt associated to this transaction.
    - receipt_type: `int >= 0` The numeric value for the Etsy channel that serviced the purchase: 0 for Etsy.com, 1 for a Pattern shop.
    - seller_user_id: `int >= 1` The numeric ID for the user (seller) fulfilling the purchase.	
    - seller_email: `str` The email address string for the seller of the listing. `Nullable`	
    - buyer_user_id: `int >= 1` The numeric ID for the user making the purchase.
    - buyer_email: `str` The email address string for the buyer of the listing. `Nullable`
    - name: `str` The name string for the recipient in the shipping address.
    - first_line: `str` The first address line string for the recipient in the shipping address.
    - second_line: `str` The optional second address line string for the recipient in the shipping address. `Nullable`
    - city: `str` The city string for the recipient in the shipping address.
    - state: `str` The state string for the recipient in the shipping address. `Nullable`
    - zip: `str` The zip code string (not necessarily a number) for the recipient in the shipping address.
    - status: `str` Enum: `paid` `completed` `open` `payment processing` `canceled` `fully refunded` `partially refunded`. The current order status string. One of: paid, completed, open, payment processing or canceled.
    - formatted_address: `str` The formatted shipping address string for the recipient in the shipping address.
    - country_iso: `str` The ISO-3166 alpha-2 country code string for the recipient in the shipping address.
    - payment_method: `str` The payment method string identifying purchaser's payment method, which must be one of: `cc` (credit card), `paypal`, `check`, `mo` (money order), `bt` (bank transfer), `other`, `ideal`, `sofort`, `apple_pay`, `google`, `android_pay`, `google_pay`, `klarna`, `k_pay_in_4` (klarna), `k_pay_in_3` (klarna), or `k_financing` (klarna).
    - payment_email: `str` The email address string for the email address to which to send payment confirmation. `Nullable`
    - message_from_seller: `str` An optional message string from the seller. `Nullable`
    - message_from_buyer: `str` An optional message string from the buyer. `Nullable`
    - message_from_payment: `str` The machine-generated acknowledgement string from the payment system. `Nullable`
    - is_paid: `bool` When true, buyer paid for this purchase.
    - is_shipped: `bool` When true, seller shipped the products.
    - create_timestamp: `int >= 946684800` The receipt's creation time, in epoch seconds.
    - created_timestamp: `int >= 946684800` The receipt's creation time, in epoch seconds.
    - update_timestamp: `int >= 946684800` The time of the last update to the receipt, in epoch seconds.
    - updated_timestamp: `int >= 946684800` The time of the last update to the receipt, in epoch seconds.
    - is_gift: `bool` When true, the buyer indicated this purchase is a gift.
    - gift_message: `str` A gift message string the buyer requests delivered with the product. `Nullable`
    - grandtotal: `MonetaryAmount` A number equal to the total_price minus the coupon discount plus tax and shipping costs.
    - subtotal: `MonetaryAmount` A number equal to the total_price minus coupon discounts. Does not included tax or shipping costs.
    - total_price: `MonetaryAmount` A number equal to the sum of the individual listings' (price * quantity). Does not included tax or shipping costs.
    - total_shipping_cost: `MonetaryAmount` A number equal to the total shipping cost of the receipt.
    - total_tax_cost: `MonetaryAmount` The total sales tax of the receipt.
    - total_vat_cost: `MonetaryAmount` A number equal to the total value-added tax (VAT) of the receipt.
    - discount_amt: `MonetaryAmount` The numeric total discounted price for the receipt when using a discount (percent or fixed) coupon. Free shipping coupons are not included in this discount amount.
    - gift_wrap_price: `MonetaryAmount` The numeric price of gift wrap for this receipt.
    - shipments: `List[ShipmentStatement]` A list of shipment statements for this receipt.
    - transactions: `List[Transaction]` A list of transactions for this receipt.
    - refunds: `List[Refund]` A list of refunds for this receipt.
    """
    receipt_id: int
    receipt_type: int
    seller_user_id: int
    seller_email: Optional[str]
    buyer_user_id: int
    buyer_email: Optional[str]
    name: str
    first_line: str
    second_line: Optional[str]
    city: str
    state: Optional[str]
    zip: str
    status: OrderStatus
    formatted_address: str
    country_iso: str
    payment_method: PaymentMethod
    payment_email: Optional[str]
    message_from_seller: Optional[str]
    message_from_buyer: Optional[str]
    message_from_payment: Optional[str]
    is_paid: bool
    is_shipped: bool
    create_timestamp: datetime
    created_timestamp: datetime
    update_timestamp: datetime
    updated_timestamp: datetime
    is_gift: bool
    gift_message: Optional[str]
    grandtotal: MonetaryAmount
    subtotal: MonetaryAmount
    total_price: MonetaryAmount
    total_shipping_cost: MonetaryAmount
    total_tax_cost: MonetaryAmount
    total_vat_cost: MonetaryAmount
    discount_amt: MonetaryAmount
    gift_wrap_price: MonetaryAmount
    shipments: List[ShipmentStatement]
    transactions: List[Transaction]
    refunds: List[Refund]

    @field_validator(
        'create_timestamp',
        'created_timestamp',
        'update_timestamp',
        'updated_timestamp',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v
    
    @field_validator('status', 'payment_method', mode="before")
    @classmethod
    def to_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        else:
            return v

class LedgerEntry(BaseModel):
    """
    ## Payment account ledger entry from an Etsy shop
    ### attributes:
    - entry_id: `int >= 1` The ledger entry's numeric ID.
    - ledger_id: `int >= 1` The ledger's numeric ID.
    - sequence_number: `int` The sequence allows ledger entries to be sorted chronologically. The higher the sequence, the more recent the entry.
    - amount: `int` The amount of money credited to the ledger.
    - currency: `str` The currency of the entry on the ledger.
    - description: `str` Details what kind of ledger entry this is: a payment, refund, reversal of a failed refund, disbursement, returned disbursement, recoupment, miscellaneous credit, miscellaneous debit, or bill payment.
    - balance: `int` The amount of money in the shop's ledger the moment after this entry was applied.
    - create_date: `int >= 946684800` The date and time the ledger entry was created in Epoch seconds.
    - created_timestamp: `int >= 946684800` The date and time the ledger entry was created in Epoch seconds.
    - ledger_type: `str` The original reference type for the ledger entry.
    - reference_type: `str` The object type the ledger entry refers to.
    - reference_id: `int` The object id the ledger entry refers to. `Nullable`
    - payment_adjustments: `List[TODO]` List of refund objects on an Etsy Payments transaction. All monetary amounts are in USD pennies unless otherwise specified.
    """
    entry_id: int
    ledger_id: int
    sequence_number: int
    amount: int
    currency: str
    description: str
    balance: int
    create_date: int
    created_timestamp: datetime
    ledger_type: str
    reference_type: str
    reference_id: Optional[int]
    payment_adjustments: List[dict]  # TODO: define PaymentAdjustment object

    @field_validator(
        'create_date',
        'created_timestamp',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v
    
    @field_validator('ledger_type', 'reference_type', mode="before")
    @classmethod
    def to_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        else:
            return v
    
    def monetary_amount(self) -> MonetaryAmount:
        return MonetaryAmount(amount=self.amount, divisor=100, currency_code=CurrencyCode(self.currency))

class Payment(BaseModel):
    """
    ## Shop Payment
    ### attributes:
    - payment_id: `int >= 1` A unique numeric ID for a payment to a specific Etsy shop.
    - buyer_user_id: `int >= 1` The numeric ID for the user who paid the purchase.
    - shop_id: `int >= 1` The unique positive non-zero numeric ID for an Etsy Shop.
    - receipt_id: `int >= 1` The numeric ID for the receipt associated to this transaction.
    - amount_gross: `MonetaryAmount` An integer equal to gross amount of the order, in pennies, including shipping and taxes.
    - amount_fees: `MonetaryAmount` An integer equal to the original card processing fee of the order in pennies.
    - amount_net: `MonetaryAmount` An integer equal to the payment value, in pennies, less fees (amount_gross - amount_fees).
    - posted_gross: `MonetaryAmount` The total gross value of the payment posted once the purchase ships. This is equal to the amount_gross UNLESS the seller issues a refund prior to shipping. We consider "shipping" to be the event which "posts" to the ledger. Therefore, if the seller refunds first, we reduce the amount_gross first and post then that amount. The seller never sees the refunded amount in their ledger. This is equal to the "Credit" amount in the ledger entry.
    - posted_fees: `MonetaryAmount` The total value of the fees posted once the purchase ships. Etsy refunds a proportional amount of the fees when a seller refunds a buyer. When the seller issues a refund prior to shipping, the posted amount is less then the original.
    - posted_net: `MonetaryAmount` The total value of the payment at the time of posting, less fees. (posted_gross - posted_fees)
    - adjusted_gross: `MonetaryAmount` The gross payment amount after the seller refunds a payment, partially or fully.
    - adjusted_fees: `MonetaryAmount` The new fee amount after a seller refunds a payment, partially or fully.
    - adjusted_net: `MonetaryAmount` The total value of the payment after refunds, less fees (adjusted_gross - adjusted_fees).
    - currency: `str` The ISO (alphabetic) code string for the payment's currency.
    - shop_currency: `str` The ISO (alphabetic) code for the shop's currency. The shop displays all prices in this currency by default.
    - buyer_currency: `str` The currency string of the buyer
    - shipping_user_id: `int >= 1` The numeric ID of the user to which the seller ships the order.
    - shipping_address_id: `int >= 1` The numeric id identifying the shipping address.
    - billing_address_id: `int >= 1` The numeric ID identifying the billing address of the buyer.
    - status: `str` A string indicating the current status of the payment, most commonly "settled" or "authed".
    - shipped_timestamp: `int >= 946684800` The transaction's shipping date and time, in epoch seconds.
    - create_timestamp: `int >= 946684800` The transaction's creation date and time, in epoch seconds.
    - created_timestamp: `int >= 946684800` The transaction's creation date and time, in epoch seconds.
    - update_timestamp: `int >= 946684800` The date and time of the last change to the payment adjustment in epoch seconds.
    - updated_timestamp: `int >= 946684800` The date and time of the last change to the payment adjustment in epoch seconds.
    - payment_adjustments: `List[TODO]` List of refund objects on an Etsy Payments transaction. All monetary amounts are in USD pennies unless otherwise specified.
    """
    payment_id: int
    buyer_user_id: int
    shop_id: int
    receipt_id: int
    amount_gross: MonetaryAmount
    amount_fees: MonetaryAmount
    amount_net: MonetaryAmount
    posted_gross: Optional[MonetaryAmount]
    posted_fees: Optional[MonetaryAmount]
    posted_net: Optional[MonetaryAmount]
    adjusted_gross: Optional[MonetaryAmount]
    adjusted_fees: Optional[MonetaryAmount]
    adjusted_net: Optional[MonetaryAmount]
    currency: str
    shop_currency: Optional[str]
    buyer_currency: Optional[str]
    shipping_user_id: Optional[int]
    shipping_address_id: int
    billing_address_id: int
    status: str
    shipped_timestamp: Optional[datetime]
    create_timestamp: datetime
    created_timestamp: datetime
    update_timestamp: datetime
    updated_timestamp: datetime
    payment_adjustments: List[dict]  # TODO: define PaymentAdjustment object

    @field_validator(
        'shipped_timestamp',
        'create_timestamp',
        'created_timestamp',
        'update_timestamp',
        'updated_timestamp',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v
    
    @field_validator('status', mode="before")
    @classmethod
    def to_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        else:
            return v

class Inventory(BaseModel):
    """
    ## Inventory for a Shop Listing
    ### attributes:
    - products: `List[Product]` A JSON array of products available in a listing, even if only one product. All field names in the JSON blobs are lowercase.
    - price_on_property: `List[int]` An array of unique listing property ID integers for the properties that change product prices, if any. For example, if you charge specific prices for different sized products in the same listing, then this array contains the property ID for size.
    - quantity_on_property: `List[int]` An array of unique listing property ID integers for the properties that change the quantity of the products, if any. For example, if you stock specific quantities of different colored products in the same listing, then this array contains the property ID for color.
    - sku_on_property: `List[int]` An array of unique listing property ID integers for the properties that change the product SKU, if any. For example, if you use specific skus for different colored products in the same listing, then this array contains the property ID for color.
    - readiness_state_on_property: `List[int]` An array of unique listing property ID integers for the properties that change processing profile, if any. For example, if you need specific processing profiles for different colored products in the same listing, then this array contains the property ID for color.
    - listing: `Optional[Listing]` An enumerated string that attaches a valid association. Default value is null.
    """
    products: List[Product]
    price_on_property: List[int]
    quantity_on_property: List[int]
    sku_on_property: List[int]
    readiness_state_on_property: List[int]
    listing: Optional[Listing]

class Listing(BaseModel):
    """
    ## Shop Listing
    ### attributes:
    - listing_id: `int >= 1` The numeric ID for the listing associated to this transaction.
    - user_id: `int >= 1` The numeric ID for the user posting the listing.
    - shop_id: `int >= 1` The unique positive non-zero numeric ID for an Etsy Shop.
    - title: `str` The listing's title string. When creating or updating a listing, valid title strings contain only letters, numbers, punctuation marks, mathematical symbols, whitespace characters, ™, ©, and ®. (regex: /[^\p{L}\p{Nd}\p{P}\p{Sm}\p{Zs}™©®]/u) You can only use the %, :, & and + characters once each.
    - description: `str` A description string of the product for sale in the listing.
    - state: `str` Enum: "active" "inactive" "sold_out" "draft" "expired" When updating a listing, this value can be either active or inactive. Note: Setting a draft listing to active will also publish the listing on etsy.com and requires that the listing have an image set. Setting a sold_out listing to active will update the quantity to 1 and renew the listing on etsy.com.
    - creation_timestamp: `int >= 946684800` The listing's creation time, in epoch seconds.
    - created_timestamp: `int >= 946684800` The listing's creation time, in epoch seconds.
    - ending_timestamp: `int >= 946684800` The listing's expiration time, in epoch seconds.
    - original_creation_timestamp: `int >= 946684800` The listing's creation time, in epoch seconds.
    - last_modified_timestamp: `int >= 946684800` The time of the last update to the listing, in epoch seconds.
    - updated_timestamp: `int >= 946684800` The time of the last update to the listing, in epoch seconds.
    - state_timestamp: `int >= 946684800` The date and time of the last state change of this listing.
    - quantity: `int >= 0` The positive non-zero number of products available for purchase in the listing. Note: The listing quantity is the sum of available offering quantities. You can request the quantities for individual offerings from the ListingInventory resource using the getListingInventory endpoint.
    - shop_section_id: `int >= 1` The numeric ID of a section in a specific Etsy shop.
    - featured_rank: `int >= 1` The positive non-zero numeric position in the featured listings of the shop, with rank 1 listings appearing in the left-most position in featured listing on a shop's home page.
    - url: `str` The full URL to the listing's page on Etsy.
    - num_favorers: `int >= 0` The number of users who marked this Listing a favorite.
    - non_taxable: `bool` When true, applicable shop tax rates do not apply to this listing at checkout.
    - is_taxable: `bool` When true, applicable shop tax rates apply to this listing at checkout.
    - is_customizable: `bool` When true, a buyer may contact the seller for a customized order. The default value is true when a shop accepts custom orders. Does not apply to shops that do not accept custom orders.
    - is_personalizable: `bool` When true, this listing is personalizable. The default value is null.
    - personalization_is_required: `bool` When true, this listing requires personalization. The default value is null. Will only change if is_personalizable is 'true'.
    - personalization_char_count_max: `int` This is an integer value representing the maximum length for the personalization message entered by the buyer. Will only change if is_personalizable is 'true'.
    - personalization_instructions: `str` When true, this listing requires personalization. The default value is null. Will only change if is_personalizable is 'true'.
    - listing_type: `str` Enum: "physical" "download" "both" An enumerated type string that indicates whether the listing is physical or a digital download.
    - tags: `List[str]` A comma-separated list of tag strings for the listing. When creating or updating a listing, valid tag strings contain only letters, numbers, whitespace characters, -, ', ™, ©, and ®. (regex: /[^\p{L}\p{Nd}\p{Zs}-'™©®]/u) Default value is null.
    - materials: `List[str]` A list of material strings for materials used in the product. Valid materials strings contain only letters, numbers, and whitespace characters. (regex: /[^\p{L}\p{Nd}\p{Zs}]/u) Default value is null.
    - shipping_profile_id: `int >= 1` The numeric ID of the shipping profile associated with the listing. Required when listing type is physical.
    - return_policy_id: `int >= 1` The numeric ID of the Return Policy.
    - processing_min: `int >= 1` The minimum number of days required to process this listing. Default value is null.
    - processing_max: `int >= 1` The maximum number of days required to process this listing. Default value is null.
    - who_made: `str` Enum: "i_did" "someone_else" "collective" An enumerated string indicating who made the product. Helps buyers locate the listing under the Handmade heading. Requires 'is_supply' and 'when_made'.
    - when_made: `str` Enum: "made_to_order" "2020_2026" "2010_2019" "2007_2009" "before_2007" "2000_2006" "1990s" "1980s" "1970s" "1960s" "1950s" "1940s" "1930s" "1920s" "1910s" "1900s" "1800s" "1700s" "before_1700" An enumerated string for the era in which the maker made the product in this listing. Helps buyers locate the listing under the Vintage heading. Requires 'is_supply' and 'who_made'.
    - is_supply: `bool` When true, tags the listing as a supply product, else indicates that it's a finished product. Helps buyers locate the listing under the Supplies heading. Requires 'who_made' and 'when_made'.
    - item_weight: `float` The numeric weight of the product measured in units set in 'item_weight_unit'. Default value is null. If set, the value must be greater than 0.
    - item_weight_unit: `str` Enum: "oz" "lb" "g" "kg" A string defining the units used to measure the weight of the product. Default value is null.
    - item_length: `float` The numeric length of the product measured in units set in 'item_dimensions_unit'. Default value is null. If set, the value must be greater than 0.
    - item_width: `float` The numeric width of the product measured in units set in 'item_dimensions_unit'. Default value is null. If set, the value must be greater than 0.
    - item_height: `float` The numeric length of the product measured in units set in 'item_dimensions_unit'. Default value is null. If set, the value must be greater than 0.
    - item_dimensions_unit: `str` Enum: "in" "ft" "mm" "cm" "m" "yd" "inches" A string defining the units used to measure the dimensions of the product. Default value is null.
    - is_private: `bool` When true, this is a private listing intended for a specific buyer and hidden from shop view.
    - style: `List[str]` An array of style strings for this listing, each of which is free-form text string such as "Formal", or "Steampunk". When creating or updating a listing, the listing may have up to two styles. Valid style strings contain only letters, numbers, and whitespace characters. (regex: /[^\p{L}\p{Nd}\p{Zs}]/u) Default value is null.
    - file_data: `str` A string describing the files attached to a digital listing.
    - has_variations: `bool` When true, the listing has variations.
    - should_auto_renew: `bool` When true, renews a listing for four months upon expiration.
    - language: `str` The IETF language tag for the default language of the listing. Ex: de, en, es, fr, it, ja, nl, pl, pt, ru.
    - price: `MonetaryAmount` The positive non-zero price of the product. (Sold product listings are private) Note: The price is the minimum possible price. The getListingInventory method requests exact prices for available offerings.
    - taxonomy_id: `int` The numerical taxonomy ID of the listing. See SellerTaxonomy and BuyerTaxonomy for more information.
    - readiness_state_id: `int` The numeric ID of the processing profile associated with the listing. Returned only when the listing is active and of type physical, and the endpoint is either shop-scoped (path contains shop_id) or a single-listing request such as getListing. For every other case this field can be null.
    - suggested_title: `str` A title string suggested by Etsy. Only available for a user's own listings, when allow_suggested_title param is present, and when a shop's language setting is English. Not all listings will have suggestions.
    - shipping_profile: `List[TODO]` An array of data representing the shipping profile resource.
    - user: `User` Represents a single user of the site
    - shop: `TODO` A shop created by an Etsy user.
    - images: `List[TODO]` Represents a list of listing image resources, each of which contains the reference URLs and metadata for an image
    - videos: `List[TODO]` The single video associated with a listing.
    - inventory: `TODO` An enumerated string that attaches a valid association. Default value is null.
    - production_partners: `List[TODO]` Represents a list of production partners for a shop.
    - skus: `List[str]` A list of SKU strings for the listing. SKUs will only appear if the requesting user owns the shop and a valid matching OAuth 2 token is provided. When requested without the token it will be an empty array.
    - translations: `TODO` A list of SKU strings for the listing. SKUs will only appear if the requesting user owns the shop and a valid matching OAuth 2 token is provided. When requested without the token it will be an empty array.
    - views: `int` The number of times the listing has been viewed. This value is tabulated once per day and only for active listings, so the value is not real-time. If 0, the listing has either not been viewed, not yet tabulated, was not active during the last tabulation or there was an error fetching the value. If a value is expected, call getListing to confirm the value.
    """
    listing_id: int
    user_id: int
    shop_id: int
    title: str
    description: str
    state: str
    creation_timestamp: datetime
    created_timestamp: datetime 
    ending_timestamp: datetime
    original_creation_timestamp: datetime
    last_modified_timestamp: datetime
    updated_timestamp: datetime
    state_timestamp: Optional[datetime]
    quantity: int
    shop_section_id: Optional[int]
    featured_rank: int
    url: str
    num_favorers: int
    non_taxable: bool
    is_taxable: bool
    is_customizable: bool
    is_personalizable: bool
    personalization_is_required: bool
    personalization_char_count_max: Optional[int]
    personalization_instructions: Optional[str]
    listing_type: ListingType
    tags: List[str]
    materials: List[str]
    shipping_profile_id: Optional[int]
    return_policy_id: Optional[int]
    processing_min: Optional[int]
    processing_max: Optional[int]
    who_made: Optional[WhoMade]
    when_made: Optional[str]
    is_supply: Optional[bool]
    item_weight: Optional[float]
    item_weight_unit: Optional[WeightUnit]
    item_length: Optional[float]
    item_width: Optional[float]
    item_height: Optional[float]
    item_dimensions_unit: Optional[DimensionsUnit]
    is_private: bool
    style: List[str]
    file_data: Optional[str]
    has_variations: bool
    should_auto_renew: bool
    language: Optional[str]
    price: MonetaryAmount
    taxonomy_id: Optional[int]
    readiness_state_id: Optional[int]
    suggested_title: Optional[str]
    shipping_profile: Optional[dict]
    user: Optional[User]
    shop: Optional[dict]
    images: Optional[List[dict]]
    videos: Optional[List[dict]]
    inventory: Optional[Inventory]
    production_partners: List[dict]
    skus: List[str]
    translations: Optional[dict]
    views: int

    @field_validator(
        'creation_timestamp',
        'created_timestamp',
        'ending_timestamp',
        'original_creation_timestamp',
        'last_modified_timestamp',
        'updated_timestamp',
        'state_timestamp',
    )
    @classmethod
    def check_timestamp(cls, v):
        if isinstance(v, (int, float)):
            if v < 946684800:
                raise ValueError("Timestamp must be greater or equal to 946684800")
            return datetime.fromtimestamp(v)
        else:
            return v
    
    @field_validator(
        'state',
        'listing_type',
        'who_made',
        'when_made',
        'item_weight_unit',
        'item_dimensions_unit',
        'language',
        mode="before",
    )
    @classmethod
    def to_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        else:
            return v
