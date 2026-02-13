# Configuration

This guide covers detailed configuration options for all Etsy Integration doctypes.

## Etsy Shop

The **Etsy Shop** doctype is the main configuration point for connecting to an Etsy shop. You can create multiple Etsy Shop documents to manage multiple shops.

![Etsy Shop Form Overview](images/config-etsy-shop-full.png)

<!-- IMAGE: Screenshot of a complete/filled Etsy Shop document showing all sections: Basic Info, API Credentials (collapsed), Connection (collapsed), ERP Settings (collapsed) with a connected status -->

### Basic Information

| Field | Type | Description |
|-------|------|-------------|
| **Shop Name** | Data | Unique identifier for this shop in ERPNext. Choose any descriptive name. |
| **Status** | Select | Read-only. Shows "Disconnected" or "Connected" based on OAuth status. |

### API Credentials Section

These fields store your Etsy Personal App credentials.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **CLIENT_ID** | Data | Yes | Your Etsy app's Keystring from the Etsy Developer Portal. |
| **CLIENT_SECRET** | Password | Yes | Your Etsy app's Shared Secret. Stored securely. |
| **Redirect URI** | Data | Read-only | Auto-generated OAuth callback URL. Copy this to your Etsy app settings. |
| **Use localhost** | Check | No | Enable for local development only. Uses `http://localhost` instead of your site URL. |
| **Code Verifier** | Data | Read-only | Internal OAuth2 PKCE parameter. Auto-generated during login. |

!!! warning "Credential Security"
    Never share your CLIENT_SECRET. It's stored as a Password field and hidden in the UI after saving.

### Connection Section

These fields are automatically populated after successful OAuth authentication.

| Field | Type | Description |
|-------|------|-------------|
| **User ID** | Data | Your Etsy User ID (numeric). |
| **Shop ID** | Data | Your Etsy Shop ID (numeric). |
| **Access Token** | Password | OAuth access token. Auto-refreshed before expiration. |
| **Refresh Token** | Password | OAuth refresh token used to obtain new access tokens. |
| **Expires At** | Datetime | When the current access token expires. |
| **Token Type** | Data | Usually "Bearer". |

![Connection Section Details](images/config-connection-section.png)

<!-- IMAGE: Screenshot of the expanded "Connection" section in Etsy Shop showing User ID, Shop ID, Access Token (password field with dots), Refresh Token (password field), Expires At datetime, and Token Type filled in -->

!!! info "Token Refresh"
    The app automatically refreshes access tokens before they expire. You don't need to manually manage tokens.

### ERP Settings Section

Configure how ERPNext handles data from this Etsy shop.

#### Company & Language

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Company** | Link | Yes | ERPNext company to associate with this shop. |
| **Language** | Link | No | Language for data formatting. Defaults to System Settings > Language. |

#### Customer Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| **Customer Naming Series** | Data | `EtsyUser-{ETSY_BUYER_ID}` | Pattern for naming new Customers. Use `{ETSY_BUYER_ID}` placeholder. |
| **Customer Group** | Link | - | Default customer group. Falls back to Selling Settings > Default Customer Group. |

**Naming Series Examples:**

- `EtsyUser-{ETSY_BUYER_ID}` → `EtsyUser-123456789`
- `Etsy-.YYYY.-{ETSY_BUYER_ID}` → `Etsy-2026-123456789`
- Leave blank to use Customer doctype's default naming series

#### Sales Order & Invoice Settings

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| **Sales Order Naming Series** | Data | No | `EtsyOrder-{ETSY_ORDER_ID}` | Pattern for Sales Orders. Use `{ETSY_ORDER_ID}` placeholder. |
| **Sales Invoice Naming Series** | Data | No | `EtsyInvoice-{ETSY_ORDER_ID}` | Pattern for Sales Invoices. Use `{ETSY_ORDER_ID}` placeholder. |
| **Sales Tax Account** | Link | Yes | - | Account for product sales taxes. |
| **Shipping Tax Account** | Link | Yes | - | Account for shipping taxes. |
| **Bank Account for physical sales** | Link | Yes | - | Account for payments on physical products. |
| **Bank Account for digital sales** | Link | Yes | - | Account for payments on digital products. |

