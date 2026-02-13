# API Reference

This page provides technical documentation for developers working with the Etsy Integration codebase.

## Module Structure

```
etsy/
├── api.py              # HTTP client and high-level API wrapper
├── datastruct.py       # Pydantic models for Etsy API responses
├── hooks.py            # Frappe hooks and custom field definitions
├── install.py          # Installation and uninstallation hooks
└── etsy/
    └── doctype/
        ├── etsy_shop/        # Etsy Shop doctype
        ├── etsy_settings/    # Etsy Settings singleton
        └── etsy_listing/     # Etsy Listing doctype
```

## Core Modules

### api.py

Contains the HTTP client and API wrapper classes for interacting with Etsy API v3.

#### Helper Functions

##### `fetch_all(fetch_func, start_offset=0)`

Generator function for paginated API requests with rate limiting.

**Parameters:**
- `fetch_func` (Callable): Function that takes an offset and returns `(total_count, items_list)`
- `start_offset` (int): Starting offset for pagination (default: 0)

**Returns:**
- Iterator[T]: Yields items one at a time

**Features:**
- Automatic pagination handling
- Rate limiting (0.25s delay between requests)
- Handles partial pages

**Example:**
```python
def get_receipts(offset):
    response = api.getShopReceipts(params)
    return response['count'], response['results']

for receipt in fetch_all(get_receipts):
    process_receipt(receipt)
```

#### Query Parameter Classes

Type-safe Pydantic models for API query parameters.

##### `QP_getShopReceipts`

Query parameters for fetching shop receipts.

**Fields:**
- `shop_id` (int, required): Shop ID
- `min_created` (int, optional): Minimum creation timestamp (>= 946684800)
- `max_created` (int, optional): Maximum creation timestamp
- `min_last_modified` (int, optional): Minimum modified timestamp
- `max_last_modified` (int, optional): Maximum modified timestamp
- `limit` (int): Results per page (1-100, default: 25)
- `offset` (int): Pagination offset (>= 0)
- `sort_on` (str): Sort field - `created`, `updated`, or `receipt_id` (default: `created`)
- `sort_order` (str): Sort direction - `asc`, `desc`, etc. (default: `desc`)
- `was_paid` (bool, optional): Filter by payment status
- `was_shipped` (bool, optional): Filter by shipment status
- `was_delivered` (bool, optional): Filter by delivery status
- `was_canceled` (bool, optional): Filter by cancellation status

**Validators:**
- Timestamps must be >= 946684800 (2000-01-01)
- Limit must be between 1 and 100
- Enum fields validated against allowed values

##### `QP_getShopPaymentAccountLedgerEntries`

Query parameters for fetching ledger entries.

**Fields:**
- `shop_id` (int, required): Shop ID
- `min_created` (int, required): Minimum creation timestamp
- `max_created` (int, required): Maximum creation timestamp
- `limit` (int): Results per page (1-100, default: 25)
- `offset` (int): Pagination offset

##### `QP_getListingsByShop`

Query parameters for fetching shop listings.

**Fields:**
- `shop_id` (int, required): Shop ID
- `state` (str): Listing state - `active`, `inactive`, `sold_out`, `draft`, `expired` (default: `active`)
- `limit` (int): Results per page (1-100, default: 25)
- `offset` (int): Pagination offset
- `sort_on` (str): Sort field - `created`, `price`, `updated`, `score`
- `sort_order` (str): Sort direction
- `includes` (str, optional): Associated data to include - `Shipping`, `Images`, `Shop`, `User`, `Translations`, `Inventory`, `Videos`

#### API Classes

##### `EtsyRESTv3`

Low-level HTTP client for Etsy API v3.

**Constructor:**
```python
EtsyRESTv3(auth_header: dict, language: str = "de")
```

**Parameters:**
- `auth_header` (dict): Authorization header with Bearer token
- `language` (str): Language code for API responses (default: "de")

**Methods:**

###### `args(endpoint, headers=None, params=None, extensions=None)`

Constructs request arguments for HTTP client.

**Returns:** dict with `url`, `params`, `headers`, `extensions`

###### `getMe(client)`

Fetches authenticated user's profile.

**Returns:** Response object

###### `getUser(client, user_id)`

Fetches a user profile by ID.

**Returns:** Response object

###### `getUserAddress(client, user_address_id)`

Fetches a user address by ID.

