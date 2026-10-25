"""
Unit tests for the new risk rules (RISK-05 through RISK-09).

Tests each new rule individually:
- RISK-05: Minimum price / penny stock protection
- RISK-06: Maximum quantity per order
- RISK-07: Maximum price / fat-finger protection
- RISK-08: Daily order count limit
- RISK-09: Daily notional limit
- Combined: new rules integrate with evaluate()
"""

from decimal import Decimal

import pytest

from app.config import RiskConfig
from app.services.risk_engine import (
    check_daily_notional,
    check_daily_order_count,
    check_max_price,
    check_max_quantity,
    check_min_price,
    evaluate,
)


# ---------------------------------------------------------------------------
# RISK-05: Minimum price (penny stock protection)
# ---------------------------------------------------------------------------


class TestCheckMinPrice:
    """Tests for RISK-05: price must be at or above the minimum."""

    def test_price_above_minimum_passes(self):
        """A price well above the minimum should pass."""
        result = check_min_price(Decimal("150.00"), Decimal("1.00"))
        assert result.passed is True
        assert result.rule_id == "RISK-05"

    def test_price_at_minimum_passes(self):
        """A price exactly at the minimum (inclusive) should pass."""
        result = check_min_price(Decimal("1.00"), Decimal("1.00"))
        assert result.passed is True

    def test_price_below_minimum_fails(self):
        """A price below the minimum should fail."""
        result = check_min_price(Decimal("0.99"), Decimal("1.00"))
        assert result.passed is False
        assert "penny stock" in result.reason.lower()

    def test_penny_stock_001_rejected(self):
        """$0.01 should be rejected as a penny stock."""
        result = check_min_price(Decimal("0.01"), Decimal("1.00"))
        assert result.passed is False
        assert "penny stock" in result.reason.lower()

    def test_custom_minimum_respected(self):
        """A custom minimum of $5.00 should reject $4.99."""
        result = check_min_price(Decimal("4.99"), Decimal("5.00"))
        assert result.passed is False

    def test_custom_minimum_passes(self):
        """A custom minimum of $5.00 should pass $5.00."""
        result = check_min_price(Decimal("5.00"), Decimal("5.00"))
        assert result.passed is True


# ---------------------------------------------------------------------------
# RISK-06: Maximum quantity
# ---------------------------------------------------------------------------


class TestCheckMaxQuantity:
    """Tests for RISK-06: quantity must not exceed the maximum."""

    def test_quantity_below_max_passes(self):
        """A quantity below the max should pass."""
        result = check_max_quantity(100, 10000)
        assert result.passed is True
        assert result.rule_id == "RISK-06"

    def test_quantity_at_max_passes(self):
        """A quantity exactly at the max should pass."""
        result = check_max_quantity(10000, 10000)
        assert result.passed is True

    def test_quantity_above_max_fails(self):
        """A quantity above the max should fail."""
        result = check_max_quantity(10001, 10000)
        assert result.passed is False
        assert "exceeds" in result.reason.lower()

    def test_very_large_quantity_fails(self):
        """An extremely large quantity should fail."""
        result = check_max_quantity(1_000_000, 10000)
        assert result.passed is False


# ---------------------------------------------------------------------------
# RISK-07: Maximum price (fat-finger protection)
# ---------------------------------------------------------------------------


class TestCheckMaxPrice:
    """Tests for RISK-07: price must not exceed the maximum."""

    def test_normal_price_passes(self):
        """A normal price should pass."""
        result = check_max_price(Decimal("150.00"), Decimal("50000.00"))
        assert result.passed is True
        assert result.rule_id == "RISK-07"

    def test_price_at_max_passes(self):
        """A price exactly at the max should pass."""
        result = check_max_price(Decimal("50000.00"), Decimal("50000.00"))
        assert result.passed is True

    def test_price_above_max_fails(self):
        """A price above the max should fail (fat-finger)."""
        result = check_max_price(Decimal("50000.01"), Decimal("50000.00"))
        assert result.passed is False
        assert "fat-finger" in result.reason.lower()

    def test_absurd_price_fails(self):
        """An absurdly high price should fail."""
        result = check_max_price(Decimal("999999.99"), Decimal("50000.00"))
        assert result.passed is False


# ---------------------------------------------------------------------------
# RISK-08: Daily order count limit
# ---------------------------------------------------------------------------


