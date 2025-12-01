# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

3D Filament Scanner is a local-first web application for cataloging and managing 3D printing filament inventory. It allows users to scan box labels to extract filament information (brand, material, color, etc.) and track individual spools with purchase details and storage locations. The app is designed to be self-hosted on a Synology NAS using Docker and SQLite.

**Primary source of truth**: `README.md` - this document defines the complete architecture, data model, deployment process, and implementation roadmap. Always consult it before making structural changes.

## Current Implementation Status

**Completed:**
- ✅ Phase 1: v1 Backend (Products & Spools CRUD API)
- ✅ Automated testing with pytest
- ✅ GitHub Actions CI pipeline
- ✅ Railway deployment configuration
- ✅ PostgreSQL support for production

**Not yet implemented:**
- ⏳ Frontend (React UI)
- ⏳ OCR/label scanning functionality
- ⏳ Order/invoice management (v1.1 feature)

## Technology Stack

**Backend:**
- Python 3.11+
- FastAPI (v0.110.0+) for REST API
- SQLModel for ORM (combines SQLAlchemy + Pydantic)
- PostgreSQL (production on Railway) or SQLite (local dev: `backend/app.db`)
- psycopg2-binary for PostgreSQL support
- Uvicorn ASGI server
- pytest + httpx for testing

**Frontend (Planned):**
- React with mobile-friendly UI
- Not yet implemented

**Deployment:**
- **Production:** Railway (Platform-as-a-Service)
- **Database:** Railway PostgreSQL (free tier available)
- **Auto-deploy:** GitHub integration with automatic deploys on push to `main`
- **Alternative:** Docker + docker-compose for self-hosting (not yet configured)

## Common Commands

### Backend Development

```bash
# First-time setup: create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r backend/requirements.txt

# Run development server (with auto-reload)
python backend/main.py
# OR
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# Navigate to: http://localhost:8000/docs (Swagger UI)
# Navigate to: http://localhost:8000/redoc (ReDoc)
```

### Testing

```bash
# Run all tests from project root
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py

# Run tests with coverage report
pytest --cov=backend --cov-report=term-missing
```

### Database

**Local Development (SQLite - Default):**
The SQLite database is automatically created at `backend/app.db` on first startup. Database initialization happens via `init_db()` called in the FastAPI startup event (backend/main.py:20-22).

**Local Development (PostgreSQL):**
```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb filament_scanner

# Set environment variable
export DATABASE_URL=postgresql://localhost:5432/filament_scanner

# Run server
python backend/main.py
```

**Production (Railway PostgreSQL):**
- Railway automatically provisions PostgreSQL and sets `DATABASE_URL`
- No manual configuration needed
- Database tables are created automatically on first deployment

**Environment variables:**
- `DATABASE_URL` - Database connection string
  - SQLite: `sqlite:///./backend/app.db` (default for local)
  - PostgreSQL: `postgresql://user:pass@host:port/db` (Railway sets this)
- `PORT` - Server port (Railway sets this dynamically)

**Database operations:**
```bash
# Reset SQLite database (local dev)
rm backend/app.db

# View SQLite contents (requires sqlite3 CLI)
sqlite3 backend/app.db "SELECT * FROM product;"
sqlite3 backend/app.db "SELECT * FROM spool;"

# Reset PostgreSQL database (local dev)
dropdb filament_scanner && createdb filament_scanner
```

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

## Railway Deployment

This project is configured for deployment on Railway with automatic GitHub integration.

**Deployment Files:**
- `railway.toml` - Railway build and deployment configuration
- `Procfile` - Process definition for Railway (fallback)
- `.env.example` - Environment variable template

