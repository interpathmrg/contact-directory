"""
Tests unitarios de ImportService._validate_row.
No requieren BD: se pre-carga el mapa de sociedades en el servicio.
"""
import pytest
from unittest.mock import AsyncMock

from app.schemas.import_export import ImportRowInput
from app.services.import_service import ImportService


@pytest.fixture
def svc() -> ImportService:
    service = ImportService(db=AsyncMock())
    service._society_map = {
        "ege haina": 1,
        "siba": 2,
        "trelia": 3,
    }
    return service


def make_row(**kwargs) -> ImportRowInput:
    defaults = dict(
        nombre="Juan", apellido="Pérez", empresa="ACME",
        cargo="", puesto="", direccion="", telefono="",
        celular="", email="juan@acme.com",
        nombre_contacto_interno="", email_contacto_interno="",
        telefono_contacto_interno="", nota="", sociedad="ege haina",
    )
    defaults.update(kwargs)
    return ImportRowInput(**defaults)


# ---------------------------------------------------------------------------
# Campos obligatorios
# ---------------------------------------------------------------------------

def test_valid_row_has_no_errors(svc: ImportService):
    row = make_row()
    errors = svc._validate_row(row, seen_emails=set())
    assert errors == []


def test_missing_nombre_returns_error(svc: ImportService):
    row = make_row(nombre="")
    errors = svc._validate_row(row, seen_emails=set())
    assert any("Nombre" in e for e in errors)


def test_missing_apellido_returns_error(svc: ImportService):
    row = make_row(apellido="")
    errors = svc._validate_row(row, seen_emails=set())
    assert any("Apellido" in e for e in errors)


def test_missing_both_required_fields_returns_two_errors(svc: ImportService):
    row = make_row(nombre="", apellido="")
    errors = svc._validate_row(row, seen_emails=set())
    assert len(errors) == 2


# ---------------------------------------------------------------------------
# Validación de email
# ---------------------------------------------------------------------------

def test_invalid_email_format(svc: ImportService):
    row = make_row(email="no-es-un-email")
    errors = svc._validate_row(row, seen_emails=set())
    assert any("válido" in e for e in errors)


def test_valid_email_no_error(svc: ImportService):
    row = make_row(email="valid@email.com")
    errors = svc._validate_row(row, seen_emails=set())
    assert errors == []


def test_duplicate_email_in_file(svc: ImportService):
    row = make_row(email="dup@test.com")
    errors = svc._validate_row(row, seen_emails={"dup@test.com"})
    assert any("duplicado" in e for e in errors)


def test_empty_email_is_allowed(svc: ImportService):
    row = make_row(email="")
    errors = svc._validate_row(row, seen_emails=set())
    assert errors == []


def test_invalid_email_contacto_interno(svc: ImportService):
    row = make_row(email_contacto_interno="bad-email")
    errors = svc._validate_row(row, seen_emails=set())
    assert any("contacto interno" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Validación de sociedad
# ---------------------------------------------------------------------------

def test_invalid_society_name(svc: ImportService):
    row = make_row(sociedad="SOCIEDAD_INEXISTENTE")
    errors = svc._validate_row(row, seen_emails=set())
    assert any("Sociedad" in e for e in errors)


def test_valid_society_name_case_insensitive(svc: ImportService):
    row = make_row(sociedad="EGE HAINA")  # case insensitive
    errors = svc._validate_row(row, seen_emails=set())
    assert errors == []


def test_empty_society_is_allowed(svc: ImportService):
    row = make_row(sociedad="")
    errors = svc._validate_row(row, seen_emails=set())
    assert errors == []
