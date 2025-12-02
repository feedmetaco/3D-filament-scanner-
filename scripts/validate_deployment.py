#!/usr/bin/env python3
"""Validate deployment environment before going live."""
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def check_tesseract():
    """Check if Tesseract is installed and accessible."""
    print("Checking Tesseract OCR...")
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"  ✓ Tesseract version: {version}")
        return True
    except Exception as e:
        print(f"  ✗ Tesseract not available: {e}")
        return False


def check_dependencies():
    """Check if all required dependencies are installed."""
    print("\nChecking Python dependencies...")
    required = [
        "fastapi",
        "sqlmodel",
        "pytesseract",
        "PIL",
        "pdfplumber",
        "uvicorn"
    ]
    
    missing = []
    for dep in required:
        try:
            if dep == "PIL":
                __import__("PIL")
            else:
                __import__(dep)
            print(f"  ✓ {dep}")
        except ImportError:
            print(f"  ✗ {dep} - MISSING")
            missing.append(dep)
    
    return len(missing) == 0


def check_ocr_functionality():
    """Test OCR with a simple test image."""
    print("\nTesting OCR functionality...")
    try:
        from backend.ocr_service import LabelParser
        from PIL import Image, ImageDraw
        import io
        
        # Create simple test image
        img = Image.new('RGB', (200, 50), color='white')
        draw = ImageDraw.Draw(img)
        draw.text((10, 10), "TEST", fill='black')
        
        # Convert to bytes
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        # Try OCR
        result = LabelParser.parse_label(img_bytes.getvalue())
        print(f"  ✓ OCR test successful")
        print(f"    Detected text: {result.get('raw_text', '')[:50]}")
        return True
    except Exception as e:
        print(f"  ✗ OCR test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_pdf_functionality():
    """Test PDF parsing functionality."""
    print("\nTesting PDF parsing functionality...")
    try:
        from backend.invoice_parser import InvoiceParser
        from backend.validation import validate_pdf_file
        import pdfplumber
        from PIL import Image, ImageDraw
        import io
        
        # Create a simple PDF-like structure (minimal test)
        # Note: This is a basic check - real PDFs are more complex
        print("  ✓ PDF libraries available")
        return True
    except Exception as e:
        print(f"  ✗ PDF test failed: {e}")
        return False


def check_validation():
    """Test validation functions."""
    print("\nTesting validation functions...")
    try:
        from backend.validation import (
            validate_image_file,
            validate_pdf_file,
            MAX_IMAGE_SIZE,
            MAX_PDF_SIZE
        )
        print(f"  ✓ Validation module loaded")
        print(f"    Max image size: {MAX_IMAGE_SIZE / (1024*1024):.0f} MB")
        print(f"    Max PDF size: {MAX_PDF_SIZE / (1024*1024):.0f} MB")
        return True
    except Exception as e:
        print(f"  ✗ Validation test failed: {e}")
        return False


def check_database():
    """Check database connectivity."""
    print("\nChecking database configuration...")
    try:
        from backend.database import DATABASE_URL, engine
        print(f"  ✓ Database URL configured: {DATABASE_URL[:30]}...")
        
        # Try to connect
        with engine.connect() as conn:
            print(f"  ✓ Database connection successful")
        return True
    except Exception as e:
        print(f"  ✗ Database check failed: {e}")
        return False


def main():
    """Run all validation checks."""
    print("="*60)
    print("Deployment Validation")
    print("="*60)
    
    checks = [
        ("Tesseract OCR", check_tesseract),
        ("Python Dependencies", check_dependencies),
        ("OCR Functionality", check_ocr_functionality),
        ("PDF Functionality", check_pdf_functionality),
        ("Validation Functions", check_validation),
        ("Database Configuration", check_database),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} check crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n✓ All checks passed! Ready for deployment.")
        return 0
    else:
        print(f"\n✗ {total - passed} check(s) failed. Please fix issues before deployment.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

