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
    created_at TEXT NOT NULL
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
    """Initialize the database by creating required tables.

    Args:
        db_path: Optional path override (used for testing).
    """
    path = db_path or DATABASE_PATH
    async with aiosqlite.connect(path) as db:
        await db.execute(CREATE_ORDERS_TABLE)
        await db.commit()
