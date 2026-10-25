"""
Integration tests for simulated order execution (/execute) and pre-trade preview (/preview),
plus verification of the Phase 0 audit fixes (CHKL-01 through CHKL-10).
"""

from decimal import Decimal
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


class TestExecuteOrderEndpoint:
    """Tests for POST /api/orders/{order_id}/execute (CHKL-05 & CHKL-06)."""

    async def test_execute_approved_order_succeeds(self, async_client):
        """An approved order should transition cleanly to EXECUTED."""
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
            },
        )
        assert create_resp.status_code == 201
        order_data = create_resp.json()
        assert order_data["status"] == "APPROVED"
        order_id = order_data["order_id"]

        exec_resp = await async_client.post(f"/api/orders/{order_id}/execute")
        assert exec_resp.status_code == 200
        exec_data = exec_resp.json()
        assert exec_data["status"] == "EXECUTED"
        assert exec_data["order_id"] == order_id

        # Verify retrieval reflects EXECUTED
        get_resp = await async_client.get(f"/api/orders/{order_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "EXECUTED"

    async def test_cannot_execute_rejected_order(self, async_client):
        """A rejected order must not be executed (returns 400)."""
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "YESBANK",
                "side": "BUY",
                "quantity": 10,
                "price": "100.00",
            },
        )
        assert create_resp.status_code == 201
        order_data = create_resp.json()
        assert order_data["status"] == "REJECTED"
        order_id = order_data["order_id"]

        exec_resp = await async_client.post(f"/api/orders/{order_id}/execute")
        assert exec_resp.status_code == 400
        assert "Cannot execute a REJECTED order" in exec_resp.json()["detail"]

    async def test_cannot_re_execute_already_executed_order(self, async_client):
        """An order already in EXECUTED state cannot be re-executed (returns 409)."""
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "RELIANCE",
                "side": "BUY",
                "quantity": 5,
                "price": "100.00",
            },
        )
        order_id = create_resp.json()["order_id"]

        first_exec = await async_client.post(f"/api/orders/{order_id}/execute")
        assert first_exec.status_code == 200

        second_exec = await async_client.post(f"/api/orders/{order_id}/execute")
        assert second_exec.status_code == 409
        assert "already EXECUTED" in second_exec.json()["detail"]

    async def test_execute_nonexistent_order_returns_404(self, async_client):
        """Executing an unknown order returns 404."""
        resp = await async_client.post("/api/orders/non-existent-order-id/execute")
        assert resp.status_code == 404


class TestOrderPreviewEndpoint:
    """Tests for POST /api/orders/preview (CHKL-09 & non-mutating preview)."""

    async def test_preview_returns_all_nine_gates_without_persisting(self, async_client):
        """Preview evaluates all 9 rules and leaves database untouched."""
        resp = await async_client.post(
            "/api/orders/preview",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
                "currency": "USD",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is True
        assert len(data["risk_checks"]) == 12
        assert data["order_value"] == "1500.00"
        assert "preview_timestamp" in data

        # Confirm nothing was written to orders table
        list_resp = await async_client.get("/api/orders")
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 0

    async def test_preview_reports_rejection_reasons(self, async_client):
        """Preview reports failures for restricted symbols or invalid prices."""
        resp = await async_client.post(
            "/api/orders/preview",
            json={
                "symbol": "YESBANK",
                "side": "BUY",
                "quantity": 1,
                "price": "500001.00",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["passed"] is False
        assert len(data["rejection_reasons"]) >= 2


class TestIndianTickerSymbolFormatting:
    """Tests for Indian symbol format support in OrderCreateRequest (CHKL-08)."""

    async def test_symbols_with_ampersand_and_hyphen_pass_validation(self, async_client):
        """Symbols like M&M and BAJAJ-AUTO should be accepted by Pydantic validator."""
        for sym in ["M&M", "BAJAJ-AUTO", "L&T", "RELIANCE"]:
            resp = await async_client.post(
                "/api/orders",
                json={
                    "symbol": sym,
                    "side": "BUY",
                    "quantity": 1,
                    "price": "100.00",
                    "currency": "INR",
                },
            )
            assert resp.status_code == 201
            assert resp.json()["symbol"] == sym
            assert resp.json()["currency"] == "INR"


class TestExecutedOrdersInNotional:
    """Verifies executed orders continue contributing to daily notional (CHKL-04)."""

    async def test_executed_order_retains_notional(self, async_client):
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "100.00",  # 1000.00
            },
        )
        order_id = create_resp.json()["order_id"]

        # Execute the order
        await async_client.post(f"/api/orders/{order_id}/execute")

        # Stats should show 1000 notional even though order is EXECUTED
        stats_resp = await async_client.get("/api/orders/stats/summary")
        data = stats_resp.json()
        assert Decimal(data["today"]["total_notional"]) == Decimal("1000.00")
        assert data["today"]["approved"] == 1  # counts approved + executed
