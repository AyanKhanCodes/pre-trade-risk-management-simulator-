"""
Simulated Portfolio and Positions Management Service for AEGIS.

Settles executed simulated orders, calculates mark-to-market unrealized P&L,
and provides portfolio exposure analytics.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import aiosqlite
from pydantic import BaseModel

from app.models.order import Order, OrderSide, OrderStatus
from app.services.market_data.service import get_market_data_service

DEFAULT_ACCOUNT_ID = "default_sim_account"
INITIAL_CASH_INR = Decimal("1000000.00")  # ₹10 Lakhs


class PositionResponse(BaseModel):
    symbol: str
    quantity: int
    reserved_quantity: int = 0
    sellable_quantity: int = 0
    average_entry_price: str
    current_market_price: str
    market_value: str
    unrealized_pnl: str
    unrealized_pnl_pct: str
    updated_at: str


class PortfolioSummaryResponse(BaseModel):
    account_id: str
    currency: str
    cash_balance: str
    portfolio_value: str
    total_unrealized_pnl: str
    open_positions_count: int
    updated_at: str


async def ensure_account_exists(db: aiosqlite.Connection) -> None:
    """Initialize simulated trading account if not already created."""
    cursor = await db.execute(
        "SELECT * FROM simulated_account WHERE account_id = ?",
        (DEFAULT_ACCOUNT_ID,),
    )
    row = await cursor.fetchone()
    if row is None:
        now = datetime.now(timezone.utc).isoformat()
        await db.execute(
            """
            INSERT INTO simulated_account (account_id, currency, initial_cash, current_cash, reserved_cash, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                DEFAULT_ACCOUNT_ID,
                "INR",
                str(INITIAL_CASH_INR),
                str(INITIAL_CASH_INR),
                "0.00",
                now,
            ),
        )
        await db.commit()


async def settle_order_execution(db: aiosqlite.Connection, order: Order) -> None:
    """Settle an executed simulated order against cash and positions."""
    await ensure_account_exists(db)
    now = datetime.now(timezone.utc).isoformat()

    # Get current cash
    cursor = await db.execute(
        "SELECT current_cash FROM simulated_account WHERE account_id = ?",
        (DEFAULT_ACCOUNT_ID,),
    )
    row = await cursor.fetchone()
    current_cash = Decimal(row[0])

    # Get existing position for symbol
    cursor = await db.execute(
        "SELECT quantity, average_entry_price FROM simulated_positions WHERE symbol = ?",
        (order.symbol,),
    )
    pos_row = await cursor.fetchone()
    pos_qty = int(pos_row[0]) if pos_row else 0
    pos_avg_price = Decimal(pos_row[1]) if pos_row else Decimal("0.00")

    if order.side == OrderSide.BUY:
        # Deduct cash
        new_cash = current_cash - order.order_value
        await db.execute(
            "UPDATE simulated_account SET current_cash = ?, updated_at = ? WHERE account_id = ?",
            (str(new_cash), now, DEFAULT_ACCOUNT_ID),
        )

        # Update position
        new_qty = pos_qty + order.quantity
        new_avg = (
            ((Decimal(pos_qty) * pos_avg_price) + (Decimal(order.quantity) * order.price))
            / Decimal(new_qty)
        ).quantize(Decimal("0.05"))

        await db.execute(
            """
            INSERT INTO simulated_positions (symbol, quantity, average_entry_price, current_market_price, unrealized_pnl, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                quantity = excluded.quantity,
                average_entry_price = excluded.average_entry_price,
                updated_at = excluded.updated_at
            """,
            (order.symbol, new_qty, str(new_avg), str(order.price), "0.00", now),
        )

    elif order.side == OrderSide.SELL:
        # Add cash
        new_cash = current_cash + order.order_value
        await db.execute(
            "UPDATE simulated_account SET current_cash = ?, updated_at = ? WHERE account_id = ?",
            (str(new_cash), now, DEFAULT_ACCOUNT_ID),
        )

        # Decrement position
        new_qty = max(0, pos_qty - order.quantity)
        if new_qty == 0:
            await db.execute(
                "DELETE FROM simulated_positions WHERE symbol = ?",
                (order.symbol,),
            )
        else:
            await db.execute(
                "UPDATE simulated_positions SET quantity = ?, updated_at = ? WHERE symbol = ?",
                (new_qty, now, order.symbol),
            )

    await db.commit()


