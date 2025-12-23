from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, SQLModel

from backend.database import get_session, init_db
from backend.models import (
    Product,
    ProductCreate,
    ProductUpdate,
    Spool,
    SpoolCreate,
    SpoolChangeLog,
    SpoolDetail,
    SpoolUpdate,
)
from backend.ocr_service import LabelParser
from backend.invoice_parser import InvoiceParser


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    init_db()
    yield
    # Shutdown (if needed in future)


app = FastAPI(
    title="3D Filament Scanner API",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will restrict to frontend domain after deployment
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def read_root() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/ocr", tags=["health"])
def health_ocr() -> dict:
    """
    Health check endpoint for OCR service.
    
    Returns:
    - status: "ok" or "error"
    - tesseract_available: Whether Tesseract is installed
    - tesseract_version: Tesseract version if available
    - test_result: Result of test OCR operation
    """
    from backend.ocr_service import LabelParser, OCRError
    
    result = {
        "status": "ok",
        "tesseract_available": False,
        "tesseract_version": None,
        "test_result": None
    }
    
    # Check Tesseract availability
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        result["tesseract_available"] = True
        result["tesseract_version"] = version
        
        # Try a simple test OCR (create a small test image)
        try:
            from PIL import Image, ImageDraw, ImageFont
            import io
            
            # Create a simple test image with text
            img = Image.new('RGB', (200, 50), color='white')
            draw = ImageDraw.Draw(img)
            # Draw simple text
            draw.text((10, 10), "TEST", fill='black')
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            img.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Try OCR
            test_text = pytesseract.image_to_string(img, config='--psm 7')
            result["test_result"] = {
                "success": True,
                "detected_text": test_text.strip()[:50]  # First 50 chars
            }
        except Exception as e:
            result["test_result"] = {
                "success": False,
                "error": str(e)
            }
            result["status"] = "warning"
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
    return result


# Product Endpoints
@app.post("/api/v1/products", response_model=Product, tags=["products"])
def create_product(
    product_in: ProductCreate, session: Session = Depends(get_session)
) -> Product:
    product = Product(**product_in.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.get("/api/v1/products", response_model=List[Product], tags=["products"])
def list_products(
    brand: Optional[str] = None,
    material: Optional[str] = None,
    color_name: Optional[str] = None,
    session: Session = Depends(get_session)
) -> List[Product]:
    """List products with optional filtering by brand, material, and color_name."""
    query = select(Product)

    if brand:
        query = query.where(Product.brand.ilike(f"%{brand}%"))
    if material:
        query = query.where(Product.material.ilike(f"%{material}%"))
    if color_name:
        query = query.where(Product.color_name.ilike(f"%{color_name}%"))

    products = session.exec(query).all()
    return products


@app.get("/api/v1/products/{product_id}", response_model=Product, tags=["products"])
def get_product(product_id: int, session: Session = Depends(get_session)) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/api/v1/products/{product_id}", response_model=Product, tags=["products"])
def update_product(
    product_id: int,
    product_in: ProductUpdate,
    session: Session = Depends(get_session),
) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)
    product.updated_at = datetime.now(timezone.utc)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.delete("/api/v1/products/{product_id}", status_code=204, tags=["products"])
def delete_product(product_id: int, session: Session = Depends(get_session)) -> None:
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()


# Spool Endpoints
@app.post("/api/v1/spools", response_model=Spool, tags=["spools"])
def create_spool(spool_in: SpoolCreate, session: Session = Depends(get_session)) -> Spool:
    spool = Spool(**spool_in.model_dump())
    session.add(spool)
    session.commit()
    session.refresh(spool)

    # Record initial state for audit trail
    change_log = SpoolChangeLog(
        spool_id=spool.id,
        to_status=spool.status,
        to_location=spool.storage_location,
        note="Spool created",
    )
    session.add(change_log)
    session.commit()

    return spool


@app.get("/api/v1/spools", response_model=List[Spool], tags=["spools"])
def list_spools(
    brand: Optional[str] = None,
    material: Optional[str] = None,
    color_name: Optional[str] = None,
    storage_location: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session)
) -> List[Spool]:
    """List spools with optional filtering by status, product metadata, and storage location."""
    query = select(Spool)

    # Join with product table when product filters are used
    if any([brand, material, color_name]):
        query = query.join(Product)

    if status:
        query = query.where(Spool.status == status)
    if brand:
        query = query.where(Product.brand.ilike(f"%{brand}%"))
    if material:
        query = query.where(Product.material.ilike(f"%{material}%"))
    if color_name:
        query = query.where(Product.color_name.ilike(f"%{color_name}%"))
    if storage_location:
        query = query.where(Spool.storage_location.ilike(f"%{storage_location}%"))

    spools = session.exec(query).all()
    return spools


