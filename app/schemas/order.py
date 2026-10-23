"""
Pydantic schemas for order request validation and response serialization.

Uses Decimal for price to avoid floating-point precision issues.
"""

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


class OrderCreateRequest(BaseModel):
    """Schema for creating a new order.

    Attributes:
        symbol: Asset ticker symbol (e.g. "AAPL"). Must be non-empty.
        side: BUY or SELL.
        quantity: Number of units. Must be a positive integer.
        price: Price per unit as a decimal string (e.g. "150.00").
    """

    symbol: Annotated[str, Field(min_length=1, max_length=10)]
    side: OrderSide
    quantity: int
    price: Decimal

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
    def symbol_must_be_alphanumeric(cls, v: str) -> str:
        """Validate that symbol contains only uppercase letters and digits."""
        v = v.strip().upper()
        if not v.isalnum():
            raise ValueError(
                "Symbol must contain only letters and digits"
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

    model_config = {"from_attributes": True}


class OrderListResponse(BaseModel):
    """Schema for returning a list of orders."""

    orders: list[OrderResponse]
    total: int
