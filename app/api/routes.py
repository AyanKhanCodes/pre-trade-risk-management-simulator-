"""
API routes for the Pre-Trade Risk Management Simulator.

Defines REST endpoints for order submission, retrieval, risk configuration,
and analytics. Routes are thin — they parse requests, call services, and
return HTTP responses.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import APIRouter, HTTPException

from app.config import RULE_METADATA, get_risk_config, set_risk_config, RiskConfig
from app.database import get_db
from app.models.market import Candle, FeedHealth, Instrument, Quote
from app.models.order import InvalidStateTransitionError, OrderStatus
from app.repositories import order_repository
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
    OrderPreviewResponse,
    OrderResponse,
    RiskCheckResponse,
)
from app.schemas.risk_config import (
    RiskConfigResponse,
    RiskConfigUpdateRequest,
    RiskRuleResponse,
    RiskRulesListResponse,
)
from app.services import order_service
from app.services.market_data.service import get_market_data_service
from app.services.portfolio_service import (
    PortfolioSummaryResponse,
    PositionResponse,
    get_portfolio_summary,
    get_positions,
    get_position_and_sellable_quantity,
)
from app.services.screener_service import ScreenerResponse, run_screener

router = APIRouter()


def _order_to_response(order) -> OrderResponse:
    """Convert an Order domain object to an OrderResponse schema."""
    return OrderResponse(
        order_id=order.id,
        symbol=order.symbol,
        side=order.side.value,
        quantity=order.quantity,
        price=str(order.price),
        order_value=str(order.order_value),
        status=order.status.value,
        rejection_reasons=order.rejection_reasons,
        risk_checks=[
            RiskCheckResponse(**check) for check in order.risk_checks
        ],
        created_at=order.created_at,
        currency=getattr(order, "currency", "INR"),
    )


# ---------------------------------------------------------------------------
# Order endpoints
# ---------------------------------------------------------------------------


@router.post("/orders", response_model=OrderResponse, status_code=201)
async def create_order(request: OrderCreateRequest):
    """Create and evaluate a new order.

    The order is created, validated against all risk rules, and persisted
    with its final status (APPROVED or REJECTED).

    A risk-rejected order still returns 201 — risk rejection is a business
    outcome, not an HTTP error. Input validation failures return 422.
    """
    config = get_risk_config(currency=request.currency)
    db = await get_db()
    try:
        order = await order_service.create_and_validate_order(
            db=db,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            config=config,
            currency=request.currency,
        )
        return _order_to_response(order)
    finally:
        await db.close()


@router.post("/orders/preview", response_model=OrderPreviewResponse)
async def preview_order(request: OrderCreateRequest):
    """Pure non-mutating pre-trade risk evaluation.

    Evaluates all 9 risk gates in memory without writing to the database or altering daily counters.
    """
    config = get_risk_config(currency=request.currency)
    db = await get_db()
    try:
        preview_data = await order_service.preview_order(
            db=db,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            config=config,
            currency=request.currency,
        )
        return OrderPreviewResponse(**preview_data)
    finally:
        await db.close()


@router.post("/orders/{order_id}/execute", response_model=OrderResponse)
async def execute_order(order_id: str):
    """Transition an approved order to executed (simulated execution).

    Raises:
        404 if order not found.
        400 if order is rejected or in an invalid state for execution.
        409 if order is already executed.
    """
    db = await get_db()
    try:
        existing = await order_service.get_order(db, order_id)
        if existing is None:
            raise HTTPException(
                status_code=404, detail=f"Order '{order_id}' not found"
            )
        if existing.status == OrderStatus.EXECUTED:
            raise HTTPException(
                status_code=409, detail=f"Order '{order_id}' is already EXECUTED"
            )
        if existing.status == OrderStatus.REJECTED:
            raise HTTPException(
                status_code=400, detail="Cannot execute a REJECTED order"
            )
        if existing.status != OrderStatus.APPROVED:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot execute order in state '{existing.status.value}'",
            )

        executed = await order_service.execute_order(db, order_id)
        return _order_to_response(executed)
    except InvalidStateTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        await db.close()


@router.get("/orders", response_model=OrderListResponse)
async def list_orders():
    """List all orders, most recent first."""
    db = await get_db()
    try:
        orders = await order_service.list_orders(db)
        return OrderListResponse(
            orders=[_order_to_response(o) for o in orders],
            total=len(orders),
        )
    finally:
        await db.close()


@router.get("/orders/stats/summary")
async def get_order_stats():
    """Return aggregate order statistics for the analytics dashboard."""
    db = await get_db()
    try:
        stats = await order_repository.get_order_stats(db)
        return stats
    finally:
        await db.close()


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """Retrieve a single order by ID.

    Returns 404 if the order is not found.
    """
    db = await get_db()
    try:
        order = await order_service.get_order(db, order_id)
        if order is None:
            raise HTTPException(status_code=404, detail="Order not found")
        return _order_to_response(order)
    finally:
        await db.close()


# ---------------------------------------------------------------------------
# Risk configuration endpoints
# ---------------------------------------------------------------------------


@router.get("/risk-config", response_model=RiskConfigResponse)
async def get_risk_configuration(currency: str = "INR"):
    """Return the current risk configuration."""
    config = get_risk_config(currency=currency)
    return RiskConfigResponse(
        max_order_value=str(config.max_order_value),
        restricted_symbols=config.restricted_symbols,
        min_price=str(config.min_price),
        max_quantity=config.max_quantity,
        max_price=str(config.max_price),
        max_daily_orders=config.max_daily_orders,
        max_daily_notional=str(config.max_daily_notional),
    )


@router.put("/risk-config", response_model=RiskConfigResponse)
async def update_risk_configuration(request: RiskConfigUpdateRequest):
    """Update the risk configuration.

    Only provided fields are updated; omitted fields keep their current
    values.
    """
    config = get_risk_config()

    # Apply only the fields that were provided.
    if request.max_order_value is not None:
        config.max_order_value = request.max_order_value
    if request.restricted_symbols is not None:
        config.restricted_symbols = [
            s.strip().upper() for s in request.restricted_symbols if s.strip()
        ]
    if request.min_price is not None:
        config.min_price = request.min_price
    if request.max_quantity is not None:
        config.max_quantity = request.max_quantity
    if request.max_price is not None:
        config.max_price = request.max_price
    if request.max_daily_orders is not None:
        config.max_daily_orders = request.max_daily_orders
    if request.max_daily_notional is not None:
        config.max_daily_notional = request.max_daily_notional

    set_risk_config(config)

    return RiskConfigResponse(
        max_order_value=str(config.max_order_value),
        restricted_symbols=config.restricted_symbols,
        min_price=str(config.min_price),
        max_quantity=config.max_quantity,
        max_price=str(config.max_price),
        max_daily_orders=config.max_daily_orders,
        max_daily_notional=str(config.max_daily_notional),
    )


@router.get("/risk-rules", response_model=RiskRulesListResponse)
async def get_risk_rules():
    """Return all risk rules with metadata, descriptions, and current limits."""
    config = get_risk_config()

    rules = []
    for rule_id, meta in RULE_METADATA.items():
        current_value = None
        config_key = meta["config_key"]
        if config_key:
            raw = getattr(config, config_key, None)
            if isinstance(raw, list):
                current_value = ", ".join(raw)
            elif raw is not None:
                current_value = str(raw)

        rules.append(
            RiskRuleResponse(
                rule_id=rule_id,
                name=meta["name"],
                description=meta["description"],
                category=meta["category"],
                config_key=config_key,
                applicable_side=meta.get("applicable_side", "BOTH"),
                current_value=current_value,
                enabled=True,
            )
        )

    return RiskRulesListResponse(rules=rules)


# ---------------------------------------------------------------------------
# Market Data endpoints
# ---------------------------------------------------------------------------


@router.get("/market/status", response_model=FeedHealth)
async def get_market_feed_status():
    """Return live market feed connectivity, provider, and latency telemetry."""
    service = get_market_data_service()
    return await service.get_feed_health()


@router.get("/market/instruments", response_model=list[Instrument])
async def get_market_instruments():
    """Return supported NSE cash equity instruments."""
    service = get_market_data_service()
    return await service.get_instruments()


@router.get("/market/quotes", response_model=list[Quote])
async def get_market_quotes():
    """Return latest normalized quotes for all watchlist instruments."""
    service = get_market_data_service()
    return await service.get_quotes()


@router.get("/market/quotes/{symbol}", response_model=Quote)
async def get_market_quote(symbol: str):
    """Return latest quote for a specific symbol."""
    service = get_market_data_service()
    quote = await service.get_quote(symbol)
    if not quote:
        raise HTTPException(
            status_code=404, detail=f"Quote for symbol '{symbol}' not found"
        )
    return quote


@router.get("/market/candles", response_model=list[Candle])
async def get_market_candles(
    symbol: str, interval: str = "1m", limit: int = 100
):
    """Return historical OHLCV candlestick bars for an instrument."""
    service = get_market_data_service()
    return await service.get_candles(symbol, interval=interval, limit=limit)


# ---------------------------------------------------------------------------
# Stock Screener endpoints
# ---------------------------------------------------------------------------


@router.get("/screener", response_model=ScreenerResponse)
async def get_screener_results(
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    min_volume: int | None = None,
    min_change_pct: Decimal | None = None,
    max_change_pct: Decimal | None = None,
):
    """Filter configured universe with advisory preliminary risk eligibility."""
    return await run_screener(
        min_price=min_price,
        max_price=max_price,
        min_volume=min_volume,
        min_change_pct=min_change_pct,
        max_change_pct=max_change_pct,
    )


# ---------------------------------------------------------------------------
# Simulated Portfolio & Positions endpoints
# ---------------------------------------------------------------------------


@router.get("/portfolio/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary_endpoint():
    """Return simulated cash, portfolio valuation, and mark-to-market unrealized P&L."""
    db = await get_db()
    try:
        return await get_portfolio_summary(db)
    finally:
        await db.close()


@router.get("/portfolio/positions", response_model=list[PositionResponse])
async def get_portfolio_positions_endpoint():
    """Return simulated open positions with entry prices, market values, and P&L."""
    db = await get_db()
    try:
        return await get_positions(db)
    finally:
        await db.close()


@router.get("/portfolio/positions/{symbol}")
async def get_portfolio_single_position_endpoint(symbol: str):
    """Return held, reserved, and sellable quantity for a specific symbol."""
    db = await get_db()
    try:
        return await get_position_and_sellable_quantity(db, symbol)
    finally:
        await db.close()
