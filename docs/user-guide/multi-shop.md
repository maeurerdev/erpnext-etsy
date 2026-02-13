# Multi-Shop Setup

Manage multiple Etsy shops from a single ERPNext instance.

## How It Works

- Create one **Etsy Shop** document per Etsy shop
- Each shop has:
  - Independent OAuth credentials
  - Separate configuration (naming series, accounts, etc.)
  - Isolated synchronization (one shop's sync doesn't affect another)

## Benefits

1. **Centralized Management**: View and manage all shops from one ERPNext instance
2. **Separate Accounting**: Configure different accounts per shop for clean financial reporting
3. **Scalability**: Add new shops without changing the setup

## Example Setup

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

![Multiple Etsy Shops](../images/features-multi-shop-list.png)

<!-- IMAGE: Screenshot of Etsy Shop list view showing 2-3 shops with columns: Shop Name, Status (Connected/Disconnected), Company, and action buttons -->

## Cross-Shop Considerations

- **Customer Matching**: If the same Etsy buyer purchases from multiple shops, separate Customers are created (because naming series differ)
  - To unify customers, use the same naming series and Customer Group across shops
- **Item Conflicts**: If two shops sell items with the same Etsy Product ID, the `etsy_product_id` unique constraint prevents conflicts

## Configuration Tips

1. Create separate Etsy Shop documents for each shop
2. Use different naming series to distinguish orders (e.g., `Shop1-`, `Shop2-`)
3. Consider using different companies or cost centers for accounting separation
4. Stagger sync schedules to distribute server load
