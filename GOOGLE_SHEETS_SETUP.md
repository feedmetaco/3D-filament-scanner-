# Google Sheets Integration Setup

## Overview

Export your filament inventory (products and spools) directly to Google Sheets for easy viewing, sharing, and analysis.

---

## Setup Instructions

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Enable **Google Sheets API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google Sheets API"
   - Click "Enable"

### Step 2: Create Service Account

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "Service Account"
3. Fill in details:
   - **Name**: `filament-scanner-sheets`
   - **Description**: Service account for exporting inventory to Google Sheets
4. Click "Create and Continue"
5. Skip role assignment (not needed)
6. Click "Done"

### Step 3: Create Service Account Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose **JSON** format
5. Download the JSON file
6. **Save it securely** - this file contains credentials

### Step 4: Share Google Sheet with Service Account

1. Open or create a Google Sheet
2. Click "Share" button
3. Add the service account email (found in the JSON file, field `client_email`)
   - Example: `filament-scanner-sheets@your-project.iam.gserviceaccount.com`
4. Give it **Editor** permissions
5. Click "Send"

### Step 5: Get Spreadsheet ID

From your Google Sheet URL:
```
https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
```

Copy the `SPREADSHEET_ID_HERE` part - this is your spreadsheet ID.

### Step 6: Configure Environment Variable

**Local Development:**
```bash
export GOOGLE_SHEETS_CREDENTIALS_PATH="/path/to/your/service-account-key.json"
```

**Production (Render/Railway/etc.):**
1. Upload the JSON file to your server
2. Set environment variable:
   ```
   GOOGLE_SHEETS_CREDENTIALS_PATH=/app/credentials/service-account-key.json
   ```

**Or use base64 encoded JSON:**
```bash
# Encode JSON file
cat service-account-key.json | base64

# Set as environment variable
export GOOGLE_SHEETS_CREDENTIALS_JSON="<base64-encoded-content>"
```

---

## Usage

### API Endpoint

```http
POST /api/v1/export/google-sheets
Content-Type: application/json

{
  "spreadsheet_id": "your-spreadsheet-id",
  "sheet_name": "Inventory",  // Optional, defaults to "Inventory"
  "include_products": true,   // Optional, defaults to true
  "include_spools": true,      // Optional, defaults to true
  "spool_status": "in_stock"   // Optional, filter by status
}
```

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/export/google-sheets" \
  -H "Content-Type: application/json" \
  -d '{
    "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
    "sheet_name": "My Inventory",
    "include_products": true,
    "include_spools": true
  }'
```

### Response

```json
{
  "success": true,
  "spreadsheet_id": "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
  "sheet_name": "My Inventory",
  "rows_written": 25,
  "sheet_url": "https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0"
}
```

---

## Sheet Format

### Products Section (if included)

| ID | Brand | Line | Material | Color | Diameter (mm) | Barcode | SKU | Notes | Created At | Updated At |
|----|-------|------|----------|-------|---------------|---------|-----|-------|------------|------------|

### Spools Section (if included)

| ID | Product ID | Brand | Material | Color | Diameter (mm) | Purchase Date | Vendor | Price | Storage Location | Status | Created At | Updated At |
|----|------------|-------|----------|-------|---------------|---------------|--------|-------|------------------|--------|------------|------------|

**Features:**
- Header row is bold with dark background
- Header row is frozen (stays visible when scrolling)
- Data is formatted for easy reading

---

## Troubleshooting

### Error: "GOOGLE_SHEETS_CREDENTIALS_PATH not set"

**Solution:** Set the environment variable pointing to your service account JSON file.

### Error: "Spreadsheet not found or not accessible"

**Solutions:**
1. Check that you've shared the sheet with the service account email
2. Verify the spreadsheet ID is correct
3. Ensure the service account has Editor permissions

### Error: "Google Sheets API libraries not installed"

**Solution:** Install dependencies:
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Error: "Failed to authenticate"

**Solutions:**
1. Verify the JSON file path is correct
2. Check that the JSON file is valid
3. Ensure Google Sheets API is enabled in your Google Cloud project

---

## Security Notes

1. **Never commit** the service account JSON file to git
2. Add `*.json` to `.gitignore` (or specifically `service-account*.json`)
3. Use environment variables for the file path
4. In production, store credentials securely (encrypted storage, secrets manager)

---

## Alternative: Base64 Encoded Credentials

If you prefer not to store a file, you can encode the JSON as base64:

```python
# In backend/google_sheets.py, add support for base64:
import base64
import json

creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_JSON")
if creds_json:
    creds_info = json.loads(base64.b64decode(creds_json))
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
```

Then set:
```bash
export GOOGLE_SHEETS_CREDENTIALS_JSON="<base64-encoded-json>"
```

---

## Next Steps

1. Set up Google Cloud project and service account
2. Download service account JSON key
3. Share your Google Sheet with the service account email
4. Set `GOOGLE_SHEETS_CREDENTIALS_PATH` environment variable
5. Call the export endpoint with your spreadsheet ID

**Ready to export!** 🚀