**Returns:** Response object

###### `getShopPaymentByReceiptId(client, shop_id, receipt_id)`

Fetches payment info for a receipt.

**Returns:** Response object

###### `getShopReceipts(client, query_params)`

Fetches shop receipts with query parameters.

**Returns:** Response object

###### `getShopPaymentAccountLedgerEntries(client, query_params)`

Fetches ledger entries.

**Returns:** Response object

###### `getListingsByShop(client, query_params)`

Fetches shop listings.

**Returns:** Response object

###### `getListingImage(client, listing_id, listing_image_id)`

Fetches a listing image with caching.

**Returns:** Response object

##### `EtsyAPI`

High-level typed API wrapper using Pydantic models.

**Constructor:**
```python
EtsyAPI(etsy_shop: EtsyShop)
```

**Parameters:**
- `etsy_shop` (EtsyShop): Etsy Shop document instance

**Attributes:**
- `rest` (EtsyRESTv3): Low-level REST client
- `client` (SyncCacheClient): HTTP client with caching

**Methods:**

###### `getMe()`

Fetches authenticated user's profile.

**Returns:** `Me` (Pydantic model)

###### `getUser(user_id)`

Fetches a user profile.

**Returns:** `User` (Pydantic model)

###### `getUserAddress(user_address_id)`

Fetches a user address.

**Returns:** `Address` (Pydantic model)

###### `getShopPaymentByReceiptId(shop_id, receipt_id)`

Fetches payment info for a receipt.

**Returns:** Tuple[int, List[Payment]]

###### `getShopReceipts(**query_params)`

Fetches shop receipts with pagination.

**Returns:** Tuple[int, List[ShopReceipt]]

###### `getShopPaymentAccountLedgerEntries(**query_params)`

Fetches ledger entries.

**Returns:** Tuple[int, List[LedgerEntry]]

###### `getListingsByShop(**query_params)`

Fetches shop listings.

**Returns:** Tuple[int, List[Listing]]

###### `fetch_all(**query_params)`

Generator for fetching all records with pagination.

**Returns:** Iterator[T]

#### Scheduled Sync Functions

##### `synchronise_receipts()`

Scheduled job entry point for syncing orders across all shops.

**Behavior:**
- Fetches all Etsy Shops with status = "Connected"
- Calls `import_receipts()` on each shop
- Logs errors per shop without stopping

**Invoked by:** Scheduled Job Type (Sales Order Sync)

##### `synchronise_listings()`

Scheduled job entry point for syncing listings across all shops.

**Behavior:**
- Fetches all Etsy Shops with status = "Connected"
- Calls `import_listings()` on each shop
- Logs errors per shop without stopping

**Invoked by:** Scheduled Job Type (Item Sync)

### datastruct.py

Pydantic models for Etsy API v3 responses and data structures.

#### Core Models

##### `Me`

Authenticated user's profile data.

**Fields:**
- `user_id` (int): User ID
- `login_name` (str): Login name
- `primary_email` (str): Email address
- Additional profile fields

##### `User`

Etsy user profile.

**Fields:**
- `user_id` (int): User ID
- `first_name` (str): First name
- `last_name` (str): Last name
- Additional profile fields

##### `Address`

User address information.

**Fields:**
- `user_address_id` (int): Address ID
- `name` (str): Recipient name
- `first_line` (str): Address line 1
- `second_line` (str): Address line 2
- `city` (str): City
- `state` (str): State/province
- `zip` (str): Postal code
- `country_iso` (str): Country code (ISO)

##### `ShopReceipt`

Etsy order/receipt data.

**Fields:**
- `receipt_id` (int): Receipt ID
- `receipt_type` (int): Type code
- `buyer_user_id` (int): Buyer's user ID
- `seller_user_id` (int): Seller's user ID
- `grandtotal` (dict): Total amounts
- `subtotal` (dict): Subtotal amounts
- `total_tax_cost` (dict): Tax amounts
- `total_shipping_cost` (dict): Shipping amounts
- `is_paid` (bool): Payment status
- `is_shipped` (bool): Shipment status
- `create_timestamp` (int): Creation time
- `transactions` (List): Line items
- Additional receipt fields

##### `Payment`

Payment information.

