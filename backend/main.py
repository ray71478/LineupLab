"""
Cortex Backend FastAPI Application

Main entry point for the Cortex DFS lineup optimization backend.
Configures FastAPI app, registers routers, and sets up middleware.
"""

import logging
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from backend.exceptions import CortexException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://cortex:cortex@localhost:5432/cortex"
)

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


# Dependency for database session
def get_db() -> Session:
    """Get database session for endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Import routers AFTER defining get_db
import backend.routers.import_router as import_router_module
import backend.routers.import_history_router as import_history_router_module
import backend.routers.unmatched_players_router as unmatched_players_router_module
import backend.routers.week_router as week_router_module
import backend.routers.players_router as players_router_module
import backend.routers.smart_score_router as smart_score_router_module
import backend.routers.insights_router as insights_router_module
import backend.routers.refresh_router as refresh_router_module

# Override get_db in each router module
import_router_module.get_db = get_db
import_history_router_module.get_db = get_db
unmatched_players_router_module.get_db = get_db
week_router_module.get_db = get_db
players_router_module.get_db = get_db
smart_score_router_module.get_db = get_db
insights_router_module.get_db = get_db
refresh_router_module.get_db = get_db

from backend.routers import import_router, import_history_router, unmatched_players_router, week_router, players_router, smart_score_router, insights_router, refresh_router

# Create FastAPI app
app = FastAPI(
    title="Cortex Data Import API",
    description="API for importing and managing DFS player data",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(CortexException)
async def cortex_exception_handler(request: Request, exc: CortexException):
    """Handle custom Cortex exceptions."""
    logger.error(f"Cortex exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.message,
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "An unexpected error occurred. Please try again.",
        }
    )


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint."""
    try:
        # Test database connection
        with engine.connect() as conn:
            conn.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


# Register routers
app.include_router(import_router.router)
app.include_router(import_history_router.router)
app.include_router(unmatched_players_router.router)
app.include_router(week_router.router)
app.include_router(players_router.router)
app.include_router(smart_score_router.router)
app.include_router(insights_router.router)
app.include_router(refresh_router.router)

logger.info("Cortex backend API initialized successfully")
logger.info(f"Database: {DATABASE_URL}")
logger.info("Registered routers:")
logger.info("  - /api/import (import_router)")
logger.info("  - /api/import-history (import_history_router)")
logger.info("  - /api/unmatched-players (unmatched_players_router)")
logger.info("  - /api/weeks (week_router)")
logger.info("  - /api/players (players_router)")
logger.info("  - /api/smart-score (smart_score_router)")
logger.info("  - /api/insights (insights_router)")
logger.info("  - /api/refresh (refresh_router)")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
