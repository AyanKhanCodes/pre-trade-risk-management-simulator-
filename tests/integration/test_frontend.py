"""
Integration tests for frontend static file serving.

Verifies that FastAPI serves the built React SPA, static assets, and
handles SPA client-side routing.
"""

import pytest

pytestmark = pytest.mark.asyncio


class TestFrontendServing:
    """Tests for React frontend serving and routing."""

    async def test_root_returns_html(self, async_client):
        """Root GET / should return index.html with 200 OK."""
        response = await async_client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
        assert "Pre-Trade Risk Management System" in response.text
        assert '<div id="root">' in response.text

    async def test_spa_client_routes_return_html(self, async_client):
        """Client-side routes like /orders, /rules, /analytics should serve index.html."""
        for path in ["/orders", "/rules", "/analytics"]:
            response = await async_client.get(path)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")
            assert '<div id="root">' in response.text

    async def test_api_routes_not_shadowed(self, async_client):
        """API endpoints under /api should return JSON, not HTML."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

        response = await async_client.get("/api/risk-config")
        assert response.status_code == 200
        assert "max_order_value" in response.json()
