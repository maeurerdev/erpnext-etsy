# Connect to Etsy API

To connect ERPNext with your Etsy Shop, you need API credentials from Etsy's Developer Portal and then authenticate via OAuth2.

<div id="api-disclaimer" markdown>

!!! danger "Important — Read Before Proceeding!"
    Creating an Etsy Personal App requires you to be the authorized owner or designated administrator of both the Etsy shop and the ERPNext instance. Unauthorized creation of API credentials may violate [Etsy's API Terms of Use](https://www.etsy.com/legal/api) and could result in permanent suspension of your Etsy account.

    By proceeding, you acknowledge that: (1) you have the authority to create API credentials for this Etsy shop, (2) you are solely responsible for the secure handling of all API keys and tokens, and (3) the authors and contributors of this software accept no liability for any account suspension, data loss, security breaches, or other damages arising from the use or misuse of this integration. This software is provided "as is" under the terms of the [GPL-3.0 license](https://github.com/maeurerdev/erpnext-etsy/blob/main/LICENSE), without warranty of any kind.

<button id="api-disclaimer-accept" class="md-button md-button--primary">I acknowledge the above terms — show setup guide :material-arrow-right:</button>

</div>

<div id="api-guide" style="display: none" markdown>

## Creating an Etsy Personal App

### Step 1: Access Etsy Developer Portal

1. Go to [Etsy Developer Portal](https://www.etsy.com/developers/your-apps)
2. Sign in with your Etsy seller account
3. Click **Create a New App** or **Get Started**

![Etsy Developer Portal](../images/etsy-developer-portal.png)

### Step 2: Create a Personal App

1. **App Name**: Choose a descriptive name (e.g., "my_erpnext")
2. **Is this app for development or production?**: Select based on your needs
3. **What's the URL for your app?**: Enter your ERPNext site URL
4. **Tell us more**: Provide a brief description of how you'll use the API
5. **Terms of Use**: Review and agree to Etsy's API Terms

After submission, Etsy will approve your app (usually instantly for personal apps).

![Etsy App Creation Form](../images/etsy-create-app-form.png)

### Step 3: Get Your API Credentials

Once your app is created:

1. Navigate to your app in the [Your Apps](https://www.etsy.com/developers/your-apps) section
2. Note down your **Keystring** (this is your CLIENT_ID)
3. Note down your **Shared Secret** (this is your CLIENT_SECRET)

![Etsy App Credentials](../images/etsy-app-credentials.png)

!!! danger "Keep Credentials Secure"
    Never share your Shared Secret publicly. Store it securely.

### Step 4: Enter API Credentials

In the **API Credentials** section:

1. **CLIENT_ID**: Paste your Etsy Keystring
2. **CLIENT_SECRET**: Paste your Etsy Shared Secret
3. **Use localhost**: Check this only if running ERPNext locally (self-hosted)

The **Redirect URI** field is automatically generated. You'll need this in the next step.

![Etsy Shop API Credentials Section](../images/etsy-shop-api-credentials.png)

### Step 5: Save the Document

Click **Save** to save your Etsy Shop configuration.

### Step 6: Set Redirect URI on Etsy Developer Portal

1. Copy the **Redirect URI** from your Etsy Shop document
2. Go back to your [Etsy Personal App](https://www.etsy.com/developers/your-apps)
3. Under your app's kebab menu, click **Edit callback URLs**
![Etsy App OAuth Redirect URI](../images/etsy-shop-redirect-menu.png)
4. Paste the Redirect URI from ERPNext
![Etsy App OAuth Redirect URI](../images/etsy-oauth-redirect-uri.png)
5. Save the changes

## Authenticating with Etsy

### Step 1: Initiate OAuth Flow

1. In your saved Etsy Shop document, click the **Login** button
![Etsy Shop Login Button](../images/etsy-shop-login-button.png)
2. You'll be redirected to Etsy's authorization page
3. Review the permissions requested
4. Click **Grant Access** to authorize the app

### Step 2: Complete Authentication

After authorization:

1. You'll be redirected back to ERPNext
!!! info "An ERPNext login prompt may show up"
    Log-in with system manager account (Administrator)
2. The Etsy Shop document will automatically update with:
   - **Access Token** and **Refresh Token** (stored securely)
   - **Etsy User ID** and **Shop ID**
   - **Status**: Changed from "Disconnected" to "Connected"
   - **Expires At**: Token expiration datetime

![Etsy Shop Connected](../images/etsy-shop-connected.png)

!!! success "Authentication Complete"
    Your Etsy Shop is now connected! The app will automatically refresh tokens before they expire.

## Next Step

Your shop is connected! Proceed to [First Import & Next Steps](next-steps.md) to import your data.

</div>
