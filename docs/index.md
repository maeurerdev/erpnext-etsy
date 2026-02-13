---
hide:
  - navigation
---

# Etsy Integration for ERPNext

??? info "Legal Disclaimer"
    "Etsy" is a trademark of Etsy, Inc. This application uses the Etsy API but is **not endorsed, certified, or affiliated with Etsy, Inc.** in any way. This software is provided "as is" under the [GPL-3.0 license](https://github.com/maeurerdev/erpnext-etsy/blob/main/LICENSE), without warranty of any kind, express or implied. The authors and contributors accept no liability for any damages, data loss, account suspension, or other consequences arising from the use or misuse of this software. Use of the Etsy API is subject to [Etsy's API Terms of Use](https://www.etsy.com/legal/api) — you are solely responsible for compliance.

Welcome to the official documentation for the ERPNext Etsy Integration app. This Frappe framework application seamlessly synchronizes your Etsy shop data with ERPNext, automating your e-commerce workflows.

## :rocket: Quick Start

Ready to get started? Follow our [Getting Started](getting-started/installation.md) guide to install the app, connect your Etsy shop, and import your first data in minutes.

## Overview

The Etsy Integration app connects your Etsy shop(s) to ERPNext, enabling automatic synchronization of:

- **Orders & Receipts** — Sales Orders, Sales Invoices, and Payment Entries
- **Customers & Contacts** — Buyer information and addresses
- **Listings & Items** — Product catalog with variants and attributes

Built on the Frappe framework and designed specifically for ERPNext v15, this integration uses Etsy's official API v3 with secure OAuth2 authentication.

## :sparkles: Key Features

- **Sales Order Automation** — Import Etsy orders as complete Sales Orders with Customers, Invoices, and Payment Entries
- **Listing Management** — Sync product listings with automatic Item Template, Variant, and Attribute creation
- **Multi-Shop Support** — Manage multiple Etsy shops from a single ERPNext instance with independent configuration
- **Flexible Sync** — Manual on-demand imports, scheduled background jobs, or bulk historical imports
- **Secure Auth** — OAuth 2.0 PKCE flow with automatic token refresh

## :book: Documentation

- **[Prerequisites & Installation](getting-started/installation.md)** — Install the app via Frappe Bench
- **[Setup Your First Etsy Shop](getting-started/setup-shop.md)** — Create and configure an Etsy Shop in ERPNext
- **[Connect to Etsy API](getting-started/connect-api.md)** — Create an Etsy Personal App and authenticate
- **[First Import & Next Steps](getting-started/next-steps.md)** — Import data and enable automatic sync
- **[User Guide](user-guide/shop-configuration.md)** — In-depth configuration, features, and troubleshooting
- **[Developer Guide](developer-guide/contributing.md)** — Contributing, code style, and development setup

## Support

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/maeurerdev/erpnext-etsy/issues)
- **Repository**: [github.com/maeurerdev/erpnext-etsy](https://github.com/maeurerdev/erpnext-etsy)

## License

This project is licensed under the GNU General Public License (v3).