**Fields:**
- `payment_id` (int): Payment ID
- `buyer_user_id` (int): Buyer ID
- `shop_id` (int): Shop ID
- `receipt_id` (int): Receipt ID
- `amount_gross` (dict): Gross amount
- `amount_fees` (dict): Fee amount
- `amount_net` (dict): Net amount
- `posted_gross` (dict): Posted gross
- `posted_fees` (dict): Posted fees
- `posted_net` (dict): Posted net
- `payment_method` (str): Payment method
- `status` (str): Payment status
- Additional payment fields

##### `Listing`

Etsy listing data.

**Fields:**
- `listing_id` (int): Listing ID
- `user_id` (int): Seller user ID
- `shop_id` (int): Shop ID
- `title` (str): Listing title
- `description` (str): Description
- `state` (str): Listing state
- `url` (str): Listing URL
- `price` (dict): Price information
- `quantity` (int): Available quantity
- `images` (List): Image data
- Additional listing fields

##### `LedgerEntry`

Payment account ledger entry.

**Fields:**
- `entry_id` (int): Entry ID
- `shop_id` (int): Shop ID
- `ledger_type` (str): Entry type
- `amount` (dict): Amount
- `currency` (str): Currency code
- `description` (str): Entry description
- `create_date` (int): Creation timestamp
- Additional ledger fields

#### Enums

The module defines various enums for type safety:

- `OrderStatus`: Order status values
- `PaymentMethod`: Payment method types
- `CurrencyCode`: ISO currency codes
- `ListingState`: Listing state values
- Additional enums for various fields

### hooks.py

Frappe app hooks and configuration.

#### App Metadata

```python
app_name = "etsy"
app_title = "Etsy"
app_publisher = "Cornstarch3D"
app_description = "Etsy Integration for ERPnext"
app_email = "info@cornstarch3d.de"
app_license = "GNU General Public License (v3)"
```

#### Custom Fields Definition

The `etsy_custom_fields` dictionary defines all custom fields to be added to standard doctypes.

**Structure:**
```python
{
    "DocType Name": [
        {
            "fieldname": "field_name",
            "label": "Field Label",
            "fieldtype": "Data",
            "insert_after": "existing_field",
            "read_only": 1,
            "unique": 1,
        },
        # More fields...
    ]
}
```

**Custom Fields:**
- Customer: `etsy_customer_id` (unique)
- Contact: `etsy_customer_id` (unique)
- Sales Order: `etsy_order_id` (unique)
- Sales Invoice: `etsy_order_id` (unique)
- Item: `etsy_product_id` (unique), `etsy_listing` (link)
- Item Attribute: `etsy_listing` (link), `etsy_property_id`

#### Installation Hooks

```python
after_install = "etsy.install.after_install"
before_uninstall = "etsy.install.before_uninstall"
after_uninstall = "etsy.install.after_uninstall"
```

#### Dependencies

```python
required_apps = ["erpnext"]
```

### install.py

Installation and uninstallation routines.

#### Functions

##### `after_install()`

Runs after app installation.

**Actions:**
- Creates all custom fields defined in `hooks.py`
- Commits changes to database
- Logs success message

**Invoked:** Automatically after `bench install-app etsy`

##### `before_uninstall()`

Runs before app uninstallation.

**Actions:**
- Deletes all Scheduled Job Types created by the app
- Prevents orphaned scheduled jobs

**Invoked:** Automatically during `bench uninstall-app etsy`

##### `after_uninstall()`

Runs after app uninstallation.

**Actions:**
- Deletes all custom fields created by the app
- Cleans up database

**Invoked:** Automatically after uninstallation

## Doctype APIs

### Etsy Shop

**Module:** `etsy.etsy.doctype.etsy_shop.etsy_shop`

#### Key Methods

##### `get_auth_header()`

Returns OAuth authorization header.

**Returns:** dict with `{"Authorization": "Bearer <token>"}`

##### `refresh_token()`

Refreshes OAuth access token using refresh token.

**Actions:**
- Calls Etsy token endpoint
- Updates `access_token`, `refresh_token`, `expires_in`, `expires_in_datetime`
- Saves document

##### `import_listings()`

Imports all active listings from Etsy.

**Actions:**
- Fetches listings via API
- Creates/updates Etsy Listing documents
- Creates/updates Items, Item Templates, Item Variants
- Creates/updates Item Attributes
- Logs errors

**Invoked by:** "Import Listings" button, scheduled sync

##### `import_receipts(min_created=None)`

Imports receipts (orders) from Etsy.

