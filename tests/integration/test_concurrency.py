"""
Concurrency integration tests verifying that simultaneous orders do not evade daily limits (CRITICAL-07).
"""

import asyncio
from decimal import Decimal
import pytest

pytestmark = pytest.mark.asyncio


class TestConcurrentOrderSubmissions:
    """Tests race-condition protection on daily order count and notional caps."""

    async def test_concurrent_order_submissions_respect_daily_count_cap(self, async_client):
        """Set max daily orders to 5, fire 10 concurrent requests, exactly 5 should pass and 5 reject."""
        # Set max daily orders to 5
        await async_client.put(
            "/api/risk-config",
            json={"max_daily_orders": 5},
        )

        async def submit_one(i: int):
            return await async_client.post(
                "/api/orders",
                json={
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 1,
                    "price": "100.00",
                },
            )

        # Fire 10 parallel requests
        responses = await asyncio.gather(*(submit_one(i) for i in range(10)))

        statuses = [r.json()["status"] for r in responses]
        approved_count = statuses.count("APPROVED")
        rejected_count = statuses.count("REJECTED")

        assert approved_count == 5, f"Expected exactly 5 approved, got {approved_count}"
        assert rejected_count == 5, f"Expected exactly 5 rejected, got {rejected_count}"

        # Verify daily stats agree
        stats_resp = await async_client.get("/api/orders/stats/summary")
        data = stats_resp.json()
        assert data["today"]["total_orders"] == 10
        assert data["today"]["approved"] == 5
        assert data["today"]["rejected"] == 5
