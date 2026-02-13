# Synchronization

This page explains how data synchronization works between Etsy and ERPNext.

## Sync Overview

The Etsy Integration supports two types of synchronization:

1. **Manual Sync**: On-demand import via buttons in Etsy Shop doctype
2. **Automatic Sync**: Scheduled background jobs configured in Etsy Settings

Both types use the same underlying import methods, ensuring consistent behavior.

## Sync Direction

The integration is **one-way**: Etsy → ERPNext

- Data flows **from Etsy to ERPNext**
- Changes in ERPNext are **not** pushed back to Etsy
- Etsy is the source of truth

This design prevents accidental overwrites and keeps Etsy as your primary selling platform.

## Manual Synchronization

Trigger imports manually using buttons in the Etsy Shop doctype.

### Import Listings

**Button**: `Import Listings`

**What It Does**:
1. Fetches all active listings from Etsy for this shop
2. For each listing:
   - Creates or updates an Etsy Listing document
   - Fetches inventory data (variants, pricing, stock)
   - Creates/updates Item Templates and Item Variants
   - Creates/updates Item Attributes
3. Logs any errors to Error Log

**When to Use**:
- After adding new products on Etsy
- When product details change (pricing, descriptions, images)
- Periodically to ensure ERPNext has the latest listing data

**API Calls**:
- `GET /v3/application/shops/{shop_id}/listings`
- `GET /v3/application/listings/{listing_id}/inventory` (per listing)

### Import Receipts

**Button**: `Import Receipts`

**What It Does**:
1. Fetches recent receipts (orders) from Etsy for this shop
2. For each receipt:
   - Creates or matches a Customer based on `etsy_customer_id`
   - Creates or updates a Contact with shipping/billing addresses
   - Creates a Sales Order with line items
   - Creates a Sales Invoice (if paid)
   - Creates a Payment Entry (if paid)
3. Logs any errors to Error Log

**When to Use**:
- After receiving new orders on Etsy
- To catch up on recent orders
- Before automatic sync is enabled

**API Calls**:
- `GET /v3/application/shops/{shop_id}/receipts` (paginated)
- `GET /v3/application/shops/{shop_id}/receipts/{receipt_id}/transactions` (per receipt)

**Filters Applied**:
- Only fetches receipts updated since the last sync
- Sorts by `updated` timestamp descending

### Import Historic Receipts

**Button**: `Import Historic Receipts`

**What It Does**:
1. Opens a dialog prompting for a "From Date"
2. Fetches all receipts from that date to now
3. Processes each receipt the same as "Import Receipts"
4. Handles pagination for large date ranges

**When to Use**:
- Initial setup: Import all past orders
- Gap filling: If sync was disabled for a period
- Migration: Bringing historical data into ERPNext

**API Calls**:
- `GET /v3/application/shops/{shop_id}/receipts?min_created={timestamp}` (paginated)

**Pagination**:
- Etsy API returns up to 100 receipts per page
- The app automatically fetches all pages using the `offset` parameter

## Automatic Synchronization

Configure scheduled background jobs in Etsy Settings to automate syncing.

### How It Works

1. **Enable Sync**: Check "Enable Synchronisation" in Etsy Settings
2. **Set Intervals**: Configure sync intervals for Sales Orders and Items
3. **Save**: Etsy Settings creates/updates Scheduled Job Type documents
4. **Scheduler Runs**: ERPNext's background scheduler executes jobs based on cron expressions

### Scheduled Job Types

Two Scheduled Job Types are created:

#### 1. Sales Order Sync Job

- **Function**: `etsy.api.synchronise_receipts`
- **Frequency**: Based on "Sales Order Sync Interval" (1-60 minutes)
- **Cron Example**: `*/5 * * * *` (every 5 minutes)
- **Job Type**: `Cron`

**What It Does**:
- Loops through all Etsy Shops with status = "Connected"
- Calls `import_receipts()` on each shop
- Logs errors per shop without stopping the entire job

#### 2. Item Sync Job

- **Function**: `etsy.api.synchronise_listings`
- **Frequency**: Based on "Item Sync Interval" (1-24 hours)
- **Cron Example**: `0 */24 * * *` (every 24 hours)
- **Job Type**: `Cron`

**What It Does**:
- Loops through all Etsy Shops with status = "Connected"
- Calls `import_listings()` on each shop
- Logs errors per shop without stopping the entire job

