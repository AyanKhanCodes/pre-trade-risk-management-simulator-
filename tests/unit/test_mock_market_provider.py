"""
Unit tests for the MockMarketDataProvider and normalized market models (Phase 1).
"""

from decimal import Decimal
import pytest
from app.models.market import FeedStatus, Instrument, Quote, Candle
from app.services.market_data.mock_provider import MockMarketDataProvider
from app.services.market_data.universe import NSE_TOP_20, get_instrument_by_symbol, get_instrument_by_id


class TestMarketUniverse:
    """Verifies the top 20 NSE instrument universe."""

    def test_universe_has_twenty_stocks(self):
        assert len(NSE_TOP_20) == 20

    def test_get_by_symbol_case_insensitive(self):
        reliance = get_instrument_by_symbol("reliance")
        assert reliance is not None
        assert reliance.security_id == "2885"
        assert reliance.trading_symbol == "RELIANCE"

    def test_get_by_id(self):
        tcs = get_instrument_by_id("11536")
        assert tcs is not None
        assert tcs.trading_symbol == "TCS"

    def test_indian_tickers_with_special_characters(self):
        mm = get_instrument_by_symbol("M&M")
        assert mm is not None
        assert mm.trading_symbol == "M&M"
        assert mm.security_id == "2031"

        lt = get_instrument_by_symbol("L&T")
        assert lt is not None
        assert lt.trading_symbol == "L&T"


@pytest.mark.asyncio
class TestMockMarketDataProvider:
    """Verifies the top 20 NSE instrument universe."""

    def test_universe_has_twenty_stocks(self):
        assert len(NSE_TOP_20) == 20

    def test_get_by_symbol_case_insensitive(self):
        reliance = get_instrument_by_symbol("reliance")
        assert reliance is not None
        assert reliance.security_id == "2885"
        assert reliance.trading_symbol == "RELIANCE"

    def test_get_by_id(self):
        tcs = get_instrument_by_id("11536")
        assert tcs is not None
        assert tcs.trading_symbol == "TCS"

    def test_indian_tickers_with_special_characters(self):
        mm = get_instrument_by_symbol("M&M")
        assert mm is not None
        assert mm.trading_symbol == "M&M"
        assert mm.security_id == "2031"

        lt = get_instrument_by_symbol("L&T")
        assert lt is not None
        assert lt.trading_symbol == "L&T"


class TestMockMarketDataProvider:
    """Tests the provider interface, quote generation, and candles."""

    async def test_get_instruments(self):
        provider = MockMarketDataProvider()
        instruments = await provider.get_instruments()
        assert len(instruments) == 20
        assert any(i.trading_symbol == "RELIANCE" for i in instruments)

    async def test_get_quote_returns_populated_fields(self):
        provider = MockMarketDataProvider()
        quote = await provider.get_quote("INFY")
        assert quote is not None
        assert quote.symbol == "INFY"
        assert quote.ltp > Decimal("1000.00")
        assert quote.feed_status == FeedStatus.LIVE
        assert quote.volume > 0

    async def test_get_all_quotes(self):
        provider = MockMarketDataProvider()
        quotes = await provider.get_quotes()
        assert len(quotes) == 20

    async def test_get_candles_returns_requested_limit(self):
        provider = MockMarketDataProvider()
        candles = await provider.get_candles("TCS", interval="1m", limit=50)
        assert len(candles) == 50
        # Check OHLC ordering validity
        for c in candles:
            assert c.high >= c.low
            assert c.high >= c.open
            assert c.high >= c.close
            assert c.low <= c.open
            assert c.low <= c.close
            assert c.volume > 0

    async def test_feed_health(self):
        provider = MockMarketDataProvider()
        health = await provider.get_feed_health()
        assert health.status == FeedStatus.LIVE
        assert health.mode == "SIMULATED"
        assert health.subscribed_symbols_count == 20

    async def test_feed_status_toggle(self):
        provider = MockMarketDataProvider()
        provider.set_feed_status(FeedStatus.STALE)
        health = await provider.get_feed_health()
        assert health.status == FeedStatus.STALE
        quote = await provider.get_quote("SBIN")
        assert quote.feed_status == FeedStatus.STALE
