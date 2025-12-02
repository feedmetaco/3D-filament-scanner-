# Invoice Processing & Google Sheets Sync Plan

## Overview
This process automates the extraction of inventory data from PDF invoices (Bambu Lab and Amazon) and syncs it to a Google Sheet for tracking.

## Process Flow

1.  **Input**: Directory containing PDF invoices (`.pdf`).
2.  **Parsing**:
    *   Detect Vendor (Bambu Lab vs. Amazon).
    *   Extract Order Details (Order #, Date).
    *   Extract Line Items (Filament products, Quantity, Price, Color, Material).
3.  **Normalization**: Convert extracted data into the standardized `Product` and `Spool` format.
4.  **Export**: Authenticate with Google Sheets and append the new inventory data.

## Components

### 1. Invoice Parser (`backend/invoice_parser.py`)
*   **Bambu Lab Parser**: Existing logic to be verified against `us671552350789070849.pdf`.
    *   *Key Data*: SKU, Variant (Color/Type), Qty, Price.
*   **Amazon Parser**: New logic for `Order Details.pdf`.
    *   *Key Data*: Item Title, Price.
    *   *Filtering*: Identify filament items vs. other purchases (e.g., chargers).
    *   *Regex Strategy*: Look for "Filament", "PLA", "PETG" in titles. Extract Brand (e.g., "eSUN", "Sunlu") from title.

### 2. Google Sheets Exporter (`backend/google_sheets.py`)
*   Existing class `GoogleSheetsExporter`.
*   **Updates needed**: Ensure it can handle a list of "New Spools" specifically, or use the existing `export_to_sheet` method effectively.
*   **Setup**: Requires `GOOGLE_SHEETS_CREDENTIALS_PATH` env var and a Service Account JSON key.

### 3. Orchestration Script (`scripts/process_invoices.py`)
*   **CLI Tool**:
    *   `python scripts/process_invoices.py --input <folder_path> --sheet-id <id>`
*   **Logic**:
    1.  Load Service Account credentials.
    2.  Glob `*.pdf` in input folder.
    3.  For each PDF:
        *   Parse to get Items.
        *   Filter for Filament items.
        *   Print summary for user verification.
    4.  Batch prepare data for Google Sheets.
    5.  Upload to specified Sheet (creating "Inventory" tab if needed).

## Data Mapping

| Field | Bambu Lab Source | Amazon Source | Target Google Sheet Column |
|-------|------------------|---------------|----------------------------|
| Brand | "Bambu Lab" (Fixed) | Title (e.g., "eSUN") | Brand |
| Material | Product Name (e.g., "PLA Basic") | Title (e.g., "PLA+") | Material |
| Color | Variant (e.g., "Orange") | Title (e.g., "Black") | Color |
| Price | Item Price | Item Price | Price |
| Date | Invoice Date | Order Date | Purchase Date |
| Vendor | "Bambu Lab" | "Amazon" | Vendor |
| Qty | Qty Column | Count of items | (One row per spool) |

## Execution Steps

1.  **Setup**:
    *   Place `service_account.json` in `backend/`.
    *   Set `GOOGLE_SHEETS_CREDENTIALS_PATH`.
2.  **Run**:
    ```bash
    python scripts/process_invoices.py --dir ./invoices --sheet-id <YOUR_SHEET_ID>
    ```
3.  **Verify**: Check Google Sheet for new rows.

