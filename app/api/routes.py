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
from app.repositories import order_repository
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
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
    config = get_risk_config()
    db = await get_db()
    try:
        order = await order_service.create_and_validate_order(
            db=db,
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity,
            price=request.price,
            config=config,
        )
        return _order_to_response(order)
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
async def get_risk_configuration():
    """Return the current risk configuration."""
    config = get_risk_config()
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
                current_value=current_value,
                enabled=True,
            )
        )

    return RiskRulesListResponse(rules=rules)
