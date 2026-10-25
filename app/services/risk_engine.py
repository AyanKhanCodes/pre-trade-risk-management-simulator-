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

from app.config import RULE_METADATA, RiskConfig
from app.models.order import OrderSide


@dataclass
class RiskCheckResult:
    """Result of a single risk-rule check.

    Attributes:
        rule_id: Identifier for the rule (e.g. "RISK-01").
        passed: Whether the rule passed.
        reason: Human-readable reason if the rule failed.
        rule_name: Human-readable name of the rule.
        status: Evaluation status string ("PASS", "FAIL", "NOT_APPLICABLE").
        applicable_side: Order side applicability ("BOTH", "BUY", "SELL").
    """

    rule_id: str
    passed: bool
    reason: str = ""
    rule_name: str = ""
    status: str = "PASS"
    applicable_side: str = "BOTH"

    def __post_init__(self) -> None:
        """Populate rule_name and applicable_side from metadata if not provided."""
        if self.rule_id in RULE_METADATA:
            if not self.rule_name:
                self.rule_name = RULE_METADATA[self.rule_id]["name"]
            if self.applicable_side == "BOTH" and "applicable_side" in RULE_METADATA[self.rule_id]:
                self.applicable_side = RULE_METADATA[self.rule_id]["applicable_side"]
        if not self.passed:
            self.status = "FAIL"


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


def check_min_price(
    price: Decimal, min_price: Decimal, currency_symbol: str = "₹"
) -> RiskCheckResult:
    """RISK-05: Penny stock protection.

    Rejects orders where the price per share is below the configured
    minimum threshold.

    Args:
        price: Price per unit.
        min_price: Minimum allowed price per share.
        currency_symbol: Currency symbol prefix for diagnostics.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    if price < min_price:
        return RiskCheckResult(
            rule_id="RISK-05",
            passed=False,
            reason=(
                f"Price {currency_symbol}{price} is below minimum {currency_symbol}{min_price} "
                f"(penny stock protection)"
            ),
        )
    return RiskCheckResult(rule_id="RISK-05", passed=True)


def check_max_quantity(quantity: int, max_qty: int) -> RiskCheckResult:
    """RISK-06: Maximum quantity per order.

    Args:
        quantity: Number of units.
        max_qty: Maximum allowed quantity per order.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    if quantity > max_qty:
        return RiskCheckResult(
            rule_id="RISK-06",
            passed=False,
            reason=(
                f"Quantity {quantity} exceeds maximum allowed {max_qty}"
            ),
        )
    return RiskCheckResult(rule_id="RISK-06", passed=True)


def check_max_price(
    price: Decimal, max_price: Decimal, currency_symbol: str = "₹"
) -> RiskCheckResult:
    """RISK-07: Fat-finger protection.

    Rejects orders where the price per share exceeds a reasonable
    maximum to prevent accidental trades.

    Args:
        price: Price per unit.
        max_price: Maximum allowed price per share.
        currency_symbol: Currency symbol prefix for diagnostics.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    if price > max_price:
        return RiskCheckResult(
            rule_id="RISK-07",
            passed=False,
            reason=(
                f"Price {currency_symbol}{price} exceeds maximum {currency_symbol}{max_price} "
                f"(fat-finger protection)"
            ),
        )
    return RiskCheckResult(rule_id="RISK-07", passed=True)


def check_daily_order_count(
    current_count: int, max_count: int
) -> RiskCheckResult:
    """RISK-08: Daily order count limit.

    Checks that the number of orders already placed today (before this
    new order) has not reached the daily maximum.

    Args:
        current_count: Number of orders already placed today.
        max_count: Maximum allowed orders per day.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    if current_count >= max_count:
        return RiskCheckResult(
            rule_id="RISK-08",
            passed=False,
            reason=(
                f"Daily order count {current_count} has reached the "
                f"maximum of {max_count}"
            ),
        )
    return RiskCheckResult(rule_id="RISK-08", passed=True)


