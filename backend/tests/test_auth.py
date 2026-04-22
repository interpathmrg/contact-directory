"""Tests unitarios de creación y decodificación de JWT (sin BD, sin Azure)."""
import time

import pytest
from fastapi import HTTPException

from app.auth.dependencies import (
    CurrentUser,
    create_access_token,
    create_refresh_token,
    decode_token,
)


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

def test_create_access_token_returns_string():
    token = create_access_token(
        email="user@test.com", name="Test", role="VIEWER", permissions={}
    )
    assert isinstance(token, str)
    assert len(token) > 0


def test_access_token_has_three_parts():
    token = create_access_token(
        email="user@test.com", name="Test", role="ADMIN", permissions={}
    )
    parts = token.split(".")
    assert len(parts) == 3  # header.payload.signature


# ---------------------------------------------------------------------------
# decode_token — token válido
# ---------------------------------------------------------------------------

def test_decode_access_token_extracts_email():
    token = create_access_token(
        email="admin@example.com", name="Admin", role="ADMIN", permissions={"admin": True}
    )
    payload = decode_token(token, expected_type="access")

    assert payload["sub"] == "admin@example.com"
    assert payload["role"] == "ADMIN"
    assert payload["type"] == "access"
    assert payload["permissions"]["admin"] is True


def test_decode_refresh_token():
    token = create_refresh_token(email="user@test.com")
    payload = decode_token(token, expected_type="refresh")

    assert payload["sub"] == "user@test.com"
    assert payload["type"] == "refresh"


# ---------------------------------------------------------------------------
# decode_token — casos de error
# ---------------------------------------------------------------------------

def test_decode_wrong_type_raises():
    access_token = create_access_token(
        email="user@test.com", name="U", role="VIEWER", permissions={}
    )
    with pytest.raises(HTTPException) as exc_info:
        decode_token(access_token, expected_type="refresh")  # tipo incorrecto
    assert exc_info.value.status_code == 401


def test_decode_invalid_token_raises():
    with pytest.raises(HTTPException) as exc_info:
        decode_token("this.is.not.a.valid.token")
    assert exc_info.value.status_code == 401


def test_decode_empty_token_raises():
    with pytest.raises(HTTPException):
        decode_token("")


# ---------------------------------------------------------------------------
# CurrentUser helper
# ---------------------------------------------------------------------------

def test_current_user_is_admin():
    user = CurrentUser(email="a@b.com", name="A", role="ADMIN", permissions={})
    assert user.is_admin is True
    assert user.is_viewer is True


def test_current_user_viewer_is_not_admin():
    user = CurrentUser(email="a@b.com", name="A", role="VIEWER", permissions={})
    assert user.is_admin is False
    assert user.is_viewer is True


def test_current_user_no_role():
    user = CurrentUser(email="a@b.com", name="A", role=None, permissions={})
    assert user.is_admin is False
    assert user.is_viewer is False
