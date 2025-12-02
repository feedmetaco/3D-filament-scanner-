"""Google Sheets integration for exporting inventory data."""
import os
import logging
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class GoogleSheetsError(Exception):
    """Custom exception for Google Sheets errors."""
    pass


class GoogleSheetsExporter:
    """Export inventory data to Google Sheets."""

    @staticmethod
    def _get_sheets_service():
        """Get authenticated Google Sheets service."""
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.errors import HttpError
            
            # Check for service account credentials
            creds_path = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_PATH")
            if not creds_path:
                raise GoogleSheetsError(
                    "GOOGLE_SHEETS_CREDENTIALS_PATH environment variable not set. "
                    "Please provide path to service account JSON file."
                )
            
            if not os.path.exists(creds_path):
                raise GoogleSheetsError(f"Credentials file not found: {creds_path}")
            
            # Load credentials
            creds = service_account.Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            # Build service
            service = build('sheets', 'v4', credentials=creds)
            return service
            
        except ImportError:
            raise GoogleSheetsError(
                "Google Sheets API libraries not installed. "
                "Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
            )
        except Exception as e:
            raise GoogleSheetsError(f"Failed to authenticate with Google Sheets: {str(e)}")

    @staticmethod
    def _prepare_products_data(products: List[Dict]) -> List[List]:
        """Prepare products data for Google Sheets."""
        headers = [
            "ID", "Brand", "Line", "Material", "Color", "Diameter (mm)",
            "Barcode", "SKU", "Notes", "Created At", "Updated At"
        ]
        
        rows = [headers]
        
        for product in products:
            row = [
                product.get("id", ""),
                product.get("brand", ""),
                product.get("line", ""),
                product.get("material", ""),
                product.get("color_name", ""),
                product.get("diameter_mm", ""),
                product.get("barcode", ""),
                product.get("sku", ""),
                product.get("notes", ""),
                str(product.get("created_at", "")),
                str(product.get("updated_at", ""))
            ]
            rows.append(row)
        
        return rows

    @staticmethod
    def clear_sheet(spreadsheet_id: str, sheet_name: str = "Inventory"):
        """Clear all data from the specified sheet."""
        try:
            service = GoogleSheetsExporter._get_sheets_service()
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
        except Exception as e:
            logger.error(f"Failed to clear sheet: {e}")
            raise GoogleSheetsError(f"Failed to clear sheet: {str(e)}")

    @staticmethod
    def get_existing_order_numbers(spreadsheet_id: str, sheet_name: str = "Inventory") -> set:
        """
        Fetch all existing order numbers from the sheet.
        Returns a set of order numbers.
        """
        try:
            service = GoogleSheetsExporter._get_sheets_service()
            
            # Read all values from the sheet
            result = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return set()
            
            headers = values[0]
            try:
                # Try to find "Order Number" column
                order_col_idx = headers.index("Order Number")
            except ValueError:
                # If not found, return empty set
                return set()
                
            existing_orders = set()
            # Iterate through rows (skipping header)
            for row in values[1:]:
                if len(row) > order_col_idx:
                    order_num = row[order_col_idx].strip()
                    if order_num:
                        existing_orders.add(order_num)
                        
            return existing_orders
            
        except Exception as e:
            logger.warning(f"Could not fetch existing orders: {e}")
            return set()

    @staticmethod
    def _prepare_spools_data(spools: List[Dict], products: Optional[List[Dict]] = None) -> List[List]:
        """Prepare spools data for Google Sheets with aggregation."""
        # Create product lookup if provided
        product_lookup = {}
        if products:
            for p in products:
                product_lookup[p.get("id")] = p
        
        # Group spools
        grouped_spools = defaultdict(int)
        spool_details = {}
        
        for spool in spools:
            # Create a key for aggregation
            key = (
                spool.get("product_id"),
                spool.get("purchase_date"),
                spool.get("vendor"),
                spool.get("price"),
                spool.get("storage_location"),
                spool.get("status"),
                spool.get("order_id")
            )
            grouped_spools[key] += 1
            if key not in spool_details:
                spool_details[key] = spool
        
        headers = [
            "Brand", "Material", "Color", "Diameter (mm)", "Quantity",
            "Purchase Date", "Vendor", "Price", "Storage Location",
            "Status", "Order Number", "Product ID"
        ]
        
        rows = [headers]
        
        for key, count in grouped_spools.items():
            spool = spool_details[key]
            product_id = key[0]
            product = product_lookup.get(product_id) if product_lookup else None
            
            row = [
                product.get("brand", "") if product else "",
                product.get("material", "") if product else "",
                product.get("color_name", "") if product else "",
                product.get("diameter_mm", "") if product else "",
                count,
                str(spool.get("purchase_date", "")),
                spool.get("vendor", ""),
                spool.get("price", ""),
                spool.get("storage_location", ""),
                spool.get("status", ""),
                spool.get("order_id", ""),
                product_id
            ]
            rows.append(row)
        
        return rows

    @staticmethod
    def append_data(
        spreadsheet_id: str,
        rows: List[List],
        sheet_name: Optional[str] = None
    ) -> Dict:
        """
        Append data rows to Google Sheets.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            rows: List of rows (lists) to append
            sheet_name: Name of sheet to append to (default: "Inventory")
        
        Returns:
            Dict with success status and updated range
        """
        if not rows:
            return {"success": True, "message": "No data to append"}
            
        try:
            service = GoogleSheetsExporter._get_sheets_service()
            sheet_name = sheet_name or "Inventory"
            
            # Check if sheet exists
            try:
                spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                sheet_exists = any(s.get('properties', {}).get('title') == sheet_name 
                                 for s in spreadsheet.get('sheets', []))
            except Exception as e:
                raise GoogleSheetsError(f"Spreadsheet not found or not accessible: {spreadsheet_id}. Error: {str(e)}")
                
            if not sheet_exists:
                # Create new sheet
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
                
                # Add headers if creating new sheet
                # We assume the first row of 'rows' is NOT the header if we are appending,
                # but if we are creating a NEW sheet, we might want to add headers first.
                # For this generic append, we'll assume the caller handles headers or 
                # checks if the sheet is empty.
                
                # However, for our specific use case, we might want to ensure headers exist.
                # Let's stick to simple append.
                
            # Append data
            range_name = f"{sheet_name}!A1"
            body = {
                'values': rows
            }
            
            result = service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "updates": result.get('updates')
            }
            
        except Exception as e:
            logger.error(f"Failed to append to Google Sheets: {e}", exc_info=True)
            raise GoogleSheetsError(f"Failed to append to Google Sheets: {str(e)}")

    @staticmethod
    def export_to_sheet(
        spreadsheet_id: str,
        products: Optional[List[Dict]] = None,
        spools: Optional[List[Dict]] = None,
        sheet_name: Optional[str] = None
    ) -> Dict:
        """
        Export products and/or spools to Google Sheets.
        
        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            products: List of product dictionaries
            spools: List of spool dictionaries
            sheet_name: Name of sheet to create/update (default: "Inventory")
        
        Returns:
            Dict with success status and sheet URL
        """
        if not products and not spools:
            raise GoogleSheetsError("At least one of products or spools must be provided")
        
        try:
            service = GoogleSheetsExporter._get_sheets_service()
            sheet_name = sheet_name or "Inventory"
            
            # Prepare data
            all_data = []
            
            if products:
                products_data = GoogleSheetsExporter._prepare_products_data(products)
                all_data.extend(products_data)
                if spools:
                    # Add separator row
                    all_data.append([])
            
            if spools:
                # Get products if needed for spool data
                products_for_lookup = products if products else None
                spools_data = GoogleSheetsExporter._prepare_spools_data(spools, products_for_lookup)
                all_data.extend(spools_data)
            
            # Get spreadsheet info and check if sheet exists
            try:
                spreadsheet = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
                sheet_exists = any(s.get('properties', {}).get('title') == sheet_name 
                                 for s in spreadsheet.get('sheets', []))
            except Exception as e:
                raise GoogleSheetsError(f"Spreadsheet not found or not accessible: {spreadsheet_id}. Error: {str(e)}")
            
            if not sheet_exists:
                # Create new sheet
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
            
            # Clear existing data and write new data
            range_name = f"{sheet_name}!A1"
            
            # Clear sheet
            service.spreadsheets().values().clear(
                spreadsheetId=spreadsheet_id,
                range=f"{sheet_name}!A:Z"
            ).execute()
            
            # Write data
            body = {
                'values': all_data
            }
            result = service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Format header row (bold, freeze)
            sheet_id = None
            for sheet in spreadsheet.get('sheets', []):
                if sheet.get('properties', {}).get('title') == sheet_name:
                    sheet_id = sheet.get('properties', {}).get('sheetId')
                    break
            
            if sheet_id is not None:
                # Format header row
                format_requests = [
                    {
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
                    },
                    {
                        'updateSheetProperties': {
                            'properties': {
                                'sheetId': sheet_id,
                                'gridProperties': {
                                    'frozenRowCount': 1
                                }
                            },
                            'fields': 'gridProperties.frozenRowCount'
                        }
                    }
                ]
                
                service.spreadsheets().batchUpdate(
                    spreadsheetId=spreadsheet_id,
                    body={'requests': format_requests}
                ).execute()
            
            sheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}"
            
            return {
                "success": True,
                "spreadsheet_id": spreadsheet_id,
                "sheet_name": sheet_name,
                "rows_written": len(all_data) - 1,  # Exclude header
                "sheet_url": sheet_url
            }
            
        except GoogleSheetsError:
            raise
        except Exception as e:
            logger.error(f"Failed to export to Google Sheets: {e}", exc_info=True)
            raise GoogleSheetsError(f"Failed to export to Google Sheets: {str(e)}")

