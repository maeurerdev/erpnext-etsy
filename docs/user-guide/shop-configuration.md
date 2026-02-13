# Shop Configuration

The **Etsy Shop** doctype is the main configuration point for connecting to an Etsy shop. You can create multiple Etsy Shop documents to manage multiple shops.

![Etsy Shop Form Overview](../images/config-etsy-shop-full.png)

<!-- IMAGE: Screenshot of a complete/filled Etsy Shop document showing all sections: Basic Info, API Credentials (collapsed), Connection (collapsed), ERP Settings (collapsed) with a connected status -->

## Basic Information

| Field | Type | Description |
|-------|------|-------------|
| **Shop Name** | Data | Unique identifier for this shop in ERPNext. Choose any descriptive name. |
| **Status** | Select | Read-only. Shows "Disconnected" or "Connected" based on OAuth status. |

## API Credentials Section

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

## Connection Section

These fields are automatically populated after successful OAuth authentication.

| Field | Type | Description |
|-------|------|-------------|
| **User ID** | Data | Your Etsy User ID (numeric). |
| **Shop ID** | Data | Your Etsy Shop ID (numeric). |
| **Access Token** | Password | OAuth access token. Auto-refreshed before expiration. |
| **Refresh Token** | Password | OAuth refresh token used to obtain new access tokens. |
| **Expires At** | Datetime | When the current access token expires. |
| **Token Type** | Data | Usually "Bearer". |

![Connection Section Details](../images/config-connection-section.png)

<!-- IMAGE: Screenshot of the expanded "Connection" section in Etsy Shop showing User ID, Shop ID, Access Token (password field with dots), Refresh Token (password field), Expires At datetime, and Token Type filled in -->

!!! info "Token Refresh"
    The app automatically refreshes access tokens before they expire. You don't need to manually manage tokens.

## ERP Settings Section

Configure how ERPNext handles data from this Etsy shop.

### Company & Language

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Company** | Link | Yes | ERPNext company to associate with this shop. |
| **Language** | Link | No | Language for data formatting. Defaults to System Settings > Language. |

### Customer Settings

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| **Customer Naming Series** | Data | `EtsyUser-{ETSY_BUYER_ID}` | Pattern for naming new Customers. Use `{ETSY_BUYER_ID}` placeholder. |
| **Customer Group** | Link | - | Default customer group. Falls back to Selling Settings > Default Customer Group. |

**Naming Series Examples:**

- `EtsyUser-{ETSY_BUYER_ID}` → `EtsyUser-123456789`
- `Etsy-.YYYY.-{ETSY_BUYER_ID}` → `Etsy-2026-123456789`
- Leave blank to use Customer doctype's default naming series

### Sales Order & Invoice Settings

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

### Item Settings

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| **Item Group** | Link | No | Default item group for imported listings. Falls back to Stock Settings > Default Item Group. |
| **Default Unit of Measure** | Link | No | Default UOM for items. Can be overridden per listing in Etsy Listing doctype. |

## Buttons and Actions

| Button | When Visible | Action |
|--------|--------------|--------|
| **Login** | When disconnected | Initiates OAuth2 flow to authenticate with Etsy. |
| **Disconnect** | When connected | Revokes tokens and disconnects the shop. |
| **Import Listings** | When connected | Fetches all active listings from Etsy and creates/updates Etsy Listing documents. |
| **Import Receipts** | When connected | Imports recent orders (receipts) from Etsy as Sales Orders. |
| **Import Historic Receipts** | When connected | Opens dialog to bulk import orders from a specific date. |

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
