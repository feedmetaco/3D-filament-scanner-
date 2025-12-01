import re
from typing import Dict, Optional
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from io import BytesIO


class LabelParser:
    """Parse filament box labels using OCR and brand-specific patterns."""

    BRAND_PATTERNS = {
        "esun": {
            "identifier": r"e(SUN|sun)",
            "material": r"(PLA\+|PLA|ABS|PETG|TPU)",
            "color": r"(?:Printers,?\s+|,\s+)?(White|Black|Red|Blue|Green|Yellow|Orange|Purple|Grey|Gray|Transparent|Natural|Silver|Gold|Pink|Brown|Cyan|Magenta|[A-Z][a-z]+)",
            "diameter": r"(1\.75|2\.85|3\.0)[\s]?mm",
            "barcode": r"X0[A-Z0-9IO]{2}[A-Z0-9IO]{2}[A-Z0-9IO]{4}"
        },
        "sunlu": {
            "identifier": r"SUNLU",
            "material": r"(SILK[\s]+PLA|PLA\+|PLA|ABS|PETG|TPU)",
            "color": r"(White|Black|Red|Blue|Green|Yellow|Orange|Purple|Grey|Gray|Silver|Gold|Pink|Brown|Cyan|Magenta|[A-Z][a-z]+)",
            "diameter": r"(1\.75|2\.85|3\.0)[\s]?mm",
            "barcode": r"X[0-9]{4}[A-Z0-9]{6}"
        },
        "bambu": {
            "identifier": r"Bambu[\s]*Lab",
            "material": r"(PETG[\s-]?HF|PETG|PLA[\s-]?Basic|PLA[\s-]?Matte|PLA[\s-]?Silk|PLA|ABS|TPU)",
            "color": r"(Black|White|Red|Blue|Green|Yellow|Orange|Purple|Grey|Gray|Natural|Transparent|Silver|Gold|Pink|Brown|Cyan|Magenta|[A-Z][a-z]+)",
            "diameter": r"(1\.75|2\.85|3\.0)[\s]?mm",
            "barcode": None  # Bambu uses QR codes
        }
    }

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> Image.Image:
        """Convert uploaded image to format suitable for OCR."""
        img = Image.open(BytesIO(image_bytes))

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize if image is very small (improves OCR accuracy)
        width, height = img.size
        if width < 800 or height < 800:
            scale_factor = max(800 / width, 800 / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Increase sharpness for clearer text
        img = img.filter(ImageFilter.SHARPEN)

        # Increase contrast for better OCR
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)

        # Increase brightness slightly
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.2)

        return img

    @staticmethod
    def detect_brand(text: str) -> Optional[str]:
        """Detect brand from OCR text."""
        text_lower = text.lower()
        # Remove spaces for better matching
        text_no_space = text_lower.replace(" ", "").replace("\n", "")

        # eSUN variations
        if "esun" in text_no_space or "e-sun" in text_lower or "e sun" in text_lower:
            return "esun"
        # Sunlu
        elif "sunlu" in text_no_space:
            return "sunlu"
        # Bambu Lab
        elif "bambu" in text_no_space or "bambulab" in text_no_space:
            return "bambu"
        return None

    @staticmethod
    def parse_label(image_bytes: bytes) -> Dict[str, Optional[str]]:
        """
        Parse filament label image and extract structured data.

        Returns dict with keys: brand, material, color_name, diameter_mm, barcode
        """
        # Preprocess and run OCR
        img = LabelParser.preprocess_image(image_bytes)

        # Configure Tesseract for better accuracy
        # PSM 3 = Fully automatic page segmentation (default)
        # OEM 3 = Default OCR Engine Mode (both legacy and LSTM)
        custom_config = r'--oem 3 --psm 3'
        text = pytesseract.image_to_string(img, config=custom_config)

        # Detect brand
        brand = LabelParser.detect_brand(text)
        if not brand:
            return {
                "brand": None,
                "material": None,
                "color_name": None,
                "diameter_mm": None,
                "barcode": None,
                "raw_text": text
            }

        patterns = LabelParser.BRAND_PATTERNS[brand]

        # Extract fields using brand-specific patterns
        brand_names = {
            "esun": "eSUN",
            "sunlu": "Sunlu",
            "bambu": "Bambu Lab"
        }
        result = {
            "brand": brand_names.get(brand, brand.title()),
            "material": None,
            "color_name": None,
            "diameter_mm": None,
            "barcode": None,
            "raw_text": text
        }

        # Material
        # First try standard pattern
        material_match = re.search(patterns["material"], text, re.IGNORECASE)
        if material_match:
            # Normalize material name (remove hyphens, standardize spacing)
            material = material_match.group(1).upper()
            material = material.replace("-", " ")  # Convert hyphens to spaces
            material = " ".join(material.split())  # Normalize whitespace
            result["material"] = material
        else:
            # Fallback: look for common material names anywhere in text
            text_upper = text.upper()
            if "PLA+" in text_upper or "PLA +" in text_upper:
                result["material"] = "PLA+"
            elif "PLA" in text_upper:
                result["material"] = "PLA"
            elif "PETG" in text_upper:
                result["material"] = "PETG"
            elif "ABS" in text_upper:
                result["material"] = "ABS"
            elif "TPU" in text_upper:
                result["material"] = "TPU"

        # Color
        color_match = re.search(patterns["color"], text, re.IGNORECASE)
        if color_match:
            result["color_name"] = color_match.group(1).title()
        else:
            # Fallback: search for common colors anywhere in text
            common_colors = ["White", "Black", "Red", "Blue", "Green", "Yellow",
                           "Orange", "Purple", "Grey", "Gray", "Silver", "Gold",
                           "Pink", "Brown", "Natural", "Transparent"]
            for color in common_colors:
                if re.search(r'\b' + color + r'\b', text, re.IGNORECASE):
                    result["color_name"] = color
                    break

        # Diameter
        diameter_match = re.search(patterns["diameter"], text)
        if diameter_match:
            result["diameter_mm"] = float(diameter_match.group(1))

        # Barcode (if pattern exists)
        if patterns["barcode"]:
            barcode_match = re.search(patterns["barcode"], text)
            if barcode_match:
                result["barcode"] = barcode_match.group(0)

        return result
