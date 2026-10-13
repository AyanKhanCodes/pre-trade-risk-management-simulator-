"""
Unit tests for order model creation and enum validation.

Tests:
- Order creation with valid data.
- OrderSide enum values.
- OrderStatus enum values.
- Default field values.
"""

from decimal import Decimal

from app.models.order import Order, OrderSide, OrderStatus


class TestOrderSide:
    """Tests for the OrderSide enum."""

    def test_buy_value(self):
        assert OrderSide.BUY.value == "BUY"

    def test_sell_value(self):
        assert OrderSide.SELL.value == "SELL"

    def test_from_string_buy(self):
        assert OrderSide("BUY") == OrderSide.BUY

    def test_from_string_sell(self):
        assert OrderSide("SELL") == OrderSide.SELL

    def test_invalid_side_raises(self):
        """An invalid side string should raise ValueError."""
        import pytest

        with pytest.raises(ValueError):
            OrderSide("HOLD")


class TestOrderStatus:
    """Tests for the OrderStatus enum."""

    def test_all_states_exist(self):
        """All documented states should be defined."""
        expected = {"CREATED", "VALIDATING", "APPROVED", "REJECTED", "EXECUTED"}
        actual = {s.value for s in OrderStatus}
        assert actual == expected

    def test_from_string(self):
        assert OrderStatus("CREATED") == OrderStatus.CREATED
        assert OrderStatus("APPROVED") == OrderStatus.APPROVED


class TestOrderCreation:
    """Tests for creating Order instances."""

    def test_create_order_with_valid_data(self):
        """An order created with valid data should have correct attributes."""
        order = Order(
            id="ord-001",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            price=Decimal("150.00"),
            order_value=Decimal("1500.00"),
        )
        assert order.id == "ord-001"
        assert order.symbol == "AAPL"
        assert order.side == OrderSide.BUY
        assert order.quantity == 10
        assert order.price == Decimal("150.00")
        assert order.order_value == Decimal("1500.00")

    def test_default_status_is_created(self):
        """Orders should default to CREATED status."""
        order = Order(
            id="ord-002",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=1,
            price=Decimal("100.00"),
            order_value=Decimal("100.00"),
        )
        assert order.status == OrderStatus.CREATED

    def test_default_rejection_reasons_is_empty(self):
        """Orders should default to empty rejection reasons."""
        order = Order(
            id="ord-003",
            symbol="AAPL",
            side=OrderSide.SELL,
            quantity=5,
            price=Decimal("200.00"),
            order_value=Decimal("1000.00"),
        )
        assert order.rejection_reasons == []

    def test_order_value_uses_decimal(self):
        """Order value should be a Decimal, not a float."""
        order = Order(
            id="ord-004",
            symbol="AAPL",
            side=OrderSide.BUY,
            quantity=10,
            price=Decimal("150.00"),
            order_value=Decimal(10) * Decimal("150.00"),
        )
        assert isinstance(order.order_value, Decimal)
        assert order.order_value == Decimal("1500.00")
