"""Tests unitarios del módulo de Excel/CSV (sin BD)."""
import io

import pytest

from app.utils.excel_handler import (
    COLUMNS,
    contacts_to_csv,
    contacts_to_excel,
    generate_template,
    parse_csv,
    parse_excel,
)


# ---------------------------------------------------------------------------
# generate_template
# ---------------------------------------------------------------------------

def test_generate_template_returns_bytes():
    content = generate_template(society_names=["ACME", "TEST"])
    assert isinstance(content, bytes)
    assert len(content) > 1000  # Un .xlsx siempre tiene tamaño considerable


def test_generate_template_without_societies():
    content = generate_template()
    assert isinstance(content, bytes)


# ---------------------------------------------------------------------------
# parse_csv
# ---------------------------------------------------------------------------

def test_parse_csv_basic():
    csv_content = b"Nombre,Apellido,Email,Empresa\nJuan,Perez,juan@test.com,ACME\n"
    rows = parse_csv(csv_content)
    assert len(rows) == 1
    assert rows[0]["nombre"] == "Juan"
    assert rows[0]["apellido"] == "Perez"
    assert rows[0]["email"] == "juan@test.com"


def test_parse_csv_skips_empty_rows():
    csv_content = b"Nombre,Apellido\nJuan,Perez\n\n\n"
    rows = parse_csv(csv_content)
    assert len(rows) == 1


def test_parse_csv_handles_utf8_bom():
    csv_content = "﻿Nombre,Apellido\nMaría,García\n".encode("utf-8-sig")
    rows = parse_csv(csv_content)
    assert rows[0]["nombre"] == "María"


def test_parse_csv_with_template_headers():
    """Acepta los mismos encabezados que genera generate_template."""
    labels = ",".join(label for _, label, _ in COLUMNS)
    csv_content = (labels + "\nJuan,Perez,EmpresaX,,,,,,juan@test.com,,,,, EGE HAINA\n").encode("utf-8")
    rows = parse_csv(csv_content)
    assert len(rows) == 1
    assert rows[0]["nombre"] == "Juan"


def test_parse_csv_multiple_rows():
    csv_content = b"Nombre,Apellido\nA,B\nC,D\nE,F\n"
    rows = parse_csv(csv_content)
    assert len(rows) == 3


# ---------------------------------------------------------------------------
# parse_excel
# ---------------------------------------------------------------------------

def test_parse_excel_round_trip():
    """Genera Excel y lo parsea de vuelta."""
    contacts = [
        {"nombre": "Ana", "apellido": "Lopez", "empresa": "TechCorp",
         "cargo": "", "puesto": "", "direccion": "", "telefono": "",
         "celular": "", "email": "ana@tech.com", "nombre_contacto_interno": "",
         "email_contacto_interno": "", "telefono_contacto_interno": "",
         "nota": "", "sociedad": "SIBA"},
    ]
    xlsx_bytes = contacts_to_excel(contacts)
    rows = parse_excel(xlsx_bytes)

    assert len(rows) == 1
    assert rows[0]["nombre"] == "Ana"
    assert rows[0]["apellido"] == "Lopez"
    assert rows[0]["email"] == "ana@tech.com"


def test_parse_excel_empty_file():
    from openpyxl import Workbook
    wb = Workbook()
    ws = wb.active
    buf = io.BytesIO()
    wb.save(buf)
    rows = parse_excel(buf.getvalue())
    assert rows == []


# ---------------------------------------------------------------------------
# contacts_to_csv / contacts_to_excel
# ---------------------------------------------------------------------------

def test_contacts_to_csv_returns_bytes():
    data = [{"nombre": "Carlos", "apellido": "Ruiz", "empresa": "Empresa", "email": "c@r.com",
              "cargo": "", "puesto": "", "direccion": "", "telefono": "", "celular": "",
              "nombre_contacto_interno": "", "email_contacto_interno": "",
              "telefono_contacto_interno": "", "nota": "", "sociedad": ""}]
    result = contacts_to_csv(data)
    assert isinstance(result, bytes)
    assert b"Carlos" in result


def test_contacts_to_excel_returns_bytes():
    data = [{"nombre": "Carlos", "apellido": "Ruiz", "empresa": "Empresa", "email": "c@r.com",
              "cargo": "", "puesto": "", "direccion": "", "telefono": "", "celular": "",
              "nombre_contacto_interno": "", "email_contacto_interno": "",
              "telefono_contacto_interno": "", "nota": "", "sociedad": ""}]
    result = contacts_to_excel(data)
    assert isinstance(result, bytes)
    assert len(result) > 1000


def test_contacts_to_csv_empty():
    result = contacts_to_csv([])
    assert isinstance(result, bytes)
    # Solo encabezados
    lines = result.decode("utf-8-sig").strip().splitlines()
    assert len(lines) == 1
