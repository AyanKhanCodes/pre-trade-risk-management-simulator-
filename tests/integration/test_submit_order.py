"""
Integration tests for order submission (FR-01) and validation (FR-02).

Tests the complete path:
    API request → request validation → order service → risk engine → database → API response

Covers:
- Valid order submission and approval
- Risk-rejected orders with reasons
- Input validation (missing fields, wrong types)
- Order retrieval (single and list)
- Boundary values at the API level
"""

from decimal import Decimal

import pytest
import pytest_asyncio


# All tests in this module use the async_client fixture from conftest.py.
pytestmark = pytest.mark.asyncio


class TestSubmitOrder:
    """Integration tests for POST /api/orders (FR-01 + FR-02)."""

    async def test_valid_order_is_approved(self, async_client):
        """A valid order should be created and approved."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["rejection_reasons"] == []
        assert data["symbol"] == "AAPL"
        assert data["side"] == "BUY"
        assert data["quantity"] == 10
        assert data["price"] == "150.00"
        assert data["order_value"] == "1500.00"
        assert data["order_id"]  # Should be assigned.
        # Risk checks should be populated.
        assert len(data["risk_checks"]) > 0
        assert all(c["passed"] for c in data["risk_checks"])

    async def test_sell_order_is_approved(self, async_client):
        """A valid SELL order should also be approved."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "SELL",
                "quantity": 5,
                "price": "200.00",
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "APPROVED"

    async def test_order_exceeding_max_value_rejected(self, async_client):
        """An order exceeding the max value should be rejected with a reason."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 1,
                "price": "10000.01",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "REJECTED"
        assert len(data["rejection_reasons"]) >= 1
        assert any(
            "exceeds" in r.lower() for r in data["rejection_reasons"]
        )

    async def test_restricted_symbol_rejected(self, async_client):
        """An order for a restricted symbol should be rejected."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "TSLA",
                "side": "BUY",
                "quantity": 10,
                "price": "100.00",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "REJECTED"
        assert any(
            "restricted" in r.lower() for r in data["rejection_reasons"]
        )

    async def test_zero_quantity_rejected(self, async_client):
        """An order with zero quantity should be rejected (422 from Pydantic)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 0,
                "price": "100.00",
            },
        )
        assert response.status_code == 422

    async def test_negative_quantity_rejected(self, async_client):
        """An order with negative quantity should be rejected (422)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": -5,
                "price": "100.00",
            },
        )
        assert response.status_code == 422

    async def test_zero_price_rejected(self, async_client):
        """An order with zero price should be rejected (422)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "0",
            },
        )
        assert response.status_code == 422

    async def test_negative_price_rejected(self, async_client):
        """An order with negative price should be rejected (422)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "-50.00",
            },
        )
        assert response.status_code == 422

    async def test_missing_symbol_returns_422(self, async_client):
        """A request missing the symbol field should return 422."""
        response = await async_client.post(
            "/api/orders",
            json={
                "side": "BUY",
                "quantity": 10,
                "price": "100.00",
            },
        )
        assert response.status_code == 422

    async def test_missing_side_returns_422(self, async_client):
        """A request missing the side field should return 422."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "quantity": 10,
                "price": "100.00",
            },
        )
        assert response.status_code == 422

    async def test_invalid_side_returns_422(self, async_client):
        """An unsupported side value should return 422."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "HOLD",
                "quantity": 10,
                "price": "100.00",
            },
        )
        assert response.status_code == 422

    async def test_empty_body_returns_422(self, async_client):
        """An empty request body should return 422."""
        response = await async_client.post("/api/orders", json={})
        assert response.status_code == 422

    async def test_malformed_json_returns_422(self, async_client):
        """Malformed JSON should return 422."""
        response = await async_client.post(
            "/api/orders",
            content="not-json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 422

    # Boundary values at the API level.
    async def test_boundary_9999_99_approved(self, async_client):
        """$9,999.99 should be approved (below limit)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 1,
                "price": "9999.99",
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "APPROVED"

    async def test_boundary_10000_00_approved(self, async_client):
        """$10,000.00 should be approved (at limit, inclusive)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 1,
                "price": "10000.00",
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "APPROVED"

    async def test_boundary_10000_01_rejected(self, async_client):
        """$10,000.01 should be rejected (above limit)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 1,
                "price": "10000.01",
            },
        )
        assert response.status_code == 201
        assert response.json()["status"] == "REJECTED"

    async def test_multiple_failures_all_reasons_returned(self, async_client):
        """When both restricted symbol AND over max value, both reasons appear."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "TSLA",
                "side": "BUY",
                "quantity": 1,
                "price": "10000.01",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "REJECTED"
        assert len(data["rejection_reasons"]) >= 2

    # --- New rules ---

    async def test_penny_stock_rejected(self, async_client):
        """An order with price $0.01 should be rejected (penny stock protection)."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 100,
                "price": "0.50",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "REJECTED"
        assert any(
            "penny stock" in r.lower() for r in data["rejection_reasons"]
        )

    async def test_risk_checks_in_response(self, async_client):
        """Risk check details should be included in the order response."""
        response = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
            },
        )
        data = response.json()
        assert "risk_checks" in data
        assert len(data["risk_checks"]) == 9  # 9 rules total
        for check in data["risk_checks"]:
            assert "rule_id" in check
            assert "rule_name" in check
            assert "passed" in check
            assert "reason" in check


class TestOrderRetrieval:
    """Integration tests for GET /api/orders and GET /api/orders/{id} (FR-01 persistence)."""

    async def test_get_order_by_id(self, async_client):
        """A created order should be retrievable by its ID."""
        # Create an order first.
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
            },
        )
        order_id = create_resp.json()["order_id"]

        # Retrieve it.
        get_resp = await async_client.get(f"/api/orders/{order_id}")
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["order_id"] == order_id
        assert data["symbol"] == "AAPL"
        assert data["status"] == "APPROVED"
        # Risk checks should survive retrieval.
        assert len(data["risk_checks"]) > 0

    async def test_get_nonexistent_order_returns_404(self, async_client):
        """Requesting a non-existent order should return 404."""
        response = await async_client.get("/api/orders/nonexistent-id")
        assert response.status_code == 404

    async def test_list_orders_includes_submitted(self, async_client):
        """Submitted orders should appear in the order list."""
        # Create two orders.
        await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
            },
        )
        await async_client.post(
            "/api/orders",
            json={
                "symbol": "GOOGL",
                "side": "SELL",
                "quantity": 5,
                "price": "200.00",
            },
        )

        # List all orders.
        response = await async_client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["orders"]) == 2

    async def test_list_orders_empty_initially(self, async_client):
        """The order list should be empty when no orders have been created."""
        response = await async_client.get("/api/orders")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["orders"] == []

    async def test_rejection_reasons_survive_retrieval(self, async_client):
        """Rejection reasons should be persisted and returned on retrieval."""
        create_resp = await async_client.post(
            "/api/orders",
            json={
                "symbol": "TSLA",
                "side": "BUY",
                "quantity": 10,
                "price": "100.00",
            },
        )
        order_id = create_resp.json()["order_id"]

        get_resp = await async_client.get(f"/api/orders/{order_id}")
        data = get_resp.json()
        assert data["status"] == "REJECTED"
        assert len(data["rejection_reasons"]) >= 1
        assert any(
            "restricted" in r.lower() for r in data["rejection_reasons"]
        )


class TestHealthAndConfig:
    """Tests for health check and risk config endpoints."""

    async def test_health_endpoint(self, async_client):
        """Health endpoint should return healthy status."""
        response = await async_client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    async def test_risk_config_endpoint(self, async_client):
        """Risk config endpoint should return the current configuration."""
        response = await async_client.get("/api/risk-config")
        assert response.status_code == 200
        data = response.json()
        assert "max_order_value" in data
        assert "restricted_symbols" in data
        assert data["max_order_value"] == "10000.00"
        assert "TSLA" in data["restricted_symbols"]
        # New fields should be present.
        assert "min_price" in data
        assert "max_quantity" in data
        assert "max_price" in data
        assert "max_daily_orders" in data
        assert "max_daily_notional" in data

    async def test_update_risk_config(self, async_client):
        """PUT /api/risk-config should update the configuration."""
        response = await async_client.put(
            "/api/risk-config",
            json={"max_order_value": "5000.00", "min_price": "2.00"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["max_order_value"] == "5000.00"
        assert data["min_price"] == "2.00"
        # Other fields should remain unchanged.
        assert "TSLA" in data["restricted_symbols"]

    async def test_risk_rules_endpoint(self, async_client):
        """GET /api/risk-rules should return all rules with metadata."""
        response = await async_client.get("/api/risk-rules")
        assert response.status_code == 200
        data = response.json()
        assert "rules" in data
        assert len(data["rules"]) == 9  # 9 rules total
        rule_ids = {r["rule_id"] for r in data["rules"]}
        assert "RISK-01" in rule_ids
        assert "RISK-05" in rule_ids  # Penny stock rule
        assert "RISK-09" in rule_ids  # Daily notional rule
        # Each rule should have metadata.
        for rule in data["rules"]:
            assert rule["name"]
            assert rule["description"]
            assert rule["category"]

    async def test_order_stats_endpoint(self, async_client):
        """GET /api/orders/stats/summary should return aggregate statistics."""
        # Create a couple of orders first.
        await async_client.post(
            "/api/orders",
            json={
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 10,
                "price": "150.00",
            },
        )
        await async_client.post(
            "/api/orders",
            json={
                "symbol": "TSLA",
                "side": "BUY",
                "quantity": 10,
                "price": "100.00",
            },
        )

        response = await async_client.get("/api/orders/stats/summary")
        assert response.status_code == 200
        data = response.json()
        assert "today" in data
        assert "all_time" in data
        assert "top_symbols" in data
        assert data["all_time"]["total_orders"] == 2
