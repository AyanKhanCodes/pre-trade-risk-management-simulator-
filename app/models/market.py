"""
Market data domain models and enums for the AEGIS Indian Market-Data Workstation.
"""

from __future__ import annotations

import enum
from decimal import Decimal
from pydantic import BaseModel, Field


class ExchangeSegment(str, enum.Enum):
    """Supported exchange segments."""

    NSE_EQ = "NSE_EQ"
    BSE_EQ = "BSE_EQ"


class FeedStatus(str, enum.Enum):
    """Truthful feed freshness and connectivity status."""

    LIVE = "LIVE"
    STALE = "STALE"
    DISCONNECTED = "DISCONNECTED"
    MARKET_CLOSED = "MARKET_CLOSED"


class Instrument(BaseModel):
    """Metadata for an exchange-traded equity instrument."""

    security_id: str
    trading_symbol: str
    exchange_segment: str = ExchangeSegment.NSE_EQ.value
    company_name: str
    isin: str
    lot_size: int = 1
    tick_size: Decimal = Decimal("0.05")
    currency: str = "INR"

    model_config = {"from_attributes": True}


class Quote(BaseModel):
    """Normalized latest market quote snapshot."""

    security_id: str
    symbol: str
    ltp: Decimal
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal  # Previous day close
    change: Decimal
    change_pct: Decimal
    volume: int
    timestamp: str
    feed_status: FeedStatus = FeedStatus.LIVE

    model_config = {"from_attributes": True}


class Candle(BaseModel):
    """OHLCV candlestick bar."""

    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int

    model_config = {"from_attributes": True}


class FeedHealth(BaseModel):
    """Telemetry report for market data feed."""

    status: FeedStatus
    provider: str
    subscribed_symbols_count: int
    last_heartbeat_utc: str
    latency_ms: float = 0.0
    mode: str = "SIMULATED"  # "LIVE", "DEMO", "SIMULATED"
