import re
from typing import List, Dict, Optional
from datetime import datetime
import pdfplumber


class InvoiceParser:
    """Parse PDF invoices to extract filament order information."""

    @staticmethod
    def parse_bambu_invoice(pdf_bytes: bytes) -> Dict[str, any]:
        """
        Parse Bambu Lab invoice PDF and extract order and product information.

        Returns dict with:
        - order_number: str
        - order_date: date
        - vendor: str ("Bambu Lab")
        - items: List[Dict] with product details
        """
        import io

        result = {
            "order_number": None,
            "order_date": None,
            "vendor": "Bambu Lab",
            "items": []
        }

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            # Extract text from all pages
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"

            # Extract order number
            order_match = re.search(r"Order Number:\s*([A-Za-z0-9]+)", full_text)
            if order_match:
                result["order_number"] = order_match.group(1)

            # Extract order date (use Invoice Date as proxy for purchase date)
            date_match = re.search(r"Invoice Date:\s*(\d{4}-\d{2}-\d{2})", full_text)
            if date_match:
                result["order_date"] = datetime.strptime(date_match.group(1), "%Y-%m-%d").date()

            # Parse product items - look for filament products
            # Pattern: Product name, SKU, Variant, Qty, Price info
            items = InvoiceParser._extract_bambu_products(full_text)
            result["items"] = items

        return result

    @staticmethod
    def _extract_bambu_products(text: str) -> List[Dict]:
        """Extract individual product items from Bambu invoice text."""
        items = []

        # Split by lines and process sequentially
        lines = [line.strip() for line in text.split("\n")]
        i = 0

        while i < len(lines):
            line = lines[i]

            # Look for filament product names (PLA, PETG, TPU, etc.)
            # Handle various formats: "PLA Basic", "PLA Silk Multi-Color", "TPU for AMS", "PLA Tough+", etc.
            # Also handle cases where product name might be split across lines
            product_name = None
            
            # Check if current line starts with a material type
            material_match = re.match(r"^(PLA|PETG|ABS|TPU|ASA)(\s+(Basic|Silk|Matte|Tough\+|Tough|Multi-Color|for AMS|HF))?", line, re.IGNORECASE)
            
            if material_match:
                # Product name might be on this line or continue on next line
                product_name = line
                i += 1
                
                # Check if product name continues on next line (e.g., "PLA Silk" on one line, "Multi-Color" on next)
                if i < len(lines) and not lines[i].startswith(("SKU:", "WA STATE", "TAX", "Variant:")):
                    # Check if next line continues the product name
                    next_line = lines[i]
                    if re.match(r"^(Multi-Color|for AMS|HF)", next_line, re.IGNORECASE):
                        product_name += " " + next_line
                        i += 1
            else:
                i += 1
                continue

            if not product_name:
                i += 1
                continue

            # Skip WA STATE TAX line
            if i < len(lines) and "WA STATE" in lines[i]:
                i += 1

            # Next line should have SKU
            sku = None
            if i < len(lines) and lines[i].startswith("SKU:"):
                sku_match = re.search(r"SKU:\s*([A-Z0-9-]+)", lines[i])
                sku = sku_match.group(1) if sku_match else None
                i += 1

            # Skip TAX line
            if i < len(lines) and "TAX" in lines[i] and "WA STATE" not in lines[i]:
                i += 1

            # Next line has quantity and prices
            # Format: "SPLFREE 1 $19.99 $7.00 $1.22 $12.99" or "SPL 1 $24.99 $2.50 $2.11 $22.49"
            # Sometimes quantity/price might be on same line as SKU or variant
            qty = 1
            price = None
            
            # Look ahead a few lines to find quantity/price
            # Format variations:
            # - "SPLFREE 1 $19.99 $7.00 $1.22 $12.99"
            # - "SPL 1 $24.99 $2.50 $2.11 $22.49"  
            # - "1 $24.99 $2.50 $2.11 $22.49" (no SPL prefix - PLA Silk, TPU, PLA Tough+)
            # - "2 $23.99 $19.19 $2.70 $28.79" (PLA Tough+ with quantity 2)
            for look_ahead in range(i, min(i + 5, len(lines))):
                qty_price_line = lines[look_ahead]
                # Try patterns: SPLFREE/SPL with qty/price, or just qty/price at start of line
                # Match: "SPLFREE 1 $19.99" or "SPL 1 $24.99" or "1 $24.99" or "2 $23.99"
                qty_match = re.search(r"^(?:SPL(?:FREE)?\s+)?(\d+)\s+\$(\d+\.\d+)", qty_price_line)
                if qty_match:
                    qty = int(qty_match.group(1))
                    price = float(qty_match.group(2))
                    i = look_ahead + 1
                    break
            else:
                # If no quantity/price found, continue to next line
                i += 1

            # Skip WA CITY TAX line (if separate)
            if i < len(lines) and lines[i] == "WA CITY" or (lines[i].startswith("WA CITY") and "TAX" not in lines[i]):
                i += 1

            # Next line(s) have variant info
            # Format variations:
            # - "Variant: Orange (10300) / Refill /"
            # - "Variant: Dawn Radiance (13912) WA CITY"
            # - "Variant: White (12107) / WA CITY"
            # - Might be split across multiple lines
            color_name = None
            variant_line = ""

            # Collect variant info (might be across multiple lines)
            # Look ahead up to 5 lines for variant information
            for look_ahead in range(i, min(i + 5, len(lines))):
                line = lines[look_ahead]
                
                # Stop if we hit a new product
                if re.match(r"^(PLA|PETG|ABS|TPU|ASA)", line):
                    break
                    
                # Stop if we hit summary sections
                if line.startswith(("Items Subtotal", "Shipping", "Grand total", "Total exclude")):
                    break
                
                # Collect variant line
                if line.startswith("Variant:") or ("(" in line and ")" in line and not line.startswith("PLA")):
                    variant_line += " " + line
                    # Check if we have enough info (color name in parentheses)
                    if "(" in variant_line and ")" in variant_line:
                        i = look_ahead + 1
                        break
                elif variant_line and not line.startswith(("TAX", "WA STATE", "WA CITY", "SKU", "SPL")):
                    # Continue collecting if we're in the middle of variant info
                    variant_line += " " + line
                    if "kg" in variant_line or ("(" in variant_line and ")" in variant_line):
                        i = look_ahead + 1
                        break
            else:
                i += 1

            # Parse color from variant
            color_match = re.search(r"Variant:\s*([^(]+?)\s*\(", variant_line)
            if color_match:
                color_name = color_match.group(1).strip()
                # Clean up color name - remove trailing TAX, WA STATE, etc.
                color_name = re.sub(r'\s+(TAX|WA STATE|WA CITY|Refill|Filament|with spool|/).*$', '', color_name, flags=re.IGNORECASE).strip()
                # Remove extra whitespace
                color_name = " ".join(color_name.split())

            # Extract material type from product name
            material = None
            product_upper = product_name.upper()
            
            if "PLA" in product_upper:
                if "SILK" in product_upper and "MULTI" in product_upper:
                    material = "PLA SILK MULTI-COLOR"
                elif "SILK" in product_upper:
                    material = "PLA SILK"
                elif "MATTE" in product_upper:
                    material = "PLA MATTE"
                elif "TOUGH+" in product_upper or "TOUGH" in product_upper:
                    material = "PLA TOUGH+"
                elif "BASIC" in product_upper:
                    material = "PLA BASIC"
                else:
                    material = "PLA"
            elif "PETG" in product_upper:
                material = "PETG HF" if "HF" in product_upper else "PETG"
            elif "ABS" in product_upper:
                material = "ABS"
            elif "TPU" in product_upper:
                material = "TPU"
            elif "ASA" in product_upper:
                material = "ASA"

            # Only add if we have essential info
            if material and color_name:
                items.append({
                    "brand": "Bambu Lab",
                    "material": material,
                    "color_name": color_name,
                    "diameter_mm": 1.75,  # Bambu standard
                    "sku": sku,
                    "quantity": qty,
                    "price": price,
                    "product_line": product_name
                })

        return items

    @staticmethod
    def parse_amazon_invoice(pdf_bytes: bytes) -> Dict[str, any]:
        """
        Parse Amazon invoice PDF.
        
        Returns dict with:
        - order_number: str
        - order_date: date
        - vendor: str ("Amazon")
        - items: List[Dict] with product details
        """
        import io
        
        result = {
            "order_number": None,
            "order_date": None,
            "vendor": "Amazon",
            "items": []
        }
        
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
                
            # Extract order number
            # Pattern: Order # 112-3645497-2433833
            order_match = re.search(r"Order #\s*(\d{3}-\d{7}-\d{7})", full_text)
            if order_match:
                result["order_number"] = order_match.group(1)
                
            # Extract order date
            # Pattern: Order placed November 23, 2025
            date_match = re.search(r"Order placed\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", full_text)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    result["order_date"] = datetime.strptime(date_str, "%B %d, %Y").date()
                except ValueError:
                    pass
                    
            # Extract items
            # Amazon Order Details PDF structure is block-based.
            # We'll look for price patterns and backtrack to find product details
            result["items"] = InvoiceParser._extract_amazon_products(full_text)
            
        return result

    @staticmethod
    def _extract_amazon_products(text: str) -> List[Dict]:
        """Extract product items from Amazon invoice text."""
        items = []
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Look for price line which marks end of an item block usually
            # Format: $19.97 or $13.03
            price_match = re.match(r"^\$(\d+\.\d{2})$", line)
            
            if price_match:
                price = float(price_match.group(1))
                
                # Backtrack to find product description
                # Usually: 
                # [Product Description lines...]
                # Sold by: ...
                # Return or replace items: ...
                # $Price
                
                # Look back for "Sold by:"
                sold_by_idx = -1
                for j in range(i - 1, max(-1, i - 10), -1):
                    if lines[j].startswith("Sold by:") or lines[j].startswith("Supplied by:"):
                        sold_by_idx = j
                        break
                
                if sold_by_idx != -1:
                    # Product description is before "Sold by"
                    # It might be 1-4 lines (Amazon descriptions can be long)
                    description_lines = []
                    # Go back from sold_by_idx until we hit a date, price, or another known marker
                    # or just take the previous 2-4 lines which usually contain the title
                    
                    # Simple heuristic: Take lines above Sold by, stopping if we see:
                    # - Delivered/Order placed (header info)
                    # - Return or replace (next item's footer)
                    # - Order # (header)
                    # - Another price line (previous item)
                    for k in range(sold_by_idx - 1, max(-1, sold_by_idx - 6), -1):
                        prev_line = lines[k]
                        # Stop if we hit header/footer markers
                        if (prev_line.startswith("Delivered") or 
                            "Order placed" in prev_line or 
                            prev_line.startswith("Return or replace") or
                            prev_line.startswith("Order #") or
                            prev_line.startswith("Supplied by:")):
                            break
                        # Stop if we hit another price (previous item)
                        if re.match(r"^\$(\d+\.\d{2})$", prev_line):
                            break
                        description_lines.insert(0, prev_line)
                    
                    full_description = " ".join(description_lines).strip()
                    
                    # Clean up: Remove any leading price that might have been included
                    full_description = re.sub(r'^\$\d+\.\d{2}\s+', '', full_description)
                    
                    # Check if it's a filament
                    if "filament" in full_description.lower() or "pla" in full_description.lower() or "petg" in full_description.lower():
                        item_data = InvoiceParser._parse_amazon_filament_description(full_description, price)
                        if item_data:
                            items.append(item_data)
                            
            i += 1
            
        return items

    @staticmethod
    def _parse_amazon_filament_description(description: str, price: float) -> Optional[Dict]:
        """Parse Amazon product description string into structured data."""
        desc_lower = description.lower()
        
        # Brand detection
        brand = "Unknown"
        if "esun" in desc_lower:
            brand = "eSUN"
        elif "sunlu" in desc_lower:
            brand = "Sunlu"
        elif "overture" in desc_lower:
            brand = "Overture"
        elif "polymaker" in desc_lower:
            brand = "Polymaker"
        elif "hatchbox" in desc_lower:
            brand = "Hatchbox"
        elif "bambu" in desc_lower:
            brand = "Bambu Lab"
            
        # Material detection
        material = "PLA"  # Default
        if "pla+" in desc_lower or "pla plus" in desc_lower:
            material = "PLA+"
        elif "pla matte" in desc_lower or "matte pla" in desc_lower:
            material = "PLA Matte"
        elif "pla silk" in desc_lower or "silk pla" in desc_lower:
            material = "PLA Silk"
        elif "pla" in desc_lower:
            material = "PLA"
        elif "petg" in desc_lower:
            material = "PETG"
        elif "tpu" in desc_lower:
            material = "TPU"
        elif "abs" in desc_lower:
            material = "ABS"
        elif "asa" in desc_lower:
            material = "ASA"
            
        # Color detection
        # Look for color name usually at end or separated by commas
        # Heuristic: Look for common color names
        colors = [
            "black", "white", "grey", "gray", "red", "blue", "green", "yellow", 
            "orange", "purple", "pink", "gold", "silver", "copper", "brown", "pine green",
            "deep black", "cold white", "cool white"
        ]
        
        color_name = "Unknown"
        found_colors = []
        for c in colors:
            if c in desc_lower:
                found_colors.append(c)
        
        if found_colors:
            # Pick the longest match (e.g., "deep black" over "black")
            color_name = max(found_colors, key=len).title()
            
        # Diameter
        diameter = 1.75
        if "2.85" in description:
            diameter = 2.85
            
        return {
            "brand": brand,
            "material": material,
            "color_name": color_name,
            "diameter_mm": diameter,
            "sku": None, # Amazon doesn't easily show SKU in description
            "quantity": 1, # Assumed 1 unless parsed otherwise
            "price": price,
            "product_line": description[:50] + "..." # Truncate for reference
        }

    @staticmethod
    def detect_vendor(pdf_bytes: bytes) -> Optional[str]:
        """Detect which vendor an invoice is from based on PDF content."""
        import io

        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            first_page_text = pdf.pages[0].extract_text() if pdf.pages else ""

            if "bambulab" in first_page_text.lower() or "bambu lab" in first_page_text.lower():
                return "bambu"
            elif "amazon" in first_page_text.lower():
                return "amazon"

        return None

    @staticmethod
    def parse_invoice(pdf_bytes: bytes) -> Dict[str, any]:
        """
        Auto-detect vendor and parse invoice accordingly.

        Returns dict with order info and extracted items.
        """
        vendor = InvoiceParser.detect_vendor(pdf_bytes)

        if vendor == "bambu":
            return InvoiceParser.parse_bambu_invoice(pdf_bytes)
        elif vendor == "amazon":
            return InvoiceParser.parse_amazon_invoice(pdf_bytes)
        else:
            raise ValueError("Unknown or unsupported invoice vendor")
