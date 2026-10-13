"""
Order domain models and state machine for the Pre-Trade Risk Management Simulator.

Contains the Order model, enums for status and side, and the centralized
state-transition logic. All state-transition validation lives here.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


class OrderSide(str, enum.Enum):
    """Valid order sides."""

    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    """Order lifecycle states.

    Valid transitions:
        CREATED -> VALIDATING
        VALIDATING -> APPROVED
        VALIDATING -> REJECTED
        APPROVED -> EXECUTED
    """

    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXECUTED = "EXECUTED"


# Centralized transition table: maps each state to the set of states it can move to.
VALID_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.CREATED: {OrderStatus.VALIDATING},
    OrderStatus.VALIDATING: {OrderStatus.APPROVED, OrderStatus.REJECTED},
    OrderStatus.APPROVED: {OrderStatus.EXECUTED},
    OrderStatus.REJECTED: set(),
    OrderStatus.EXECUTED: set(),
}


class InvalidStateTransitionError(Exception):
    """Raised when an order attempts a forbidden state transition."""

    def __init__(self, current: OrderStatus, target: OrderStatus) -> None:
        self.current = current
        self.target = target
        super().__init__(
            f"Invalid state transition: {current.value} -> {target.value}"
        )


def validate_transition(current: OrderStatus, target: OrderStatus) -> None:
    """Check that the transition from current to target is allowed.

    Raises:
        InvalidStateTransitionError: If the transition is not in VALID_TRANSITIONS.
    """
    allowed = VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current, target)


@dataclass
class Order:
    """Domain model for a trading order.

    Attributes:
        id: Unique order identifier (assigned by the system).
        symbol: Asset ticker symbol (e.g. "AAPL").
        side: BUY or SELL.
        quantity: Number of units (positive integer).
        price: Price per unit (positive Decimal).
        order_value: Computed as quantity × price.
        status: Current lifecycle state.
        rejection_reasons: List of reasons if the order was rejected.
        created_at: Timestamp when the order was created.
    """

    id: str
    symbol: str
    side: OrderSide
    quantity: int
    price: Decimal
    order_value: Decimal
    status: OrderStatus = OrderStatus.CREATED
    rejection_reasons: list[str] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def transition_to(self, new_status: OrderStatus) -> None:
        """Transition this order to a new status.

        Validates the transition before applying it.

        Raises:
            InvalidStateTransitionError: If the transition is not allowed.
        """
        validate_transition(self.status, new_status)
        self.status = new_status
