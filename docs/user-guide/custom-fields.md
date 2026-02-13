# Custom Fields & Data Mapping

The app adds read-only custom fields to standard ERPNext doctypes for linking Etsy data, and maps Etsy fields to ERPNext documents during import.

## Custom Fields on Standard Doctypes

![Custom Field on Customer](../images/config-custom-field-customer.png)

<!-- IMAGE: Screenshot of Customer form showing the "Etsy Customer ID" custom field positioned after "Naming Series", with a value populated (e.g., "123456789") and marked as read-only -->

### Customer

| Field | Type | Unique | Description |
|-------|------|--------|-------------|
| **Etsy Customer ID** | Data | Yes | Etsy Buyer User ID. Used to match existing customers. |

Appears after the "Naming Series" field. Prevents duplicate customer creation for the same Etsy buyer.

### Contact

| Field | Type | Unique | Description |
|-------|------|--------|-------------|
| **Etsy Customer ID** | Data | Yes | Etsy Buyer User ID. Links contact to Etsy buyer. |

Appears after "Company Name". Links the contact to the corresponding Etsy customer.

### Sales Order

| Field | Type | Unique | Description |
|-------|------|--------|-------------|
| **Etsy Order ID** | Data | Yes | Etsy Receipt ID (transaction ID). |

Appears after "Naming Series". Prevents duplicate Sales Orders for the same Etsy transaction.

![Custom Field on Sales Order](../images/config-custom-field-sales-order.png)

<!-- IMAGE: Screenshot of Sales Order form showing the "Etsy Order ID" custom field near the top after "Naming Series", with a value like "3456789012" visible and marked as read-only -->

### Sales Invoice

| Field | Type | Unique | Description |
|-------|------|--------|-------------|
| **Etsy Order ID** | Data | Yes | Etsy Receipt ID. Links invoice to Etsy order. |

Appears after "Naming Series". Links the invoice to the corresponding Etsy transaction.

### Item

| Field | Type | Unique | Description |
|-------|------|--------|-------------|
| **Etsy Product ID** | Data | Yes | Etsy Product ID (variant-specific identifier). |
| **Etsy Listing** | Link | No | Links to the Etsy Listing doctype. |

Appears after "Naming Series". Links the item to its Etsy listing and prevents duplicates.

### Item Attribute

| Field | Type | Unique | Description |
|-------|------|--------|-------------|
| **Etsy Listing** | Link | No | Links to the Etsy Listing doctype. |
| **Etsy Property ID** | Data | No | Etsy's internal property ID (e.g., property ID for "Color"). |

Appears after "Numeric Values". Links item attributes back to their Etsy listing.

## Data Mapping

How Etsy data maps to ERPNext documents during import.

### Customer Mapping

| Etsy Field | ERPNext Field |
|------------|---------------|
| Buyer User ID | `etsy_customer_id` (custom field) |
| Buyer Name | Customer Name (from naming series) |
| - | Customer Group (from Etsy Shop config) |
| - | Language (from Etsy Shop config) |

### Contact Mapping

| Etsy Field | ERPNext Field |
|------------|---------------|
| Buyer Email | Email |
| Buyer Name | Full Name |
| Shipping Name | Address Line 1 (in Address doctype) |
| Shipping Address1 | Address Line 2 |
| Shipping City | City |
| Shipping State | State |
| Shipping Zip | Postal Code |
| Shipping Country | Country |

### Sales Order Mapping

| Etsy Field | ERPNext Field |
|------------|---------------|
| Receipt ID | `etsy_order_id` (custom field) |
| Create Timestamp | Transaction Date |
| Buyer User ID | Customer (matched via `etsy_customer_id`) |
| Grandtotal | Grand Total |
| Line Items | Sales Order Items (multiple rows) |
| Sales Tax | Taxes and Charges (sales tax account) |
| Shipping Cost | Sales Order Item (separate row for shipping) |

### Item Mapping

| Etsy Field | ERPNext Field |
|------------|---------------|
| Product ID | `etsy_product_id` (custom field) |
| Listing ID | `etsy_listing` (custom field, link) |
| Title | Item Name |
| Description | Description |
| Price | Standard Rate |
| Quantity | Stock UOM (if maintain stock) |
| Primary Image | Image |
