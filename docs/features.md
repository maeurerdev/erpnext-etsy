# Features

This page provides an in-depth look at all features of the Etsy Integration app.

## Sales Order Synchronization

Automatically import Etsy orders (receipts) into ERPNext as complete Sales Orders with all related documents.

### What Gets Imported

For each Etsy order, the integration creates:

#### 1. Customer
- **Automatic creation** if the Etsy Buyer ID doesn't exist
- **Automatic matching** if a customer with the same Etsy Customer ID already exists
- Customer name follows the configured naming series (default: `EtsyUser-{ETSY_BUYER_ID}`)
- Linked to the configured Customer Group
- Marked with unique `etsy_customer_id` custom field

![Customer from Etsy](images/features-customer-created.png)

<!-- IMAGE: Screenshot of a Customer document created from Etsy showing the customer name (e.g., "EtsyUser-123456789"), Customer Group, and the "Etsy Customer ID" custom field populated -->

#### 2. Contact
- Created or updated for each customer
- **Billing Address** extracted from Etsy order
- **Shipping Address** extracted from Etsy order
- Phone number and email (if provided by buyer)
- Linked to the Customer via Contact link

![Contact with Addresses](images/features-contact-addresses.png)

<!-- IMAGE: Screenshot of a Contact document showing email, phone, and the "Addresses & Contacts" section with both shipping and billing addresses populated from Etsy order data -->

#### 3. Sales Order
- One Sales Order per Etsy receipt
- Contains all line items with:
  - Correct product/variant mapping to ERPNext Items
  - Quantities and pricing from Etsy
  - Item descriptions
- **Taxes** calculated and added:
  - Product sales tax (if applicable)
  - Shipping tax (if applicable)
- **Shipping charges** added as a separate line item
- Status automatically set based on Etsy payment status
- Unique `etsy_order_id` custom field prevents duplicates

#### 4. Sales Invoice
- Automatically created if the Etsy order is paid
- Mirrors the Sales Order line items
- Submitted automatically
- Linked to the Sales Order

#### 5. Payment Entry
- Created when payment is complete on Etsy
- Amount matches the Etsy payment total
- Posted to the configured bank account:
  - Physical products → Bank Account for physical sales
  - Digital products → Bank Account for digital sales
- Payment method mapped from Etsy (credit card, PayPal, etc.)
- References the Sales Invoice

### Handling Edge Cases

#### Partial Shipments
If an Etsy order has multiple shipments, each shipment is tracked, but a single Sales Order is created for the entire order.

#### Refunds and Cancellations
The integration doesn't automatically process refunds. You need to manually create credit notes in ERPNext if an Etsy order is refunded.

#### Gift Messages and Notes
Buyer notes and gift messages from Etsy are added to the Sales Order comments/notes section.

#### Missing Items
If an Etsy line item references a product that hasn't been imported as an Item:
- The integration attempts to create the item on-the-fly
- If it fails, the error is logged, and that specific order is skipped
- You can manually import the listing first, then re-import the order

## Listing Import

Import your Etsy product listings into ERPNext as Items, complete with variants and attributes.

### What Gets Imported

#### 1. Etsy Listing Document
- One Etsy Listing document per active listing on Etsy
- Stores listing metadata:
  - Title, description
  - Status (Active, Inactive, Sold Out, etc.)
  - Primary image
  - Views and likes count
  - Inventory data (JSON)
- Configuration for Item creation

#### 2. Item Templates (for listings with variants)
- Created if the listing has multiple variants (e.g., different sizes or colors)
- Named according to the configured Item Name in Etsy Listing
- Linked to the configured Item Group
- Has variant attributes defined

![Item Template with Variants](images/features-item-template.png)

<!-- IMAGE: Screenshot of an Item Template document showing "Has Variants" checked, the "Attributes" table with multiple attributes (e.g., Color, Size), and the "Variants" section listing all Item Variants created from the template -->

#### 3. Item Variants
- One Item Variant per product offering
- Named with variant attribute values (e.g., `T-Shirt-Red-Large`)
- Pricing set based on Etsy inventory data
- Stock levels can be synced (if Maintain Stock is enabled)
- Unique `etsy_product_id` links it to Etsy

![Item Variant](images/features-item-variant.png)

<!-- IMAGE: Screenshot of an Item Variant document showing the variant name with attributes (e.g., "T-Shirt-Red-Large"), the "Variant Of" field pointing to the Item Template, attribute values (Color: Red, Size: Large), pricing, and the "Etsy Product ID" and "Etsy Listing" custom fields populated -->

#### 4. Item Attributes
- Attributes like "Color", "Size", "Material" are created automatically
- Mapped from Etsy's property system
- Linked back to the Etsy Listing via custom fields
- Attribute values populated from all variants

![Item Attribute](images/features-item-attribute.png)

<!-- IMAGE: Screenshot of an Item Attribute document (e.g., "Color") showing the attribute name, "Item Attribute Values" table with values (Red, Blue, Green, etc.), and the "Etsy Listing" and "Etsy Property ID" custom fields at the bottom -->