### Cron Expression Calculation

The app converts your interval settings to cron expressions:

| Interval | Cron Expression | Meaning |
|----------|-----------------|---------|
| 5 minutes | `*/5 * * * *` | Every 5 minutes |
| 15 minutes | `*/15 * * * *` | Every 15 minutes |
| 1 hour | `0 * * * *` | Every hour at minute 0 |
| 6 hours | `0 */6 * * *` | Every 6 hours |
| 24 hours | `0 */24 * * *` | Every 24 hours |

### Disabling Sync

To disable synchronization:

- **Globally**: Uncheck "Enable Synchronisation" in Etsy Settings
- **Per Data Type**: Set sync interval to `0`

When disabled, Scheduled Job Types are updated with `stopped = 1`, preventing further execution.

### Monitoring

**In Etsy Settings**:
- **Last Sync**: Shows when the job last ran successfully
- **Next Sync**: Shows when the job will run next
- **Scheduler Link**: Direct link to the Scheduled Job Type

![Monitoring in Etsy Settings](images/sync-monitoring-settings.png)

<!-- IMAGE: Screenshot of Etsy Settings with sync enabled, showing populated "Last Sync" and "Next Sync" timestamps, and clickable "Scheduler Link" fields for both Sales Order and Item sync sections -->

**In Scheduled Job Type**:
- View the job document via the Scheduler Link
- Check **Last Execution** timestamp
- View execution logs

![Scheduled Job Execution](images/sync-scheduled-job-execution.png)

<!-- IMAGE: Screenshot of a Scheduled Job Type document showing execution details: "Last Execution" timestamp, execution status, and potentially a "View Logs" section or similar monitoring info -->

**In Error Log**:
- All sync errors are logged with full tracebacks
- Search for "Etsy" in Error Log to find integration-related errors

## Sync Behavior Details

### Duplicate Prevention

The integration uses unique custom fields to prevent duplicate records:

| DocType | Unique Field | Purpose |
|---------|--------------|---------|
| Customer | `etsy_customer_id` | Prevents duplicate customers for the same Etsy buyer |
| Contact | `etsy_customer_id` | Prevents duplicate contacts |
| Sales Order | `etsy_order_id` | Prevents duplicate orders for the same Etsy receipt |
| Sales Invoice | `etsy_order_id` | Links invoice to order |
| Item | `etsy_product_id` | Prevents duplicate items for the same Etsy product |

**How It Works**:
- Before creating a new document, the app checks if one with the same Etsy ID exists
- If it exists, the record is updated (or skipped if no updates are needed)
- If it doesn't exist, a new record is created

### Update Logic

#### Listings
When re-importing a listing:
- **Etsy Listing**: Title, description, image, status, views, likes updated
- **Items**: Name, description, pricing updated
- **Item Variants**: New variants added; existing variants updated
- **Item Attributes**: New values added to attributes

#### Receipts
When re-importing a receipt:
- If the Sales Order already exists (matched by `etsy_order_id`), it's **skipped**
- Orders are not updated after initial creation
- Subsequent changes on Etsy (e.g., address updates) require manual ERPNext edits

### Error Handling During Sync

Each record is processed in a try-except block:

```python
for receipt in receipts:
    try:
        # Process receipt
        create_customer()
        create_sales_order()
        create_sales_invoice()
        create_payment_entry()
        frappe.db.commit()  # Commit this record
    except Exception as e:
        frappe.db.rollback()  # Rollback only this record
        frappe.log_error(title=f"Etsy Sync Error: Receipt {receipt.id}", message=traceback.format_exc())
        continue  # Move to next record
```

This ensures:
- One bad record doesn't stop the entire sync
- Each record is atomic (all-or-nothing)
- Errors are logged for later review

### Rate Limiting

To respect Etsy's API rate limits:

- **Delay Between Requests**: 0.25 seconds (250ms)
- **Implementation**: In `EtsyAPI.fetch_all()` method
- **Applies To**: Paginated requests (listing inventory, receipts)

**Etsy Rate Limits** (as of API v3):
- 10 requests per second per OAuth token
- The 250ms delay ensures ~4 requests/second, well within limits

### Pagination

Etsy API returns results in pages. The integration handles this automatically.

#### Pagination Parameters
- `limit`: Number of records per page (default: 100)
- `offset`: Starting position for the page (default: 0)

