"""
Unit tests for order state transitions.

Verifies:
- All valid transitions succeed.
- All invalid transitions raise InvalidStateTransitionError.
- The order's status is not mutated on an invalid transition attempt.
"""

import pytest

from app.models.order import (
    InvalidStateTransitionError,
    Order,
    OrderSide,
    OrderStatus,
    validate_transition,
)
from decimal import Decimal


class TestValidateTransition:
    """Tests for the validate_transition() function."""

    # Valid transitions.
    @pytest.mark.parametrize(
        "current,target",
        [
            (OrderStatus.CREATED, OrderStatus.VALIDATING),
            (OrderStatus.VALIDATING, OrderStatus.APPROVED),
            (OrderStatus.VALIDATING, OrderStatus.REJECTED),
            (OrderStatus.APPROVED, OrderStatus.EXECUTED),
        ],
    )
    def test_valid_transitions_succeed(self, current, target):
        """All documented valid transitions should not raise."""
        validate_transition(current, target)  # Should not raise.

    # Invalid transitions (representative from project plan section 6).
    @pytest.mark.parametrize(
        "current,target",
        [
            (OrderStatus.REJECTED, OrderStatus.EXECUTED),
            (OrderStatus.CREATED, OrderStatus.EXECUTED),
            (OrderStatus.VALIDATING, OrderStatus.EXECUTED),
            (OrderStatus.EXECUTED, OrderStatus.APPROVED),
            (OrderStatus.EXECUTED, OrderStatus.EXECUTED),
            (OrderStatus.REJECTED, OrderStatus.APPROVED),
            (OrderStatus.APPROVED, OrderStatus.VALIDATING),
            (OrderStatus.APPROVED, OrderStatus.CREATED),
            (OrderStatus.CREATED, OrderStatus.APPROVED),
            (OrderStatus.CREATED, OrderStatus.REJECTED),
        ],
    )
    def test_invalid_transitions_raise(self, current, target):
        """All forbidden transitions should raise InvalidStateTransitionError."""
        with pytest.raises(InvalidStateTransitionError) as exc_info:
            validate_transition(current, target)
        assert exc_info.value.current == current
        assert exc_info.value.target == target


class TestOrderTransitionTo:
    """Tests for the Order.transition_to() method."""

    def _make_order(self, status: OrderStatus = OrderStatus.CREATED) -> Order:
        """Create a test order with the given initial status."""
        return Order(
            id="test-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            price=Decimal("100.00"),
            order_value=Decimal("1000.00"),
            status=status,
        )

    def test_valid_transition_updates_status(self):
        """A valid transition should update the order's status."""
        order = self._make_order(OrderStatus.CREATED)
        order.transition_to(OrderStatus.VALIDATING)
        assert order.status == OrderStatus.VALIDATING

    def test_invalid_transition_does_not_mutate_status(self):
        """An invalid transition should leave the order's status unchanged."""
        order = self._make_order(OrderStatus.CREATED)
        original_status = order.status
        with pytest.raises(InvalidStateTransitionError):
            order.transition_to(OrderStatus.EXECUTED)
        assert order.status == original_status

    def test_full_valid_lifecycle(self):
        """Walk through the full valid lifecycle: CREATED → VALIDATING → APPROVED."""
        order = self._make_order(OrderStatus.CREATED)
        order.transition_to(OrderStatus.VALIDATING)
        assert order.status == OrderStatus.VALIDATING
        order.transition_to(OrderStatus.APPROVED)
        assert order.status == OrderStatus.APPROVED

    def test_rejection_lifecycle(self):
        """Walk through the rejection lifecycle: CREATED → VALIDATING → REJECTED."""
        order = self._make_order(OrderStatus.CREATED)
        order.transition_to(OrderStatus.VALIDATING)
        order.transition_to(OrderStatus.REJECTED)
        assert order.status == OrderStatus.REJECTED

    def test_rejected_order_cannot_be_executed(self):
        """A rejected order must not transition to EXECUTED."""
        order = self._make_order(OrderStatus.REJECTED)
        with pytest.raises(InvalidStateTransitionError):
            order.transition_to(OrderStatus.EXECUTED)
        assert order.status == OrderStatus.REJECTED

    def test_already_executed_cannot_execute_again(self):
        """An executed order must not be executed a second time."""
        order = self._make_order(OrderStatus.EXECUTED)
        with pytest.raises(InvalidStateTransitionError):
            order.transition_to(OrderStatus.EXECUTED)
        assert order.status == OrderStatus.EXECUTED
