# Troubleshooting

This guide helps you diagnose and resolve common issues with the Etsy Integration.

## OAuth and Authentication Issues

### Error: "OAuth callback failed" or "Invalid redirect URI"

**Symptoms**:
- Clicking "Login" redirects to Etsy, but callback fails
- Error message about redirect URI mismatch

**Causes**:
- Redirect URI in ERPNext doesn't match the one configured in your Etsy Personal App
- Site URL is incorrect or has changed

**Solutions**:

1. **Verify Redirect URI**:
   - In ERPNext: Open Etsy Shop → Copy the "Redirect URI" field
   - In Etsy Developer Portal: Go to your app → OAuth Redirect URIs
   - Ensure they **exactly match** (including `http://` or `https://`, port numbers, trailing slashes)

2. **Update Site URL**:
   ```bash
   bench config dns_multitenant off
   bench --site [site-name] set-config host_name "https://yourdomain.com"
   ```

3. **Use localhost for Development**:
   - In Etsy Shop, check "Use localhost"
   - Add `http://localhost:8000/api/method/etsy.etsy.doctype.etsy_shop.etsy_shop.oauth_callback` to Etsy app

### Error: "Access token expired"

**Symptoms**:
- API requests fail with "401 Unauthorized"
- Etsy Shop status shows "Connected" but imports fail

**Causes**:
- Access token expired and refresh failed
- Refresh token is invalid or revoked

**Solutions**:

1. **Reconnect the Shop**:
   - Click "Disconnect" in Etsy Shop
   - Click "Login" to re-authenticate
   - This generates fresh tokens

2. **Check Token Expiry**:
   - Look at "Expires At" field in Etsy Shop
   - If it's in the past, tokens need refresh

3. **Verify OAuth Credentials**:
   - Ensure CLIENT_ID and CLIENT_SECRET are correct
   - Regenerate them in Etsy Developer Portal if needed

### Error: "Invalid client credentials"

**Symptoms**:
- OAuth flow fails immediately
- Error about invalid client_id or client_secret

**Causes**:
- Incorrect CLIENT_ID or CLIENT_SECRET
- Credentials copied with extra spaces or characters

**Solutions**:

1. **Re-enter Credentials**:
   - Go to Etsy Developer Portal → Your Apps
   - Copy Keystring (CLIENT_ID) carefully
   - Copy Shared Secret (CLIENT_SECRET) carefully
   - Paste into Etsy Shop fields, ensure no extra spaces

2. **Check App Status on Etsy**:
   - Ensure your Etsy Personal App is active (not suspended)

## Import Issues

### Orders Not Importing

**Symptoms**:
- Click "Import Receipts" but no Sales Orders are created
- Sync runs but order count doesn't increase

**Diagnosis Steps**:

1. **Check Error Log**:
   - Go to: Home > Tools > Error Log
   - Search for "Etsy" or filter by today's date
   - Review error messages

![Error Log with Etsy Errors](images/troubleshoot-error-log.png)

<!-- IMAGE: Screenshot of Error Log list filtered/searched for "Etsy" showing one or more error entries with titles like "Etsy Import Error" and timestamps -->

2. **Verify Connection**:
   - Open Etsy Shop document
   - Check "Status" field shows "Connected"
   - Check "Expires At" is in the future

3. **Check Etsy Shop Configuration**:
   - Ensure required fields are filled:
     - Company
     - Sales Tax Account
     - Shipping Tax Account
     - Bank Accounts

**Common Errors and Fixes**:

#### "Account Not Found"
- **Error**: `Account 'Sales Tax' does not exist`
- **Fix**: Set valid tax accounts in Etsy Shop → Sales Order & Invoice Settings

#### "Customer Creation Failed"
- **Error**: `Customer naming series not set`
- **Fix**: Set Customer Naming Series in Etsy Shop → Customer Settings (or leave blank for default)

#### "Item Not Found"
- **Error**: `Item with Etsy Product ID X not found`
- **Fix**: Import listings first before importing orders
  - Click "Import Listings" in Etsy Shop
  - Then retry "Import Receipts"

### Listings Not Importing

