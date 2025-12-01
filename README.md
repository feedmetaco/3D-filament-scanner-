# 3D Filament Scanner

A production-ready web application for cataloging and managing 3D printing filament inventory. Track filament spools by brand, material, color, and storage location with purchase details and pricing.

**Live Status:** Phase 1 Complete (Backend API) | Deployed on Railway

---

## Quick Links

- **Repository:** `feedmetaco/3D-filament-scanner-`
- **Deployment:** Railway (PostgreSQL + FastAPI)
- **API Documentation:** `/docs` (Swagger UI) and `/redoc` (ReDoc)
- **Tech Stack:** Python 3.11+ | FastAPI | SQLModel | PostgreSQL/SQLite

---

## Features

### ✅ Phase 1: Core Backend (Completed)
- **Product Management:** Track unique filament types (brand, material, color, diameter)
- **Spool Inventory:** Individual spool tracking with purchase info and storage location
- **Status Tracking:** Mark spools as `in_stock`, `used_up`, `donated`, or `lost`
- **REST API:** Full CRUD operations for products and spools
- **Database:** PostgreSQL (production) or SQLite (local dev)
- **Testing:** Automated test suite with pytest
- **CI/CD:** GitHub Actions pipeline

### 🚧 Planned Features
- **Phase 2:** React frontend with mobile-friendly UI
- **Phase 3:** OCR label scanning (Tesseract) for quick spool entry
- **Phase 4:** Invoice parsing and order management
- **Phase 5:** Advanced filtering and search capabilities

---

## Railway Deployment Guide

