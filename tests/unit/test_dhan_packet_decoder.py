"""
Unit tests for DhanPacketDecoder (Phase 2 binary packet unpacking).
"""

from decimal import Decimal
import struct
import pytest
from app.services.market_data.dhan_provider import DhanPacketDecoder


class TestDhanPacketDecoder:
    """Verifies binary decoding of DhanHQ WebSocket packets."""

    def test_truncated_packet_returns_none(self):
        assert DhanPacketDecoder.decode(b"") is None
        assert DhanPacketDecoder.decode(b"\x00\x01\x02") is None

    def test_decode_ticker_packet(self):
        # Header (8 bytes): feed_code=2, msg_len=16, exchange_seg=1 (NSE_EQ), security_id=2885
        # Payload (8 bytes): ltp=2945.50 (float), ltt=1700000000 (uint32)
        header = struct.pack("<BBHi", 2, 16, 1, 2885)
        payload = struct.pack("<fI", 2945.50, 1700000000)
        packet = header + payload

        decoded = DhanPacketDecoder.decode(packet)
        assert decoded is not None
        assert decoded["feed_code"] == 2
        assert decoded["security_id"] == "2885"
        assert decoded["exchange_segment"] == 1
        assert decoded["ltp"] == Decimal("2945.5")
        assert "timestamp" in decoded

    def test_decode_quote_packet(self):
        # Header (8 bytes): feed_code=4, msg_len=32, exchange_seg=1, security_id=11536
        # Payload: ltp=3890.0, vol=50000, high=3920.0, low=3870.0, open=3880.0, close=3865.0
        header = struct.pack("<BBHi", 4, 32, 1, 11536)
        payload = struct.pack("<fIffff", 3890.0, 50000, 3920.0, 3870.0, 3880.0, 3865.0)
        packet = header + payload

        decoded = DhanPacketDecoder.decode(packet)
        assert decoded is not None
        assert decoded["feed_code"] == 4
        assert decoded["security_id"] == "11536"
        assert decoded["ltp"] == Decimal("3890.0")
        assert decoded["volume"] == 50000
        assert decoded["high"] == Decimal("3920.0")
        assert decoded["low"] == Decimal("3870.0")
