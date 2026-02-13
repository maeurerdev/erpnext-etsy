# Orders & Customers

Automatically import Etsy orders (receipts) into ERPNext as complete Sales Orders with all related documents.

## What Gets Imported

For each Etsy order, the integration creates:

### 1. Customer

- **Automatic creation** if the Etsy Buyer ID doesn't exist
- **Automatic matching** if a customer with the same Etsy Customer ID already exists
- Customer name follows the configured naming series (default: `EtsyUser-{ETSY_BUYER_ID}`)
- Linked to the configured Customer Group
- Marked with unique `etsy_customer_id` custom field

![Customer from Etsy](../images/features-customer-created.png)

<!-- IMAGE: Screenshot of a Customer document created from Etsy showing the customer name (e.g., "EtsyUser-123456789"), Customer Group, and the "Etsy Customer ID" custom field populated -->

### 2. Contact

- Created or updated for each customer
- **Billing Address** extracted from Etsy order
- **Shipping Address** extracted from Etsy order
- Phone number and email (if provided by buyer)
- Linked to the Customer via Contact link

![Contact with Addresses](../images/features-contact-addresses.png)

<!-- IMAGE: Screenshot of a Contact document showing email, phone, and the "Addresses & Contacts" section with both shipping and billing addresses populated from Etsy order data -->

### 3. Sales Order

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

### 4. Sales Invoice

- Automatically created if the Etsy order is paid
- Mirrors the Sales Order line items
- Submitted automatically
- Linked to the Sales Order

### 5. Payment Entry

- Created when payment is complete on Etsy
- Amount matches the Etsy payment total
- Posted to the configured bank account:
  - Physical products → Bank Account for physical sales
  - Digital products → Bank Account for digital sales
- Payment method mapped from Etsy (credit card, PayPal, etc.)
- References the Sales Invoice

## Handling Edge Cases

### Partial Shipments

If an Etsy order has multiple shipments, each shipment is tracked, but a single Sales Order is created for the entire order.

### Refunds and Cancellations

The integration doesn't automatically process refunds. You need to manually create credit notes in ERPNext if an Etsy order is refunded.

### Gift Messages and Notes

Buyer notes and gift messages from Etsy are added to the Sales Order comments/notes section.

### Missing Items

If an Etsy line item references a product that hasn't been imported as an Item:

- The integration attempts to create the item on-the-fly
- If it fails, the error is logged, and that specific order is skipped
- You can manually import the listing first, then re-import the order

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
- Errors are logged individually — one bad order won't stop the entire import
- You can monitor progress in the ERPNext background jobs

!!! tip "Chunking Large Imports"
    For very large imports (>1000 orders), consider importing in smaller date ranges to avoid timeouts.
