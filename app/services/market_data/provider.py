"""
Abstract base class interface for Market Data Providers in AEGIS.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Callable

from app.models.market import Candle, FeedHealth, Instrument, Quote


class MarketDataProvider(ABC):
    """Interface for streaming and historical market data feeds."""

    @abstractmethod
    async def get_instruments(self) -> list[Instrument]:
        """Return list of entitled/supported instruments."""
        pass

    @abstractmethod
    async def get_quote(self, symbol: str) -> Quote | None:
        """Fetch latest quote snapshot for a symbol."""
        pass

    @abstractmethod
    async def get_quotes(self) -> list[Quote]:
        """Fetch all latest quotes for the configured watchlist."""
        pass

    @abstractmethod
    async def get_candles(
        self, symbol: str, interval: str = "1m", limit: int = 100
    ) -> list[Candle]:
        """Fetch historical candlestick bars for a symbol."""
        pass

    @abstractmethod
    async def get_feed_health(self) -> FeedHealth:
        """Return current connection and health telemetry."""
        pass

    @abstractmethod
    async def subscribe(self, symbols: list[str]) -> None:
        """Subscribe to live updates for symbols."""
        pass

    @abstractmethod
    async def unsubscribe(self, symbols: list[str]) -> None:
        """Unsubscribe from live updates."""
        pass

    @abstractmethod
    async def stream_quotes(self) -> AsyncGenerator[Quote, None]:
        """Asynchronously yield live quote ticks."""
        pass

    @abstractmethod
    async def start(self) -> None:
        """Start the provider connection/tasks."""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Gracefully shut down provider connections."""
        pass
