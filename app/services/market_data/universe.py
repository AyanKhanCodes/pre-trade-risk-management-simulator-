"""
Bounded universe of top 20 liquid NSE cash equities for AEGIS Simulator (Nifty 50 subset).
"""

from decimal import Decimal
from app.models.market import Instrument

NSE_TOP_20: list[Instrument] = [
    Instrument(
        security_id="2885",
        trading_symbol="RELIANCE",
        company_name="Reliance Industries Limited",
        isin="INE002A01018",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="11536",
        trading_symbol="TCS",
        company_name="Tata Consultancy Services Ltd",
        isin="INE467B01029",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="1333",
        trading_symbol="HDFCBANK",
        company_name="HDFC Bank Limited",
        isin="INE040A01034",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="1594",
        trading_symbol="INFY",
        company_name="Infosys Limited",
        isin="INE009A01021",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="4963",
        trading_symbol="ICICIBANK",
        company_name="ICICI Bank Limited",
        isin="INE090A01021",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="1394",
        trading_symbol="HINDUNILVR",
        company_name="Hindustan Unilever Ltd",
        isin="INE030A01027",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="1660",
        trading_symbol="ITC",
        company_name="ITC Limited",
        isin="INE154A01025",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="3045",
        trading_symbol="SBIN",
        company_name="State Bank of India",
        isin="INE062A01020",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="10604",
        trading_symbol="BHARTIARTL",
        company_name="Bharti Airtel Limited",
        isin="INE397D01024",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="317",
        trading_symbol="BAJFINANCE",
        company_name="Bajaj Finance Limited",
        isin="INE296A01024",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="11483",
        trading_symbol="L&T",
        company_name="Larsen & Toubro Ltd",
        isin="INE018A01030",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="1922",
        trading_symbol="KOTAKBANK",
        company_name="Kotak Mahindra Bank Ltd",
        isin="INE237A01028",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="7229",
        trading_symbol="HCLTECH",
        company_name="HCL Technologies Ltd",
        isin="INE860A01027",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="5900",
        trading_symbol="AXISBANK",
        company_name="Axis Bank Limited",
        isin="INE238A01034",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="236",
        trading_symbol="ASIANPAINT",
        company_name="Asian Paints Limited",
        isin="INE021A01026",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="10999",
        trading_symbol="MARUTI",
        company_name="Maruti Suzuki India Limited",
        isin="INE585B01010",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="3351",
        trading_symbol="SUNPHARMA",
        company_name="Sun Pharmaceutical Industries Ltd",
        isin="INE044A01036",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="3506",
        trading_symbol="TITAN",
        company_name="Titan Company Limited",
        isin="INE280A01028",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="3499",
        trading_symbol="TATASTEEL",
        company_name="Tata Steel Limited",
        isin="INE081A01020",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
    Instrument(
        security_id="2031",
        trading_symbol="M&M",
        company_name="Mahindra & Mahindra Ltd",
        isin="INE101A01026",
        tick_size=Decimal("0.05"),
        lot_size=1,
    ),
]

_SYMBOL_TO_INSTRUMENT: dict[str, Instrument] = {
    inst.trading_symbol.upper(): inst for inst in NSE_TOP_20
}
_ID_TO_INSTRUMENT: dict[str, Instrument] = {
    inst.security_id: inst for inst in NSE_TOP_20
}


def get_instrument_by_symbol(symbol: str) -> Instrument | None:
    """Look up instrument by trading symbol (case-insensitive)."""
    return _SYMBOL_TO_INSTRUMENT.get(symbol.strip().upper())


def get_instrument_by_id(security_id: str) -> Instrument | None:
    """Look up instrument by security ID."""
    return _ID_TO_INSTRUMENT.get(security_id.strip())