**Parameters:**
- `min_created` (int, optional): Minimum creation timestamp for filtering

**Actions:**
- Fetches receipts via API
- Creates/matches Customers
- Creates/updates Contacts with addresses
- Creates Sales Orders
- Creates Sales Invoices (if paid)
- Creates Payment Entries (if paid)
- Logs errors

**Invoked by:** "Import Receipts" button, "Import Historic Receipts" button, scheduled sync

##### `oauth_callback(code, state)`

OAuth callback handler.

**Parameters:**
- `code` (str): Authorization code from Etsy
- `state` (str): State parameter for CSRF protection

**Actions:**
- Exchanges code for tokens
- Saves tokens to document
- Fetches user and shop IDs
- Updates status to "Connected"

**Invoked by:** Etsy OAuth redirect

### Etsy Settings

**Module:** `etsy.etsy.doctype.etsy_settings.etsy_settings`

#### Key Methods

##### `validate()`

Validates settings before save.

**Actions:**
- Validates sync interval ranges
- Creates/updates Scheduled Job Types based on intervals
- Generates cron expressions

##### `create_scheduled_job(job_name, method, cron)`

Creates or updates a Scheduled Job Type.

**Parameters:**
- `job_name` (str): Job type name
- `method` (str): Python path to function
- `cron` (str): Cron expression

### Etsy Listing

**Module:** `etsy.etsy.doctype.etsy_listing.etsy_listing`

#### Key Methods

##### `update_attributes()`

Creates/updates Item Attributes from listing properties.

**Actions:**
- Extracts properties from inventory JSON
- Creates Item Attributes if they don't exist
- Adds attribute values

##### `update_items()`

Creates/updates Items or Item Variants from listing.

**Actions:**
- Determines if listing has variants
- Creates Item Template (if variants) or single Item (if no variants)
- Creates Item Variants for each product offering
- Sets pricing, descriptions, images
- Links items via `etsy_product_id` custom field

## Database Schema

### Custom Fields

All custom fields are read-only and use the `Data` fieldtype except for links.

| DocType | Field Name | Type | Unique | Purpose |
|---------|------------|------|--------|---------|
| Customer | `etsy_customer_id` | Data | Yes | Link to Etsy buyer |
| Contact | `etsy_customer_id` | Data | Yes | Link to Etsy buyer |
| Sales Order | `etsy_order_id` | Data | Yes | Link to Etsy receipt |
| Sales Invoice | `etsy_order_id` | Data | Yes | Link to Etsy receipt |
| Item | `etsy_product_id` | Data | Yes | Link to Etsy product |
| Item | `etsy_listing` | Link | No | Reference to Etsy Listing |
| Item Attribute | `etsy_listing` | Link | No | Reference to Etsy Listing |
| Item Attribute | `etsy_property_id` | Data | No | Etsy property ID |

## Error Handling Pattern

All import methods follow this pattern:

```python
for record in records:
    try:
        # Process record
        process_record(record)
        frappe.db.commit()  # Commit this record
    except Exception as e:
        frappe.db.rollback()  # Rollback only this record
        frappe.log_error(
            title=f"Etsy Error: {context}",
            message=traceback.format_exc()
        )
        continue  # Move to next record
```

This ensures:
- Atomic record processing
- Error isolation
- Comprehensive error logging
- Resilience to individual failures

## Rate Limiting

The integration respects Etsy's rate limits:

- **Delay:** 0.25 seconds between paginated requests
- **Implementation:** `time.sleep(0.25)` in `fetch_all()` function
- **Etsy Limit:** 10 requests/second per token
- **Actual Rate:** ~4 requests/second (well within limit)

## Authentication Flow

### OAuth 2.0 PKCE

```
1. User clicks "Login" button
   ↓
2. App generates code_verifier and code_challenge
   ↓
3. User redirected to Etsy authorization page
   ↓
4. User approves, Etsy redirects back with authorization code
   ↓
5. App exchanges code + code_verifier for tokens
   ↓
6. Tokens saved, status set to "Connected"
```

### Token Refresh

```
1. API call initiated
   ↓
2. Check if access_token is expired
   ↓
3. If expired: Call refresh_token() method
   ↓
4. Use new access_token for API call
```

## Next Steps

- **[Development](development.md)** - Contributing and development guide
- **[Features](features.md)** - User-facing features documentation
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
