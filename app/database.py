"""
SQLite database setup for the Pre-Trade Risk Management Simulator.

Provides async database connection management and table creation.
Uses aiosqlite for async SQLite operations.
"""

import aiosqlite

DATABASE_PATH = "orders.db"

# SQL to create the orders table.
CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price TEXT NOT NULL,
    order_value TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'CREATED',
    rejection_reasons TEXT NOT NULL DEFAULT '[]',
    risk_checks TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    currency TEXT NOT NULL DEFAULT 'USD'
);

CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);

CREATE TABLE IF NOT EXISTS simulated_account (
    account_id TEXT PRIMARY KEY,
    currency TEXT NOT NULL DEFAULT 'INR',
    initial_cash TEXT NOT NULL,
    current_cash TEXT NOT NULL,
    reserved_cash TEXT NOT NULL DEFAULT '0',
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS simulated_positions (
    symbol TEXT PRIMARY KEY,
    quantity INTEGER NOT NULL,
    average_entry_price TEXT NOT NULL,
    current_market_price TEXT NOT NULL,
    unrealized_pnl TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


async def get_db() -> aiosqlite.Connection:
    """Create and return an async database connection.

    The caller is responsible for closing the connection.
    """
    db = await aiosqlite.connect(DATABASE_PATH)
    db.row_factory = aiosqlite.Row
    return db


async def init_db(db_path: str | None = None) -> None:
    """Initialize the database by creating required tables and applying migrations.

    Args:
        db_path: Optional path override (used for testing).
    """
    path = db_path or DATABASE_PATH
    async with aiosqlite.connect(path) as db:
        await db.executescript(CREATE_ORDERS_TABLE)
        # Automatic migration: ensure columns exist if database existed prior
        cursor = await db.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in await cursor.fetchall()]
        if "risk_checks" not in columns:
            await db.execute(
                "ALTER TABLE orders ADD COLUMN risk_checks TEXT NOT NULL DEFAULT '[]'"
            )
        if "currency" not in columns:
            await db.execute(
                "ALTER TABLE orders ADD COLUMN currency TEXT NOT NULL DEFAULT 'USD'"
            )
        await db.commit()