**Symptoms**:
- Click "Import Listings" but no Etsy Listing documents are created
- Items not created in ERPNext

**Diagnosis Steps**:

1. **Check Active Listings on Etsy**:
   - Log in to Etsy → Shop Manager → Listings
   - Ensure you have active listings
   - The integration only imports "Active" listings

2. **Check Error Log**:
   - Look for "Listing import failed" errors
   - Review specific error messages

**Common Errors and Fixes**:

#### "Item Group Not Set"
- **Error**: `Item Group is required`
- **Fix**: Set Item Group in Etsy Shop → Item Settings OR in each Etsy Listing → Settings tab

#### "UOM Not Found"
- **Error**: `Unit of Measure 'Nos' does not exist`
- **Fix**: Set a valid UOM in Etsy Shop → Item Settings OR in each Etsy Listing → Settings tab

#### "Invalid Item Name"
- **Error**: `Item Name exceeds maximum length`
- **Fix**: Edit the Etsy Listing → Settings tab → Set a shorter Item Name (max 60 characters)

### Duplicate Records

**Symptoms**:
- Multiple Customers for the same Etsy buyer
- Multiple Sales Orders for the same Etsy receipt

**Causes**:
- Custom fields not created properly during installation
- Database index not applied

**Solutions**:

1. **Re-run Installation Hook**:
   ```bash
   bench --site [site-name] console
   ```
   ```python
   from etsy.install import after_install
   after_install()
   exit()
   ```

2. **Verify Custom Fields**:
   ```bash
   bench --site [site-name] console
   ```
   ```python
   import frappe
   # Check if etsy_customer_id field exists on Customer
   frappe.get_all("Custom Field", filters={"dt": "Customer", "fieldname": "etsy_customer_id"})
   exit()
   ```

3. **Manually Remove Duplicates**:
   - Identify duplicate records
   - Merge or delete duplicates manually
   - Ensure future imports don't create duplicates

## Synchronization Issues

### Automatic Sync Not Running

**Symptoms**:
- "Last Sync" timestamp in Etsy Settings doesn't update
- Orders/listings not syncing automatically

**Diagnosis Steps**:

1. **Check Scheduler Status**:
   ```bash
   bench --site [site-name] console
   ```
   ```python
   import frappe
   frappe.get_value("System Settings", None, "scheduler_enabled")
   # Should return 1 (enabled)
   exit()
   ```

2. **Enable Scheduler** (if disabled):
   ```bash
   bench --site [site-name] enable-scheduler
   bench restart
   ```

3. **Check Scheduled Job Types**:
   - Go to: Home > Tools > Scheduled Job Type
   - Search for "Etsy"
   - Verify:
     - "Stopped" is unchecked
     - "Cron Format" is set correctly

![Scheduled Job Type Troubleshooting](images/troubleshoot-scheduled-job.png)

<!-- IMAGE: Screenshot of a Scheduled Job Type document showing the "Stopped" checkbox (should be unchecked for active jobs), "Cron Format" field with a cron expression, and "Last Execution" timestamp to verify it's running -->

**Common Fixes**:

#### Scheduler Disabled
```bash
bench --site [site-name] enable-scheduler
bench restart
```

#### Job Marked as Stopped
- Open the Scheduled Job Type document
- Uncheck "Stopped"
- Save

#### Cron Expression Invalid
- Check "Cron Format" field in Scheduled Job Type
- Should be like `*/5 * * * *` for 5-minute intervals
- Edit Etsy Settings and save to regenerate cron

### Sync Errors in Error Log

**Symptoms**:
- Sync runs but creates errors in Error Log
- Some records imported successfully, others fail

**Diagnosis**:
- Review Error Log entries for specific error messages
- Each error is isolated to a single record

**Common Errors**:

#### "Unique constraint violated"
- **Error**: `Duplicate entry 'X' for key 'etsy_order_id'`
- **Meaning**: Order already exists (expected behavior)
- **Action**: No action needed; duplicate prevention working correctly

#### "Document not saved"
- **Error**: `Sales Order could not be saved`
- **Meaning**: Validation failed (missing required field, invalid data)
- **Action**: Review error message for specific field, fix configuration

