# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

3D Filament Scanner is a local-first web application for cataloging and managing 3D printing filament inventory. It allows users to scan box labels to extract filament information (brand, material, color, etc.) and track individual spools with purchase details and storage locations. The app is designed to be self-hosted on a Synology NAS using Docker and SQLite.

**Primary source of truth**: `README.md` (PROJECT_PLAN.md) - this document defines the complete architecture, data model, and implementation phases. Always consult it before making structural changes.

## Current Implementation Status

**Completed:**
- ✅ Phase 1: v1 Backend (Products & Spools CRUD API)
- ✅ Automated testing with pytest
- ✅ GitHub Actions CI pipeline

**Not yet implemented:**
- ⏳ Frontend (React UI)
- ⏳ OCR/label scanning functionality
- ⏳ Docker deployment configuration
- ⏳ Order/invoice management (v1.1 feature)

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (v0.110.0+) for REST API
- SQLModel for ORM (combines SQLAlchemy + Pydantic)
- SQLite for database (file-based: `backend/app.db`)
- Uvicorn ASGI server
- pytest + httpx for testing

**Frontend (Planned):**
- React with mobile-friendly UI
- Not yet implemented

**Deployment (Planned):**
- Docker + docker-compose
- Target: Synology NAS (local network)

## Common Commands

### Backend Development

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run development server (with auto-reload)
python backend/main.py
# OR
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# Navigate to: http://localhost:8000/docs
```

### Testing

```bash
# Run all tests from project root
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py
```

### Database

The SQLite database is automatically created at `backend/app.db` on first startup. Database initialization happens via `init_db()` called in the FastAPI startup event (backend/main.py:20-22).

**Environment variable:**
- `DATABASE_URL` - Override default SQLite path (defaults to `sqlite:///./backend/app.db`)

## Architecture

### Data Model

The application uses a two-entity model representing filament products and individual spools:

**Product** (`backend/models.py:26-37`)
- Represents a unique filament type (e.g., "Sunlu PLA Yellow 1.75mm")
- Core fields: `brand`, `material`, `color_name`, `diameter_mm`
- Optional fields: `line` (product line), `notes`, `barcode`, `sku`
- **Weight is implicitly 1kg per spool, not stored in database**
- One-to-many relationship with Spools

**Spool** (`backend/models.py:65-77`)
- Represents one physical box/spool of a Product
- Links to Product via `product_id` foreign key
- Purchase metadata: `purchase_date`, `vendor`, `price`
- Tracking: `storage_location`, `photo_path`
- Status enum: `in_stock`, `used_up`, `donated`, `lost`
- `order_id` field exists for future v1.1 Order management

### API Structure

All endpoints use `/api/v1/` prefix:

**Health Check:**
- `GET /` - Returns `{"status": "ok"}`

**Products:**
- `POST /api/v1/products` - Create product
- `GET /api/v1/products` - List all products
- `GET /api/v1/products/{product_id}` - Get by ID
- `PUT /api/v1/products/{product_id}` - Update product
- `DELETE /api/v1/products/{product_id}` - Delete product

**Spools:**
- `POST /api/v1/spools` - Create spool
- `GET /api/v1/spools` - List all spools
- `GET /api/v1/spools/{spool_id}` - Get by ID
- `PUT /api/v1/spools/{spool_id}` - Update spool
- `DELETE /api/v1/spools/{spool_id}` - Delete spool

**Planned but not implemented:**
- Query parameter filtering for products/spools (by brand, material, color, status)
- `POST /api/spools/{id}/mark-used` - Quick status update endpoint
- `POST /api/spools/from-photo` - OCR-based spool creation (Phase 3)

### Component Flow

```
Client Request → FastAPI Router (main.py)
                       ↓
                 Dependency: get_session() (database.py)
                       ↓
                 Database Session
                       ↓
                 SQLModel ORM (models.py)
                       ↓
                 SQLite Database
```

**Key architectural patterns:**
- Dependency injection for database sessions (`Depends(get_session)`)
- SQLModel provides both ORM models and Pydantic schemas
- Separate Create/Update schemas for API requests
- Test database uses in-memory SQLite with dependency override

### Testing Architecture

Tests use FastAPI's TestClient with an in-memory SQLite database (`tests/test_api.py`). The test suite:
- Overrides the `get_session` dependency to use test database
- Automatically creates/drops tables between tests
- Tests full request/response cycle (integration tests)
- Validates foreign key relationships and constraints

## Project Coordination

This project follows a unique multi-agent workflow defined in README.md. Key principles:

1. **README.md is the source of truth** - The README serves as PROJECT_PLAN.md and defines all architecture, data model, and implementation phases. Consult it before making structural changes.

2. **Implementation phases** are clearly defined:
   - Phase 0: Repo initialization ✅
   - Phase 1: v1 Backend (Products & Spools) ✅
   - Phase 2: v1 Frontend (React UI) - Not started
   - Phase 3: v1 Label Scanning (OCR) - Not started
   - Phase 4: Deployment to Synology - Not started
   - Phase 5: v1.1 Orders & Pricing - Not started

3. **Stay within scope** - Don't add features beyond the current phase unless explicitly requested. The README contains detailed checklists for each phase.

4. **Future features** planned but NOT to be implemented yet:
   - Tesseract OCR integration with pytesseract
   - Brand-specific label parsers (Sunlu, eSUN, Bambu)
   - Order and OrderItem models for invoice tracking
   - Docker/docker-compose configuration
   - React frontend application

## Development Notes

**Database location:**
- Development: `./backend/app.db` (gitignored, created automatically)
- Tests: In-memory SQLite (`:memory:`)

**API documentation:**
- FastAPI auto-generates Swagger UI at `/docs`
- ReDoc available at `/redoc`

**Code organization:**
- `backend/main.py` - FastAPI app and all route handlers
- `backend/models.py` - SQLModel definitions for Product and Spool
- `backend/database.py` - Database engine, session management, and init
- `backend/requirements.txt` - Python dependencies
- `tests/test_api.py` - API integration tests

**When adding new endpoints:**
1. Define request/response schemas in `models.py` if needed
2. Add route handler in `main.py` with proper dependency injection
3. Add tests in `tests/test_api.py`
4. Run `pytest` to verify
5. Check auto-generated docs at `/docs` to confirm schema

**SQLModel patterns used:**
- Base classes (e.g., `ProductBase`) define shared fields
- Table models (e.g., `Product`) add `id`, timestamps, and relationships
- Create schemas (e.g., `ProductCreate`) inherit from base
- Update schemas (e.g., `ProductUpdate`) make all fields Optional

**Timestamp handling:**
- All models have `created_at` and `updated_at` fields
- `created_at` auto-set on creation via `default_factory=datetime.utcnow`
- `updated_at` manually updated in PUT endpoints via `datetime.utcnow()`
