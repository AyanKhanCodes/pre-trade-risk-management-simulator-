"""
Stock Screener Service for AEGIS Indian Market-Data Workstation.

Provides filtering over the entitled NSE universe with preliminary advisory risk evaluation.
"""

from __future__ import annotations

from decimal import Decimal
from pydantic import BaseModel

from app.config import get_risk_config
from app.models.market import FeedStatus
from app.services.market_data.service import get_market_data_service


class ScreenerStockResult(BaseModel):
    security_id: str
    symbol: str
    company_name: str
    ltp: str
    change: str
    change_pct: str
    volume: int
    feed_status: str
    timestamp: str
    preliminary_eligible: bool
    risk_flags: list[str]


class ScreenerResponse(BaseModel):
    total_screened: int
    matches_count: int
    results: list[ScreenerStockResult]


async def run_screener(
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    min_volume: int | None = None,
    min_change_pct: Decimal | None = None,
    max_change_pct: Decimal | None = None,
) -> ScreenerResponse:
    market_service = get_market_data_service()
    quotes = await market_service.get_quotes()
    instruments = await market_service.get_instruments()
    inst_map = {i.trading_symbol: i for i in instruments}
    config = get_risk_config()
    restricted_upper = [s.upper() for s in config.restricted_symbols]

    results: list[ScreenerStockResult] = []

    for q in quotes:
        # Filtering conditions
        if min_price is not None and q.ltp < min_price:
            continue
        if max_price is not None and q.ltp > max_price:
            continue
        if min_volume is not None and q.volume < min_volume:
            continue
        if min_change_pct is not None and q.change_pct < min_change_pct:
            continue
        if max_change_pct is not None and q.change_pct > max_change_pct:
            continue

        # Preliminary Advisory Risk Checks (Advisory only; distinct from final approval)
        risk_flags = []
        if q.symbol.upper() in restricted_upper:
            risk_flags.append(f"Restricted symbol ({q.symbol})")
        if q.ltp < config.min_price:
            risk_flags.append(f"Price below minimum floor ({config.min_price})")

        eligible = len(risk_flags) == 0
        inst = inst_map.get(q.symbol)
        comp_name = inst.company_name if inst else q.symbol

        results.append(
            ScreenerStockResult(
                security_id=q.security_id,
                symbol=q.symbol,
                company_name=comp_name,
                ltp=str(q.ltp),
                change=str(q.change),
                change_pct=str(q.change_pct),
                volume=q.volume,
                feed_status=q.feed_status.value,
                timestamp=q.timestamp,
                preliminary_eligible=eligible,
                risk_flags=risk_flags,
            )
        )

    return ScreenerResponse(
        total_screened=len(quotes),
        matches_count=len(results),
        results=results,
    )