async def get_position_and_sellable_quantity(
    db: aiosqlite.Connection, symbol: str, exclude_order_id: str | None = None
) -> dict:
    """Retrieve held quantity, reserved sell quantity, and net sellable quantity for a symbol.

    Args:
        db: Active database connection.
        symbol: The ticker symbol to check.
        exclude_order_id: Optional order ID to exclude from reservations.

    Returns:
        Dict with keys: symbol, held_qty, reserved_qty, sellable_qty.
    """
    clean_sym = symbol.strip().upper()

    # 1. Held quantity from simulated_positions
    cursor = await db.execute(
        "SELECT quantity FROM simulated_positions WHERE symbol = ?",
        (clean_sym,),
    )
    pos_row = await cursor.fetchone()
    held_qty = int(pos_row[0]) if pos_row else 0

    # 2. Open approved sell reservations from orders table
    if exclude_order_id:
        res_cursor = await db.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) FROM orders 
            WHERE symbol = ? AND side = 'SELL' AND status = 'APPROVED' AND id != ?
            """,
            (clean_sym, exclude_order_id),
        )
    else:
        res_cursor = await db.execute(
            """
            SELECT COALESCE(SUM(quantity), 0) FROM orders 
            WHERE symbol = ? AND side = 'SELL' AND status = 'APPROVED'
            """,
            (clean_sym,),
        )
    res_row = await res_cursor.fetchone()
    reserved_qty = int(res_row[0]) if res_row else 0

    sellable_qty = max(0, held_qty - reserved_qty)
    return {
        "symbol": clean_sym,
        "held_qty": held_qty,
        "reserved_qty": reserved_qty,
        "sellable_qty": sellable_qty,
    }


async def get_positions(db: aiosqlite.Connection) -> list[PositionResponse]:
    """Retrieve simulated positions with mark-to-market prices, reservations, and P&L."""
    cursor = await db.execute("SELECT symbol, quantity, average_entry_price, updated_at FROM simulated_positions")
    rows = await cursor.fetchall()
    market_service = get_market_data_service()

    positions: list[PositionResponse] = []
    for row in rows:
        sym = row[0]
        qty = int(row[1])
        avg_price = Decimal(row[2])
        updated_at = row[3]

        pos_info = await get_position_and_sellable_quantity(db, sym)
        reserved = pos_info["reserved_qty"]
        sellable = pos_info["sellable_qty"]

        quote = await market_service.get_quote(sym)
        ltp = quote.ltp if quote else avg_price
        market_val = (Decimal(qty) * ltp).quantize(Decimal("0.05"))
        pnl = (market_val - (Decimal(qty) * avg_price)).quantize(Decimal("0.05"))
        cost_basis = Decimal(qty) * avg_price
        pnl_pct = (
            ((pnl / cost_basis) * Decimal("100")).quantize(Decimal("0.01"))
            if cost_basis > 0
            else Decimal("0.00")
        )

        positions.append(
            PositionResponse(
                symbol=sym,
                quantity=qty,
                reserved_quantity=reserved,
                sellable_quantity=sellable,
                average_entry_price=str(avg_price),
                current_market_price=str(ltp),
                market_value=str(market_val),
                unrealized_pnl=str(pnl),
                unrealized_pnl_pct=str(pnl_pct),
                updated_at=updated_at,
            )
        )
    return positions


async def get_portfolio_summary(db: aiosqlite.Connection) -> PortfolioSummaryResponse:
    """Retrieve aggregate cash, portfolio valuation, and unrealized P&L."""
    await ensure_account_exists(db)
    cursor = await db.execute(
        "SELECT current_cash, currency FROM simulated_account WHERE account_id = ?",
        (DEFAULT_ACCOUNT_ID,),
    )
    row = await cursor.fetchone()
    cash = Decimal(row[0])
    currency = row[1]

    positions = await get_positions(db)
    total_positions_val = sum(
        (Decimal(p.market_value) for p in positions), Decimal("0.00")
    )
    total_unrealized_pnl = sum(
        (Decimal(p.unrealized_pnl) for p in positions), Decimal("0.00")
    )
    total_portfolio_val = (cash + total_positions_val).quantize(Decimal("0.05"))

    return PortfolioSummaryResponse(
        account_id=DEFAULT_ACCOUNT_ID,
        currency=currency,
        cash_balance=str(cash.quantize(Decimal("0.05"))),
        portfolio_value=str(total_portfolio_val),
        total_unrealized_pnl=str(total_unrealized_pnl),
        open_positions_count=len(positions),
        updated_at=datetime.now(timezone.utc).isoformat(),
    )
