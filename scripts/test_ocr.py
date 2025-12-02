#!/usr/bin/env python3
"""Test OCR functionality with sample images."""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.ocr_service import LabelParser, OCRError
from backend.validation import validate_image_file, ValidationError


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
                "dimensions": metadata["size"],
                "file_size_mb": round(metadata["file_size_bytes"] / (1024 * 1024), 2)
            }
            print(f"✓ Validation passed: {metadata['format']} {metadata['size'][0]}x{metadata['size'][1]}")
        except ValidationError as e:
            result["validation"] = {"success": False, "error": str(e)}
            result["errors"].append(f"Validation failed: {e}")
            print(f"✗ Validation failed: {e}")
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
    
    return result


def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_ocr.py <image_path> [image_path2 ...]")
        print("\nExample:")
        print("  python scripts/test_ocr.py tests/samples/label_sunlu.jpg")
        sys.exit(1)
    
    results = []
    for image_path in sys.argv[1:]:
        result = test_ocr(image_path)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    successful = sum(1 for r in results if r["success"])
    print(f"Total images tested: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    
    if successful < len(results):
        print("\nFailed tests:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['file']}: {', '.join(r['errors'])}")
    
    sys.exit(0 if successful == len(results) else 1)


if __name__ == "__main__":
    main()