#### Example Flow
1. Request: `GET /receipts?limit=100&offset=0` → Returns 100 receipts
2. Request: `GET /receipts?limit=100&offset=100` → Returns next 100 receipts
3. Continue until API returns fewer than 100 receipts (last page)

**Implementation**: `EtsyAPI.fetch_all()` method in `api.py`

## Sync Performance

### Factors Affecting Performance

1. **Order Volume**: More orders = longer sync time
2. **Listing Count**: More listings = longer sync time
3. **Network Latency**: Distance to Etsy's API servers
4. **ERPNext Load**: High database load can slow down document creation
5. **Variant Complexity**: Listings with many variants take longer to process

### Optimization Tips

#### For High-Volume Shops
- **Increase sync interval**: Use 10-15 minutes for Sales Orders instead of 5
- **Stagger schedules**: If managing multiple shops, offset their sync times
- **Historical imports**: Run during off-peak hours

#### For Performance Monitoring
- **Enable RQ (Redis Queue)**: Use ERPNext's background job system for better performance
- **Monitor Error Log**: Check for recurring errors that slow down sync
- **Database Indexing**: Ensure custom fields (`etsy_*`) are indexed

### Expected Sync Times

Approximate times (varies by server and network):

| Operation | Record Count | Estimated Time |
|-----------|--------------|----------------|
| Import Listings | 100 listings | 2-5 minutes |
| Import Receipts | 100 orders | 3-7 minutes |
| Historic Import | 1000 orders | 20-40 minutes |

!!! info "Background Processing"
    Syncs run in the background via ERPNext Scheduler. They don't block your UI or other operations.

## Data Freshness

How often your data is up-to-date depends on sync intervals:

| Sync Interval | Data Freshness | Use Case |
|---------------|----------------|----------|
| 1-5 minutes | Near real-time | High-volume shops, critical order processing |
| 10-30 minutes | Recent | Moderate-volume shops, standard operations |
| 1-6 hours | Periodic | Low-volume shops, non-critical updates |
| 24 hours | Daily | Listings that change infrequently |

### Recommended Intervals

- **Sales Orders**: 5-10 minutes (orders need quick processing)
- **Listings**: 24 hours (listings change less frequently)

Adjust based on your shop's order volume and operational needs.

## Manual vs. Automatic Sync

| Aspect | Manual Sync | Automatic Sync |
|--------|-------------|----------------|
| **Trigger** | Button click | Scheduled cron job |
| **Frequency** | On-demand | Recurring (based on interval) |
| **User Interaction** | Required | None (background) |
| **Use Case** | Immediate updates, testing | Ongoing operations |
| **Error Visibility** | Immediate feedback | Check Error Log |

**Best Practice**: Use manual sync during setup and testing, then enable automatic sync for production.

## Troubleshooting Sync Issues

### Sync Not Running

**Check**:
1. Is "Enable Synchronisation" checked in Etsy Settings?
2. Is the sync interval set to a value > 0?
3. Are Scheduled Job Types active (not stopped)?
4. Is ERPNext Scheduler enabled? (Check `site_config.json` for `scheduler_enabled`)

**Solution**:
- Enable the scheduler: `bench --site [site-name] set-config scheduler_enabled 1`
- Restart bench: `bench restart`

### Duplicate Records

**Symptom**: Multiple customers/orders for the same Etsy buyer/receipt

**Cause**: Custom field `etsy_*_id` not unique or not set correctly

**Solution**:
- Verify custom fields are created: `bench console` → `frappe.get_all("Custom Field", filters={"fieldname": ["like", "etsy_%"]})`
- Re-run `after_install()`: `bench console` → `from etsy.install import after_install; after_install()`

### Orders Not Importing

**Symptom**: Sync runs but no Sales Orders created

**Check**:
1. Are there new orders on Etsy?
2. Check Error Log for import errors
3. Verify Etsy Shop is "Connected"

**Common Errors**:
- Missing Item: Import listing first
- Invalid Tax Account: Check configuration in Etsy Shop

### Slow Sync

**Symptom**: Sync takes a long time or times out

**Solutions**:
- Reduce sync interval to avoid large backlogs
- Import historical data in smaller date ranges
- Increase timeout in site_config.json: `"job_timeout": 1800`

## Next Steps

- **[Troubleshooting](troubleshooting.md)** - Detailed troubleshooting guide
- **[API Reference](api-reference.md)** - Technical API details
- **[Development](development.md)** - Contribute to the project
