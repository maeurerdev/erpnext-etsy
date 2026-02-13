# Setup Your First Etsy Shop

Create and configure an Etsy Shop document in ERPNext.

## Step 1: Create Etsy Shop Document

1. In ERPNext, search for **Etsy Shop** in the Awesome Bar
2. Click **New** to create a new Etsy Shop document
![New Etsy Shop Document](../images/etsy-shop-new.png)
3. Enter your **Shop Name** (any descriptive name, e.g., "My Etsy Store")

## Step 2: Configure ERP Settings

Configure how ERPNext should handle Etsy data:

### Company & Language
- **Company**: Select the ERPNext company for this shop
- **Language**: (Optional) Set language for data formatting

### Sales Order & Invoice Settings
- **Sales Order Naming Series**: Default is `EtsyOrder-{ETSY_ORDER_ID}`
  - Use `{ETSY_ORDER_ID}` as placeholder
- **Sales Invoice Naming Series**: Default is `EtsyInvoice-{ETSY_ORDER_ID}`
- **Sales Tax Account**: **Required** — Select account for product taxes
- **Shipping Tax Account**: **Required** — Select account for shipping taxes
- **Bank Account for physical sales**: **Required** — Account for physical product payments
- **Bank Account for digital sales**: **Required** — Account for digital product payments

### Customer Settings
- **Customer Naming Series**: Default is `EtsyUser-{ETSY_BUYER_ID}`
  - Use `{ETSY_BUYER_ID}` as placeholder
  - Example: `Etsy-.YYYY.-{ETSY_BUYER_ID}` for year-based naming
- **Customer Group**: (Optional) Assign a default customer group

### Item Settings
- **Item Group**: (Optional) Default item group for imported listings
- **Default Unit of Measure**: (Optional) Default UOM for items (can be set per listing)

![Etsy Shop ERP Settings](../images/etsy-shop-erp-settings.png)

## Step 3: Save the Document

Click **Save** to save your Etsy Shop configuration.

## Next Step

Now proceed to [Connect to Etsy API](connect-api.md) to authenticate your shop.
