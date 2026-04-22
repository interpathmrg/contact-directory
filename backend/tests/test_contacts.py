"""
Tests de los endpoints de contactos.
- Sin auth → 403
- VIEWER → puede listar, no puede crear/editar/eliminar
- ADMIN → acceso completo
La BD se mockea con AsyncMock y se parchea ContactService en cada test.
"""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.contact_service import ContactService, PaginatedResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fake_contact():
    return {
        "id": str(uuid.uuid4()),
        "nombre": "Juan",
        "apellido": "Pérez",
        "empresa": "ACME",
        "cargo": None,
        "puesto": None,
        "direccion": None,
        "telefono": None,
        "celular": None,
        "email": "juan@acme.com",
        "nombre_contacto_interno": None,
        "email_contacto_interno": None,
        "telefono_contacto_interno": None,
        "nota": None,
        "sociedad_id": None,
        "society": None,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-01T00:00:00Z",
        "updated_by": None,
        "is_active": True,
    }


# ---------------------------------------------------------------------------
# Sin autenticación
# ---------------------------------------------------------------------------

async def test_list_contacts_without_token_returns_403():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/contacts")
    assert response.status_code == 403


async def test_create_contact_without_token_returns_403():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/contacts", json={})
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# VIEWER — solo lectura
# ---------------------------------------------------------------------------

async def test_viewer_can_list_contacts(override_viewer):
    with patch.object(ContactService, "list_contacts", new_callable=AsyncMock) as mock_list, \
         patch.object(ContactService, "list_societies", new_callable=AsyncMock) as mock_soc:
        mock_list.return_value = PaginatedResult(items=[], total=0)
        mock_soc.return_value = []

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/contacts")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] == 0
    assert data["page"] == 1


async def test_viewer_cannot_create_contact_returns_403(override_viewer):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/contacts", json={
            "nombre": "Test", "apellido": "User"
        })
    assert response.status_code == 403


async def test_viewer_cannot_delete_contact_returns_403(override_viewer):
    contact_id = str(uuid.uuid4())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(f"/api/contacts/{contact_id}")
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# ADMIN — acceso completo
# ---------------------------------------------------------------------------

async def test_admin_can_list_contacts(override_admin):
    with patch.object(ContactService, "list_contacts", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = PaginatedResult(items=[], total=0)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/contacts")

    assert response.status_code == 200


async def test_admin_create_contact_validates_schema(override_admin):
    """Sin nombre → 422 por validación Pydantic, no llega al servicio."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/contacts", json={"apellido": "Solo"})
    assert response.status_code == 422


async def test_admin_create_contact_calls_service(override_admin, fake_contact):
    from app.models.contact import Contact

    mock_contact = AsyncMock(spec=Contact)
    for k, v in fake_contact.items():
        setattr(mock_contact, k, v)
    mock_contact.society = None

    with patch.object(ContactService, "create", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = mock_contact

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/contacts", json={
                "nombre": "Juan",
                "apellido": "Pérez",
                "email": "juan@acme.com",
            })

    mock_create.assert_called_once()
    assert response.status_code == 201


async def test_admin_delete_contact_calls_service(override_admin):
    contact_id = str(uuid.uuid4())

    with patch.object(ContactService, "soft_delete", new_callable=AsyncMock) as mock_delete:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/contacts/{contact_id}")

    mock_delete.assert_called_once()
    assert response.status_code == 204


# ---------------------------------------------------------------------------
# Parámetros de paginación
# ---------------------------------------------------------------------------

async def test_pagination_params_passed_to_service(override_admin):
    with patch.object(ContactService, "list_contacts", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = PaginatedResult(items=[], total=0)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            await client.get("/api/contacts?page=3&page_size=50&order_by=empresa&order_dir=desc")

    call_kwargs = mock_list.call_args.kwargs
    assert call_kwargs["page"] == 3
    assert call_kwargs["page_size"] == 50
    assert call_kwargs["order_by"] == "empresa"
    assert call_kwargs["order_dir"] == "desc"
