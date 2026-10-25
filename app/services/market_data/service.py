"""
Central Market Data Service for AEGIS Simulator.

Orchestrates the active provider (DhanHQ vs Mock), caches latest quote snapshots,
and broadcasts normalized ticks to connected browser WebSocket clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

from app.models.market import Candle, FeedHealth, Instrument, Quote
from app.services.market_data.dhan_provider import DhanHQMarketDataProvider
from app.services.market_data.mock_provider import MockMarketDataProvider
from app.services.market_data.provider import MarketDataProvider

logger = logging.getLogger("aegis.market_data")


class MarketDataService:
    """Singleton service managing market data feeds and WebSocket subscribers."""

    def __init__(self, provider: MarketDataProvider | None = None) -> None:
        if provider:
            self._provider = provider
        else:
            dhan = DhanHQMarketDataProvider()
            self._provider = dhan if dhan.is_configured else MockMarketDataProvider()

        self._active_connections: set[WebSocket] = set()
        self._streaming_task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    @property
    def provider(self) -> MarketDataProvider:
        return self._provider

    def set_provider(self, provider: MarketDataProvider) -> None:
        """Allow switching provider dynamically (e.g. for testing)."""
        self._provider = provider

    async def get_instruments(self) -> list[Instrument]:
        return await self._provider.get_instruments()

    async def get_quote(self, symbol: str) -> Quote | None:
        return await self._provider.get_quote(symbol)

    async def get_quotes(self) -> list[Quote]:
        return await self._provider.get_quotes()

    async def get_candles(
        self, symbol: str, interval: str = "1m", limit: int = 100
    ) -> list[Candle]:
        return await self._provider.get_candles(symbol, interval=interval, limit=limit)

    async def get_feed_health(self) -> FeedHealth:
        health = await self._provider.get_feed_health()
        return health

    async def connect_client(self, websocket: WebSocket) -> None:
        """Register a new frontend WebSocket subscriber."""
        await websocket.accept()
        async with self._lock:
            self._active_connections.add(websocket)

    async def disconnect_client(self, websocket: WebSocket) -> None:
        """Unregister a disconnected frontend WebSocket."""
        async with self._lock:
            self._active_connections.discard(websocket)

    async def broadcast_tick(self, quote: Quote) -> None:
        """Broadcast quote to all active WebSockets."""
        if not self._active_connections:
            return

        payload = json.dumps(
            {
                "type": "QUOTE",
                "data": {
                    "security_id": quote.security_id,
                    "symbol": quote.symbol,
                    "ltp": str(quote.ltp),
                    "open": str(quote.open),
                    "high": str(quote.high),
                    "low": str(quote.low),
                    "close": str(quote.close),
                    "change": str(quote.change),
                    "change_pct": str(quote.change_pct),
                    "volume": quote.volume,
                    "timestamp": quote.timestamp,
                    "feed_status": quote.feed_status.value,
                },
            }
        )

        dead_connections = []
        async with self._lock:
            for ws in list(self._active_connections):
                try:
                    await ws.send_text(payload)
                except Exception:
                    dead_connections.append(ws)

            for ws in dead_connections:
                self._active_connections.discard(ws)

    async def _stream_loop(self) -> None:
        """Internal background task reading ticks from provider and broadcasting."""
        try:
            async for quote in self._provider.stream_quotes():
                await self.broadcast_tick(quote)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in market data stream loop: {e}")

    async def start(self) -> None:
        """Start provider and background streaming worker."""
        await self._provider.start()
        if self._streaming_task is None or self._streaming_task.done():
            self._streaming_task = asyncio.create_task(self._stream_loop())

    async def stop(self) -> None:
        """Stop provider and cancel streaming worker."""
        if self._streaming_task:
            self._streaming_task.cancel()
            try:
                await self._streaming_task
            except asyncio.CancelledError:
                pass
            self._streaming_task = None
        await self._provider.stop()


# Global singleton instance
_market_service: MarketDataService | None = None


def get_market_data_service() -> MarketDataService:
    global _market_service
    if _market_service is None:
        _market_service = MarketDataService()
    return _market_service
