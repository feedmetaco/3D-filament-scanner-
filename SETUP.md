# 3D Filament Scanner - Development Setup

## ✅ Setup Complete!

Your development environment is ready to go. Here's what's been set up:

### What's Installed

- ✅ Python 3.13.5 virtual environment (`venv/`)
- ✅ All backend dependencies (FastAPI, SQLModel, Uvicorn, pytest, etc.)
- ✅ Project structure cloned from GitHub
- ✅ Tests passing (2/2 tests)

### Project Structure

```
3D Filament Scanner/
├── backend/           # FastAPI backend application
│   ├── main.py       # API routes and FastAPI app
│   ├── models.py     # SQLModel data models (Product, Spool)
│   ├── database.py   # Database engine and session management
│   └── requirements.txt
├── tests/            # Test suite
│   └── test_api.py   # API integration tests
├── README.md         # Project plan and architecture
├── CLAUDE.md         # Development notes for Claude
└── venv/             # Python virtual environment (gitignored)
```

## Quick Start

### 1. Activate Virtual Environment

```bash
cd "/Users/samis/Documents/3D Filament Scanner"
source venv/bin/activate
```

### 2. Run Backend Server

```bash
# Option 1: Using Python directly
python backend/main.py

# Option 2: Using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start on `http://localhost:8000`

### 3. Access API Documentation

Once the server is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_api.py
```

## Current Status

### ✅ Completed (Phase 1)
- Backend API with Product and Spool CRUD endpoints
- SQLite database with SQLModel ORM
- Automated testing with pytest
- GitHub Actions CI (if configured)

### ⏳ Next Steps (From README.md)
- **Phase 2**: Frontend (React UI) - Not started
- **Phase 3**: Label Scanning (OCR) - Not started
- **Phase 4**: Docker deployment - Not started
- **Phase 5**: Orders & Pricing (v1.1) - Not started

## API Endpoints

### Products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products` - List all products
- `GET /api/v1/products/{id}` - Get product by ID
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product

### Spools
- `POST /api/v1/spools` - Create spool
- `GET /api/v1/spools` - List all spools
- `GET /api/v1/spools/{id}` - Get spool by ID
- `PUT /api/v1/spools/{id}` - Update spool
- `DELETE /api/v1/spools/{id}` - Delete spool

## Database

The SQLite database is automatically created at `backend/app.db` on first startup.

To reset the database:
```bash
rm backend/app.db
# Then restart the server - it will recreate the database
```

## Development Notes

- **Source of Truth**: `README.md` contains the complete project plan
- **Code Style**: Follow existing patterns in `backend/main.py` and `backend/models.py`
- **Testing**: All new endpoints should have corresponding tests in `tests/test_api.py`

## Troubleshooting

### Virtual Environment Issues
If you get import errors, make sure the virtual environment is activated:
```bash
source venv/bin/activate
```

### Port Already in Use
If port 8000 is busy, change it:
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8001
```

### Database Locked
If you see database lock errors, make sure only one instance of the server is running.

## Next Development Session

1. Activate virtual environment: `source venv/bin/activate`
2. Start backend: `python backend/main.py`
3. Open API docs: http://localhost:8000/docs
4. Start coding! 🚀

