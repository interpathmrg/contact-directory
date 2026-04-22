"""Tests de los endpoints de health y ready (no requieren auth ni BD)."""
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_returns_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_returns_ready_when_db_ok():
    with patch("app.main.engine") as mock_engine:
        mock_conn = AsyncMock()
        mock_conn.execute = AsyncMock()
        mock_engine.connect.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_engine.connect.return_value.__aexit__ = AsyncMock(return_value=False)

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"


async def test_ready_returns_503_when_db_fails():
    with patch("app.main.engine") as mock_engine:
        mock_engine.connect.return_value.__aenter__ = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ready")

    assert response.status_code == 503
