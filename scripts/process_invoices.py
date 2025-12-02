#!/usr/bin/env python3
import os
import sys
import glob
import argparse
import logging
from datetime import datetime
from typing import List, Dict

# Add project root to python path to allow importing backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.invoice_parser import InvoiceParser
from backend.google_sheets import GoogleSheetsExporter, GoogleSheetsError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def process_invoices(input_dir: str, sheet_id: str, dry_run: bool = False, clear_sheet: bool = False):
    """
    Process PDF invoices in the input directory and sync to Google Sheets.
    """
    if not os.path.exists(input_dir):
        logger.error(f"Input directory not found: {input_dir}")
        return

    # Clear sheet if requested
    if clear_sheet and not dry_run:
        logger.info(f"Clearing sheet {sheet_id}...")
        try:
            GoogleSheetsExporter.clear_sheet(sheet_id)
            logger.info("Sheet cleared successfully.")
        except Exception as e:
            logger.error(f"Failed to clear sheet: {e}")
            return

    pdf_files = glob.glob(os.path.join(input_dir, "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return

    # Get existing order numbers to prevent duplication
    existing_orders = set()
    if not clear_sheet and not dry_run:
        try:
            existing_orders = GoogleSheetsExporter.get_existing_order_numbers(sheet_id)
            logger.info(f"Found {len(existing_orders)} existing orders in sheet.")
        except Exception as e:
            logger.warning(f"Could not fetch existing orders: {e}")

    logger.info(f"Found {len(pdf_files)} PDF files in {input_dir}")

    all_spools = []

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        logger.info(f"Processing {filename}...")
        
        try:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            
            # Parse Invoice
            data = InvoiceParser.parse_invoice(pdf_bytes)
            
            vendor = data.get("vendor")
            order_date = data.get("order_date")
            order_number = data.get("order_number")
            items = data.get("items", [])
            
            # Check for duplicates
            if order_number and order_number in existing_orders:
                logger.warning(f"  Skipping {filename} - Order {order_number} already exists.")
                continue

            if not items:
                logger.warning(f"  No items found in {filename}")
                continue
                
            logger.info(f"  Vendor: {vendor}, Order: {order_number}, Items: {len(items)}")
            
            for item in items:
                qty = item.get("quantity", 1)
                # Expand quantity into individual spool rows
                for _ in range(qty):
                    spool_row = [
                        "", # ID (Auto)
                        "", # Product ID (Unknown)
                        item.get("brand", ""),
                        item.get("material", ""),
                        item.get("color_name", ""),
                        str(item.get("diameter_mm", 1.75)),
                        str(order_date) if order_date else "",
                        vendor,
                        item.get("price", 0.0),
                        "Unsorted", # Storage Location
                        "in_stock", # Status
                        datetime.now().isoformat(), # Created At
                        datetime.now().isoformat(),  # Updated At
                        order_number if order_number else "" # Order Number
                    ]
                    all_spools.append(spool_row)
                    
        except Exception as e:
            logger.error(f"  Error processing {filename}: {str(e)}")

    if not all_spools:
        logger.info("No new spools extracted.")
        return

    logger.info(f"Extracted {len(all_spools)} new spools.")
    
    if dry_run:
        logger.info("Dry run enabled. Skipping upload.")
        for row in all_spools:
            logger.info(f"  Preview: {row}")
        return

    # Upload to Google Sheets
    try:
        logger.info(f"Uploading to Google Sheet ({sheet_id})...")
        result = GoogleSheetsExporter.append_data(
            spreadsheet_id=sheet_id,
            rows=all_spools,
            sheet_name="Inventory"
        )
        logger.info("Upload successful!")
        logger.info(f"Updated range: {result.get('updates', {}).get('updatedRange')}")
        
    except GoogleSheetsError as e:
        logger.error(f"Google Sheets Error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Extract filament data from PDF invoices and upload to Google Sheets.")
    parser.add_argument("--dir", "-d", required=True, help="Directory containing PDF invoices")
    parser.add_argument("--sheet-id", "-s", required=True, help="Google Sheet ID")
    parser.add_argument("--dry-run", action="store_true", help="Parse only, do not upload")
    parser.add_argument("--clear", action="store_true", help="Clear sheet before processing")
    
    args = parser.parse_args()
    
    process_invoices(args.dir, args.sheet_id, args.dry_run, args.clear)

if __name__ == "__main__":
    main()

