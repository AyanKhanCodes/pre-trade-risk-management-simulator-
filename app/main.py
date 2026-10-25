"""
FastAPI application entry point for the Pre-Trade Risk Management Simulator.

Sets up the application, lifespan handler for DB initialization,
CORS middleware, includes all API routes under /api, and serves
the built React frontend for all other routes.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.database import init_db
from app.services.market_data.service import get_market_data_service

# Path to the built React frontend (output of `npm run build`).
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes the database and starts market data stream on startup.
    """
    await init_db()
    market_service = get_market_data_service()
    await market_service.start()
    yield
    await market_service.stop()


app = FastAPI(
    title="Pre-Trade Risk Management Simulator",
    description=(
        "An educational simulator that evaluates simulated trading orders "
        "against configurable risk rules before approval."
    ),
    version="0.3.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes under /api prefix.
app.include_router(router, prefix="/api")


@app.get("/api/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}


# ---------------------------------------------------------------------------
# WebSocket streaming endpoint (mounted before SPA catch-all)
# ---------------------------------------------------------------------------


@app.websocket("/ws/market")
async def websocket_market_feed(websocket: WebSocket):
    """Normalized live market data feed for connected UI clients."""
    service = get_market_data_service()
    await service.connect_client(websocket)
    try:
        while True:
            # Keep connection alive; process client messages if any
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        await service.disconnect_client(websocket)


# ---------------------------------------------------------------------------
# Serve the built React frontend (production mode).
# ---------------------------------------------------------------------------

if os.path.isdir(_STATIC_DIR):
    # Serve Vite build assets (JS, CSS, images).
    _assets_dir = os.path.join(_STATIC_DIR, "assets")
    if os.path.isdir(_assets_dir):
        app.mount(
            "/assets",
            StaticFiles(directory=_assets_dir),
            name="assets",
        )

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str = ""):
        """Serve the React SPA.

        For any route that is not an API endpoint or a known static asset,
        return the React index.html and let React Router handle the route.
        """
        # Try to serve the exact file first (e.g. favicon.ico, robots.txt).
        candidate = os.path.join(_STATIC_DIR, full_path)
        if full_path and os.path.isfile(candidate):
            return FileResponse(candidate)
        # Fall back to index.html for client-side routing.
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))
