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

            # Look for filament product names (PLA, PETG, etc.)
            # Format: "PLA Basic", "PLA Silk Multi-Color", "PETG HF", etc.
            if re.match(r"^(PLA|PETG|ABS|TPU|ASA)", line):
                product_name = line
                i += 1

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
                if i < len(lines) and "TAX" in lines[i]:
                    i += 1

                # Next line has quantity and prices
                # Format: "SPLFREE 1 $19.99 $7.00 $1.22 $12.99"
                qty = 1
                price = None
                if i < len(lines):
                    qty_price_line = lines[i]
                    qty_match = re.search(r"SPLFREE\s+(\d+)\s+\$(\d+\.\d+)", qty_price_line)
                    if qty_match:
                        qty = int(qty_match.group(1))
                        price = float(qty_match.group(2))
                    i += 1

                # Skip WA CITY TAX line
                if i < len(lines) and "WA CITY" in lines[i]:
                    i += 1

                # Next line(s) have variant info
                # Format: "Variant: Orange (10300) / Refill /" or split across lines
                color_name = None
                variant_line = ""

                # Collect variant info (might be across multiple lines)
                while i < len(lines) and (lines[i].startswith("Variant:") or
                                          ("(" in lines[i] and ")" in lines[i]) or
                                          (variant_line and not lines[i].startswith(("PLA", "PETG", "ABS", "TPU", "ASA", "WA STATE", "TAX", "Bambu")))):
                    variant_line += " " + lines[i]
                    i += 1
                    if "kg" in variant_line or "mm" in variant_line:
                        break

                # Parse color from variant
                color_match = re.search(r"Variant:\s*([^(]+?)\s*\(", variant_line)
                if color_match:
                    color_name = color_match.group(1).strip()
                    # Clean up color name - remove trailing TAX, WA STATE, etc.
                    color_name = re.sub(r'\s+(TAX|WA STATE|WA CITY).*$', '', color_name, flags=re.IGNORECASE).strip()

                # Extract material type from product name
                material = None
                if "PLA" in product_name:
                    if "Silk" in product_name:
                        material = "PLA SILK"
                    elif "Matte" in product_name:
                        material = "PLA MATTE"
                    elif "Basic" in product_name:
                        material = "PLA BASIC"
                    elif "Multi-Color" in product_name:
                        material = "PLA MULTI-COLOR"
                    else:
                        material = "PLA"
                elif "PETG" in product_name:
                    material = "PETG HF" if "HF" in product_name else "PETG"
                elif "ABS" in product_name:
                    material = "ABS"
                elif "TPU" in product_name:
                    material = "TPU"
                elif "ASA" in product_name:
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
            else:
                i += 1

        return items

    @staticmethod
    def parse_amazon_invoice(pdf_bytes: bytes) -> Dict[str, any]:
        """
        Parse Amazon invoice PDF.

        Returns similar structure to Bambu parser.
        """
        # TODO: Implement Amazon invoice parser
        # Different format than Bambu Lab
        return {
            "order_number": None,
            "order_date": None,
            "vendor": "Amazon",
            "items": []
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