@app.get("/api/v1/spools/with-products", tags=["spools"])
def list_spools_with_products(
    status: Optional[str] = None,
    session: Session = Depends(get_session)
) -> List[Dict]:
    """List spools with product information included (for Google Sheets export)."""
    query = select(Spool)
    
    if status:
        query = query.where(Spool.status == status)
    
    spools = session.exec(query).all()
    
    # Get all product IDs
    product_ids = {spool.product_id for spool in spools}
    
    # Fetch products
    products = {}
    if product_ids:
        product_query = select(Product).where(Product.id.in_(product_ids))
        product_list = session.exec(product_query).all()
        products = {p.id: p for p in product_list}
    
    # Combine spool and product data
    result = []
    for spool in spools:
        product = products.get(spool.product_id)
        spool_dict = {
            "id": spool.id,
            "product_id": spool.product_id,
            "purchase_date": spool.purchase_date.isoformat() if spool.purchase_date else None,
            "vendor": spool.vendor,
            "price": spool.price,
            "storage_location": spool.storage_location,
            "status": spool.status.value,
            "created_at": spool.created_at.isoformat() if spool.created_at else None,
            "updated_at": spool.updated_at.isoformat() if spool.updated_at else None,
        }
        result.append(spool_dict)
    
    return result


def _build_spool_detail(spool: Spool, session: Session) -> SpoolDetail:
    change_logs = session.exec(
        select(SpoolChangeLog)
        .where(SpoolChangeLog.spool_id == spool.id)
        .order_by(SpoolChangeLog.created_at.desc())
    ).all()

    spool_data = spool.model_dump()
    return SpoolDetail.model_validate({**spool_data, "change_logs": change_logs})


@app.get("/api/v1/spools/{spool_id}", response_model=SpoolDetail, tags=["spools"])
def get_spool_with_history(spool_id: int, session: Session = Depends(get_session)) -> SpoolDetail:
    spool = session.get(Spool, spool_id)
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    return _build_spool_detail(spool, session)


@app.put("/api/v1/spools/{spool_id}", response_model=SpoolDetail, tags=["spools"])
def update_spool(
    spool_id: int, spool_in: SpoolUpdate, session: Session = Depends(get_session)
) -> SpoolDetail:
    spool = session.get(Spool, spool_id)
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")

    previous_status = spool.status
    previous_location = spool.storage_location

    update_data = spool_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(spool, key, value)
    spool.updated_at = datetime.now(timezone.utc)

    session.add(spool)
    session.commit()
    session.refresh(spool)

    status_changed = "status" in update_data and previous_status != spool.status
    location_changed = "storage_location" in update_data and previous_location != spool.storage_location

    if status_changed or location_changed:
        change_log = SpoolChangeLog(
            spool_id=spool.id,
            from_status=previous_status if status_changed else None,
            to_status=spool.status if status_changed else None,
            from_location=previous_location if location_changed else None,
            to_location=spool.storage_location if location_changed else None,
        )
        session.add(change_log)
        session.commit()

    return _build_spool_detail(spool, session)


@app.delete("/api/v1/spools/{spool_id}", status_code=204, tags=["spools"])
def delete_spool(spool_id: int, session: Session = Depends(get_session)) -> None:
    spool = session.get(Spool, spool_id)
    if not spool:
        raise HTTPException(status_code=404, detail="Spool not found")
    session.delete(spool)
    session.commit()


# OCR Endpoint
@app.post("/api/v1/ocr/parse-label", tags=["ocr"])
async def parse_label(file: UploadFile = File(...)):
    """
    Upload a filament box label image and extract structured data.

    Returns parsed fields: brand, material, color_name, diameter_mm, barcode, raw_text, ocr_confidence, strategy_used

    The raw_text field shows exactly what Tesseract OCR extracted from the image.
    This is useful for debugging when fields are not detected correctly.
    
    The ocr_confidence field indicates OCR quality (0-100).
    The strategy_used field shows which preprocessing strategy worked best.
    
    Supported formats: JPEG, PNG, WebP
    Maximum file size: 10 MB
    """
    from backend.validation import validate_image_file, ValidationError
    
    try:
        # Read image bytes
        image_bytes = await file.read()
        
        # Validate image file (size, format, dimensions)
        try:
            img, metadata = validate_image_file(
                image_bytes,
                filename=file.filename,
                content_type=file.content_type
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Image validation failed",
                    "message": str(e),
                    "suggestion": "Please ensure the image is a valid JPEG, PNG, or WebP file under 10 MB"
                }
            )
        
        # Parse label using OCR
        from backend.ocr_service import OCRError
        try:
            result = LabelParser.parse_label(image_bytes)
            # Add validation metadata to response
            result["validation"] = {
                "file_size_mb": round(metadata["file_size_bytes"] / (1024 * 1024), 2),
                "image_dimensions": f"{metadata['size'][0]}x{metadata['size'][1]}",
                "image_format": metadata["format"]
            }
            return result
        except OCRError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "OCR processing failed",
                    "message": str(e),
                    "suggestion": "Please ensure the image is clear, well-lit, and contains readable text. Try retaking the photo with better lighting."
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Unexpected error in OCR endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while processing the image",
                "suggestion": "Please try again. If the problem persists, check the image format and try a different image."
            }
        )