!!! tip "Separate Bank Accounts"
    Etsy distinguishes between physical and digital sales. Configure separate accounts to track them differently.

**Naming Series Examples:**

- `EtsyOrder-{ETSY_ORDER_ID}` → `EtsyOrder-3456789012`
- `SO-.YYYY.-Etsy-{ETSY_ORDER_ID}` → `SO-2026-Etsy-3456789012`

#### Item Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Item Group** | Link | No | Default item group for imported listings. Falls back to Stock Settings > Default Item Group. |
| **Default Unit of Measure** | Link | No | Default UOM for items. Can be overridden per listing in Etsy Listing doctype. |

### Buttons and Actions

| Button | When Visible | Action |
|--------|--------------|--------|
| **Login** | When disconnected | Initiates OAuth2 flow to authenticate with Etsy. |
| **Disconnect** | When connected | Revokes tokens and disconnects the shop. |
| **Import Listings** | When connected | Fetches all active listings from Etsy and creates/updates Etsy Listing documents. |
| **Import Receipts** | When connected | Imports recent orders (receipts) from Etsy as Sales Orders. |
| **Import Historic Receipts** | When connected | Opens dialog to bulk import orders from a specific date. |

## Etsy Settings

The **Etsy Settings** doctype is a singleton that controls automatic synchronization schedules. There's only one instance system-wide.

### Enable Synchronization

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| **Enable Synchronisation** | Check | Unchecked | Master switch to enable/disable all automatic syncing. |

When disabled, all scheduled sync jobs are stopped. You can still manually import data via Etsy Shop buttons.

### Sales Order Synchronization

Configure automatic order synchronization.

| Field | Type | Range | Default | Description |
|-------|------|-------|---------|-------------|
| **Sync Interval** | Int | 1-60 minutes | 5 | How often to sync orders. Set to `0` to disable. |
| **Last Sync** | Datetime | Read-only | - | Timestamp of last successful sync. |
| **Next Sync** | Datetime | Read-only | - | When the next sync will run. |
| **Scheduler Link** | Link | Read-only | - | Link to the Scheduled Job Type document. |

### Item Synchronization

Configure automatic listing synchronization.

| Field | Type | Range | Default | Description |
|-------|------|-------|---------|-------------|
| **Sync Interval** | Int | 1-24 hours | 24 | How often to sync listings. Set to `0` to disable. |
| **Last Sync** | Datetime | Read-only | - | Timestamp of last successful sync. |
| **Next Sync** | Datetime | Read-only | - | When the next sync will run. |
| **Scheduler Link** | Link | Read-only | - | Link to the Scheduled Job Type document. |

### How Scheduled Jobs Work

When you save Etsy Settings with synchronization enabled:

1. The app creates or updates **Scheduled Job Type** documents
2. Cron expressions are generated based on your interval settings
3. ERPNext Scheduler automatically runs these jobs in the background
4. Each job syncs data for all connected Etsy Shops

**Cron Calculation Examples:**

- Sales Order Sync Interval: `5` minutes → Cron: `*/5 * * * *`
- Item Sync Interval: `24` hours → Cron: `0 */24 * * *`

!!! tip "Performance Consideration"
    Sales orders change frequently, so a 5-minute interval is reasonable. Listings change less often, so 24 hours is sufficient for most shops.

## Etsy Listing

The **Etsy Listing** doctype represents individual Etsy listings. These are automatically created when you import listings from Etsy.

![Etsy Listing Form](images/config-etsy-listing.png)

<!-- IMAGE: Screenshot of Etsy Listing document showing both tabs: "Details" tab (selected) with listing info, image, title, description, and "Settings" tab with Item Settings fields -->

