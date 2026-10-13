"""
Risk engine for the Pre-Trade Risk Management Simulator.

Evaluates orders against configurable risk rules.
Designed as a pure component: given an order and risk configuration,
returns predictable validation results. No database or HTTP concerns.

All monetary calculations use Decimal for precision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.config import RiskConfig


@dataclass
class RiskCheckResult:
    """Result of a single risk-rule check.

    Attributes:
        rule_id: Identifier for the rule (e.g. "RISK-01").
        passed: Whether the rule passed.
        reason: Human-readable reason if the rule failed.
    """

    rule_id: str
    passed: bool
    reason: str = ""


@dataclass
class RiskResult:
    """Aggregated result of all risk-rule evaluations.

    Attributes:
        passed: True only if ALL rules passed.
        rejection_reasons: List of human-readable reasons for each failed rule.
        check_results: Detailed per-rule results.
    """

    passed: bool = True
    rejection_reasons: list[str] = field(default_factory=list)
    check_results: list[RiskCheckResult] = field(default_factory=list)


def check_max_order_value(
    quantity: int, price: Decimal, max_value: Decimal
) -> RiskCheckResult:
    """RISK-01: Check that order value does not exceed the maximum.

    The check is inclusive: an order worth exactly max_value passes.

    Args:
        quantity: Number of units.
        price: Price per unit.
        max_value: Maximum allowed order value.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    order_value = Decimal(quantity) * price
    if order_value > max_value:
        return RiskCheckResult(
            rule_id="RISK-01",
            passed=False,
            reason=(
                f"Order value {order_value} exceeds the maximum "
                f"allowed value of {max_value}"
            ),
        )
    return RiskCheckResult(rule_id="RISK-01", passed=True)


def check_restricted_symbol(
    symbol: str, restricted_symbols: list[str]
) -> RiskCheckResult:
    """RISK-02: Check that the symbol is not in the restricted list.

    Comparison is case-insensitive.

    Args:
        symbol: Asset ticker symbol.
        restricted_symbols: List of restricted symbols.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    restricted_upper = [s.upper() for s in restricted_symbols]
    if symbol.upper() in restricted_upper:
        return RiskCheckResult(
            rule_id="RISK-02",
            passed=False,
            reason=f"Symbol '{symbol}' is restricted from trading",
        )
    return RiskCheckResult(rule_id="RISK-02", passed=True)


def check_quantity_validity(quantity: int) -> RiskCheckResult:
    """RISK-03: Check that the quantity is a positive integer.

    Args:
        quantity: Number of units.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    if not isinstance(quantity, int) or isinstance(quantity, bool):
        return RiskCheckResult(
            rule_id="RISK-03",
            passed=False,
            reason="Quantity must be a positive integer",
        )
    if quantity <= 0:
        return RiskCheckResult(
            rule_id="RISK-03",
            passed=False,
            reason="Quantity must be a positive integer",
        )
    return RiskCheckResult(rule_id="RISK-03", passed=True)


def check_price_validity(price: Decimal) -> RiskCheckResult:
    """RISK-04: Check that the price is a positive decimal.

    Args:
        price: Price per unit.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    if not isinstance(price, Decimal):
        return RiskCheckResult(
            rule_id="RISK-04",
            passed=False,
            reason="Price must be a positive decimal",
        )
    if price <= 0:
        return RiskCheckResult(
            rule_id="RISK-04",
            passed=False,
            reason="Price must be a positive decimal",
        )
    return RiskCheckResult(rule_id="RISK-04", passed=True)


def evaluate(
    quantity: int,
    price: Decimal,
    symbol: str,
    config: RiskConfig,
) -> RiskResult:
    """Evaluate an order against all risk rules.

    All rules are evaluated (no short-circuit). If multiple rules fail,
    all applicable rejection reasons are returned.

    Args:
        quantity: Number of units.
        price: Price per unit.
        symbol: Asset ticker symbol.
        config: Risk configuration with limits and restricted symbols.

    Returns:
        RiskResult with aggregated pass/fail and all rejection reasons.
    """
    checks = [
        check_quantity_validity(quantity),
        check_price_validity(price),
        check_max_order_value(quantity, price, config.max_order_value),
        check_restricted_symbol(symbol, config.restricted_symbols),
    ]

    result = RiskResult()
    result.check_results = checks

    for check in checks:
        if not check.passed:
            result.passed = False
            result.rejection_reasons.append(check.reason)

    return result