### Prerequisites
1. **Railway Account:** Free tier available at [railway.app](https://railway.app)
2. **GitHub Repository:** Your fork/clone of this repo connected to Railway
3. **PostgreSQL Database:** Provisioned through Railway (free tier included)

### Step-by-Step Deployment

#### 1. Connect Repository to Railway

1. Log in to Railway dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose `feedmetaco/3D-filament-scanner-`
5. Railway will auto-detect the Python app

#### 2. Add PostgreSQL Database

1. In your Railway project, click "+ New"
2. Select "Database" → "Add PostgreSQL"
3. Railway will automatically provision a Postgres database
4. The `DATABASE_URL` environment variable is set automatically

#### 3. Configure Environment Variables

Railway automatically sets:
- `PORT` - The port your app should listen on
- `DATABASE_URL` - PostgreSQL connection string (format: `postgresql://user:pass@host:port/db`)

**No manual configuration needed!** The app detects these automatically.

#### 4. Deploy

1. Railway will automatically deploy when you push to `main`
2. Initial deployment takes 2-3 minutes
3. Database tables are created automatically on first startup
4. Access your API at the Railway-provided URL

#### 5. Verify Deployment

Once deployed, visit your Railway app URL:
- `https://your-app.railway.app/` - Health check (returns `{"status": "ok"}`)
- `https://your-app.railway.app/docs` - Interactive API documentation
- `https://your-app.railway.app/api/v1/products` - Products endpoint

### Managing Your Deployment

**View Logs:**
```bash
# Railway CLI (optional)
railway logs
```

**Redeploy:**
- Push changes to GitHub `main` branch
- Railway automatically rebuilds and deploys

**Database Access:**
- Use Railway's PostgreSQL dashboard to query/inspect data
- Or connect via `psql` using the `DATABASE_URL` from Railway

**Monitor Usage:**
- Railway free tier: 500 hours/month, 512 MB RAM
- Check usage in Railway dashboard

---

## Local Development

### Initial Setup

```bash
# Clone repository
git clone https://github.com/feedmetaco/3D-filament-scanner-.git
cd "3D Filament Scanner"

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
```

### Running the Server

```bash
# Option 1: Direct Python
python backend/main.py

# Option 2: Uvicorn with auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
# Open: http://localhost:8000/docs
```

### Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=backend --cov-report=term-missing

# Run specific test file
pytest tests/test_api.py
```

### Database

**Local Development (SQLite):**
- Database file: `backend/app.db` (auto-created)
- No setup required, works out of the box

**Local Development (PostgreSQL):**
```bash
# Install PostgreSQL locally (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb filament_scanner

# Set environment variable
export DATABASE_URL=postgresql://localhost:5432/filament_scanner

# Run server (tables created automatically)
python backend/main.py
```

**Reset Database:**
```bash
# SQLite
rm backend/app.db

# PostgreSQL
dropdb filament_scanner && createdb filament_scanner
```

---

## API Reference

### Base URL
- **Production:** `https://your-app.railway.app`
- **Local:** `http://localhost:8000`

### Endpoints

#### Health Check
```http
GET /
```
Returns: `{"status": "ok"}`

#### Products

```http
POST   /api/v1/products         # Create product
GET    /api/v1/products         # List all products
GET    /api/v1/products/{id}    # Get product by ID
PUT    /api/v1/products/{id}    # Update product
DELETE /api/v1/products/{id}    # Delete product
```

**Example Product:**
```json
{
  "brand": "Sunlu",
  "line": "PLA+",
  "material": "PLA",
  "color_name": "Yellow",
  "diameter_mm": 1.75,
  "notes": "High strength filament",
  "barcode": "1234567890",
  "sku": "SUN-PLA-YEL"
}
```

#### Spools

```http
POST   /api/v1/spools          # Create spool
GET    /api/v1/spools          # List all spools
GET    /api/v1/spools/{id}     # Get spool by ID
PUT    /api/v1/spools/{id}     # Update spool
DELETE /api/v1/spools/{id}     # Delete spool
```

**Example Spool:**
```json
{
  "product_id": 1,
  "purchase_date": "2025-12-01",
  "vendor": "Amazon",
  "price": 19.99,
  "storage_location": "Shelf A2",
  "status": "in_stock"
}
```

**Spool Status Values:**
- `in_stock` - Available for use
- `used_up` - Completely consumed
- `donated` - Given away
- `lost` - Cannot locate

---

## Data Model

### Product
Represents a unique filament type (e.g., "Sunlu PLA Yellow 1.75mm")

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | auto | Primary key |
| `brand` | string | ✓ | Manufacturer (Sunlu, eSUN, Bambu Lab) |
| `line` | string | | Product line (PLA+, Pro, etc.) |
| `material` | string | ✓ | Material type (PLA, PETG, TPU, ABS) |
| `color_name` | string | ✓ | Color description |
| `diameter_mm` | float | ✓ | Filament diameter (usually 1.75 or 2.85) |
| `notes` | string | | Additional notes |
| `barcode` | string | | Product barcode from label |
| `sku` | string | | Vendor SKU |
| `created_at` | datetime | auto | Creation timestamp |
| `updated_at` | datetime | auto | Last update timestamp |

**Note:** Weight is implicitly 1kg per spool (not stored in database)

### Spool
Represents one physical spool/box of a Product

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | integer | auto | Primary key |
| `product_id` | integer | ✓ | Foreign key to Product |
| `purchase_date` | date | | When purchased |
| `vendor` | string | | Where purchased (Amazon, Bambu, etc.) |
| `price` | float | | Purchase price per spool |
| `storage_location` | string | | Physical location (Shelf A2, Drybox 1) |
| `photo_path` | string | | Path to label photo |
| `status` | enum | ✓ | in_stock, used_up, donated, lost |
| `order_id` | integer | | (Future) Link to Order |
| `created_at` | datetime | auto | Creation timestamp |
| `updated_at` | datetime | auto | Last update timestamp |

---

## Project Structure

```
3D-filament-scanner-/
├── backend/
│   ├── main.py          # FastAPI app and route handlers
│   ├── models.py        # SQLModel data models
│   ├── database.py      # Database engine and session management
│   └── requirements.txt # Python dependencies
├── tests/
│   └── test_api.py      # API integration tests
├── .github/
│   └── workflows/
│       └── ci.yml       # GitHub Actions CI pipeline
├── railway.toml         # Railway deployment config
├── Procfile             # Process definition for Railway
├── .env.example         # Environment variable template
├── CLAUDE.md            # Development guide for AI assistants
└── README.md            # This file
```

---

## Technology Decisions

### Why FastAPI?
- Modern async Python framework
- Automatic OpenAPI documentation
- Type safety with Pydantic
- High performance (comparable to Node.js/Go)

### Why SQLModel?
- Combines SQLAlchemy (ORM) + Pydantic (validation)
- Single source of truth for data models
- Type hints for IDE support
- Easy migration between SQLite and PostgreSQL

### Why PostgreSQL (Production)?
- Railway provides free PostgreSQL instance
- Production-grade reliability
- Better for multi-user scenarios (vs SQLite)
- Easy to scale when needed

### Why SQLite (Local Dev)?
- Zero configuration required
- Perfect for single-user local development
- Fast iteration and testing
- Same codebase works with both databases

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./backend/app.db` | Database connection string |
| `PORT` | `8000` | Server port (set by Railway in production) |

**Railway automatically sets:**
- `DATABASE_URL` - PostgreSQL connection string
- `PORT` - Dynamic port assignment

---

## Contributing

### Development Workflow

1. **Fork and clone** the repository
2. **Create a branch** for your feature: `git checkout -b feature/my-feature`
3. **Make changes** and add tests
4. **Run tests** locally: `pytest`
5. **Commit changes:** Follow conventional commits format
6. **Push and create PR** to `main` branch

### Code Style
- Follow existing patterns in `backend/main.py` and `backend/models.py`
- Use type hints for all function signatures
- Add docstrings for complex functions
- Ensure tests pass before pushing

### Testing
- All new endpoints must have corresponding tests
- Tests use in-memory SQLite database
- Integration tests cover full request/response cycle

---

## Troubleshooting

### Railway Deployment Issues

**Build Fails:**
- Check Railway logs for specific error
- Verify `requirements.txt` has all dependencies
- Ensure Python version compatibility (3.11+)

**Database Connection Errors:**
- Verify PostgreSQL service is running in Railway
- Check that `DATABASE_URL` is set (automatic in Railway)
- Review connection pooling settings in `backend/database.py`

**App Won't Start:**
- Check that `PORT` environment variable is used
- Verify Railway logs for startup errors
- Test locally first with same configuration

### Local Development Issues

**Import Errors:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r backend/requirements.txt
```

**Port Already in Use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9

# Or use different port
uvicorn backend.main:app --reload --port 8001
```

**Database Locked:**
- Ensure only one server instance is running
- Close any database browser connections
- Delete `backend/app.db` and restart

---

## Roadmap

### Phase 1: Core Backend ✅ (Complete)
- Product and Spool CRUD API
- PostgreSQL support for production
- Railway deployment configuration
- Automated testing and CI/CD

### Phase 2: Frontend (Next)
- React SPA with mobile-responsive UI
- Product and spool management interface
- Filtering and search functionality
- Dashboard with inventory summary

### Phase 3: Label Scanning
- Tesseract OCR integration
- Brand-specific label parsers (Sunlu, eSUN, Bambu)
- Photo upload and automatic product detection
- Mobile camera integration

### Phase 4: Order Management
- Invoice upload and parsing
- Order tracking with line items
- Automatic spool creation from orders
- Price history and analytics

### Phase 5: Advanced Features
- Barcode/QR code scanning
- Progressive Web App (PWA) support
- Inventory alerts and reminders
- Export functionality (CSV, Excel)

---

## License

This project is open source and available under the MIT License.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/feedmetaco/3D-filament-scanner-/issues)
- **Discussions:** [GitHub Discussions](https://github.com/feedmetaco/3D-filament-scanner-/discussions)
- **Documentation:** See `/docs` endpoint when server is running

---

## Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [SQLModel](https://sqlmodel.tiangolo.com/) - SQL database ORM with Python types
- [Railway](https://railway.app/) - Infrastructure platform
- [PostgreSQL](https://www.postgresql.org/) - Production database

---

**Ready to deploy?** Follow the [Railway Deployment Guide](#railway-deployment-guide) above to get started!
