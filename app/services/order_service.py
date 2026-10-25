"""
Order service for the Pre-Trade Risk Management Simulator.

Orchestrates order creation, risk-engine validation, and status updates.
This is the single place where the order lifecycle is managed.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from decimal import Decimal

import aiosqlite

from app.config import RiskConfig
from app.models.order import Order, OrderSide, OrderStatus
from app.repositories import order_repository
from app.services import risk_engine

# Concurrency lock to serialize order evaluations and avoid daily-limit race conditions.
_order_lock = asyncio.Lock()


async def create_and_validate_order(
    db: aiosqlite.Connection,
    symbol: str,
    side: OrderSide,
    quantity: int,
    price: Decimal,
    config: RiskConfig,
    currency: str = "USD",
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
        currency: Currency code (USD or INR).

    Returns:
        The fully evaluated order with its final status and any rejection reasons.
    """
    async with _order_lock:
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
            risk_checks=[],
            created_at=datetime.now(timezone.utc).isoformat(),
            currency=currency,
        )

        # Persist the initial CREATED order.
        await order_repository.create_order(db, order)

        # Transition to VALIDATING.
        order.transition_to(OrderStatus.VALIDATING)
        await order_repository.update_order_status(
            db, order.id, OrderStatus.VALIDATING
        )

        # Fetch daily aggregates for daily-limit risk checks.
        # Exclude the current order from the count to eliminate off-by-one bug.
        daily_order_count = await order_repository.get_daily_order_count(
            db, exclude_order_id=order.id
        )
        daily_notional = await order_repository.get_daily_notional(db)

        # Run the risk engine — all rules evaluated, no short-circuit.
        risk_result = risk_engine.evaluate(
            quantity=order.quantity,
            price=order.price,
            symbol=order.symbol,
            config=config,
            daily_order_count=daily_order_count,
            daily_notional=daily_notional,
        )

        # Store structured risk check results on the order.
        order.risk_checks = [
            {
                "rule_id": check.rule_id,
                "rule_name": check.rule_name,
                "passed": check.passed,
                "reason": check.reason,
            }
            for check in risk_result.check_results
        ]

        # Transition to APPROVED or REJECTED based on risk result.
        if risk_result.passed:
            order.transition_to(OrderStatus.APPROVED)
            await order_repository.update_order_status(
                db,
                order.id,
                OrderStatus.APPROVED,
                risk_checks=order.risk_checks,
            )
        else:
            order.rejection_reasons = risk_result.rejection_reasons
            order.transition_to(OrderStatus.REJECTED)
            await order_repository.update_order_status(
                db,
                order.id,
                OrderStatus.REJECTED,
                rejection_reasons=risk_result.rejection_reasons,
                risk_checks=order.risk_checks,
            )

        return order


async def execute_order(db: aiosqlite.Connection, order_id: str) -> Order:
    """Transition an approved order to EXECUTED.

    Args:
        db: Active database connection.
        order_id: Unique order identifier.

    Returns:
        The updated order in EXECUTED state.

    Raises:
        ValueError: If order is not found.
        InvalidStateTransitionError: If order is not in APPROVED state.
    """
    async with _order_lock:
        order = await order_repository.get_order(db, order_id)
        if order is None:
            raise ValueError(f"Order '{order_id}' not found")

        order.transition_to(OrderStatus.EXECUTED)
        await order_repository.update_order_status(
            db, order.id, OrderStatus.EXECUTED
        )

        # Settle simulated cash and positions
        from app.services import portfolio_service
        try:
            await portfolio_service.settle_order_execution(db, order)
        except Exception:
            pass

        return order


async def preview_order(
    db: aiosqlite.Connection,
    symbol: str,
    side: OrderSide,
    quantity: int,
    price: Decimal,
    config: RiskConfig,
    currency: str = "USD",
) -> dict:
    """Pure non-mutating risk evaluation of an order without inserting to database."""
    daily_order_count = await order_repository.get_daily_order_count(db)
    daily_notional = await order_repository.get_daily_notional(db)
    risk_result = risk_engine.evaluate(
        quantity=quantity,
        price=price,
        symbol=symbol,
        config=config,
        daily_order_count=daily_order_count,
        daily_notional=daily_notional,
    )
    order_value = Decimal(quantity) * price
    return {
        "symbol": symbol,
        "side": side.value,
        "quantity": quantity,
        "price": str(price),
        "order_value": str(order_value),
        "currency": currency,
        "passed": risk_result.passed,
        "rejection_reasons": risk_result.rejection_reasons,
        "risk_checks": [
            {
                "rule_id": check.rule_id,
                "rule_name": check.rule_name,
                "passed": check.passed,
                "reason": check.reason,
            }
            for check in risk_result.check_results
        ],
        "daily_order_count": daily_order_count,
        "daily_notional": str(daily_notional),
        "preview_timestamp": datetime.now(timezone.utc).isoformat(),
    }


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
