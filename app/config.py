"""
Risk configuration for the Pre-Trade Risk Management Simulator.

Defines configurable risk limits and restricted symbols.
All monetary values use Decimal for precision.
"""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class RiskConfig:
    """Configuration for risk-rule evaluation.

    Attributes:
        max_order_value: Maximum allowed order value (quantity × price).
                         Orders at exactly this value pass RISK-01.
        restricted_symbols: List of ticker symbols that are blocked from trading.
    """

    max_order_value: Decimal = Decimal("10000.00")
    restricted_symbols: list[str] = field(
        default_factory=lambda: ["TSLA"]
    )


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
