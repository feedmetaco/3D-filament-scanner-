#!/usr/bin/env python3
"""Test OCR and PDF parsing, writing results to Google Sheets after each test."""
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ocr_service import LabelParser, OCRError
from backend.invoice_parser import InvoiceParser
from backend.validation import validate_image_file, validate_pdf_file, ValidationError
from backend.google_sheets import GoogleSheetsExporter, GoogleSheetsError


# Google Sheets configuration
SPREADSHEET_ID = "1S_p8HbdtKmJfeZ-k-gwsz3YMJGYiu3UF_pSpYnlQSgQ"
TEST_RESULTS_SHEET = "Test Results"


def write_ocr_result_to_sheets(result: dict, spreadsheet_id: str, sheet_name: str):
    """Write OCR test result to Google Sheets."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = Path(result["file"]).name
        
        # Prepare row data
        row = [
            timestamp,
            "OCR",
            file_name,
            "✓" if result["success"] else "✗",
            result["ocr_result"].get("brand", "N/A") if result.get("ocr_result") else "N/A",
            result["ocr_result"].get("material", "N/A") if result.get("ocr_result") else "N/A",  # Material column
            "N/A",  # Order # column (not applicable for OCR)
            result["ocr_result"].get("color_name", "N/A") if result.get("ocr_result") else "N/A",
            f"{result['ocr_result'].get('diameter_mm', 'N/A')} mm" if result.get("ocr_result") and result["ocr_result"].get("diameter_mm") else "N/A",
            result["ocr_result"].get("strategy_used", "N/A") if result.get("ocr_result") else "N/A",
            ", ".join(result["errors"]) if result.get("errors") else "None",
            result["validation"].get("format", "N/A") if result.get("validation") else "N/A",
            f"{result['validation'].get('file_size_mb', 0):.2f} MB" if result.get("validation") else "N/A",
        ]
        
        GoogleSheetsExporter.append_data(spreadsheet_id, [row], sheet_name)
        print(f"  ✓ Written to Google Sheets")
        
    except GoogleSheetsError as e:
        print(f"  ⚠ Failed to write to Google Sheets: {e}")
    except Exception as e:
        print(f"  ⚠ Failed to write to Google Sheets: {e}")


def write_pdf_result_to_sheets(result: dict, spreadsheet_id: str, sheet_name: str):
    """Write PDF test result to Google Sheets."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_name = Path(result["file"]).name
        
        parse_result = result.get("parse_result") or {}
        items = parse_result.get("items", []) if parse_result else []
        
        # For PDF results, write one row per item so materials are clearly visible
        rows_to_write = []
        
        if items:
            for item in items:
                material = item.get("material", "N/A")
                # Ensure material is not None or empty
                if not material or material == "N/A":
                    material = "N/A"
                
                row = [
                    timestamp,
                    "PDF",
                    file_name,
                    "✓" if result["success"] else "✗",
                    parse_result.get("vendor", "N/A") if parse_result else "N/A",
                    material,  # Material column - one per item
                    parse_result.get("order_number", "N/A") if parse_result else "N/A",  # Order # column
                    str(parse_result.get("order_date", "N/A")) if parse_result else "N/A",
                    item.get("quantity", 1),  # Items count per item
                    f"${item.get('price', 0):.2f}",  # Price per item
                    ", ".join(result["errors"]) if result.get("errors") else "None",
                    result["validation"].get("page_count", "N/A") if result.get("validation") else "N/A",
                    f"{result['validation'].get('file_size_mb', 0):.2f} MB" if result.get("validation") else "N/A",
                ]
                rows_to_write.append(row)
        else:
            # No items found, write summary row
            row = [
                timestamp,
                "PDF",
                file_name,
                "✓" if result["success"] else "✗",
                parse_result.get("vendor", "N/A") if parse_result else "N/A",
                "N/A",  # No material
                parse_result.get("order_number", "N/A") if parse_result else "N/A",
                str(parse_result.get("order_date", "N/A")) if parse_result else "N/A",
                0,
                "N/A",
                ", ".join(result["errors"]) if result.get("errors") else "None",
                result["validation"].get("page_count", "N/A") if result.get("validation") else "N/A",
                f"{result['validation'].get('file_size_mb', 0):.2f} MB" if result.get("validation") else "N/A",
            ]
            rows_to_write.append(row)
        
        if rows_to_write:
            GoogleSheetsExporter.append_data(spreadsheet_id, rows_to_write, sheet_name)
            print(f"  ✓ Written {len(rows_to_write)} row(s) to Google Sheets")
        
    except GoogleSheetsError as e:
        print(f"  ⚠ Failed to write to Google Sheets: {e}")
    except Exception as e:
        print(f"  ⚠ Failed to write to Google Sheets: {e}")
        import traceback
        traceback.print_exc()


