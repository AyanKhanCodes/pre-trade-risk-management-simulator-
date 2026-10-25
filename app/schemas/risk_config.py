"""
Pydantic schemas for risk configuration request validation and response
serialization.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class RiskConfigUpdateRequest(BaseModel):
    """Schema for updating the risk configuration.

    All fields are optional; only provided fields are updated.
    """

    max_order_value: Decimal | None = None
    restricted_symbols: list[str] | None = None
    min_price: Decimal | None = None
    max_quantity: int | None = None
    max_price: Decimal | None = None
    max_daily_orders: int | None = None
    max_daily_notional: Decimal | None = None

    @field_validator("max_order_value", "min_price", "max_price", "max_daily_notional")
    @classmethod
    def decimal_must_be_positive(cls, v: Decimal | None) -> Decimal | None:
        """Validate that decimal config values are positive."""
        if v is not None and v <= 0:
            raise ValueError("Value must be a positive number")
        return v

    @field_validator("max_quantity", "max_daily_orders")
    @classmethod
    def int_must_be_positive(cls, v: int | None) -> int | None:
        """Validate that integer config values are positive."""
        if v is not None and v <= 0:
            raise ValueError("Value must be a positive integer")
        return v


class RiskConfigResponse(BaseModel):
    """Schema for returning the current risk configuration."""

    max_order_value: str
    restricted_symbols: list[str]
    min_price: str
    max_quantity: int
    max_price: str
    max_daily_orders: int
    max_daily_notional: str


class RiskRuleResponse(BaseModel):
    """Schema for a single risk rule with its metadata."""

    rule_id: str
    name: str
    description: str
    category: str
    config_key: str
    applicable_side: str = "BOTH"
    current_value: str | None = None
    enabled: bool = True


class RiskRulesListResponse(BaseModel):
    """Schema for returning all risk rules."""

    rules: list[RiskRuleResponse]
