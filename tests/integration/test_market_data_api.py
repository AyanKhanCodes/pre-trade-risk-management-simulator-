"""
Integration tests for the Market Data Workstation REST & WebSocket APIs,
Stock Screener, and Portfolio Accounting (Phases 1-6).
"""

from decimal import Decimal
import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.asyncio


class TestMarketDataEndpoints:
    """Tests for /api/market/* endpoints."""

    async def test_get_market_status(self, async_client):
        resp = await async_client.get("/api/market/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "provider" in data
        assert data["subscribed_symbols_count"] == 20

    async def test_get_market_instruments(self, async_client):
        resp = await async_client.get("/api/market/instruments")
        assert resp.status_code == 200
        instruments = resp.json()
        assert len(instruments) == 20
        symbols = [i["trading_symbol"] for i in instruments]
        assert "RELIANCE" in symbols
        assert "M&M" in symbols

    async def test_get_market_quotes(self, async_client):
        resp = await async_client.get("/api/market/quotes")
        assert resp.status_code == 200
        quotes = resp.json()
        assert len(quotes) == 20
        for q in quotes:
            assert Decimal(q["ltp"]) > 0

    async def test_get_single_quote(self, async_client):
        resp = await async_client.get("/api/market/quotes/INFY")
        assert resp.status_code == 200
        quote = resp.json()
        assert quote["symbol"] == "INFY"
        assert Decimal(quote["ltp"]) > Decimal("1000.00")

    async def test_get_quote_nonexistent_returns_404(self, async_client):
        resp = await async_client.get("/api/market/quotes/UNKNOWN_STOCK")
        assert resp.status_code == 404

    async def test_get_market_candles(self, async_client):
        resp = await async_client.get("/api/market/candles?symbol=TCS&interval=1m&limit=30")
        assert resp.status_code == 200
        candles = resp.json()
        assert len(candles) == 30
        for c in candles:
            assert Decimal(c["high"]) >= Decimal(c["low"])


class TestStockScreenerEndpoint:
    """Tests for GET /api/screener."""

    async def test_screener_without_filters_returns_all_matches(self, async_client):
        resp = await async_client.get("/api/screener")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_screened"] == 20
        assert data["matches_count"] == 20
        assert len(data["results"]) == 20

    async def test_screener_with_price_filter(self, async_client):
        resp = await async_client.get("/api/screener?min_price=2000.00&max_price=4000.00")
        assert resp.status_code == 200
        data = resp.json()
        for r in data["results"]:
            price = Decimal(r["ltp"])
            assert price >= Decimal("2000.00")
            assert price <= Decimal("4000.00")

    async def test_screener_preliminary_risk_flagging(self, async_client):
        # Update config so RELIANCE is restricted
        await async_client.put(
            "/api/risk-config",
            json={"restricted_symbols": ["RELIANCE"]},
        )
        resp = await async_client.get("/api/screener")
        assert resp.status_code == 200
        data = resp.json()
        reliance_result = next((r for r in data["results"] if r["symbol"] == "RELIANCE"), None)
        assert reliance_result is not None
        assert reliance_result["preliminary_eligible"] is False
        assert any("Restricted symbol" in flag for flag in reliance_result["risk_flags"])


class TestPortfolioAndSettlementEndpoints:
    """Tests for simulated positions and cash ledger (Phase 6)."""

    async def test_initial_portfolio_summary(self, async_client):
        resp = await async_client.get("/api/portfolio/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert Decimal(data["cash_balance"]) == Decimal("1000000.00")
        assert data["currency"] == "INR"
        assert data["open_positions_count"] == 0

    async def test_execution_settles_cash_and_creates_position(self, async_client):
        # Create a BUY order of 10 shares of RELIANCE @ 2900
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "RELIANCE",
                "side": "BUY",
                "quantity": 10,
                "price": "2900.00",
                "currency": "INR",
            },
        )
        assert create_resp.status_code == 201
        order_id = create_resp.json()["order_id"]

        # Execute order
        exec_resp = await async_client.post(f"/api/orders/{order_id}/execute")
        assert exec_resp.status_code == 200

        # Verify cash deducted: 10 * 2900 = 29,000 -> Cash = 10,00,000 - 29,000 = 9,71,000
        summary_resp = await async_client.get("/api/portfolio/summary")
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert Decimal(summary["cash_balance"]) == Decimal("971000.00")
        assert summary["open_positions_count"] == 1

        # Verify position details
        pos_resp = await async_client.get("/api/portfolio/positions")
        assert pos_resp.status_code == 200
        positions = pos_resp.json()
        assert len(positions) == 1
        pos = positions[0]
        assert pos["symbol"] == "RELIANCE"
        assert pos["quantity"] == 10
        assert Decimal(pos["average_entry_price"]) == Decimal("2900.00")
