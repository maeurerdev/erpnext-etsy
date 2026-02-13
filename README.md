# Etsy Integration for ERPNext

> [!IMPORTANT]
> The term 'Etsy' is a trademark of Etsy, Inc. This application uses the Etsy API but is not endorsed or certified by Etsy, Inc.

[![ERPNext](https://img.shields.io/badge/ERPNext-v15-blue)](https://github.com/frappe/erpnext)

**📖 [Read the full documentation](https://maeurerdev.github.io/erpnext-etsy)**


## 🌟 Features
- ✅ **Sales Order Synchronization**  
  Automatically pulls new orders from Etsy into ERPNext as **Sales Orders**, including:  
  - Customer creation / matching
  - Shipping & billing addresses
  - Line items with correct variants & pricing
  - Taxes, shipping charges
  - **Sales Invoice** and **Payment Entry** generation
- ✅ **Etsy Listing Import**  
  Automatically retrieves missing item details (title, description, images, attributes, variants, pricing, etc.) directly from your Etsy shop to populate or complete records in ERPNext - The **Etsy Listing** doctype allows configuration and management on a per listing level.
- ✅ **Import Sales History**  
  Bulk import historical Etsy orders (back to a chosen date) to bring your ERPNext records up to date quickly — ideal during initial setup or after a period of disconnection.
- ✅ **Multi-Shop Support**  
  Connect and manage **multiple** Etsy shops from a single ERPNext instance. Each shop can have its own configuration, credentials, and settings.
- ✅ **Configurable Sync Scheduling**  
  Run synchronization manually, on a schedule (via ERPNext Scheduler).
- ✅ **Secure OAuth Authentication**  
  Uses Etsy's OAuth 2.0 flow for safe, token-based access (personal access token required).


## 🚀 Getting Started

### 🔧 Installation
You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app https://github.com/maeurerdev/erpnext-etsy
bench --site $SITE_NAME install-app etsy
```

### ⚙️ Configuration 
- Create a new **Etsy Shop**
  - Setup a new [Personal App](https://www.etsy.com/developers/your-apps) on the Etsy Website
  - Copy the redirect URL from ERP and paste it under the Personal App Settings
  - Enter your Etsy API Keystring and Shared Secret to ERP Etsy Shop API section
  - Click the Login Button to start OAuth2 flow
- Go to **Etsy Settings** to enable and configure automatic sync