def initialize_test_sheet(spreadsheet_id: str, sheet_name: str):
    """Initialize the test results sheet with headers."""
    try:
        headers = [
            "Timestamp",
            "Test Type",
            "File Name",
            "Status",
            "Brand/Vendor",
            "Material",
            "Order #",
            "Color/Order Date",
            "Diameter/Items Count",
            "Strategy/Total Value",
            "Errors",
            "Format/Pages",
            "File Size",
        ]
        
        # Check if sheet exists and has headers
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH")
            if not creds_path:
                print("⚠ GOOGLE_SHEETS_CREDENTIALS_PATH not set, skipping sheet initialization")
                return
            
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            service = build('sheets', 'v4', credentials=creds)
            
            # Check if sheet exists
            spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
            sheet_exists = any(s.get('properties', {}).get('title') == sheet_name 
                             for s in spreadsheet.get('sheets', []))
            
            if not sheet_exists:
                # Create sheet with headers
                requests = [{
                    'addSheet': {
                        'properties': {
                            'title': sheet_name
                        }
                    }
                }]
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': requests}
                ).execute()
                
                # Write headers
                body = {'values': [headers]}
                service.spreadsheets().values().update(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A1",
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                
                # Format header row
                sheet_id = None
                for sheet in spreadsheet.get('sheets', []):
                    if sheet.get('properties', {}).get('title') == sheet_name:
                        sheet_id = sheet.get('properties', {}).get('sheetId')
                        break
                
                if sheet_id is not None:
                    format_requests = [{
                        'repeatCell': {
                            'range': {
                                'sheetId': sheet_id,
                                'startRowIndex': 0,
                                'endRowIndex': 1
                            },
                            'cell': {
                                'userEnteredFormat': {
                                    'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                                    'textFormat': {'foregroundColor': {'red': 1.0, 'green': 1.0, 'blue': 1.0}, 'bold': True}
                                }
                            },
                            'fields': 'userEnteredFormat(backgroundColor,textFormat)'
                        }
                    }]
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=spreadsheet_id,
                        body={'requests': format_requests}
                    ).execute()
                
                print(f"✓ Created test results sheet: {sheet_name}")
            else:
                # Check if headers exist
                result = service.spreadsheets().values().get(
                    spreadsheetId=spreadsheet_id,
                    range=f"{sheet_name}!A1:M1"
                ).execute()
                
                if not result.get('values') or result['values'][0] != headers:
                    # Update headers
                    body = {'values': [headers]}
                    service.spreadsheets().values().update(
                        spreadsheetId=spreadsheet_id,
                        range=f"{sheet_name}!A1",
                        valueInputOption='USER_ENTERED',
                        body=body
                    ).execute()
                    print(f"✓ Updated headers in sheet: {sheet_name}")
                else:
                    print(f"✓ Test results sheet ready: {sheet_name}")
                    
        except Exception as e:
            print(f"⚠ Failed to initialize sheet: {e}")
            
    except Exception as e:
        print(f"⚠ Failed to initialize test sheet: {e}")