### Details Tab

#### Listing Information

| Field | Type | Editable | Description |
|-------|------|----------|-------------|
| **Listing ID** | Data | No | Etsy's unique listing identifier. Auto-populated. |
| **Status** | Select | No | Listing status: Active, Inactive, Sold Out, Draft, Expired, Edit. |
| **Image** | Attach Image | No | Primary listing image. Auto-fetched from Etsy. |
| **Etsy Shop** | Link | No | Which Etsy Shop this listing belongs to. |
| **Views** | Int | No | Number of views on Etsy. |
| **Likes** | Int | No | Number of favorites on Etsy. |
| **Title** | Small Text | Yes | Listing title from Etsy. Editable for reference. |
| **Description** | Text Editor | Yes | Listing description from Etsy. Editable for reference. |
| **Inventory** | Long Text | No | JSON representation of inventory data from Etsy. |

!!! note "Editing Restrictions"
    Most fields are read-only as they're synced from Etsy. Editing Title or Description here doesn't change them on Etsy—these are for reference only.

### Settings Tab

Configure how this listing is handled in ERPNext when creating/updating Items.

#### Item Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Item Name** | Data | Yes | Base name for Item Template. Max 60 characters. |
| **Item Group** | Link | Yes | Item Group for this listing's items. Must not be a group (leaf node only). |
| **Unit of Measure** | Link | Yes | UOM for this listing's items. |
| **Maintain Stock** | Check | Yes (default: checked) | Whether to track inventory for this listing's items. |

**Item Creation Behavior:**

- If the listing has variants, an **Item Template** is created with the Item Name
- Each variant becomes an **Item Variant** with a generated name (e.g., `ItemName-Red-Small`)
- If the listing has no variants, a single **Item** is created

!!! tip "Item Group Configuration"
    Choose a specific, non-group Item Group. For example, use "Jewelry" instead of "Products" if "Products" has child groups.

### Inventory Data

The **Inventory** field stores the raw JSON response from Etsy's inventory API. This includes:

- Product offerings (variants)
- Pricing information
- Stock levels
- Property values (size, color, etc.)

This data is used internally by the app to create Item Attributes and Item Variants.

## Custom Fields on Standard Doctypes

The app adds read-only custom fields to standard ERPNext doctypes for tracking Etsy data.

![Custom Field on Customer](images/config-custom-field-customer.png)

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

![Custom Field on Sales Order](images/config-custom-field-sales-order.png)

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

## Configuration Best Practices

### Security

- **Rotate credentials** periodically by creating a new Etsy Personal App
- **Restrict permissions** to System Manager role only
- **Backup your site** before major configuration changes

### Naming Series

- **Use unique prefixes** (e.g., `Etsy-`) to distinguish Etsy orders from manual orders
- **Include year** for better organization: `Etsy-.YYYY.-{ETSY_ORDER_ID}`
- **Keep it short** to avoid issues with field length limits

### Accounts Configuration

- **Separate tax accounts** for sales and shipping taxes help with reporting
- **Dedicated bank accounts** for Etsy make reconciliation easier
- **Use sub-accounts** if managing multiple shops (e.g., `Bank - Etsy Shop 1`)

### Sync Intervals

- **Start conservative**: Begin with longer intervals and adjust based on order volume
- **Balance load**: Don't set all shops to sync at the same time
- **Monitor performance**: Check Error Log for any sync failures

### Multi-Shop Setup

When managing multiple shops:

1. Create separate Etsy Shop documents for each shop
2. Use different naming series to distinguish orders (e.g., `Shop1-`, `Shop2-`)
3. Consider using different companies or cost centers for accounting separation
4. Stagger sync schedules to distribute server load

## Next Steps

- **[Features](features.md)** - Learn what the integration can do
- **[Synchronization](synchronization.md)** - Understand sync behavior in detail
- **[Troubleshooting](troubleshooting.md)** - Solve common configuration issues
