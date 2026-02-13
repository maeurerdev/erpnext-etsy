# Prerequisites & Installation

This guide will walk you through installing the Etsy Integration app for ERPNext.

## Prerequisites

Before you begin, ensure you have:

- **Frappe Framework** and **ERPNext v15** or higher installed
- **Frappe Bench** CLI tool installed
- **System Manager** role in ERPNext
- An active **Etsy seller account** with at least one shop

## Step 1: Install the App

Install the Etsy Integration app using the Frappe Bench CLI:

```bash
# Navigate to your bench directory
cd /path/to/your/bench

# Get the app from GitHub
bench get-app https://github.com/maeurerdev/erpnext-etsy

# Install the app on your site
bench --site your-site-name install-app etsy
```

## Step 2: Verify Installation

After installation, verify that the app is active:

1. Log in to your ERPNext site
2. Go to **Module List** (via search or Home)
3. You should see the **Etsy** module

Alternatively, search for "Etsy Shop" or "Etsy Settings" in the Awesome Bar.

## Next Step

Once the app is installed, proceed to [Setup Your First Etsy Shop](setup-shop.md).
