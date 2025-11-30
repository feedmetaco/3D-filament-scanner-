import os
import sys
from pathlib import Path
from typing import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Ensure the app uses an in-memory database for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from backend.database import engine, get_session  # noqa: E402
from backend.main import app  # noqa: E402


def override_get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
def setup_database() -> Iterator[None]:
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


def test_create_and_retrieve_product(client: TestClient) -> None:
    payload = {
        "brand": "Sunlu",
        "line": "PLA+",
        "material": "PLA",
        "color_name": "Yellow",
        "diameter_mm": 1.75,
        "notes": "Test product",
        "barcode": "1234567890",
        "sku": "SUN-PLA-YEL",
    }

    response = client.post("/api/v1/products", json=payload)
    assert response.status_code == 200
    product = response.json()

    fetched = client.get(f"/api/v1/products/{product['id']}")
    assert fetched.status_code == 200
    retrieved = fetched.json()

    assert retrieved["brand"] == payload["brand"]
    assert retrieved["diameter_mm"] == payload["diameter_mm"]


def test_create_and_update_spool(client: TestClient) -> None:
    product_payload = {
        "brand": "Bambu",
        "line": "PLA Basic",
        "material": "PLA",
        "color_name": "White",
        "diameter_mm": 1.75,
    }
    product_resp = client.post("/api/v1/products", json=product_payload)
    assert product_resp.status_code == 200
    product_id = product_resp.json()["id"]

    spool_payload = {
        "product_id": product_id,
        "vendor": "Bambu",
        "price": 25.5,
        "storage_location": "Shelf A2",
        "status": "in_stock",
    }

    spool_resp = client.post("/api/v1/spools", json=spool_payload)
    assert spool_resp.status_code == 200
    spool = spool_resp.json()

    update_payload = {"status": "used_up"}
    update_resp = client.put(
        f"/api/v1/spools/{spool['id']}",
        json=update_payload,
    )
    assert update_resp.status_code == 200

    fetched_resp = client.get(f"/api/v1/spools/{spool['id']}")
    assert fetched_resp.status_code == 200
    assert fetched_resp.json()["status"] == "used_up"
