# First Import & Next Steps

Your Etsy shop is connected. Let's import your first data and set up automatic synchronization.

## First Data Import

### Import Listings

1. In your Etsy Shop document, click **Import Listings**
2. The app will fetch all active listings from your Etsy shop
3. Check the **Etsy Listing** doctype to see imported listings
4. Items, Item Attributes, and Item Variants will be created automatically

![Etsy Shop Import Buttons](../images/etsy-shop-import-buttons.png)

<!-- IMAGE: Screenshot of connected Etsy Shop document showing the action buttons: "Disconnect", "Import Listings", "Import Receipts", and "Import Historic Receipts" in the toolbar -->

![Etsy Listing List](../images/etsy-listing-list.png)

<!-- IMAGE: Screenshot of Etsy Listing doctype list view showing multiple listings with columns: Listing ID, Title, Status, Etsy Shop, and thumbnail images -->

### Import Orders

1. In your Etsy Shop document, click **Import Receipts**
2. The app will import recent orders from Etsy
3. For each order, the app creates:
   - **Customer** (if new)
   - **Contact** (with shipping/billing addresses)
   - **Sales Order** (with line items)
   - **Sales Invoice** (if payment is complete)
   - **Payment Entry** (if payment is complete)

![Sales Order from Etsy](../images/sales-order-from-etsy.png)

<!-- IMAGE: Screenshot of a Sales Order in ERPNext that was created from Etsy showing the custom field "Etsy Order ID" populated, customer info, items, and totals -->

### Import Historical Orders

To import orders from a specific date range:

1. Click **Import Historic Receipts** button
2. Enter a **From Date** (how far back to import)
3. Click **Import**
4. The app will bulk import all orders since that date

![Import Historic Receipts Dialog](../images/import-historic-receipts-dialog.png)

<!-- IMAGE: Screenshot of the "Import Historic Receipts" dialog/popup showing a date picker field for "From Date" and "Import" button -->

!!! info "Initial Import Recommendation"
    For your first import, consider importing 30-90 days of historical data to establish a baseline.

## Enabling Automatic Synchronization

### Step 1: Open Etsy Settings

1. Search for **Etsy Settings** in the Awesome Bar
2. This is a singleton doctype (only one instance)

![Etsy Settings Document](../images/etsy-settings.png)

<!-- IMAGE: Screenshot of Etsy Settings document showing "Enable Synchronisation" checkbox unchecked, and two sections: "Sales Order - Synchronisation" and "Item - Synchronisation" with their respective sync interval fields -->

### Step 2: Enable Synchronization

1. Check **Enable Synchronisation**
2. Configure sync intervals:
   - **Sales Order Sync Interval**: In minutes (default: 5, range: 1-60)
   - **Item Sync Interval**: In hours (default: 24, range: 1-24)
3. Click **Save**

The app will automatically create Scheduled Job Types and start syncing in the background.

![Etsy Settings Enabled](../images/etsy-settings-enabled.png)

<!-- IMAGE: Screenshot of Etsy Settings with "Enable Synchronisation" checked, showing sync intervals configured (e.g., 5 minutes for sales orders, 24 hours for items), and the "Last Sync", "Next Sync", and "Scheduler Link" fields now visible and populated -->

### Step 3: Monitor Sync Status

Back in Etsy Settings, you can view:

- **Last Sync**: Timestamp of last successful sync
- **Next Sync**: When the next sync is scheduled
- **Scheduler Link**: Link to the Scheduled Job Type

!!! tip "Disable Sync Temporarily"
    Set sync interval to `0` to disable automatic sync for that data type.

## Quick Reference

### Etsy Shop Buttons

| Button | Action |
|--------|--------|
| **Login** | Start OAuth2 authentication flow |
| **Disconnect** | Revoke tokens and disconnect shop |
| **Import Listings** | Fetch all active listings |
| **Import Receipts** | Import recent orders |
| **Import Historic Receipts** | Bulk import orders from date |

### Default Naming Series

| DocType | Default Pattern |
|---------|----------------|
| Customer | `EtsyUser-{ETSY_BUYER_ID}` |
| Sales Order | `EtsyOrder-{ETSY_ORDER_ID}` |
| Sales Invoice | `EtsyInvoice-{ETSY_ORDER_ID}` |

!!! note "Customizable Naming"
    All naming series can be customized in the Etsy Shop document.

### Common Commands

```bash
# Uninstall the app
bench --site your-site-name uninstall-app etsy --no-backup

# Reinstall after updates
bench --site your-site-name migrate

# Run tests
bench --site your-site-name run-tests --app etsy

# Build assets after changes
bench build --app etsy
```

## What's Next?

Now that you're up and running, explore the User Guide for deeper configuration:

- **[Shop Configuration](../user-guide/shop-configuration.md)** — All Etsy Shop doctype fields and options
- **[Listings & Items](../user-guide/listings-and-items.md)** — How listings become Items in ERPNext
- **[Orders & Customers](../user-guide/orders-and-customers.md)** — Sales Order sync details and edge cases
- **[Synchronization](../user-guide/synchronization.md)** — Manual vs automatic sync, scheduling, and monitoring
- **[Troubleshooting](../user-guide/troubleshooting.md)** — Common issues and solutions
