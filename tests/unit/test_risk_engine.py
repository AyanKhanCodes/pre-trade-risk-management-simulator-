"""
Unit tests for the risk engine.

Tests each risk rule individually and the aggregate evaluate() function.
Covers:
- RISK-01: Maximum order value (including boundary values)
- RISK-02: Restricted symbol check
- RISK-03: Quantity validity
- RISK-04: Price validity
- Combined: multiple failures return all reasons
"""

from decimal import Decimal

import pytest

from app.config import RiskConfig
from app.services.risk_engine import (
    RiskResult,
    check_max_order_value,
    check_price_validity,
    check_quantity_validity,
    check_restricted_symbol,
    evaluate,
)


# ---------------------------------------------------------------------------
# RISK-01: Maximum order value
# ---------------------------------------------------------------------------


class TestCheckMaxOrderValue:
    """Tests for RISK-01: order value must not exceed the configured maximum."""

    def test_value_below_limit_passes(self):
        """An order value well below the limit should pass."""
        result = check_max_order_value(10, Decimal("100.00"), Decimal("10000.00"))
        assert result.passed is True
        assert result.rule_id == "RISK-01"

    def test_value_at_exact_limit_passes(self):
        """An order worth exactly the max (inclusive) should pass."""
        result = check_max_order_value(1, Decimal("10000.00"), Decimal("10000.00"))
        assert result.passed is True

    def test_value_above_limit_fails(self):
        """An order value above the limit should fail."""
        result = check_max_order_value(1, Decimal("10000.01"), Decimal("10000.00"))
        assert result.passed is False
        assert "exceeds" in result.reason.lower()

    # Boundary-value analysis (section 9.2 of the project plan)
    def test_boundary_9999_99_passes(self):
        """$9,999.99 is below the limit and should pass."""
        result = check_max_order_value(1, Decimal("9999.99"), Decimal("10000.00"))
        assert result.passed is True

    def test_boundary_10000_00_passes(self):
        """$10,000.00 is exactly at the limit and should pass (inclusive)."""
        result = check_max_order_value(1, Decimal("10000.00"), Decimal("10000.00"))
        assert result.passed is True

    def test_boundary_10000_01_fails(self):
        """$10,000.01 is above the limit and should fail."""
        result = check_max_order_value(1, Decimal("10000.01"), Decimal("10000.00"))
        assert result.passed is False

    def test_large_quantity_multiplied(self):
        """100 × $100.01 = $10,001.00 should fail."""
        result = check_max_order_value(100, Decimal("100.01"), Decimal("10000.00"))
        assert result.passed is False

    def test_quantity_times_price_exactly_at_limit(self):
        """100 × $100.00 = $10,000.00 should pass."""
        result = check_max_order_value(100, Decimal("100.00"), Decimal("10000.00"))
        assert result.passed is True

    def test_very_small_order_passes(self):
        """1 × $0.01 = $0.01 should pass."""
        result = check_max_order_value(1, Decimal("0.01"), Decimal("10000.00"))
        assert result.passed is True


# ---------------------------------------------------------------------------
# RISK-02: Restricted symbol
# ---------------------------------------------------------------------------


class TestCheckRestrictedSymbol:
    """Tests for RISK-02: symbol must not be in the restricted list."""

    def test_allowed_symbol_passes(self):
        """An unrestricted symbol should pass."""
        result = check_restricted_symbol("AAPL", ["TSLA"])
        assert result.passed is True

    def test_restricted_symbol_fails(self):
        """A restricted symbol should fail."""
        result = check_restricted_symbol("TSLA", ["TSLA"])
        assert result.passed is False
        assert "restricted" in result.reason.lower()

    def test_case_insensitive_match(self):
        """Restriction check should be case-insensitive."""
        result = check_restricted_symbol("tsla", ["TSLA"])
        assert result.passed is False

    def test_empty_restricted_list_passes(self):
        """With no restrictions, any symbol should pass."""
        result = check_restricted_symbol("TSLA", [])
        assert result.passed is True

    def test_multiple_restricted_symbols(self):
        """Check against a list with multiple restricted symbols."""
        restricted = ["TSLA", "GME", "AMC"]
        assert check_restricted_symbol("GME", restricted).passed is False
        assert check_restricted_symbol("AAPL", restricted).passed is True


# ---------------------------------------------------------------------------
# RISK-03: Quantity validity
# ---------------------------------------------------------------------------


