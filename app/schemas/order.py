"""
Pydantic schemas for order request validation and response serialization.

Uses Decimal for price to avoid floating-point precision issues.
"""

import re
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

from app.models.order import OrderSide


class RiskCheckResponse(BaseModel):
    """Schema for a single risk check result in the order response."""

    rule_id: str
    rule_name: str
    passed: bool
    reason: str
    status: str = "PASS"
    applicable_side: str = "BOTH"


class OrderCreateRequest(BaseModel):
    """Schema for creating a new order.

    Attributes:
        symbol: Asset ticker symbol (e.g. "AAPL", "M&M", "RELIANCE"). Must be non-empty.
        side: BUY or SELL.
        quantity: Number of units. Must be a positive integer.
        price: Price per unit as a decimal string (e.g. "150.00").
        currency: Currency code (USD or INR).
    """

    symbol: Annotated[str, Field(min_length=1, max_length=15)]
    side: OrderSide
    quantity: int
    price: Decimal
    currency: str = Field(default="INR", pattern="^(INR|USD)$")

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v: int) -> int:
        """Validate that quantity is a positive integer."""
        if v <= 0:
            raise ValueError("Quantity must be a positive integer")
        return v

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: Decimal) -> Decimal:
        """Validate that price is a positive decimal."""
        if v <= 0:
            raise ValueError("Price must be a positive decimal")
        return v

    @field_validator("symbol")
    @classmethod
    def symbol_must_be_valid(cls, v: str) -> str:
        """Validate that symbol contains only uppercase letters, digits, '&', and '-'."""
        v = v.strip().upper()
        if not re.match(r"^[A-Z0-9&-]{1,15}$", v):
            raise ValueError(
                "Symbol must contain only letters, digits, '&', and '-'"
            )
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "AAPL",
                    "side": "BUY",
                    "quantity": 10,
                    "price": "150.00",
                    "currency": "USD",
                }
            ]
        }
    }


class OrderResponse(BaseModel):
    """Schema for returning order data in API responses."""

    order_id: str
    symbol: str
    side: str
    quantity: int
    price: str
    order_value: str
    status: str
    rejection_reasons: list[str]
    risk_checks: list[RiskCheckResponse]
    created_at: str
    currency: str = "USD"

    model_config = {"from_attributes": True}


class OrderPreviewResponse(BaseModel):
    """Schema for returning non-mutating order preview evaluation."""

    symbol: str
    side: str
    quantity: int
    price: str
    order_value: str
    currency: str
    passed: bool
    rejection_reasons: list[str]
    risk_checks: list[RiskCheckResponse]
    daily_order_count: int
    daily_notional: str
    held_quantity: int = 0
    reserved_quantity: int = 0
    sellable_quantity: int = 0
    preview_timestamp: str


class OrderListResponse(BaseModel):
    """Schema for returning a list of orders."""

    orders: list[OrderResponse]
    total: int