# Invoice Parsing Endpoint
@app.post("/api/v1/invoice/parse", tags=["invoice"])
async def parse_invoice(file: UploadFile = File(...)):
    """
    Upload a PDF invoice and extract order information with all filament products.

    Returns:
    - order_number: Order ID from invoice
    - order_date: Purchase date
    - vendor: Vendor name (e.g., "Bambu Lab", "Amazon")
    - items: List of products with brand, material, color_name, diameter_mm, quantity, price
    
    Supported formats: PDF only
    Maximum file size: 20 MB
    Maximum pages: 50
    """
    from backend.validation import validate_pdf_file, ValidationError
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Validate PDF file (size, format, pages)
        try:
            metadata = validate_pdf_file(
                pdf_bytes,
                filename=file.filename,
                content_type=file.content_type
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PDF validation failed",
                    "message": str(e),
                    "suggestion": "Please ensure the file is a valid PDF under 20 MB with 50 pages or less"
                }
            )
        
        # Parse invoice
        try:
            result = InvoiceParser.parse_invoice(pdf_bytes)
            # Add validation metadata to response
            result["validation"] = {
                "file_size_mb": round(metadata["file_size_bytes"] / (1024 * 1024), 2),
                "page_count": metadata["page_count"],
                "has_extractable_text": metadata.get("has_text", False)
            }
            return result
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invoice parsing failed",
                    "message": str(e),
                    "suggestion": "This invoice format may not be supported. Currently supported: Bambu Lab invoices. Please check the invoice format."
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Unexpected error in invoice parsing: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while parsing the invoice",
                "suggestion": "Please try again. If the problem persists, ensure the PDF is not corrupted or password-protected."
            }
        )


# Bulk Import from Invoice
@app.post("/api/v1/invoice/import", tags=["invoice"])
async def import_from_invoice(
    file: UploadFile = File(...),
    session: Session = Depends(get_session)
):
    """
    Upload a PDF invoice and automatically create Products and Spools for all items.

    This endpoint:
    1. Parses the invoice to extract all filament products
    2. Creates or finds matching Product records
    3. Creates Spool records for each quantity with purchase details
    4. Returns summary of created records

    Returns:
    - products_created: Number of new products
    - spools_created: Number of new spools
    - order_number: Order ID from invoice
    - items: List of created products and spools
    
    Supported formats: PDF only
    Maximum file size: 20 MB
    """
    from backend.validation import validate_pdf_file, ValidationError
    
    try:
        # Read PDF bytes
        pdf_bytes = await file.read()
        
        # Validate PDF file
        try:
            metadata = validate_pdf_file(
                pdf_bytes,
                filename=file.filename,
                content_type=file.content_type
            )
        except ValidationError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "PDF validation failed",
                    "message": str(e),
                    "suggestion": "Please ensure the file is a valid PDF under 20 MB"
                }
            )

        try:
            # Parse invoice
            invoice_data = InvoiceParser.parse_invoice(pdf_bytes)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invoice parsing failed",
                    "message": str(e),
                    "suggestion": "This invoice format may not be supported. Currently supported: Bambu Lab invoices."
                }
            )

        products_created = 0
        spools_created = 0
        imported_items = []

        for item in invoice_data["items"]:
            # Check if product exists
            query = select(Product).where(
                Product.brand == item["brand"],
                Product.material == item["material"],
                Product.color_name == item["color_name"],
                Product.diameter_mm == item["diameter_mm"]
            )
            existing_product = session.exec(query).first()

            if existing_product:
                product = existing_product
            else:
                # Create new product
                product = Product(
                    brand=item["brand"],
                    material=item["material"],
                    color_name=item["color_name"],
                    diameter_mm=item["diameter_mm"],
                    line=item.get("product_line"),
                    sku=item.get("sku")
                )
                session.add(product)
                session.flush()  # Get product ID
                products_created += 1

            # Create spools for each quantity
            for _ in range(item["quantity"]):
                spool = Spool(
                    product_id=product.id,
                    purchase_date=invoice_data["order_date"],
                    vendor=invoice_data["vendor"],
                    price=item.get("price"),
                    status="in_stock"
                )
                session.add(spool)
                spools_created += 1

            imported_items.append({
                "product_id": product.id,
                "brand": product.brand,
                "material": product.material,
                "color_name": product.color_name,
                "quantity": item["quantity"],
                "price": item.get("price")
            })

        session.commit()

        return {
            "success": True,
            "products_created": products_created,
            "spools_created": spools_created,
            "order_number": invoice_data["order_number"],
            "order_date": invoice_data["order_date"],
            "vendor": invoice_data["vendor"],
            "items": imported_items
        }
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"Unexpected error in invoice import: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred while importing the invoice",
                "suggestion": "Please try again. If the problem persists, check the invoice format and ensure all required fields are present."
            }
        )


