"""
Unit tests for SELL-Side Risk Rules (RISK-10, RISK-11, RISK-12).

Tests:
- RISK-10: Available Holdings Verification / Short-Selling Prohibition
- RISK-11: Open Sell Order Reservation
- RISK-12: Position Ledger Integrity & Fail-Safe
- Engine evaluation with BUY and SELL side contexts
"""

from decimal import Decimal
import pytest

from app.config import RiskConfig
from app.models.order import OrderSide
from app.services.risk_engine import (
    check_available_holdings,
    check_sell_reservation,
    check_ledger_integrity,
    evaluate,
)


@pytest.fixture
def risk_config():
    return RiskConfig(
        max_order_value=Decimal("500000.00"),
        restricted_symbols=["RESTRICTED"],
        min_price=Decimal("1.00"),
        max_quantity=10000,
        max_price=Decimal("200000.00"),
        max_daily_orders=100,
        max_daily_notional=Decimal("5000000.00"),
    )


class TestRisk10AvailableHoldings:
    """Tests for RISK-10 Available Holdings Check."""

    def test_buy_side_is_not_applicable(self):
        result = check_available_holdings(
            side=OrderSide.BUY,
            quantity=10,
            symbol="RELIANCE",
            position_context={"held_qty": 0},
        )
        assert result.passed is True
        assert result.status == "NOT_APPLICABLE"
        assert result.applicable_side == "SELL"

    def test_sell_without_holdings_fails(self):
        result = check_available_holdings(
            side=OrderSide.SELL,
            quantity=10,
            symbol="RELIANCE",
            position_context={"held_qty": 0},
        )
        assert result.passed is False
        assert result.status == "FAIL"
        assert "short-selling is prohibited" in result.reason.lower()

    def test_sell_with_none_context_fails(self):
        result = check_available_holdings(
            side=OrderSide.SELL,
            quantity=10,
            symbol="RELIANCE",
            position_context=None,
        )
        assert result.passed is False
        assert result.status == "FAIL"

    def test_sell_with_positive_holdings_passes(self):
        result = check_available_holdings(
            side=OrderSide.SELL,
            quantity=10,
            symbol="RELIANCE",
            position_context={"held_qty": 50},
        )
        assert result.passed is True
        assert result.status == "PASS"


class TestRisk11SellReservation:
    """Tests for RISK-11 Open Sell Order Reservation."""

    def test_buy_side_is_not_applicable(self):
        result = check_sell_reservation(
            side=OrderSide.BUY,
            quantity=10,
            symbol="TCS",
            position_context={"held_qty": 0, "reserved_qty": 0, "sellable_qty": 0},
        )
        assert result.passed is True
        assert result.status == "NOT_APPLICABLE"
        assert result.applicable_side == "SELL"

    def test_sell_within_sellable_quantity_passes(self):
        result = check_sell_reservation(
            side=OrderSide.SELL,
            quantity=20,
            symbol="TCS",
            position_context={"held_qty": 50, "reserved_qty": 10, "sellable_qty": 40},
        )
        assert result.passed is True
        assert result.status == "PASS"

    def test_sell_exceeding_sellable_quantity_due_to_reservations_fails(self):
        result = check_sell_reservation(
            side=OrderSide.SELL,
            quantity=30,
            symbol="TCS",
            position_context={"held_qty": 50, "reserved_qty": 35, "sellable_qty": 15},
        )
        assert result.passed is False
        assert result.status == "FAIL"
        assert "reserved by open orders" in result.reason

    def test_sell_exceeding_held_quantity_without_prior_reservations_fails(self):
        result = check_sell_reservation(
            side=OrderSide.SELL,
            quantity=60,
            symbol="TCS",
            position_context={"held_qty": 50, "reserved_qty": 0, "sellable_qty": 50},
        )
        assert result.passed is False
        assert result.status == "FAIL"
        assert "exceeds total available holdings" in result.reason


class TestRisk12LedgerIntegrity:
    """Tests for RISK-12 Position Ledger Integrity & Fail-Safe."""

    def test_buy_side_is_not_applicable(self):
        result = check_ledger_integrity(
            side=OrderSide.BUY,
            symbol="INFY",
            position_context={"held_qty": -5},
        )
        assert result.passed is True
        assert result.status == "NOT_APPLICABLE"
        assert result.applicable_side == "SELL"

    def test_sell_with_negative_position_fails(self):
        result = check_ledger_integrity(
            side=OrderSide.SELL,
            symbol="INFY",
            position_context={"held_qty": -10},
        )
        assert result.passed is False
        assert result.status == "FAIL"
        assert "negative quantity detected" in result.reason

    def test_sell_with_none_context_fails(self):
        result = check_ledger_integrity(
            side=OrderSide.SELL,
            symbol="INFY",
            position_context=None,
        )
        assert result.passed is False
        assert result.status == "FAIL"

    def test_sell_with_valid_ledger_passes(self):
        result = check_ledger_integrity(
            side=OrderSide.SELL,
            symbol="INFY",
            position_context={"held_qty": 25},
        )
        assert result.passed is True
        assert result.status == "PASS"


class TestFullEngineEvaluationMatrix:
    """Tests evaluate() function with 12-rule matrix across BUY and SELL."""

    def test_evaluate_returns_12_rules_for_buy(self, risk_config):
        result = evaluate(
            quantity=10,
            price=Decimal("100.00"),
            symbol="RELIANCE",
            config=risk_config,
            side=OrderSide.BUY,
        )
        assert len(result.check_results) == 12
        sell_rules = [c for c in result.check_results if c.rule_id in ("RISK-10", "RISK-11", "RISK-12")]
        assert len(sell_rules) == 3
        assert all(c.status == "NOT_APPLICABLE" for c in sell_rules)
        assert all(c.passed for c in sell_rules)
        assert result.passed is True

    def test_evaluate_returns_12_rules_for_sell_with_holdings(self, risk_config):
        pos_ctx = {"held_qty": 100, "reserved_qty": 20, "sellable_qty": 80}
        result = evaluate(
            quantity=50,
            price=Decimal("2000.00"),
            symbol="RELIANCE",
            config=risk_config,
            side=OrderSide.SELL,
            position_context=pos_ctx,
        )
        assert len(result.check_results) == 12
        sell_rules = [c for c in result.check_results if c.rule_id in ("RISK-10", "RISK-11", "RISK-12")]
        assert all(c.status == "PASS" for c in sell_rules)
        assert result.passed is True

    def test_evaluate_fails_short_selling_on_sell(self, risk_config):
        pos_ctx = {"held_qty": 0, "reserved_qty": 0, "sellable_qty": 0}
        result = evaluate(
            quantity=10,
            price=Decimal("2000.00"),
            symbol="RELIANCE",
            config=risk_config,
            side=OrderSide.SELL,
            position_context=pos_ctx,
        )
        assert len(result.check_results) == 12
        assert result.passed is False
        assert any("short-selling is prohibited" in r.lower() for r in result.rejection_reasons)
