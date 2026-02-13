# Listings & Items

Import your Etsy product listings into ERPNext as Items, complete with variants and attributes.

## Listing Import Workflow

When you click **Import Listings** in an Etsy Shop (or when automatic sync runs), the app:

1. Fetches all active listings from Etsy for this shop
2. For each listing:
   - Creates or updates an **Etsy Listing** document
   - Fetches inventory data (variants, pricing, stock)
   - Creates/updates **Item Templates** and **Item Variants**
   - Creates/updates **Item Attributes**
3. Logs any errors to Error Log

## What Gets Imported

### Etsy Listing Document

One Etsy Listing document per active listing on Etsy. Stores listing metadata:

- Title, description
- Status (Active, Inactive, Sold Out, etc.)
- Primary image
- Views and likes count
- Inventory data (JSON)
- Configuration for Item creation

### Item Templates (for listings with variants)

- Created if the listing has multiple variants (e.g., different sizes or colors)
- Named according to the configured Item Name in Etsy Listing
- Linked to the configured Item Group
- Has variant attributes defined

![Item Template with Variants](../images/features-item-template.png)

<!-- IMAGE: Screenshot of an Item Template document showing "Has Variants" checked, the "Attributes" table with multiple attributes (e.g., Color, Size), and the "Variants" section listing all Item Variants created from the template -->

### Item Variants

- One Item Variant per product offering
- Named with variant attribute values (e.g., `T-Shirt-Red-Large`)
- Pricing set based on Etsy inventory data
- Stock levels can be synced (if Maintain Stock is enabled)
- Unique `etsy_product_id` links it to Etsy

![Item Variant](../images/features-item-variant.png)

<!-- IMAGE: Screenshot of an Item Variant document showing the variant name with attributes (e.g., "T-Shirt-Red-Large"), the "Variant Of" field pointing to the Item Template, attribute values (Color: Red, Size: Large), pricing, and the "Etsy Product ID" and "Etsy Listing" custom fields populated -->

### Item Attributes

- Attributes like "Color", "Size", "Material" are created automatically
- Mapped from Etsy's property system
- Linked back to the Etsy Listing via custom fields
- Attribute values populated from all variants

![Item Attribute](../images/features-item-attribute.png)

<!-- IMAGE: Screenshot of an Item Attribute document (e.g., "Color") showing the attribute name, "Item Attribute Values" table with values (Red, Blue, Green, etc.), and the "Etsy Listing" and "Etsy Property ID" custom fields at the bottom -->

### Images

- Primary listing image attached to the Item or Item Template
- Variant-specific images (if available) attached to Item Variants

## Item Creation Logic

The app uses the following logic when creating items:

```
IF listing has variants:
    CREATE Item Template with base name
    FOR each variant:
        CREATE Item Variant with attributes
ELSE:
    CREATE single Item
```

## Updating Existing Items

When re-importing a listing that already has items in ERPNext:

- **Item Template/Item**: Name, description, and images are updated
- **Item Variants**: New variants are created; existing ones are updated
- **Pricing**: Updated to match current Etsy prices
- **Stock levels**: Not automatically synced (to prevent conflicts with ERPNext inventory management)

!!! warning "Manual Stock Management"
    The integration does **not** push stock levels from ERPNext back to Etsy. Stock management is one-way (Etsy → ERPNext) and only on initial import.

## Handling Attributes

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

## Etsy Listing Doctype Configuration

The Etsy Listing doctype lets you configure how each listing is handled in ERPNext.

![Etsy Listing Form](../images/config-etsy-listing.png)

<!-- IMAGE: Screenshot of Etsy Listing document showing both tabs: "Details" tab (selected) with listing info, image, title, description, and "Settings" tab with Item Settings fields -->

### Details Tab

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
    Most fields are read-only as they're synced from Etsy. Editing Title or Description here doesn't change them on Etsy — these are for reference only.

### Settings Tab

Configure how this listing is handled in ERPNext when creating/updating Items.

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
