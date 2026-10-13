"""
FastAPI application entry point for the Pre-Trade Risk Management Simulator.

Sets up the application, lifespan handler for DB initialization,
CORS middleware, and includes all API routes.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler.

    Initializes the database on startup.
    """
    await init_db()
    yield


app = FastAPI(
    title="Pre-Trade Risk Management Simulator",
    description=(
        "An educational simulator that evaluates simulated trading orders "
        "against configurable risk rules before approval."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware for future frontend integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes.
app.include_router(router)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}
