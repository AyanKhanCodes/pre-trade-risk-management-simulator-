"""
API routes for the Pre-Trade Risk Management Simulator.

Defines REST endpoints for order submission, retrieval, and risk configuration.
Routes are thin — they parse requests, call services, and return HTTP responses.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_risk_config
from app.database import get_db
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
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
        created_at=order.created_at,
    )


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


@router.get("/risk-config")
async def get_risk_configuration():
    """Return the current risk configuration."""
    config = get_risk_config()
    return {
        "max_order_value": str(config.max_order_value),
        "restricted_symbols": config.restricted_symbols,
    }
