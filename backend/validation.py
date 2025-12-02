"""File validation utilities for uploads."""
import os
from typing import Tuple, Optional
from PIL import Image
from io import BytesIO
import pdfplumber


# File size limits (in bytes)
MAX_IMAGE_SIZE = 15 * 1024 * 1024  # 15 MB
MAX_PDF_SIZE = 20 * 1024 * 1024     # 20 MB

# Image dimension limits
MIN_IMAGE_DIMENSION = 100  # pixels
MAX_IMAGE_DIMENSION = 8000  # pixels

# Supported image formats (MPO is JPEG-based, DNG is TIFF-based, so PIL can handle them)
SUPPORTED_IMAGE_FORMATS = {"JPEG", "PNG", "WEBP", "JPG", "MPO", "TIFF", "DNG"}
SUPPORTED_IMAGE_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/mpo",  # Multi-Picture Object (JPEG-based)
    "image/tiff",  # TIFF format
    "image/x-adobe-dng"  # Digital Negative (TIFF-based)
}

# Supported PDF MIME types
SUPPORTED_PDF_MIME_TYPES = {
    "application/pdf"
}

# Max PDF pages (to prevent processing huge files)
MAX_PDF_PAGES = 50


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_image_file(
    file_bytes: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> Tuple[Image.Image, dict]:
    """
    Validate image file and return PIL Image object with metadata.
    
    Args:
        file_bytes: Image file bytes
        filename: Original filename (optional, for extension check)
        content_type: MIME type (optional)
    
    Returns:
        Tuple of (PIL Image, metadata dict)
    
    Raises:
        ValidationError: If validation fails
    """
    # Check file size
    file_size = len(file_bytes)
    if file_size == 0:
        raise ValidationError("File is empty")
    
    if file_size > MAX_IMAGE_SIZE:
        raise ValidationError(
            f"File too large: {file_size / (1024*1024):.1f} MB. "
            f"Maximum allowed: {MAX_IMAGE_SIZE / (1024*1024):.0f} MB. "
            "Please compress the image or use a smaller file."
        )
    
    # Validate content-type if provided
    if content_type and content_type not in SUPPORTED_IMAGE_MIME_TYPES:
        raise ValidationError(
            f"Unsupported image format: {content_type}. "
            f"Supported formats: JPEG, PNG, WebP"
        )
    
    # Validate file extension if provided
    if filename:
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext not in {"jpg", "jpeg", "png", "webp", "mpo", "dng", "tiff", "tif"}:
            raise ValidationError(
                f"Unsupported file extension: .{ext}. "
                "Supported: .jpg, .jpeg, .png, .webp, .mpo, .dng, .tiff, .tif"
            )
    
    # Try to open and validate image
    try:
        img = Image.open(BytesIO(file_bytes))
        
        # Verify image is readable
        img.verify()
        
        # Reopen after verify (verify closes the image)
        img = Image.open(BytesIO(file_bytes))
        
        # Check image format (MPO is JPEG-based, convert to JPEG for processing)
        if img.format not in SUPPORTED_IMAGE_FORMATS:
            raise ValidationError(
                f"Unsupported image format: {img.format}. "
                f"Supported formats: {', '.join(sorted(SUPPORTED_IMAGE_FORMATS - {'MPO'}))}"
            )
        
        # Convert MPO/DNG to RGB (MPO is JPEG-based, DNG is TIFF-based)
        if img.format == "MPO":
            # MPO files contain multiple JPEG images, extract the first one
            img = img.convert("RGB")
        elif img.format in ("TIFF", "DNG"):
            # DNG/TIFF files may have different color modes, convert to RGB
            if img.mode != "RGB":
                img = img.convert("RGB")
        
        # Check dimensions
        width, height = img.size
        min_dim = min(width, height)
        max_dim = max(width, height)
        
        if min_dim < MIN_IMAGE_DIMENSION:
            raise ValidationError(
                f"Image too small: {width}x{height} pixels. "
                f"Minimum dimension: {MIN_IMAGE_DIMENSION} pixels. "
                "Please use a higher resolution image."
            )
        
        if max_dim > MAX_IMAGE_DIMENSION:
            raise ValidationError(
                f"Image too large: {width}x{height} pixels. "
                f"Maximum dimension: {MAX_IMAGE_DIMENSION} pixels. "
                "Please resize the image."
            )
        
        # Return image and metadata
        metadata = {
            "format": img.format,
            "size": (width, height),
            "mode": img.mode,
            "file_size_bytes": file_size
        }
        
        return img, metadata
        
    except Image.UnidentifiedImageError:
        raise ValidationError(
            "Invalid image file. File may be corrupted or not a valid image format. "
            "Please try a different image file."
        )
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Failed to validate image: {str(e)}")


def validate_pdf_file(
    file_bytes: bytes,
    filename: Optional[str] = None,
    content_type: Optional[str] = None
) -> dict:
    """
    Validate PDF file and return metadata.
    
    Args:
        file_bytes: PDF file bytes
        filename: Original filename (optional, for extension check)
        content_type: MIME type (optional)
    
    Returns:
        Metadata dict with page_count, file_size, etc.
    
    Raises:
        ValidationError: If validation fails
    """
    # Check file size
    file_size = len(file_bytes)
    if file_size == 0:
        raise ValidationError("File is empty")
    
    if file_size > MAX_PDF_SIZE:
        raise ValidationError(
            f"File too large: {file_size / (1024*1024):.1f} MB. "
            f"Maximum allowed: {MAX_PDF_SIZE / (1024*1024):.0f} MB. "
            "Please use a smaller PDF file."
        )
    
    # Validate content-type if provided
    if content_type and content_type not in SUPPORTED_PDF_MIME_TYPES:
        raise ValidationError(
            f"Unsupported file format: {content_type}. "
            "Only PDF files are supported."
        )
    
    # Validate file extension if provided
    if filename:
        ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if ext != "pdf":
            raise ValidationError(
                f"Unsupported file extension: .{ext}. "
                "Only .pdf files are supported."
            )
    
    # Try to open and validate PDF
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            
            # Check page count
            if page_count == 0:
                raise ValidationError("PDF has no pages")
            
            if page_count > MAX_PDF_PAGES:
                raise ValidationError(
                    f"PDF has too many pages: {page_count}. "
                    f"Maximum allowed: {MAX_PDF_PAGES} pages. "
                    "Please split the PDF or use a smaller file."
                )
            
            # Try to extract text from first page (verify it's not corrupted)
            try:
                first_page_text = pdf.pages[0].extract_text()
                if first_page_text is None:
                    # PDF might be image-based (scanned), that's okay
                    pass
            except Exception:
                # If we can't extract text, PDF might be image-based or corrupted
                # We'll let the parser handle this
                pass
            
            metadata = {
                "page_count": page_count,
                "file_size_bytes": file_size,
                "has_text": first_page_text is not None if 'first_page_text' in locals() else None
            }
            
            return metadata
            
    except pdfplumber.exceptions.PDFSyntaxError:
        raise ValidationError(
            "Invalid PDF file. File may be corrupted or not a valid PDF. "
            "Please try a different PDF file."
        )
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Failed to validate PDF: {str(e)}")

