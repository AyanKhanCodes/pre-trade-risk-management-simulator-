"""
Risk configuration for the Pre-Trade Risk Management Simulator.

Defines configurable risk limits and restricted symbols.
All monetary values use Decimal for precision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class RiskConfig:
    """Configuration for risk-rule evaluation.

    Attributes:
        max_order_value: Maximum allowed order value (quantity × price).
                         Orders at exactly this value pass RISK-01.
        restricted_symbols: List of ticker symbols that are blocked from trading.
        min_price: Minimum allowed price per share (penny stock protection).
        max_quantity: Maximum allowed quantity per order.
        max_price: Maximum allowed price per share (fat-finger protection).
        max_daily_orders: Maximum number of orders allowed per day.
        max_daily_notional: Maximum total notional value allowed per day.
    """

    max_order_value: Decimal = Decimal("10000.00")
    restricted_symbols: list[str] = field(
        default_factory=lambda: ["TSLA", "GME", "AMC"]
    )
    min_price: Decimal = Decimal("1.00")
    max_quantity: int = 10000
    max_price: Decimal = Decimal("50000.00")
    max_daily_orders: int = 50
    max_daily_notional: Decimal = Decimal("500000.00")


# Human-readable metadata for each risk rule, consumed by the UI.
RULE_METADATA: dict[str, dict[str, str]] = {
    "RISK-01": {
        "name": "Maximum Order Value",
        "description": (
            "Single order value (quantity × price) must not exceed the "
            "configured maximum."
        ),
        "category": "Position Limits",
        "config_key": "max_order_value",
    },
    "RISK-02": {
        "name": "Restricted Symbol",
        "description": (
            "Certain symbols are blocked from trading due to compliance "
            "or volatility concerns."
        ),
        "category": "Compliance",
        "config_key": "restricted_symbols",
    },
    "RISK-03": {
        "name": "Quantity Validity",
        "description": "Order quantity must be a positive integer.",
        "category": "Input Validation",
        "config_key": "",
    },
    "RISK-04": {
        "name": "Price Validity",
        "description": "Price must be a positive number.",
        "category": "Input Validation",
        "config_key": "",
    },
    "RISK-05": {
        "name": "Minimum Price (Penny Stock Protection)",
        "description": (
            "Rejects orders with a price below the minimum threshold to "
            "prevent penny stock trades."
        ),
        "category": "Price Controls",
        "config_key": "min_price",
    },
    "RISK-06": {
        "name": "Maximum Quantity",
        "description": (
            "Single order quantity must not exceed the configured maximum "
            "to control position size."
        ),
        "category": "Position Limits",
        "config_key": "max_quantity",
    },
    "RISK-07": {
        "name": "Maximum Price (Fat Finger Protection)",
        "description": (
            "Rejects orders with an unreasonably high price to prevent "
            "accidental trades."
        ),
        "category": "Price Controls",
        "config_key": "max_price",
    },
    "RISK-08": {
        "name": "Daily Order Count Limit",
        "description": (
            "Total number of orders placed today must not exceed the "
            "configured daily maximum."
        ),
        "category": "Activity Limits",
        "config_key": "max_daily_orders",
    },
    "RISK-09": {
        "name": "Daily Notional Limit",
        "description": (
            "Total notional value of all orders placed today must not "
            "exceed the configured daily maximum."
        ),
        "category": "Activity Limits",
        "config_key": "max_daily_notional",
    },
}


# Global default configuration.
# Tests can override by creating a new RiskConfig instance.
_default_config: RiskConfig | None = None


def get_risk_config() -> RiskConfig:
    """Return the current risk configuration, creating defaults if needed."""
    global _default_config
    if _default_config is None:
        _default_config = RiskConfig()
    return _default_config


def set_risk_config(config: RiskConfig) -> None:
    """Replace the global risk configuration (useful for testing)."""
    global _default_config
    _default_config = config
