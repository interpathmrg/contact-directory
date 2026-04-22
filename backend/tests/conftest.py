"""
Fixtures compartidos para todos los tests.
Los tests usan mocks en lugar de una BD real para aislamiento y velocidad.
"""
import pytest
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.auth.dependencies import CurrentUser, get_current_user
from app.database import get_db
from app.main import app


# ---------------------------------------------------------------------------
# Usuarios mock
# ---------------------------------------------------------------------------

@pytest.fixture
def admin_user() -> CurrentUser:
    return CurrentUser(
        email="admin@test.com",
        name="Test Admin",
        role="ADMIN",
        permissions={"contacts": ["read", "write", "delete"], "admin": True},
    )


@pytest.fixture
def viewer_user() -> CurrentUser:
    return CurrentUser(
        email="viewer@test.com",
        name="Test Viewer",
        role="VIEWER",
        permissions={"contacts": ["read"], "admin": False},
    )


# ---------------------------------------------------------------------------
# Base de datos mock
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db() -> AsyncMock:
    """Sesión de BD simulada con AsyncMock."""
    return AsyncMock()


# ---------------------------------------------------------------------------
# Overrides de dependencias FastAPI
# ---------------------------------------------------------------------------

@pytest.fixture
def override_admin(admin_user: CurrentUser, mock_db: AsyncMock):
    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: admin_user
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_viewer(viewer_user: CurrentUser, mock_db: AsyncMock):
    async def _get_db():
        yield mock_db

    app.dependency_overrides[get_current_user] = lambda: viewer_user
    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Cliente HTTP de test
# ---------------------------------------------------------------------------

@pytest.fixture
async def client() -> AsyncClient:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
