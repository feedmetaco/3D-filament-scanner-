import re
import logging
from typing import Dict, Optional, Tuple
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from io import BytesIO

logger = logging.getLogger(__name__)


class OCRError(Exception):
    """Custom exception for OCR-related errors."""
    pass


class LabelParser:
    """Parse filament box labels using OCR and brand-specific patterns."""

    # Chinese to English color name mappings (for Bambu Lab labels)
    CHINESE_COLOR_MAP = {
        "黑色": "Black",
        "白色": "White",
        "红色": "Red",
        "蓝色": "Blue",
        "绿色": "Green",
        "黄色": "Yellow",
        "橙色": "Orange",
        "紫色": "Purple",
        "灰色": "Grey",
        "银色": "Silver",
        "金色": "Gold",
        "粉色": "Pink",
        "棕色": "Brown",
        "自然色": "Natural",
        "透明": "Transparent",
        "青色": "Cyan",
        "洋红色": "Magenta",
    }

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
            "material": r"(PETG[\s-]?HF|PETG|PLA[\s-]?Basic|PLA[\s-]?Matte|PLA[\s-]?Silk|PLA|ABS|TPU|ASA)",
            "color": r"(Black|White|Red|Blue|Green|Yellow|Orange|Purple|Grey|Gray|Natural|Transparent|Silver|Gold|Pink|Brown|Cyan|Magenta|[A-Z][a-z]+)",
            "diameter": r"(1\.75|2\.85|3\.0)[\s]?mm|(1\.75|2\.85|3\.0)[\s]?毫米",  # Support both mm and Chinese 毫米
            "barcode": None  # Bambu uses QR codes
        }
    }

    # PSM modes optimized for labels (try in order of preference)
    PSM_MODES = [
        6,   # Uniform block of text (best for labels)
        11,  # Sparse text (good for labels with spacing)
        3,   # Fully automatic (fallback)
        7,   # Single text line (fallback)
    ]

    @staticmethod
    def _check_tesseract_available() -> bool:
        """Check if Tesseract is installed and accessible."""
        try:
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.error(f"Tesseract not available: {e}")
            return False

    @staticmethod
    def _validate_image(image_bytes: bytes) -> Image.Image:
        """Validate and load image, raising descriptive errors."""
        try:
            img = Image.open(BytesIO(image_bytes))
            # Verify image is readable
            img.verify()
            # Reopen after verify (verify closes the image)
            img = Image.open(BytesIO(image_bytes))
            return img
        except Exception as e:
            raise OCRError(f"Invalid image format or corrupted image: {str(e)}")

    @staticmethod
    def _preprocess_basic(img: Image.Image) -> Image.Image:
        """Basic preprocessing: orientation, format, size."""
        # Auto-rotate based on EXIF orientation (important for phone photos)
        try:
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass  # If EXIF data missing or error, continue

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Resize to optimal size for OCR
        width, height = img.size
        max_dimension = 2000
        min_dimension = 800

        # Downscale if too large
        if width > max_dimension or height > max_dimension:
            scale_factor = max_dimension / max(width, height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Upscale if too small
        elif width < min_dimension or height < min_dimension:
            scale_factor = max(min_dimension / width, min_dimension / height)
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        return img

    @staticmethod
    def _preprocess_strategy_1(img: Image.Image) -> Image.Image:
        """Strategy 1: Moderate enhancement (good for clear labels)."""
        img = LabelParser._preprocess_basic(img)
        # Light sharpening
        img = img.filter(ImageFilter.SHARPEN)
        # Moderate contrast enhancement
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.5)
        return img

    @staticmethod
    def _preprocess_strategy_2(img: Image.Image) -> Image.Image:
        """Strategy 2: Grayscale + binarization (good for high contrast labels)."""
        img = LabelParser._preprocess_basic(img)
        # Convert to grayscale
        img = img.convert("L")
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0)
        # Binarize (convert to pure black/white)
        threshold = 128
        img = img.point(lambda x: 255 if x > threshold else 0, mode='1')
        # Convert back to RGB for Tesseract
        img = img.convert("RGB")
        return img

    @staticmethod
    def _preprocess_strategy_3(img: Image.Image) -> Image.Image:
        """Strategy 3: Aggressive enhancement (for poor quality images)."""
        img = LabelParser._preprocess_basic(img)
        # Sharpening
        img = img.filter(ImageFilter.SHARPEN)
        # High contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.5)
        # Brightness adjustment
        brightness_enhancer = ImageEnhance.Brightness(img)
        img = brightness_enhancer.enhance(1.3)
        return img

    @staticmethod
    def _preprocess_strategy_4(img: Image.Image) -> Image.Image:
        """Strategy 4: Minimal processing (for already good images)."""
        img = LabelParser._preprocess_basic(img)
        # Just light sharpening
        img = img.filter(ImageFilter.SHARPEN)
        return img

    @staticmethod
    def _run_ocr_with_config(img: Image.Image, psm: int, lang: str = 'eng+chi_sim') -> Tuple[str, float]:
        """
        Run OCR with specific PSM mode and return text with confidence.
        
        Args:
            img: Preprocessed image
            psm: Page Segmentation Mode
            lang: Language(s) to use (default: 'eng+chi_sim' for English + Chinese)
        
        Returns:
            Tuple of (text, average_confidence)
        """
        config = f'--oem 3 --psm {psm} -l {lang}'
        try:
            # Get detailed data including confidence
            data = pytesseract.image_to_data(img, config=config, output_type=pytesseract.Output.DICT)
            
            # Extract text and calculate average confidence
            text_parts = []
            confidences = []
            
            for i, conf in enumerate(data['conf']):
                if int(conf) > 0:  # Valid confidence
                    text_parts.append(data['text'][i])
                    confidences.append(float(conf))
            
            text = ' '.join(text_parts).strip()
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            return text, avg_confidence
        except Exception as e:
            logger.warning(f"OCR failed with PSM {psm}: {e}")
            # Fallback to simple text extraction
            text = pytesseract.image_to_string(img, config=config)
            return text, 0.0

    @staticmethod
    def _extract_text_multiple_strategies(image_bytes: bytes) -> Tuple[str, str]:
        """
        Try multiple preprocessing strategies and PSM modes to get best OCR result.
        
        Returns:
            Tuple of (best_text, strategy_used)
        """
        original_img = LabelParser._validate_image(image_bytes)
        
        strategies = [
            ("strategy_1_moderate", LabelParser._preprocess_strategy_1),
            ("strategy_4_minimal", LabelParser._preprocess_strategy_4),
            ("strategy_2_grayscale", LabelParser._preprocess_strategy_2),
            ("strategy_3_aggressive", LabelParser._preprocess_strategy_3),
        ]
        
        best_text = ""
        best_confidence = 0.0
        best_strategy = "unknown"
        best_psm = 6
        
        for strategy_name, strategy_func in strategies:
            try:
                preprocessed_img = strategy_func(original_img.copy())
                
                # Try different PSM modes
                for psm in LabelParser.PSM_MODES:
                    try:
                        text, confidence = LabelParser._run_ocr_with_config(preprocessed_img, psm)
                        
                        # Check if we got meaningful text
                        if text and len(text.strip()) > 10:  # At least some text
                            # Prefer higher confidence or longer text
                            if confidence > best_confidence or (confidence > 0 and len(text) > len(best_text)):
                                best_text = text
                                best_confidence = confidence
                                best_strategy = strategy_name
                                best_psm = psm
                                
                                # If confidence is very high, we can stop early
                                if confidence > 80:
                                    logger.info(f"High confidence OCR result: {confidence:.1f}% using {strategy_name} PSM{psm}")
                                    return best_text, f"{strategy_name}_psm{psm}"
                    except Exception as e:
                        logger.debug(f"PSM {psm} failed for {strategy_name}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"Strategy {strategy_name} failed: {e}")
                continue
        
        if best_text:
            logger.info(f"Best OCR result: confidence {best_confidence:.1f}% using {best_strategy} PSM{best_psm}")
            return best_text, f"{best_strategy}_psm{best_psm}"
        else:
            # Last resort: try original image with default settings (English + Chinese)
            try:
                img = LabelParser._preprocess_basic(original_img)
                text = pytesseract.image_to_string(img, config='--oem 3 --psm 3 -l eng+chi_sim')
                return text, "fallback"
            except Exception as e:
                raise OCRError(f"All OCR strategies failed. Last error: {str(e)}")

    @staticmethod
    def detect_brand(text: str) -> Optional[str]:
        """Detect brand from OCR text."""
        if not text:
            return None
            
        text_lower = text.lower()
        # Remove spaces for better matching
        text_no_space = text_lower.replace(" ", "").replace("\n", "")

        # Bambu Lab - check first (before eSUN) since "Lab" might be misread
        if "bambu" in text_no_space or "bambulab" in text_no_space or "bambu lab" in text_lower:
            return "bambu"
        # eSUN variations
        elif "esun" in text_no_space or "e-sun" in text_lower or "e sun" in text_lower:
            return "esun"
        # Sunlu
        elif "sunlu" in text_no_space:
            return "sunlu"
        return None

    @staticmethod
    def parse_label(image_bytes: bytes) -> Dict[str, Optional[str]]:
        """
        Parse filament label image and extract structured data.

        Returns dict with keys: brand, material, color_name, diameter_mm, barcode, raw_text, ocr_confidence, strategy_used
        
        Raises:
            OCRError: If OCR fails or Tesseract is not available
        """
        # Check Tesseract availability
        if not LabelParser._check_tesseract_available():
            raise OCRError(
                "Tesseract OCR is not installed or not accessible. "
                "Please ensure Tesseract is installed and in your PATH."
            )

        try:
            # Extract text using multiple strategies
            text, strategy_used = LabelParser._extract_text_multiple_strategies(image_bytes)
            
            if not text or len(text.strip()) < 5:
                return {
                    "brand": None,
                    "material": None,
                    "color_name": None,
                    "diameter_mm": None,
                    "barcode": None,
                    "raw_text": text or "",
                    "ocr_confidence": 0.0,
                    "strategy_used": strategy_used,
                    "error": "No text detected in image. Please ensure the image is clear and contains readable text."
                }

            # Detect brand
            brand = LabelParser.detect_brand(text)
            if not brand:
                return {
                    "brand": None,
                    "material": None,
                    "color_name": None,
                    "diameter_mm": None,
                    "barcode": None,
                    "raw_text": text,
                    "ocr_confidence": 0.0,
                    "strategy_used": strategy_used,
                    "error": f"Could not detect brand. Detected text: {text[:200]}..."
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
                "raw_text": text,
                "ocr_confidence": 0.0,
                "strategy_used": strategy_used
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
                # Check compound materials first (PETG HF before PETG, PLA+ before PLA)
                if "PETG HF" in text_upper or "PETGHF" in text_upper or "PETG-HF" in text_upper:
                    result["material"] = "PETG HF"
                elif "PLA+" in text_upper or "PLA +" in text_upper or "PLA PLUS" in text_upper:
                    result["material"] = "PLA+"
                elif "PETG" in text_upper:
                    result["material"] = "PETG"
                elif "PLA" in text_upper:
                    result["material"] = "PLA"
                elif "ABS" in text_upper:
                    result["material"] = "ABS"
                elif "TPU" in text_upper:
                    result["material"] = "TPU"

            # Color
            # First, check for Chinese color names (for Bambu Lab labels)
            if brand == "bambu":
                for chinese_color, english_color in LabelParser.CHINESE_COLOR_MAP.items():
                    if chinese_color in text:
                        result["color_name"] = english_color
                        break

            # Try common English color word search (more reliable than regex patterns)
            if not result["color_name"]:
                common_colors = ["White", "Black", "Red", "Blue", "Green", "Yellow",
                               "Orange", "Purple", "Grey", "Gray", "Silver", "Gold",
                               "Pink", "Brown", "Natural", "Transparent", "Cyan", "Magenta"]

                for color in common_colors:
                    if re.search(r'\b' + color + r'\b', text, re.IGNORECASE):
                        result["color_name"] = color
                        break

            # If no common color found, try brand-specific pattern
            if not result["color_name"]:
                color_match = re.search(patterns["color"], text, re.IGNORECASE)
                if color_match:
                    color_candidate = color_match.group(1).strip()
                    # Filter out invalid colors (brand names, materials, single letters, etc.)
                    invalid_patterns = [
                        r'^[A-Z0-9]{1,3}$',  # Short codes like "A1", "HIF"
                        r'(?i)^(esun|sunlu|bambu|pla|petg|abs|tpu|filament)',  # Brand/material names
                    ]
                    is_valid = True
                    for pattern in invalid_patterns:
                        if re.match(pattern, color_candidate):
                            is_valid = False
                            break

                    if is_valid and len(color_candidate) > 3:
                        result["color_name"] = color_candidate.title()

            # Diameter
            diameter_match = re.search(patterns["diameter"], text)
            if diameter_match:
                # Try group 1 first (mm format), then group 2 (Chinese format)
                diameter_str = diameter_match.group(1) or diameter_match.group(2)
                if diameter_str:
                    result["diameter_mm"] = float(diameter_str)
            else:
                # Fallback: look for diameter anywhere in text (handles Chinese labels)
                # Pattern: number followed by mm or 毫米
                fallback_diameter = re.search(r'(1\.75|2\.85|3\.0)[\s]*(?:mm|毫米)', text, re.IGNORECASE)
                if fallback_diameter:
                    result["diameter_mm"] = float(fallback_diameter.group(1))

            # Barcode (if pattern exists)
            if patterns["barcode"]:
                barcode_match = re.search(patterns["barcode"], text)
                if barcode_match:
                    result["barcode"] = barcode_match.group(0)
                else:
                    # Fallback: look for barcode-like patterns (common OCR substitutions)
                    # X003II1ZZL might be read as X0O3II1ZZL, X003l11ZZL, etc.
                    # General pattern: X followed by alphanumeric characters
                    fallback_match = re.search(r'X[0O][0O][0-9A-Z]{2}[0-9A-Z]{2}[0-9A-Z]{4}', text, re.IGNORECASE)
                    if fallback_match:
                        barcode = fallback_match.group(0).upper()
                        # Fix common OCR mistakes
                        barcode = barcode.replace('O', '0')  # O → 0
                        result["barcode"] = barcode

            return result

        except OCRError:
            # Re-raise OCR errors
            raise
        except Exception as e:
            logger.error(f"Unexpected error during OCR parsing: {e}", exc_info=True)
            raise OCRError(f"Failed to parse label: {str(e)}")