**How Railway Deployment Works:**
1. Push code to GitHub `main` branch
2. Railway automatically detects changes and starts build
3. Railway provisions PostgreSQL database (if not already created)
4. Railway sets `DATABASE_URL` and `PORT` environment variables
5. App starts with `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
6. Database tables are created automatically on first startup

**Railway Setup Steps (First Time):**
1. Log in to Railway dashboard (railway.app)
2. Create new project from GitHub repo
3. Add PostgreSQL database service to project
4. Railway automatically links database and sets `DATABASE_URL`
5. Deploy happens automatically

**Monitoring:**
- View logs in Railway dashboard
- Check database in Railway PostgreSQL service
- Monitor usage: Railway free tier has 500 hours/month, 512 MB RAM

**Important Notes:**
- Railway uses PostgreSQL, not SQLite
- Database configuration in `backend/database.py` automatically handles both
- Connection pooling is configured for PostgreSQL (pool_size=10, max_overflow=20)
- `psycopg2-binary` is required in `requirements.txt` for PostgreSQL support

## Project Coordination

This project follows a structured workflow defined in README.md. Key principles:

1. **README.md is the source of truth** - The README defines all architecture, data model, deployment process, and implementation roadmap. Consult it before making structural changes.

2. **Implementation phases:**
   - Phase 1: Core Backend ✅ (Complete - includes Railway deployment)
   - Phase 2: Frontend (Next - React UI)
   - Phase 3: Label Scanning (OCR with Tesseract)
   - Phase 4: Order Management (Invoice parsing)
   - Phase 5: Advanced Features (PWA, barcode scanning, etc.)

3. **Stay within scope** - Don't add features beyond the current phase unless explicitly requested. Focus on completing Phase 2 (Frontend) next.

4. **Future features** planned but NOT to be implemented yet:
   - React frontend with mobile-responsive UI
   - Tesseract OCR integration with pytesseract
   - Brand-specific label parsers (Sunlu, eSUN, Bambu)
   - Order and OrderItem models for invoice tracking
   - Docker/docker-compose configuration for self-hosting

## Development Notes

**Database configuration:**
- Local development: `./backend/app.db` (SQLite, gitignored, created automatically)
- Production (Railway): PostgreSQL (connection string set via `DATABASE_URL` env var)
- Tests: In-memory SQLite (`:memory:`)
- Database engine configuration in `backend/database.py` automatically detects database type

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

## Common Troubleshooting

**Import errors after fresh clone:**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Verify dependencies installed: `pip install -r backend/requirements.txt`
- Check Python version: `python --version` (requires 3.11+)

**Port 8000 already in use:**
- Find and kill existing process: `lsof -ti:8000 | xargs kill -9`
- Or use a different port: `uvicorn backend.main:app --reload --port 8001`

**Database locked errors:**
- Ensure only one server instance is running
- Check for stale processes: `ps aux | grep uvicorn`
- Reset database if needed: `rm backend/app.db` and restart

**Test failures:**
- Tests use in-memory database via `DATABASE_URL=sqlite:///:memory:`
- Ensure test database isolation by checking `tests/test_api.py:14-15`
- Run tests with `-v` flag for detailed output

**Foreign key constraint failures:**
- When creating a Spool, ensure the `product_id` references an existing Product
- Verify Product exists before Spool creation in tests and API calls

## Key Implementation Details

**Foreign key relationships:**
- Spools MUST reference a valid Product (`product_id` foreign key)
- Deleting a Product will fail if it has associated Spools (database constraint)
- Consider implementing cascade deletion or orphan handling if needed

**Status enum values:**
- Spool status values are lowercase with underscores: `in_stock`, `used_up`, `donated`, `lost`
- Defined in `backend/models.py:8-12` as `SpoolStatus` enum
- API accepts/returns string values matching the enum

**Date handling:**
- `purchase_date` is a `date` type (not `datetime`)
- Pass dates as ISO format strings: `"2025-12-01"`
- Timestamps (`created_at`, `updated_at`) are full `datetime` objects

**Update endpoint pattern:**
- PUT endpoints accept partial updates via `exclude_unset=True` on model dump
- Only provided fields are updated; omitted fields remain unchanged
- `updated_at` is manually set in the endpoint handler (backend/main.py:69, 121)
