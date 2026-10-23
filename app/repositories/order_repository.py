"""
Order repository for the Pre-Trade Risk Management Simulator.

Handles all database operations for orders using async SQLite.
Rejection reasons and risk checks are stored as JSON text columns.
All queries use parameterized statements to prevent SQL injection.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
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
                           status, rejection_reasons, risk_checks, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            json.dumps(order.risk_checks),
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
    risk_checks: list[dict] | None = None,
) -> Order | None:
    """Update an order's status and optionally its rejection reasons and risk checks.

    Args:
        db: Active database connection.
        order_id: The order's unique identifier.
        new_status: The new status to set.
        rejection_reasons: Optional list of rejection reasons.
        risk_checks: Optional list of structured risk check results.

    Returns:
        The updated order if found, None otherwise.
    """
    fields = ["status = ?"]
    params: list = [new_status.value]

    if rejection_reasons is not None:
        fields.append("rejection_reasons = ?")
        params.append(json.dumps(rejection_reasons))

    if risk_checks is not None:
        fields.append("risk_checks = ?")
        params.append(json.dumps(risk_checks))

    params.append(order_id)
    set_clause = ", ".join(fields)

    await db.execute(
        f"UPDATE orders SET {set_clause} WHERE id = ?",
        tuple(params),
    )
    await db.commit()
    return await get_order(db, order_id)


async def get_daily_order_count(db: aiosqlite.Connection) -> int:
    """Count orders created today (UTC).

    Args:
        db: Active database connection.

    Returns:
        Number of orders placed today.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cursor = await db.execute(
        "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",
        (f"{today}%",),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def get_daily_notional(db: aiosqlite.Connection) -> Decimal:
    """Sum of all order values created today (UTC).

    Args:
        db: Active database connection.

    Returns:
        Total notional value of orders placed today.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    cursor = await db.execute(
        "SELECT COALESCE(SUM(CAST(order_value AS REAL)), 0) "
        "FROM orders WHERE created_at LIKE ?",
        (f"{today}%",),
    )
    row = await cursor.fetchone()
    return Decimal(str(row[0])) if row else Decimal("0")


async def get_order_stats(db: aiosqlite.Connection) -> dict:
    """Return aggregate statistics for the analytics dashboard.

    Args:
        db: Active database connection.

    Returns:
        Dictionary with today's and all-time statistics.
    """
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Total orders (all time).
    cursor = await db.execute("SELECT COUNT(*) FROM orders")
    total_all = (await cursor.fetchone())[0]

    # Today's orders.
    cursor = await db.execute(
        "SELECT COUNT(*) FROM orders WHERE created_at LIKE ?",
        (f"{today}%",),
    )
    total_today = (await cursor.fetchone())[0]

    # Approved today.
    cursor = await db.execute(
        "SELECT COUNT(*) FROM orders "
        "WHERE status = 'APPROVED' AND created_at LIKE ?",
        (f"{today}%",),
    )
    approved_today = (await cursor.fetchone())[0]

    # Rejected today.
    cursor = await db.execute(
        "SELECT COUNT(*) FROM orders "
        "WHERE status = 'REJECTED' AND created_at LIKE ?",
        (f"{today}%",),
    )
    rejected_today = (await cursor.fetchone())[0]

    # Today's notional value.
    cursor = await db.execute(
        "SELECT COALESCE(SUM(CAST(order_value AS REAL)), 0) "
        "FROM orders WHERE created_at LIKE ?",
        (f"{today}%",),
    )
    notional_today = Decimal(str((await cursor.fetchone())[0]))

    # All-time approved.
    cursor = await db.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'APPROVED'"
    )
    approved_all = (await cursor.fetchone())[0]

    # All-time rejected.
    cursor = await db.execute(
        "SELECT COUNT(*) FROM orders WHERE status = 'REJECTED'"
    )
    rejected_all = (await cursor.fetchone())[0]

    # All-time notional value.
    cursor = await db.execute(
        "SELECT COALESCE(SUM(CAST(order_value AS REAL)), 0) FROM orders"
    )
    notional_all = Decimal(str((await cursor.fetchone())[0]))

    # Approval rates.
    approval_rate_today = (
        round(approved_today / total_today * 100, 1)
        if total_today > 0
        else 0
    )
    approval_rate_all = (
        round(approved_all / total_all * 100, 1) if total_all > 0 else 0
    )

    # Top symbols by order count.
    cursor = await db.execute(
        "SELECT symbol, COUNT(*) as cnt FROM orders "
        "GROUP BY symbol ORDER BY cnt DESC LIMIT 5"
    )
    top_symbols = [
        {"symbol": row[0], "count": row[1]}
        for row in await cursor.fetchall()
    ]

    return {
        "today": {
            "total_orders": total_today,
            "approved": approved_today,
            "rejected": rejected_today,
            "approval_rate": approval_rate_today,
            "total_notional": str(notional_today),
        },
        "all_time": {
            "total_orders": total_all,
            "approved": approved_all,
            "rejected": rejected_all,
            "approval_rate": approval_rate_all,
            "total_notional": str(notional_all),
        },
        "top_symbols": top_symbols,
    }


def _row_to_order(row: aiosqlite.Row) -> Order:
    """Convert a database row to an Order domain object.

    Args:
        row: A database row with order columns.

    Returns:
        An Order instance.
    """
    rejection_reasons = []
    try:
        if "rejection_reasons" in row.keys() and row["rejection_reasons"]:
            rejection_reasons = json.loads(row["rejection_reasons"])
    except (IndexError, KeyError, TypeError):
        rejection_reasons = []

    risk_checks = []
    try:
        if "risk_checks" in row.keys() and row["risk_checks"]:
            risk_checks = json.loads(row["risk_checks"])
    except (IndexError, KeyError, TypeError):
        risk_checks = []

    return Order(
        id=row["id"],
        symbol=row["symbol"],
        side=OrderSide(row["side"]),
        quantity=row["quantity"],
        price=Decimal(row["price"]),
        order_value=Decimal(row["order_value"]),
        status=OrderStatus(row["status"]),
        rejection_reasons=rejection_reasons,
        risk_checks=risk_checks,
        created_at=row["created_at"],
    )
