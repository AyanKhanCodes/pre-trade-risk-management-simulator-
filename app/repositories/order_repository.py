"""
Order repository for the Pre-Trade Risk Management Simulator.

Handles all database operations for orders using async SQLite.
Rejection reasons are stored as a JSON text column.
All queries use parameterized statements to prevent SQL injection.
"""

from __future__ import annotations

import json
from decimal import Decimal

import aiosqlite

from app.models.order import Order, OrderSide, OrderStatus


async def create_order(db: aiosqlite.Connection, order: Order) -> Order:
    """Insert a new order into the database.

    Args:
        db: Active database connection.
        order: The order to persist.

    Returns:
        The persisted order.
    """
    await db.execute(
        """
        INSERT INTO orders (id, symbol, side, quantity, price, order_value,
                           status, rejection_reasons, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order.id,
            order.symbol,
            order.side.value,
            order.quantity,
            str(order.price),
            str(order.order_value),
            order.status.value,
            json.dumps(order.rejection_reasons),
            order.created_at,
        ),
    )
    await db.commit()
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
    cursor = await db.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        return None
    return _row_to_order(row)


async def list_orders(db: aiosqlite.Connection) -> list[Order]:
    """Retrieve all orders, most recent first.

    Args:
        db: Active database connection.

    Returns:
        List of all orders.
    """
    cursor = await db.execute(
        "SELECT * FROM orders ORDER BY created_at DESC"
    )
    rows = await cursor.fetchall()
    return [_row_to_order(row) for row in rows]


async def update_order_status(
    db: aiosqlite.Connection,
    order_id: str,
    new_status: OrderStatus,
    rejection_reasons: list[str] | None = None,
) -> Order | None:
    """Update an order's status and optionally its rejection reasons.

    Args:
        db: Active database connection.
        order_id: The order's unique identifier.
        new_status: The new status to set.
        rejection_reasons: Optional list of rejection reasons.

    Returns:
        The updated order if found, None otherwise.
    """
    if rejection_reasons is not None:
        await db.execute(
            """
            UPDATE orders
            SET status = ?, rejection_reasons = ?
            WHERE id = ?
            """,
            (new_status.value, json.dumps(rejection_reasons), order_id),
        )
    else:
        await db.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (new_status.value, order_id),
        )
    await db.commit()
    return await get_order(db, order_id)


def _row_to_order(row: aiosqlite.Row) -> Order:
    """Convert a database row to an Order domain object.

    Args:
        row: A database row with order columns.

    Returns:
        An Order instance.
    """
    return Order(
        id=row["id"],
        symbol=row["symbol"],
        side=OrderSide(row["side"]),
        quantity=row["quantity"],
        price=Decimal(row["price"]),
        order_value=Decimal(row["order_value"]),
        status=OrderStatus(row["status"]),
        rejection_reasons=json.loads(row["rejection_reasons"]),
        created_at=row["created_at"],
    )
