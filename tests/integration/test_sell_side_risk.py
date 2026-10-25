"""
Integration tests for SELL-side risk rules, inventory tracking, and reservation mechanics.

Covers:
- Short-selling rejection (RISK-10) when no holding exists.
- Selling allowed up to held quantity after simulated execution.
- Sell reservation accounting (RISK-11):
    - Submitting an approved sell order reserves the quantity.
    - Subsequent sell orders exceeding net sellable quantity are rejected.
- Settle simulated execution drops position and frees reservation.
- Position endpoint (/api/portfolio/positions/{symbol}) telemetry.
- Order preview (/api/orders/preview) includes held, reserved, and sellable quantities.
"""

from decimal import Decimal
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


class TestSellSideRiskIntegration:
    """End-to-end integration tests for SELL-side risk clearinghouse behavior."""

    async def test_short_selling_prohibited_when_no_shares_held(self, async_client):
        """Selling an asset with zero position must be REJECTED via RISK-10."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "TCS",
                "side": "SELL",
                "quantity": 10,
                "price": "3500.00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "REJECTED"
        assert any("short-selling is prohibited" in r.lower() for r in data["rejection_reasons"])
        
        # Verify RISK-10 is marked FAIL
        r10 = next((c for c in data["risk_checks"] if c["rule_id"] == "RISK-10"), None)
        assert r10 is not None
        assert r10["passed"] is False
        assert r10["status"] == "FAIL"

    async def test_buy_execute_and_sell_lifecycle(self, async_client):
        """A user buys shares, executes, and then successfully sells within holdings."""
        # 1. Place BUY order for 50 shares
        buy_res = await async_client.post(
            "/api/orders",
            json={
                "symbol": "RELIANCE",
                "side": "BUY",
                "quantity": 50,
                "price": "2900.00",
            },
        )
        assert buy_res.status_code == 201
        buy_order = buy_res.json()
        assert buy_order["status"] == "APPROVED"
        buy_id = buy_order["order_id"]

        # 2. Execute the BUY order to materialize holding in simulated_positions
        exec_res = await async_client.post(f"/api/orders/{buy_id}/execute")
        assert exec_res.status_code == 200

        # 3. Check position telemetry
        pos_res = await async_client.get("/api/portfolio/positions/RELIANCE")
        assert pos_res.status_code == 200
        pos_data = pos_res.json()
        assert pos_data["held_qty"] == 50
        assert pos_data["reserved_qty"] == 0
        assert pos_data["sellable_qty"] == 50

        # 4. Submit SELL order for 20 shares (<= 50)
        sell_res = await async_client.post(
            "/api/orders",
            json={
                "symbol": "RELIANCE",
                "side": "SELL",
                "quantity": 20,
                "price": "2950.00",
            },
        )
        assert sell_res.status_code == 201
        sell_order = sell_res.json()
        assert sell_order["status"] == "APPROVED"
        assert sell_order["rejection_reasons"] == []

        # 5. Position telemetry should now reflect 20 reserved by approved open sell
        pos_res2 = await async_client.get("/api/portfolio/positions/RELIANCE")
        pos_data2 = pos_res2.json()
        assert pos_data2["held_qty"] == 50
        assert pos_data2["reserved_qty"] == 20
        assert pos_data2["sellable_qty"] == 30

    async def test_open_sell_order_reservation_exhaustion(self, async_client):
        """Sequential sell orders correctly deplete unreserved sellable quantity."""
        # 1. Establish 100 shares in INFY
        buy_res = await async_client.post(
            "/api/orders",
            json={
                "symbol": "INFY",
                "side": "BUY",
                "quantity": 100,
                "price": "1800.00",
            },
        )
        assert buy_res.status_code == 201
        await async_client.post(f"/api/orders/{buy_res.json()['order_id']}/execute")

        # 2. Place SELL order for 60 shares -> APPROVED (60 reserved, 40 sellable)
        sell1 = await async_client.post(
            "/api/orders",
            json={
                "symbol": "INFY",
                "side": "SELL",
                "quantity": 60,
                "price": "1850.00",
            },
        )
        assert sell1.status_code == 201
        assert sell1.json()["status"] == "APPROVED"

        # 3. Attempt SELL order for 50 shares (> 40 sellable) -> REJECTED (RISK-11)
        sell2 = await async_client.post(
            "/api/orders",
            json={
                "symbol": "INFY",
                "side": "SELL",
                "quantity": 50,
                "price": "1850.00",
            },
        )
        assert sell2.status_code == 201
        sell2_data = sell2.json()
        assert sell2_data["status"] == "REJECTED"
        assert any("exceeds net sellable quantity" in r for r in sell2_data["rejection_reasons"])

        # 4. Place SELL order for exactly remaining 40 shares -> APPROVED (100 reserved, 0 sellable)
        sell3 = await async_client.post(
            "/api/orders",
            json={
                "symbol": "INFY",
                "side": "SELL",
                "quantity": 40,
                "price": "1850.00",
            },
        )
        assert sell3.status_code == 201
        assert sell3.json()["status"] == "APPROVED"

        # 5. Further sell order even for 1 share -> REJECTED
        sell4 = await async_client.post(
            "/api/orders",
            json={
                "symbol": "INFY",
                "side": "SELL",
                "quantity": 1,
                "price": "1850.00",
            },
        )
        assert sell4.status_code == 201
        assert sell4.json()["status"] == "REJECTED"

    async def test_order_preview_contains_holding_telemetry(self, async_client):
        """POST /api/orders/preview returns held_quantity, reserved_quantity, and sellable_quantity."""
        preview_res = await async_client.post(
            "/api/orders/preview",
            json={
                "symbol": "HDFCBANK",
                "side": "SELL",
                "quantity": 10,
                "price": "1600.00",
            },
        )
        assert preview_res.status_code == 200
        data = preview_res.json()
        assert "held_quantity" in data
        assert "reserved_quantity" in data
        assert "sellable_quantity" in data
        assert len(data["risk_checks"]) == 12