def test_ocr(image_path: str) -> dict:
    """Test OCR on a single image file."""
    print(f"\n{'='*60}")
    print(f"Testing OCR: {image_path}")
    print(f"{'='*60}")
    
    result = {
        "file": image_path,
        "success": False,
        "validation": None,
        "ocr_result": None,
        "errors": []
    }
    
    try:
        # Read image file
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        print(f"File size: {len(image_bytes) / 1024:.1f} KB")
        
        # Validate image
        try:
            img, metadata = validate_image_file(image_bytes, filename=image_path)
            result["validation"] = {
                "success": True,
                "format": metadata["format"],
                "size": metadata["size"],
                "file_size_mb": round(len(image_bytes) / (1024 * 1024), 2)
            }
            print(f"✓ Validation passed: {metadata['format']} {metadata['size'][0]}x{metadata['size'][1]}")
        except ValidationError as e:
            result["validation"] = {"success": False, "error": str(e)}
            result["errors"].append(f"Validation failed: {e}")
            print(f"✗ Validation failed: {e}")
            write_ocr_result_to_sheets(result, SPREADSHEET_ID, TEST_RESULTS_SHEET)
            return result
        
        # Run OCR
        try:
            ocr_result = LabelParser.parse_label(image_bytes)
            result["ocr_result"] = ocr_result
            result["success"] = True
            
            print(f"\nOCR Results:")
            print(f"  Brand: {ocr_result.get('brand', 'Not detected')}")
            print(f"  Material: {ocr_result.get('material', 'Not detected')}")
            print(f"  Color: {ocr_result.get('color_name', 'Not detected')}")
            print(f"  Diameter: {ocr_result.get('diameter_mm', 'Not detected')} mm")
            print(f"  Barcode: {ocr_result.get('barcode', 'Not detected')}")
            print(f"  Confidence: {ocr_result.get('ocr_confidence', 0):.1f}%")
            print(f"  Strategy: {ocr_result.get('strategy_used', 'unknown')}")
            
            if ocr_result.get('raw_text'):
                print(f"\nRaw OCR Text (first 200 chars):")
                print(f"  {ocr_result['raw_text'][:200]}...")
            
            if ocr_result.get('error'):
                print(f"\n⚠ Warning: {ocr_result['error']}")
            
        except OCRError as e:
            result["errors"].append(f"OCR failed: {e}")
            print(f"✗ OCR failed: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")
            print(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
    
    except FileNotFoundError:
        result["errors"].append(f"File not found: {image_path}")
        print(f"✗ File not found: {image_path}")
    except Exception as e:
        result["errors"].append(f"Error reading file: {e}")
        print(f"✗ Error reading file: {e}")
    
    # Write to Google Sheets
    write_ocr_result_to_sheets(result, SPREADSHEET_ID, TEST_RESULTS_SHEET)
    
    return result


def test_pdf(pdf_path: str) -> dict:
    """Test PDF parsing on a single PDF file."""
    print(f"\n{'='*60}")
    print(f"Testing PDF: {pdf_path}")
    print(f"{'='*60}")
    
    result = {
        "file": pdf_path,
        "success": False,
        "validation": None,
        "parse_result": None,
        "errors": []
    }
    
    try:
        # Read PDF file
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"File size: {len(pdf_bytes) / 1024:.1f} KB")
        
        # Validate PDF
        try:
            metadata = validate_pdf_file(pdf_bytes, filename=pdf_path)
            result["validation"] = {
                "success": True,
                "page_count": metadata.get("page_count", 0),
                "file_size_mb": round(metadata.get("file_size_bytes", len(pdf_bytes)) / (1024 * 1024), 2)
            }
            page_count = result["validation"]["page_count"]
            print(f"✓ Validation passed: {page_count} pages, {result['validation']['file_size_mb']} MB")
        except ValidationError as e:
            result["validation"] = {"success": False, "error": str(e)}
            result["errors"].append(f"Validation failed: {e}")
            print(f"✗ Validation failed: {e}")
            write_pdf_result_to_sheets(result, SPREADSHEET_ID, TEST_RESULTS_SHEET)
            return result
        
        # Parse invoice
        try:
            # Detect vendor and parse accordingly
            import io
            import pdfplumber
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                first_page_text = pdf.pages[0].extract_text() or ""
            
            if "bambu" in first_page_text.lower() or "bambu lab" in first_page_text.lower():
                parse_result = InvoiceParser.parse_bambu_invoice(pdf_bytes)
            elif "amazon" in first_page_text.lower() or "order #" in first_page_text.lower():
                parse_result = InvoiceParser.parse_amazon_invoice(pdf_bytes)
            else:
                parse_result = InvoiceParser.parse_invoice(pdf_bytes)
            
            result["parse_result"] = parse_result
            result["success"] = True
            
            print(f"\nInvoice Parsing Results:")
            print(f"  Vendor: {parse_result.get('vendor', 'Unknown')}")
            print(f"  Order Number: {parse_result.get('order_number', 'Not detected')}")
            print(f"  Order Date: {parse_result.get('order_date', 'Not detected')}")
            print(f"  Items Found: {len(parse_result.get('items', []))}")
            
            if parse_result.get('items'):
                print(f"\n  Items:")
                for i, item in enumerate(parse_result['items'], 1):
                    qty = item.get('quantity', 1)
                    price = item.get('price', 0)
                    price_str = f"${price:.2f}" if price else "N/A"
                    print(f"    {i}. {item.get('brand')} {item.get('material')} {item.get('color_name')} "
                          f"(Qty: {qty}, Price: {price_str})")
            
        except ValueError as e:
            result["errors"].append(f"Parsing failed: {e}")
            print(f"✗ Parsing failed: {e}")
        except Exception as e:
            result["errors"].append(f"Unexpected error: {e}")
            print(f"✗ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
    
    except FileNotFoundError:
        result["errors"].append(f"File not found: {pdf_path}")
        print(f"✗ File not found: {pdf_path}")
    except Exception as e:
        result["errors"].append(f"Error reading file: {e}")
        print(f"✗ Error reading file: {e}")
    
    # Write to Google Sheets (only if we have parse_result or errors)
    if result.get("parse_result") is not None or result.get("errors"):
        write_pdf_result_to_sheets(result, SPREADSHEET_ID, TEST_RESULTS_SHEET)
    
    return result


def main():
    """Main test function."""
    # Set up Google Sheets credentials path
    creds_path = Path(__file__).parent.parent / "filament-scanner-03cb020dceec.json"
    if creds_path.exists():
        os.environ["GOOGLE_SHEETS_CREDENTIALS_PATH"] = str(creds_path)
        print(f"✓ Using Google Sheets credentials: {creds_path}")
    else:
        print(f"⚠ Google Sheets credentials not found at: {creds_path}")
        print("  Tests will run but results won't be written to Google Sheets")
    
    # Initialize test sheet
    if os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH"):
        initialize_test_sheet(SPREADSHEET_ID, TEST_RESULTS_SHEET)
    
    # Find all test files
    project_root = Path(__file__).parent.parent
    image_files = list(project_root.glob("IMG_*.JPG")) + list(project_root.glob("IMG_*.DNG"))
    pdf_files = list(project_root.glob("*.pdf"))
    
    print(f"\n{'='*70}")
    print("COMPREHENSIVE TEST SUITE")
    print(f"{'='*70}")
    print(f"\nFound {len(image_files)} image files and {len(pdf_files)} PDF files")
    
    all_results = []
    
    # Test all images
    print(f"\n{'='*70}")
    print("TESTING OCR (IMAGE FILES)")
    print(f"{'='*70}")
    ocr_results = []
    for image_path in sorted(image_files):
        result = test_ocr(str(image_path))
        ocr_results.append(result)
        all_results.append(result)
    
    # Test all PDFs
    print(f"\n{'='*70}")
    print("TESTING PDF PARSING")
    print(f"{'='*70}")
    pdf_results = []
    for pdf_path in sorted(pdf_files):
        result = test_pdf(str(pdf_path))
        pdf_results.append(result)
        all_results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}")
    
    ocr_successful = sum(1 for r in ocr_results if r["success"])
    pdf_successful = sum(1 for r in pdf_results if r["success"])
    
    print(f"\nOCR Tests:")
    print(f"  Total: {len(ocr_results)}")
    print(f"  Successful: {ocr_successful}")
    print(f"  Failed: {len(ocr_results) - ocr_successful}")
    
    print(f"\nPDF Tests:")
    print(f"  Total: {len(pdf_results)}")
    print(f"  Successful: {pdf_successful}")
    print(f"  Failed: {len(pdf_results) - pdf_successful}")
    
    print(f"\nOverall:")
    print(f"  Total Tests: {len(all_results)}")
    print(f"  Successful: {ocr_successful + pdf_successful}")
    print(f"  Failed: {len(all_results) - (ocr_successful + pdf_successful)}")
    
    if os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH"):
        print(f"\n✓ All results written to Google Sheets:")
        print(f"  https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit#gid=0")
    
    sys.exit(0 if (ocr_successful == len(ocr_results) and pdf_successful == len(pdf_results)) else 1)


if __name__ == "__main__":
    main()