#### 5. Images
- Primary listing image attached to the Item or Item Template
- Variant-specific images (if available) attached to Item Variants

### Item Creation Logic

The app uses the following logic when creating items:

```
IF listing has variants:
    CREATE Item Template with base name
    FOR each variant:
        CREATE Item Variant with attributes
ELSE:
    CREATE single Item
```

### Updating Existing Items

When re-importing a listing that already has items in ERPNext:

- **Item Template/Item**: Name, description, and images are updated
- **Item Variants**: New variants are created; existing ones are updated
- **Pricing**: Updated to match current Etsy prices
- **Stock levels**: Not automatically synced (to prevent conflicts with ERPNext inventory management)

!!! warning "Manual Stock Management"
    The integration does **not** push stock levels from ERPNext back to Etsy. Stock management is one-way (Etsy → ERPNext) and only on initial import.

### Handling Attributes

Etsy uses a property-based system for variants (e.g., property_id 200 = "Color"). The integration:

1. Maps Etsy property IDs to human-readable attribute names
2. Creates Item Attributes in ERPNext if they don't exist
3. Links attributes to the Etsy Listing via the `etsy_property_id` custom field
4. Populates attribute values from all variants

**Example:**

Etsy Listing with variants:
- Red, Small
- Red, Large
- Blue, Small
- Blue, Large

Results in:
- Item Attribute "Color" with values: Red, Blue
- Item Attribute "Size" with values: Small, Large
- Item Template with these two attributes
- 4 Item Variants

## Historical Order Import

Bulk import orders from a specific date range to catch up on past orders.

### Use Cases

- **Initial Setup**: Import all orders since you started selling on Etsy
- **Gap Filling**: If synchronization was disabled for a period, import missing orders
- **Migration**: When moving from another system to ERPNext

### How It Works

1. Click **Import Historic Receipts** in an Etsy Shop document
2. Enter a **From Date** (e.g., "2025-01-01")
3. The app fetches all orders from that date to now
4. Orders are processed in batches with pagination
5. Each order creates the same documents as regular sync (Customer, Sales Order, etc.)

### Performance Considerations

- Importing thousands of orders can take time
- The app includes rate limiting (0.25-second delay between API calls) to respect Etsy's rate limits
- Errors are logged individually—one bad order won't stop the entire import
- You can monitor progress in the ERPNext background jobs

!!! tip "Chunking Large Imports"
    For very large imports (>1000 orders), consider importing in smaller date ranges to avoid timeouts.

## Multi-Shop Support

Manage multiple Etsy shops from a single ERPNext instance.

### How It Works

- Create one **Etsy Shop** document per Etsy shop
- Each shop has:
  - Independent OAuth credentials
  - Separate configuration (naming series, accounts, etc.)
  - Isolated synchronization (one shop's sync doesn't affect another)

### Benefits

1. **Centralized Management**: View and manage all shops from one ERPNext instance
2. **Separate Accounting**: Configure different accounts per shop for clean financial reporting
3. **Scalability**: Add new shops without changing the setup

### Example Setup

```
ERPNext Instance
├── Etsy Shop: "Handmade Jewelry"
│   ├── Company: My Business LLC
│   ├── Customer Naming: JewelryCustomer-{ETSY_BUYER_ID}
│   └── Bank Account: Jewelry Etsy Account
├── Etsy Shop: "Vintage Clothing"
│   ├── Company: My Business LLC
│   ├── Customer Naming: VintageCustomer-{ETSY_BUYER_ID}
│   └── Bank Account: Vintage Etsy Account
```

![Multiple Etsy Shops](images/features-multi-shop-list.png)

<!-- IMAGE: Screenshot of Etsy Shop list view showing 2-3 shops with columns: Shop Name, Status (Connected/Disconnected), Company, and action buttons -->

### Cross-Shop Considerations

- **Customer Matching**: If the same Etsy buyer purchases from multiple shops, separate Customers are created (because naming series differ)
  - To unify customers, use the same naming series and Customer Group across shops
- **Item Conflicts**: If two shops sell items with the same Etsy Product ID, the `etsy_product_id` unique constraint prevents conflicts

## Scheduled Synchronization

Automate data syncing on a recurring schedule.

### Configuration

Set up schedules in **Etsy Settings**:

- **Sales Order Sync**: 1-60 minutes (default: 5 minutes)
- **Item Sync**: 1-24 hours (default: 24 hours)

### How Scheduled Sync Works

1. When Etsy Settings is saved with sync enabled:
   - **Scheduled Job Type** documents are created/updated
   - Cron expressions are calculated based on intervals
2. ERPNext Scheduler runs these jobs automatically
3. Each job iterates through all connected Etsy Shops and syncs data
4. Errors are logged to the Error Log doctype

![Scheduled Job Type](images/features-scheduled-job-type.png)

