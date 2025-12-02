#!/usr/bin/env python3
"""Test PDF invoice parsing functionality."""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.invoice_parser import InvoiceParser
from backend.validation import validate_pdf_file, ValidationError


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
                "page_count": metadata["page_count"],
                "file_size_mb": round(metadata["file_size_bytes"] / (1024 * 1024), 2),
                "has_text": metadata.get("has_text", False)
            }
            print(f"✓ Validation passed: {metadata['page_count']} pages, {result['validation']['file_size_mb']} MB")
        except ValidationError as e:
            result["validation"] = {"success": False, "error": str(e)}
            result["errors"].append(f"Validation failed: {e}")
            print(f"✗ Validation failed: {e}")
            return result
        
        # Parse invoice
        try:
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
                    price = item.get('price')
                    price_str = f"${price:.2f}" if price else "N/A"
                    print(f"    {i}. {item.get('brand')} {item.get('material')} {item.get('color_name')} "
                          f"(Qty: {item.get('quantity', 0)}, Price: {price_str})")
            
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
    
    return result


def main():
    """Main test function."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_pdf.py <pdf_path> [pdf_path2 ...]")
        print("\nExample:")
        print("  python scripts/test_pdf.py tests/samples/invoice_bambu.pdf")
        sys.exit(1)
    
    results = []
    for pdf_path in sys.argv[1:]:
        result = test_pdf(pdf_path)
        results.append(result)
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary")
    print(f"{'='*60}")
    successful = sum(1 for r in results if r["success"])
    print(f"Total PDFs tested: {len(results)}")
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