class TestCheckDailyOrderCount:
    """Tests for RISK-08: daily order count must not exceed the maximum."""

    def test_below_limit_passes(self):
        """Order count below the limit should pass."""
        result = check_daily_order_count(10, 50)
        assert result.passed is True
        assert result.rule_id == "RISK-08"

    def test_at_limit_fails(self):
        """Order count at the limit should fail (no more allowed)."""
        result = check_daily_order_count(50, 50)
        assert result.passed is False

    def test_above_limit_fails(self):
        """Order count above the limit should fail."""
        result = check_daily_order_count(51, 50)
        assert result.passed is False

    def test_zero_orders_passes(self):
        """Zero orders placed today should pass."""
        result = check_daily_order_count(0, 50)
        assert result.passed is True


# ---------------------------------------------------------------------------
# RISK-09: Daily notional limit
# ---------------------------------------------------------------------------


class TestCheckDailyNotional:
    """Tests for RISK-09: daily notional must not exceed the maximum."""

    def test_within_limit_passes(self):
        """Adding this order should stay within the daily limit."""
        result = check_daily_notional(
            Decimal("100000.00"),
            Decimal("50000.00"),
            Decimal("500000.00"),
        )
        assert result.passed is True
        assert result.rule_id == "RISK-09"

    def test_exceeds_limit_fails(self):
        """Adding this order would exceed the daily limit."""
        result = check_daily_notional(
            Decimal("490000.00"),
            Decimal("20000.00"),
            Decimal("500000.00"),
        )
        assert result.passed is False
        assert "exceed" in result.reason.lower()

    def test_exactly_at_limit_passes(self):
        """Adding this order to reach exactly the limit should pass."""
        result = check_daily_notional(
            Decimal("400000.00"),
            Decimal("100000.00"),
            Decimal("500000.00"),
        )
        assert result.passed is True

    def test_zero_notional_passes(self):
        """No prior notional today should pass."""
        result = check_daily_notional(
            Decimal("0"),
            Decimal("1000.00"),
            Decimal("500000.00"),
        )
        assert result.passed is True


# ---------------------------------------------------------------------------
# Integration with evaluate()
# ---------------------------------------------------------------------------


class TestEvaluateWithNewRules:
    """Tests that new rules are integrated into the aggregate evaluate()."""

    def _default_config(self) -> RiskConfig:
        return RiskConfig(
            max_order_value=Decimal("10000.00"),
            restricted_symbols=["TSLA"],
            min_price=Decimal("1.00"),
            max_quantity=10000,
            max_price=Decimal("50000.00"),
            max_daily_orders=50,
            max_daily_notional=Decimal("500000.00"),
        )

    def test_penny_stock_rejected_in_evaluate(self):
        """A penny stock price should be caught by evaluate()."""
        result = evaluate(
            quantity=100,
            price=Decimal("0.50"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is False
        assert any("penny stock" in r.lower() for r in result.rejection_reasons)

    def test_fat_finger_rejected_in_evaluate(self):
        """An absurdly high price should be caught by evaluate()."""
        result = evaluate(
            quantity=1,
            price=Decimal("99999.99"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is False
        assert any("fat-finger" in r.lower() for r in result.rejection_reasons)

    def test_all_rules_checked_count(self):
        """evaluate() should run all 12 rules."""
        result = evaluate(
            quantity=10,
            price=Decimal("150.00"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert len(result.check_results) == 12

    def test_valid_order_passes_all_new_rules(self):
        """A valid order should pass all 9 rules."""
        result = evaluate(
            quantity=10,
            price=Decimal("150.00"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is True
        assert result.rejection_reasons == []

    def test_daily_limits_passed_to_evaluate(self):
        """Daily limit arguments should be used by evaluate()."""
        result = evaluate(
            quantity=10,
            price=Decimal("100.00"),
            symbol="AAPL",
            config=self._default_config(),
            daily_order_count=50,  # At the limit.
            daily_notional=Decimal("0"),
        )
        assert result.passed is False
        assert any("daily order count" in r.lower() for r in result.rejection_reasons)

    def test_rule_names_populated(self):
        """Each check result should have its rule_name populated."""
        result = evaluate(
            quantity=10,
            price=Decimal("150.00"),
            symbol="AAPL",
            config=self._default_config(),
        )
        for check in result.check_results:
            assert check.rule_name, f"{check.rule_id} should have a rule_name"