def check_daily_notional(
    current_notional: Decimal,
    order_value: Decimal,
    max_notional: Decimal,
    currency_symbol: str = "$",
) -> RiskCheckResult:
    """RISK-09: Daily notional limit.

    Checks that adding this order's value to the day's running total
    would not exceed the daily maximum.

    Args:
        current_notional: Total notional value of orders already placed today.
        order_value: Value of the order being evaluated.
        max_notional: Maximum allowed daily notional value.
        currency_symbol: Currency symbol prefix for diagnostics.

    Returns:
        RiskCheckResult indicating pass or fail.
    """
    projected = current_notional + order_value
    if projected > max_notional:
        return RiskCheckResult(
            rule_id="RISK-09",
            passed=False,
            reason=(
                f"Projected daily notional {currency_symbol}{projected} would exceed "
                f"the maximum of {currency_symbol}{max_notional}"
            ),
        )
    return RiskCheckResult(rule_id="RISK-09", passed=True)


def check_available_holdings(
    side: OrderSide,
    quantity: int,
    symbol: str,
    position_context: dict | None,
) -> RiskCheckResult:
    """RISK-10: Available Holdings / Short-Selling Prohibition.

    For SELL orders: verifies that the account holds a non-zero simulated position.
    Rejects any SELL when current holdings <= 0.
    For BUY orders: marked NOT_APPLICABLE.
    """
    if side != OrderSide.SELL:
        return RiskCheckResult(
            rule_id="RISK-10",
            passed=True,
            status="NOT_APPLICABLE",
            applicable_side="SELL",
            reason="Rule applicable only to SELL orders",
        )

    if position_context is None:
        return RiskCheckResult(
            rule_id="RISK-10",
            passed=False,
            status="FAIL",
            applicable_side="SELL",
            reason=f"Cannot verify holdings for {symbol} (position data unavailable)",
        )

    held_qty = position_context.get("held_qty", 0)
    if held_qty <= 0:
        return RiskCheckResult(
            rule_id="RISK-10",
            passed=False,
            status="FAIL",
            applicable_side="SELL",
            reason=(
                f"Cannot SELL {quantity} shares of {symbol} — no existing position held "
                f"(short-selling is prohibited)"
            ),
        )

    return RiskCheckResult(
        rule_id="RISK-10",
        passed=True,
        status="PASS",
        applicable_side="SELL",
        reason=f"Position held ({held_qty} shares) satisfies holding inventory requirement",
    )


def check_sell_reservation(
    side: OrderSide,
    quantity: int,
    symbol: str,
    position_context: dict | None,
) -> RiskCheckResult:
    """RISK-11: Open Sell Order Reservation.

    For SELL orders: verifies requested quantity does not exceed the net unreserved
    sellable quantity (Held Quantity - Approved Open Sells).
    For BUY orders: marked NOT_APPLICABLE.
    """
    if side != OrderSide.SELL:
        return RiskCheckResult(
            rule_id="RISK-11",
            passed=True,
            status="NOT_APPLICABLE",
            applicable_side="SELL",
            reason="Rule applicable only to SELL orders",
        )

    if position_context is None:
        return RiskCheckResult(
            rule_id="RISK-11",
            passed=False,
            status="FAIL",
            applicable_side="SELL",
            reason=f"Cannot verify sell reservations for {symbol}",
        )

    held_qty = position_context.get("held_qty", 0)
    reserved_qty = position_context.get("reserved_qty", 0)
    sellable_qty = position_context.get("sellable_qty", 0)

    if quantity > sellable_qty:
        if reserved_qty > 0:
            reason = (
                f"Requested SELL quantity of {quantity} shares exceeds net sellable "
                f"quantity of {sellable_qty} shares ({held_qty} held, {reserved_qty} reserved by open orders)"
            )
        else:
            reason = (
                f"Requested SELL quantity of {quantity} shares exceeds total "
                f"available holdings of {held_qty} shares"
            )
        return RiskCheckResult(
            rule_id="RISK-11",
            passed=False,
            status="FAIL",
            applicable_side="SELL",
            reason=reason,
        )

    return RiskCheckResult(
        rule_id="RISK-11",
        passed=True,
        status="PASS",
        applicable_side="SELL",
        reason=f"Requested {quantity} shares within net sellable quantity of {sellable_qty} shares",
    )


