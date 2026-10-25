"""
Shared test fixtures for the Pre-Trade Risk Management Simulator.

Provides:
- In-memory SQLite test database
- FastAPI test client using httpx
- Risk configuration overrides
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.config import RiskConfig, get_inr_default_config, set_risk_config
from app.database import DATABASE_PATH, init_db

# Use a test-specific database file.
TEST_DB_PATH = "test_orders.db"


@pytest.fixture(autouse=True)
def _use_test_db(monkeypatch):
    """Redirect all database operations to a test database.

    The test database is deleted after each test to ensure isolation.
    """
    import app.database as db_module

    monkeypatch.setattr(db_module, "DATABASE_PATH", TEST_DB_PATH)

    yield

    # Cleanup: remove the test database after each test.
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)


@pytest.fixture(autouse=True)
def _reset_risk_config():
    """Reset risk configuration to defaults before each test."""
    set_risk_config(get_inr_default_config())
    yield
    set_risk_config(get_inr_default_config())


@pytest_asyncio.fixture
async def async_client():
    """Create an httpx AsyncClient configured for the FastAPI test app.

    Initializes the test database before yielding the client.
    """
    # Initialize the test database.
    await init_db(TEST_DB_PATH)

    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver"
    ) as client:
        yield client