## Performance Issues

### Slow Imports

**Symptoms**:
- Imports take a very long time
- Timeouts during large historical imports

**Causes**:
- Large number of records to import
- Slow network connection
- High database load

**Solutions**:

1. **Increase Job Timeout**:
   ```bash
   bench --site [site-name] set-config job_timeout 3600
   bench restart
   ```

2. **Import in Batches**:
   - For historical imports, use smaller date ranges
   - Instead of importing 1 year, import 1 month at a time

3. **Optimize Database**:
   ```bash
   bench --site [site-name] mariadb
   ```
   ```sql
   OPTIMIZE TABLE `tabSales Order`;
   OPTIMIZE TABLE `tabCustomer`;
   OPTIMIZE TABLE `tabItem`;
   exit;
   ```

4. **Run During Off-Peak Hours**:
   - Schedule large imports during low-traffic times

### High Memory Usage

**Symptoms**:
- Server memory usage spikes during sync
- Out-of-memory errors

**Solutions**:

1. **Reduce Sync Interval**:
   - Smaller batches = lower memory usage
   - Change Sales Order interval from 5 to 10-15 minutes

2. **Increase Server Resources**:
   - Add more RAM to your server
   - Use a larger VM/instance

## Item and Variant Issues

### Variants Not Created

**Symptoms**:
- Item Template created but no Item Variants
- Listing has variations on Etsy but not in ERPNext

**Diagnosis**:
- Check Error Log for "Variant creation failed"
- Verify inventory data in Etsy Listing → Inventory field (JSON)

**Common Causes**:

1. **Missing Attributes**:
   - Item Attributes not created properly
   - **Fix**: Manually create Item Attributes matching Etsy properties (Color, Size, etc.)

2. **Invalid Attribute Values**:
   - Attribute values contain invalid characters
   - **Fix**: Edit Item Attribute, clean up values

### Item Prices Not Updating

**Symptoms**:
- Etsy prices change but ERPNext items have old prices

**Explanation**:
- Prices are updated only when you manually import listings or when auto-sync runs
- Price updates are not pushed back to Etsy

**Solutions**:
- Manually click "Import Listings" to refresh prices
- Enable automatic listing sync in Etsy Settings

### Stock Levels Out of Sync

**Symptoms**:
- Stock levels in ERPNext don't match Etsy

**Explanation**:
- Stock sync is one-way (Etsy → ERPNext) and only on initial import
- Ongoing stock sync is not supported

**Workaround**:
- Manage stock on Etsy only
- Use ERPNext for order processing and accounting, not inventory management
- Or manually update stock levels in ERPNext after Etsy changes

## Configuration Issues

### Missing Custom Fields

**Symptoms**:
- "etsy_*" fields not visible on Customer, Sales Order, etc.
- Errors about custom fields not found

**Diagnosis**:
```bash
bench --site [site-name] console
```
```python
import frappe
frappe.get_all("Custom Field", filters={"fieldname": ["like", "etsy_%"]}, pluck="name")
# Should return multiple field names
exit()
```

**Solutions**:

1. **Re-run Installation**:
   ```bash
   bench --site [site-name] console
   ```
   ```python
   from etsy.install import after_install
   after_install()
   exit()
   ```

2. **Manually Create Custom Fields**:
   - Go to: Customization > Custom Field
   - Create fields as defined in `hooks.py`

![Custom Field List](images/troubleshoot-custom-fields.png)

<!-- IMAGE: Screenshot of Custom Field list view filtered by "etsy" showing all etsy_* custom fields with columns: Field Name, DocType (Customer, Sales Order, Item, etc.), Label -->

3. **Migrate Site**:
   ```bash
   bench --site [site-name] migrate
   ```

### Naming Series Conflicts

**Symptoms**:
- Duplicate naming series errors
- Naming series not following configured pattern

**Causes**:
- Placeholder not used correctly
- Naming series conflicts with existing series

**Solutions**:

1. **Use Placeholders**:
   - For Sales Orders: `EtsyOrder-{ETSY_ORDER_ID}` (correct)
   - Not: `EtsyOrder-12345` (incorrect, hardcoded)

