"""
Order service for the Pre-Trade Risk Management Simulator.

Orchestrates order creation, risk-engine validation, and status updates.
This is the single place where the order lifecycle is managed.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import aiosqlite

from app.config import RiskConfig
from app.models.order import Order, OrderSide, OrderStatus
from app.repositories import order_repository
from app.services import risk_engine


async def create_and_validate_order(
    db: aiosqlite.Connection,
    symbol: str,
    side: OrderSide,
    quantity: int,
    price: Decimal,
    config: RiskConfig,
) -> Order:
    """Create an order, run it through the risk engine, and persist the result.

    The order goes through these transitions in a single call:
        CREATED -> VALIDATING -> APPROVED (or REJECTED)

    Args:
        db: Active database connection.
        symbol: Asset ticker symbol.
        side: BUY or SELL.
        quantity: Number of units.
        price: Price per unit.
        config: Risk configuration with limits and restrictions.

    Returns:
        The fully evaluated order with its final status and any rejection reasons.
    """
    # Calculate order value using Decimal arithmetic.
    order_value = Decimal(quantity) * price

    # Create the order in CREATED state.
    order = Order(
        id=str(uuid.uuid4()),
        symbol=symbol,
        side=side,
        quantity=quantity,
        price=price,
        order_value=order_value,
        status=OrderStatus.CREATED,
        rejection_reasons=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    # Persist the initial CREATED order.
    await order_repository.create_order(db, order)

    # Transition to VALIDATING.
    order.transition_to(OrderStatus.VALIDATING)
    await order_repository.update_order_status(
        db, order.id, OrderStatus.VALIDATING
    )

    # Run the risk engine — all rules evaluated, no short-circuit.
    risk_result = risk_engine.evaluate(
        quantity=order.quantity,
        price=order.price,
        symbol=order.symbol,
        config=config,
    )

    # Transition to APPROVED or REJECTED based on risk result.
    if risk_result.passed:
        order.transition_to(OrderStatus.APPROVED)
        await order_repository.update_order_status(
            db, order.id, OrderStatus.APPROVED
        )
    else:
        order.rejection_reasons = risk_result.rejection_reasons
        order.transition_to(OrderStatus.REJECTED)
        await order_repository.update_order_status(
            db,
            order.id,
            OrderStatus.REJECTED,
            rejection_reasons=risk_result.rejection_reasons,
        )

    return order


async def get_order(
    db: aiosqlite.Connection, order_id: str
) -> Order | None:
    """Retrieve a single order by ID.

    Args:
        db: Active database connection.
        order_id: The order's unique identifier.

    Returns:
        The order if found, None otherwise.
    """
    return await order_repository.get_order(db, order_id)


async def list_orders(db: aiosqlite.Connection) -> list[Order]:
    """Retrieve all orders, most recent first.

    Args:
        db: Active database connection.

    Returns:
        List of all orders.
    """
    return await order_repository.list_orders(db)