# Google Sheets Export Endpoint
class GoogleSheetsExportRequest(SQLModel):
    spreadsheet_id: str
    sheet_name: Optional[str] = None
    include_products: bool = True
    include_spools: bool = True
    spool_status: Optional[str] = None


@app.post("/api/v1/export/google-sheets", tags=["export"])
async def export_to_google_sheets(
    request: GoogleSheetsExportRequest,
    session: Session = Depends(get_session)
):
    """
    Export inventory data to Google Sheets.
    
    Args:
        spreadsheet_id: Google Sheets spreadsheet ID (from URL: docs.google.com/spreadsheets/d/{ID}/edit)
        sheet_name: Name of sheet to create/update (default: "Inventory")
        include_products: Whether to include products
        include_spools: Whether to include spools
        spool_status: Filter spools by status (optional)
    
    Returns:
        Success status and sheet URL
    
    Environment Variables Required:
        GOOGLE_SHEETS_CREDENTIALS_PATH: Path to Google Service Account JSON file
    """
    from backend.google_sheets import GoogleSheetsExporter, GoogleSheetsError
    
    if not request.include_products and not request.include_spools:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid request",
                "message": "At least one of include_products or include_spools must be true"
            }
        )
    
    try:
        products_data = None
        spools_data = None
        
        # Fetch products if needed
        if request.include_products:
            products = session.exec(select(Product)).all()
            products_data = [
                {
                    "id": p.id,
                    "brand": p.brand,
                    "line": p.line,
                    "material": p.material,
                    "color_name": p.color_name,
                    "diameter_mm": p.diameter_mm,
                    "barcode": p.barcode,
                    "sku": p.sku,
                    "notes": p.notes,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None,
                }
                for p in products
            ]
        
        # Fetch spools if needed
        if request.include_spools:
            query = select(Spool)
            if request.spool_status:
                query = query.where(Spool.status == request.spool_status)
            spools = session.exec(query).all()
            
            # Get products for spools
            product_ids = {s.product_id for s in spools}
            products_lookup = {}
            if product_ids:
                product_query = select(Product).where(Product.id.in_(product_ids))
                product_list = session.exec(product_query).all()
                products_lookup = {p.id: p for p in product_list}
            
            spools_data = [
                {
                    "id": s.id,
                    "product_id": s.product_id,
                    "purchase_date": s.purchase_date.isoformat() if s.purchase_date else None,
                    "vendor": s.vendor,
                    "price": s.price,
                    "storage_location": s.storage_location,
                    "status": s.status.value,
                    "created_at": s.created_at.isoformat() if s.created_at else None,
                    "updated_at": s.updated_at.isoformat() if s.updated_at else None,
                    "order_id": s.order_id
                }
                for s in spools
            ]
            
            # Convert to format expected by exporter (with product info)
            products_for_export = [
                {
                    "id": p.id,
                    "brand": p.brand,
                    "line": p.line,
                    "material": p.material,
                    "color_name": p.color_name,
                    "diameter_mm": p.diameter_mm,
                }
                for p in products_lookup.values()
            ] if products_lookup else None
        
        # Export to Google Sheets
        result = GoogleSheetsExporter.export_to_sheet(
            spreadsheet_id=request.spreadsheet_id,
            products=products_data,
            spools=spools_data,
            sheet_name=request.sheet_name
        )
        
        return result
        
    except GoogleSheetsError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Google Sheets export failed",
                "message": str(e),
                "suggestion": "Please check that GOOGLE_SHEETS_CREDENTIALS_PATH is set and points to a valid service account JSON file."
            }
        )
    except Exception as e:
        import logging
        logging.error(f"Unexpected error in Google Sheets export: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": f"Failed to export to Google Sheets: {str(e)}"
            }
        )


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