class TestCheckQuantityValidity:
    """Tests for RISK-03: quantity must be a positive integer."""

    def test_positive_quantity_passes(self):
        """A positive integer quantity should pass."""
        result = check_quantity_validity(10)
        assert result.passed is True

    def test_quantity_of_one_passes(self):
        """Minimum valid quantity (1) should pass."""
        result = check_quantity_validity(1)
        assert result.passed is True

    def test_zero_quantity_fails(self):
        """Zero quantity should fail."""
        result = check_quantity_validity(0)
        assert result.passed is False

    def test_negative_quantity_fails(self):
        """Negative quantity should fail."""
        result = check_quantity_validity(-1)
        assert result.passed is False

    def test_large_quantity_passes(self):
        """A very large positive quantity should still pass the validity check."""
        result = check_quantity_validity(1_000_000)
        assert result.passed is True

    def test_boolean_true_fails(self):
        """Boolean True (which is int subclass) should fail."""
        result = check_quantity_validity(True)
        assert result.passed is False

    def test_boolean_false_fails(self):
        """Boolean False should fail."""
        result = check_quantity_validity(False)
        assert result.passed is False


# ---------------------------------------------------------------------------
# RISK-04: Price validity
# ---------------------------------------------------------------------------


class TestCheckPriceValidity:
    """Tests for RISK-04: price must be a positive Decimal."""

    def test_positive_price_passes(self):
        """A positive Decimal price should pass."""
        result = check_price_validity(Decimal("150.00"))
        assert result.passed is True

    def test_small_positive_price_passes(self):
        """A very small positive price ($0.01) should pass."""
        result = check_price_validity(Decimal("0.01"))
        assert result.passed is True

    def test_zero_price_fails(self):
        """Zero price should fail."""
        result = check_price_validity(Decimal("0"))
        assert result.passed is False

    def test_negative_price_fails(self):
        """Negative price should fail."""
        result = check_price_validity(Decimal("-1.00"))
        assert result.passed is False

    def test_large_price_passes(self):
        """A very large price should still pass the validity check."""
        result = check_price_validity(Decimal("999999.99"))
        assert result.passed is True


# ---------------------------------------------------------------------------
# Aggregate evaluate() function
# ---------------------------------------------------------------------------


class TestEvaluate:
    """Tests for the aggregate evaluate() function."""

    def _default_config(self) -> RiskConfig:
        return RiskConfig(
            max_order_value=Decimal("10000.00"),
            restricted_symbols=["TSLA"],
        )

    def test_valid_order_approved(self):
        """A fully valid order should pass all checks."""
        result = evaluate(
            quantity=10,
            price=Decimal("150.00"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is True
        assert result.rejection_reasons == []

    def test_over_value_rejected(self):
        """An order exceeding max value should be rejected."""
        result = evaluate(
            quantity=1,
            price=Decimal("10000.01"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is False
        assert any("exceeds" in r.lower() for r in result.rejection_reasons)

    def test_restricted_symbol_rejected(self):
        """An order for a restricted symbol should be rejected."""
        result = evaluate(
            quantity=10,
            price=Decimal("100.00"),
            symbol="TSLA",
            config=self._default_config(),
        )
        assert result.passed is False
        assert any("restricted" in r.lower() for r in result.rejection_reasons)

    def test_multiple_failures_all_reported(self):
        """When multiple rules fail, all rejection reasons should be returned."""
        # Restricted symbol AND over max value.
        result = evaluate(
            quantity=1,
            price=Decimal("10000.01"),
            symbol="TSLA",
            config=self._default_config(),
        )
        assert result.passed is False
        assert len(result.rejection_reasons) >= 2
        reasons_text = " ".join(result.rejection_reasons).lower()
        assert "restricted" in reasons_text
        assert "exceeds" in reasons_text

    def test_custom_config_respected(self):
        """The engine should use the provided config, not hardcoded defaults."""
        config = RiskConfig(
            max_order_value=Decimal("500.00"),
            restricted_symbols=["AAPL"],
        )
        result = evaluate(
            quantity=10,
            price=Decimal("100.00"),
            symbol="AAPL",
            config=config,
        )
        assert result.passed is False
        reasons_text = " ".join(result.rejection_reasons).lower()
        # Both max value (10*100=1000 > 500) and restricted symbol should fail.
        assert "exceeds" in reasons_text
        assert "restricted" in reasons_text

    def test_sell_side_same_rules(self):
        """SELL orders should be checked with the same rules as BUY orders."""
        # This tests the documented MVP policy.
        result = evaluate(
            quantity=10,
            price=Decimal("150.00"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is True

    def test_exactly_at_limit_passes(self):
        """An order worth exactly the maximum should pass."""
        result = evaluate(
            quantity=100,
            price=Decimal("100.00"),
            symbol="AAPL",
            config=self._default_config(),
        )
        assert result.passed is True