def check_ledger_integrity(
    side: OrderSide,
    symbol: str,
    position_context: dict | None,
) -> RiskCheckResult:
    """RISK-12: Position Ledger Integrity & Fail-Safe.

    For SELL orders: verifies that position data is coherent and non-negative.
    For BUY orders: marked NOT_APPLICABLE.
    """
    if side != OrderSide.SELL:
        return RiskCheckResult(
            rule_id="RISK-12",
            passed=True,
            status="NOT_APPLICABLE",
            applicable_side="SELL",
            reason="Rule applicable only to SELL orders",
        )

    if position_context is None:
        return RiskCheckResult(
            rule_id="RISK-12",
            passed=False,
            status="FAIL",
            applicable_side="SELL",
            reason=f"Position ledger integrity check failed for {symbol}: missing ledger context",
        )

    held_qty = position_context.get("held_qty", 0)
    reserved_qty = position_context.get("reserved_qty", 0)
    sellable_qty = position_context.get("sellable_qty", 0)

    if held_qty < 0 or reserved_qty < 0 or sellable_qty < 0:
        return RiskCheckResult(
            rule_id="RISK-12",
            passed=False,
            status="FAIL",
            applicable_side="SELL",
            reason=f"Position ledger integrity check failed for {symbol}: negative quantity detected",
        )

    return RiskCheckResult(
        rule_id="RISK-12",
        passed=True,
        status="PASS",
        applicable_side="SELL",
        reason="Position ledger integrity verified",
    )


def evaluate(
    quantity: int,
    price: Decimal,
    symbol: str,
    config: RiskConfig,
    side: OrderSide = OrderSide.BUY,
    daily_order_count: int = 0,
    daily_notional: Decimal = Decimal("0"),
    position_context: dict | None = None,
) -> RiskResult:
    """Evaluate an order against all risk rules.

    All rules are evaluated (no short-circuit). If multiple rules fail,
    all applicable rejection reasons are returned.

    Args:
        quantity: Number of units.
        price: Price per unit.
        symbol: Asset ticker symbol.
        config: Risk configuration with limits and restricted symbols.
        side: OrderSide (BUY or SELL).
        daily_order_count: Number of orders already placed today.
        daily_notional: Total notional value of orders already placed today.
        position_context: Optional holding and reservation state for the symbol.

    Returns:
        RiskResult with aggregated pass/fail and all rejection reasons.
    """
    order_value = Decimal(quantity) * price
    curr_sym = getattr(config, "currency_symbol", "$")

    checks = [
        check_quantity_validity(quantity),
        check_price_validity(price),
        check_min_price(price, config.min_price, currency_symbol=curr_sym),
        check_max_price(price, config.max_price, currency_symbol=curr_sym),
        check_max_order_value(quantity, price, config.max_order_value),
        check_max_quantity(quantity, config.max_quantity),
        check_restricted_symbol(symbol, config.restricted_symbols),
        check_daily_order_count(daily_order_count, config.max_daily_orders),
        check_daily_notional(
            daily_notional, order_value, config.max_daily_notional, currency_symbol=curr_sym
        ),
        check_available_holdings(side, quantity, symbol, position_context),
        check_sell_reservation(side, quantity, symbol, position_context),
        check_ledger_integrity(side, symbol, position_context),
    ]

    result = RiskResult()
    result.check_results = checks

    for check in checks:
        if not check.passed:
            result.passed = False
            result.rejection_reasons.append(check.reason)

    return result
