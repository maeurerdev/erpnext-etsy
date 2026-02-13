---
hide:
  - navigation
---

# Etsy Integration for ERPNext

!!! info "Legal Disclaimer"
    The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc.

Welcome to the official documentation for the ERPNext Etsy Integration app. This Frappe framework application seamlessly synchronizes your Etsy shop data with ERPNext, automating your e-commerce workflows.

## Quick Start

Ready to get started? Follow our [Getting Started](getting-started.md) guide to:

1. Install the app via bench
2. Configure your first Etsy Shop in ERPNext
3. Create an Etsy Personal App for API access
4. Authenticate with OAuth2

## Overview

The Etsy Integration app connects your Etsy shop(s) to ERPNext, enabling automatic synchronization of:

- **Orders & Receipts** - Sales Orders, Sales Invoices, and Payment Entries
- **Customers & Contacts** - Buyer information and addresses
- **Listings & Items** - Product catalog with variants and attributes

Built on the Frappe framework and designed specifically for ERPNext v15, this integration uses Etsy's official API v3 with secure OAuth2 authentication.

## Key Features

### Sales Order Automation
Automatically import Etsy orders as ERPNext Sales Orders, complete with:

- Customer creation and matching via unique Etsy IDs
- Shipping and billing addresses
- Line items with correct variants and pricing
- Tax calculations (sales tax and shipping tax)
- Automated Sales Invoice and Payment Entry generation

### Listing Management
Retrieve and sync product listings from Etsy:

- Import listing details (title, description, images)
- Automatic Item Template and Item Variant creation
- Support for product attributes and variations
- Configurable per-listing settings via Etsy Listing doctype

### Multi-Shop Support
Manage multiple Etsy shops from a single ERPNext instance:

- Each shop has independent OAuth credentials
- Per-shop configuration for naming series, accounts, and settings
- Isolated synchronization schedules

### Flexible Synchronization
Choose how and when to sync:

- **Manual sync** - Import on-demand via buttons in Etsy Shop doctype
- **Scheduled sync** - Automated background jobs (configurable intervals)
- **Historical import** - Bulk import orders from past dates

### Secure Authentication
Uses Etsy's OAuth 2.0 PKCE flow:

- Token-based authentication
- Automatic token refresh
- Secure credential storage

## Custom Fields

The app adds read-only custom fields to standard ERPNext doctypes for linking Etsy data:

| DocType | Fields |
|---------|--------|
| Customer | `etsy_customer_id` (unique) |
| Contact | `etsy_customer_id` (unique) |
| Sales Order | `etsy_order_id` (unique) |
| Sales Invoice | `etsy_order_id` (unique) |
| Item | `etsy_product_id` (unique), `etsy_listing` (link) |
| Item Attribute | `etsy_listing` (link), `etsy_property_id` |

## Requirements

- **ERPNext**: Version 15 or higher
- **Frappe Framework**: Compatible version
- **Etsy Account**: Active Etsy seller account
- **Etsy Personal App**: API credentials (Keystring and Shared Secret)

## Documentation Structure

- **[Getting Started](getting-started.md)** - Installation and initial setup
- **[Configuration](configuration.md)** - Detailed configuration guide for all doctypes
- **[Features](features.md)** - In-depth feature documentation
- **[Synchronization](synchronization.md)** - Understanding sync behavior and scheduling
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[API Reference](api-reference.md)** - Technical API details for developers
- **[Development](development.md)** - Contributing and development guide

## Support

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/maeurerdev/erpnext-etsy/issues)
- **Repository**: [github.com/maeurerdev/erpnext-etsy](https://github.com/maeurerdev/erpnext-etsy)

## License

This project is licensed under the GNU General Public License (v3).