<!-- IMAGE: Screenshot of a Scheduled Job Type document (e.g., "Etsy: Sync Sales Orders") showing the job name, method (etsy.api.synchronise_receipts), "Cron Format" field (e.g., */5 * * * *), "Stopped" checkbox unchecked, and "Last Execution" timestamp -->

### Entry Points

The scheduled functions are defined in `etsy/api.py`:

- `synchronise_receipts()`: Called by Sales Order scheduler
- `synchronise_listings()`: Called by Item scheduler

These functions:
- Fetch all connected Etsy Shops
- Call `import_receipts()` or `import_listings()` on each shop
- Handle errors per-shop (one shop's error doesn't stop others)

### Monitoring

Check sync status in **Etsy Settings**:

- **Last Sync**: Timestamp of last successful run
- **Next Sync**: When the next run is scheduled
- **Scheduler Link**: Direct link to the Scheduled Job Type

You can also:
- View **Background Jobs** in ERPNext to see active sync jobs
- Check **Error Log** for any sync failures

![Error Log Entries](images/features-error-log.png)

<!-- IMAGE: Screenshot of Error Log list view filtered by "Etsy" showing several error entries with columns: Error (title like "Etsy Import Error: Receipt 123"), Creation timestamp, and Seen checkbox -->

## OAuth2 Authentication

Secure, token-based authentication using Etsy's OAuth 2.0 with PKCE.

### What Is PKCE?

PKCE (Proof Key for Code Exchange) is an extension to OAuth2 that provides additional security by:

- Generating a random `code_verifier` for each login
- Creating a `code_challenge` from the verifier
- Verifying the challenge during token exchange

The Etsy Integration implements this flow automatically.

### OAuth Flow

1. **Initiate**: Click **Login** in Etsy Shop
   - App generates a `code_verifier` and stores it
   - Redirects you to Etsy's authorization page
2. **Authorize**: You approve the app on Etsy
3. **Callback**: Etsy redirects back to ERPNext with an authorization code
4. **Token Exchange**: ERPNext exchanges the code for tokens
   - Access Token (valid for a limited time)
   - Refresh Token (used to get new access tokens)
5. **Store Tokens**: Tokens are saved in the Etsy Shop document

### Automatic Token Refresh

- Access tokens expire after a certain period (usually 3600 seconds)
- The app automatically refreshes tokens before they expire
- Refresh happens transparently during API calls
- No user interaction required

### Disconnecting

Click **Disconnect** in an Etsy Shop to:

- Revoke the tokens (invalidate them on Etsy's side)
- Clear token fields in the document
- Set status to "Disconnected"

You can reconnect anytime by clicking **Login** again.

## Error Handling

The integration is designed to be resilient and handle errors gracefully.

### Error Isolation

- **Per-record processing**: Each order/listing is processed in a try-except block
- **Rollback on failure**: If one order fails, the database transaction is rolled back for that order only
- **Continue processing**: Other orders continue to process
- **Error logging**: All errors are logged to ERPNext's Error Log

### Error Logging

When an error occurs:

- An **Error Log** entry is created with:
  - Full traceback
  - Context (which shop, which order/listing)
  - Timestamp
- You can view errors in: **Home > Tools > Error Log**

### Common Error Scenarios

| Scenario | Handling |
|----------|----------|
| Missing Item | Order skipped; error logged. Import listing first, then retry. |
| Invalid Tax Account | Order skipped; error logged. Fix account configuration. |
| Duplicate Order | Skipped silently (already exists). No error. |
| API Rate Limit | Request retried with exponential backoff. |
| Network Timeout | Error logged; will retry on next sync. |
| Invalid OAuth Token | Token automatically refreshed; request retried. |

### Rate Limiting

To comply with Etsy's API rate limits:

- The app includes a 0.25-second delay between paginated requests
- Defined in `EtsyAPI.fetch_all()` in `api.py`
- Prevents hitting rate limits during bulk operations

## Data Mapping

How Etsy data maps to ERPNext documents.

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

## Limitations

Current limitations of the integration:

### Read-Only Integration
- **No write-back**: Changes in ERPNext are not pushed to Etsy
- Inventory updates in ERPNext don't sync to Etsy
- Pricing changes don't update Etsy listings

### Refunds
- Refunds are not automatically processed
- You must manually create Credit Notes in ERPNext for refunded Etsy orders

### Order Updates
- Once a Sales Order is created, subsequent Etsy updates (e.g., address changes) are not synced
- You must manually update the Sales Order in ERPNext

### Stock Sync
- Stock levels are imported on initial listing import only
- No ongoing stock synchronization

### Shipping Labels
- Shipping labels from Etsy are not imported
- Tracking numbers are not automatically synced to ERPNext

### Multiple Currencies
- Each Etsy Shop operates in one currency (as defined on Etsy)
- Multi-currency support depends on ERPNext configuration
- Currency conversion must be handled in ERPNext

## Next Steps

- **[Synchronization](synchronization.md)** - Learn how sync works in detail
- **[Troubleshooting](troubleshooting.md)** - Solve common issues
- **[API Reference](api-reference.md)** - Technical API documentation