2. **Avoid Conflicts**:
   - Don't use the same naming series for Etsy and manual orders
   - Use unique prefixes like `Etsy-` or `ETSY-SO-`

3. **Leave Blank for Default**:
   - If custom naming is causing issues, leave the field blank
   - The integration will use the doctype's default naming series

## API and Network Issues

### Rate Limit Errors

**Symptoms**:
- Error: "429 Too Many Requests"
- Imports fail during large batches

**Explanation**:
- Etsy API has rate limits (10 requests/second per token)
- The app includes built-in rate limiting (250ms delay)

**Solutions**:
- Wait a few minutes and retry
- Rate limiting should handle this automatically
- If persistent, reduce sync frequency

### Network Timeouts

**Symptoms**:
- Error: "Connection timeout" or "Request timeout"
- Intermittent import failures

**Causes**:
- Slow network connection
- Etsy API temporary issues

**Solutions**:

1. **Retry Import**:
   - Manual imports can be retried immediately
   - Automatic sync will retry on next schedule

2. **Increase Timeout**:
   ```bash
   bench --site [site-name] set-config http_timeout 60
   bench restart
   ```

### SSL Certificate Errors

**Symptoms**:
- Error: "SSL certificate verification failed"

**Causes**:
- Outdated CA certificates on server
- Firewall or proxy interfering with HTTPS

**Solutions**:

1. **Update CA Certificates**:
   ```bash
   sudo apt-get update
   sudo apt-get install ca-certificates
   ```

2. **Check System Time**:
   ```bash
   date
   # Ensure system time is correct
   ```

3. **Disable SSL Verification** (not recommended for production):
   - Only as a last resort and temporary fix

## Debugging Tips

### Enable Verbose Logging

```bash
bench --site [site-name] console
```
```python
import frappe
frappe.set_value("System Settings", None, "enable_frappe_logger", 1)
frappe.db.commit()
exit()
```

Check logs:
```bash
tail -f logs/[site-name].log
```

### Test API Connection

```bash
bench --site [site-name] console
```
```python
from etsy.api import EtsyAPI
shop = frappe.get_doc("Etsy Shop", "Your Shop Name")
api = EtsyAPI(shop)
print(api.get("/application/users/me"))  # Should return user data
exit()
```

### Check Database State

```bash
bench --site [site-name] mariadb
```
```sql
-- Count Etsy-related records
SELECT COUNT(*) FROM `tabCustomer` WHERE etsy_customer_id IS NOT NULL;
SELECT COUNT(*) FROM `tabSales Order` WHERE etsy_order_id IS NOT NULL;
SELECT COUNT(*) FROM `tabEtsy Listing`;
exit;
```

### Review Scheduled Jobs

```bash
bench --site [site-name] console
```
```python
import frappe
jobs = frappe.get_all("Scheduled Job Log",
                       filters={"scheduled_job_type": ["like", "%etsy%"]},
                       fields=["name", "status", "creation"],
                       order_by="creation desc",
                       limit=10)
for job in jobs:
    print(f"{job.creation}: {job.status}")
exit()
```

## Getting Help

If you've tried the solutions above and still have issues:

1. **Check Error Log**:
   - Home > Tools > Error Log
   - Look for detailed error messages and stack traces

2. **Search GitHub Issues**:
   - Visit: [https://github.com/maeurerdev/erpnext-etsy/issues](https://github.com/maeurerdev/erpnext-etsy/issues)
   - Search for similar issues
   - Check closed issues for solutions

3. **Create a New Issue**:
   - Click "New Issue" on GitHub
   - Provide:
     - ERPNext version
     - App version (commit hash)
     - Detailed error messages from Error Log
     - Steps to reproduce
     - Relevant configuration (without sensitive data)

4. **Frappe Community**:
   - Post on [Frappe Forum](https://discuss.frappe.io/)
   - Tag with "etsy" and "integration"

## Next Steps

- **[API Reference](api-reference.md)** - Technical API documentation
- **[Development](development.md)** - Contributing to the project
- **[Configuration](configuration.md)** - Review configuration options
