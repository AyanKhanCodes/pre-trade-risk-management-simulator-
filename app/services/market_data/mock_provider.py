"""
Deterministic Mock Market Data Provider for local development, CI testing,
and demonstration without requiring live broker credentials.
"""

from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import AsyncGenerator

from app.models.market import Candle, FeedHealth, FeedStatus, Instrument, Quote
from app.services.market_data.provider import MarketDataProvider
from app.services.market_data.universe import NSE_TOP_20, get_instrument_by_symbol

_BASE_PRICES: dict[str, Decimal] = {
    "RELIANCE": Decimal("2945.50"),
    "TCS": Decimal("3890.00"),
    "HDFCBANK": Decimal("1652.75"),
    "INFY": Decimal("1824.20"),
    "ICICIBANK": Decimal("1240.00"),
    "HINDUNILVR": Decimal("2460.50"),
    "ITC": Decimal("485.30"),
    "SBIN": Decimal("812.40"),
    "BHARTIARTL": Decimal("1670.00"),
    "BAJFINANCE": Decimal("7150.00"),
    "L&T": Decimal("3540.00"),
    "KOTAKBANK": Decimal("1760.00"),
    "HCLTECH": Decimal("1845.50"),
    "AXISBANK": Decimal("1180.20"),
    "ASIANPAINT": Decimal("2980.00"),
    "MARUTI": Decimal("12450.00"),
    "SUNPHARMA": Decimal("1890.00"),
    "TITAN": Decimal("3420.00"),
    "TATASTEEL": Decimal("152.40"),
    "M&M": Decimal("2810.00"),
}


class MockMarketDataProvider(MarketDataProvider):
    """Provides realistic simulated Indian market data for the top 20 NSE stocks."""

    def __init__(self, tick_interval_seconds: float = 1.0) -> None:
        self.tick_interval_seconds = tick_interval_seconds
        self._running = False
        self._subscribed: set[str] = {inst.trading_symbol for inst in NSE_TOP_20}
        self._quotes: dict[str, Quote] = {}
        self._health_status: FeedStatus = FeedStatus.LIVE
        self._initialize_quotes()

    def _initialize_quotes(self) -> None:
        now = datetime.now(timezone.utc).isoformat()
        for inst in NSE_TOP_20:
            sym = inst.trading_symbol
            base = _BASE_PRICES.get(sym, Decimal("1000.00"))
            prev_close = base * Decimal("0.992")  # ~0.8% change
            change = base - prev_close
            change_pct = (change / prev_close) * Decimal("100")
            self._quotes[sym] = Quote(
                security_id=inst.security_id,
                symbol=sym,
                ltp=base,
                open=base * Decimal("0.998"),
                high=base * Decimal("1.008"),
                low=base * Decimal("0.990"),
                close=prev_close.quantize(Decimal("0.05")),
                change=change.quantize(Decimal("0.05")),
                change_pct=change_pct.quantize(Decimal("0.01")),
                volume=random.randint(150000, 2500000),
                timestamp=now,
                feed_status=self._health_status,
            )

    async def get_instruments(self) -> list[Instrument]:
        return list(NSE_TOP_20)

    async def get_quote(self, symbol: str) -> Quote | None:
        sym = symbol.strip().upper()
        if sym in self._quotes:
            return self._quotes[sym]
        inst = get_instrument_by_symbol(sym)
        if inst:
            return self._quotes.get(inst.trading_symbol)
        return None

    async def get_quotes(self) -> list[Quote]:
        return list(self._quotes.values())

    async def get_candles(
        self, symbol: str, interval: str = "1m", limit: int = 100
    ) -> list[Candle]:
        sym = symbol.strip().upper()
        base = _BASE_PRICES.get(sym, Decimal("1000.00"))
        candles: list[Candle] = []

        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        step = timedelta(minutes=1 if interval == "1m" else (5 if interval == "5m" else 1440))

        current_price = base * Decimal("0.98")
        for i in range(limit, 0, -1):
            ts = (now - (step * i)).isoformat()
            change = (Decimal(str(random.uniform(-0.004, 0.004))) * current_price).quantize(Decimal("0.05"))
            c_open = current_price
            c_close = current_price + change
            c_high = max(c_open, c_close) + (Decimal(str(random.uniform(0.0005, 0.003))) * current_price).quantize(Decimal("0.05"))
            c_low = min(c_open, c_close) - (Decimal(str(random.uniform(0.0005, 0.003))) * current_price).quantize(Decimal("0.05"))
            vol = random.randint(1000, 50000)
            candles.append(
                Candle(
                    timestamp=ts,
                    open=c_open.quantize(Decimal("0.05")),
                    high=c_high.quantize(Decimal("0.05")),
                    low=c_low.quantize(Decimal("0.05")),
                    close=c_close.quantize(Decimal("0.05")),
                    volume=vol,
                )
            )
            current_price = c_close

        return candles

    async def get_feed_health(self) -> FeedHealth:
        return FeedHealth(
            status=self._health_status,
            provider="DhanHQ Mock Provider (AEGIS Simulator)",
            subscribed_symbols_count=len(self._subscribed),
            last_heartbeat_utc=datetime.now(timezone.utc).isoformat(),
            latency_ms=1.5,
            mode="SIMULATED",
        )

    async def subscribe(self, symbols: list[str]) -> None:
        for s in symbols:
            self._subscribed.add(s.strip().upper())

    async def unsubscribe(self, symbols: list[str]) -> None:
        for s in symbols:
            self._subscribed.discard(s.strip().upper())

    def set_feed_status(self, status: FeedStatus) -> None:
        """Utility for test simulation (e.g. testing STALE/DISCONNECTED states)."""
        self._health_status = status
        for q in self._quotes.values():
            q.feed_status = status

    async def stream_quotes(self) -> AsyncGenerator[Quote, None]:
        """Generate ongoing simulated price updates for subscribed symbols."""
        self._running = True
        while self._running:
            await asyncio.sleep(self.tick_interval_seconds)
            if not self._subscribed:
                continue

            sym = random.choice(list(self._subscribed))
            if sym not in self._quotes:
                continue

            curr_quote = self._quotes[sym]
            # Random fluctuation between -0.15% and +0.15%
            pct = Decimal(str(random.uniform(-0.0015, 0.0015)))
            delta = (curr_quote.ltp * pct).quantize(Decimal("0.05"))
            new_ltp = curr_quote.ltp + delta
            new_high = max(curr_quote.high, new_ltp)
            new_low = min(curr_quote.low, new_ltp)
            change = new_ltp - curr_quote.close
            change_pct = (change / curr_quote.close) * Decimal("100")

            updated_quote = Quote(
                security_id=curr_quote.security_id,
                symbol=sym,
                ltp=new_ltp,
                open=curr_quote.open,
                high=new_high,
                low=new_low,
                close=curr_quote.close,
                change=change.quantize(Decimal("0.05")),
                change_pct=change_pct.quantize(Decimal("0.01")),
                volume=curr_quote.volume + random.randint(10, 500),
                timestamp=datetime.now(timezone.utc).isoformat(),
                feed_status=self._health_status,
            )
            self._quotes[sym] = updated_quote
            yield updated_quote

    async def start(self) -> None:
        self._running = True

    async def stop(self) -> None:
        self._running = False
