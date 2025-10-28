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

# Import routers
from backend.routers import import_router, import_history_router, unmatched_players_router
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


# Inject get_db into routers
import_router.get_db = get_db
import_history_router.get_db = get_db
unmatched_players_router.get_db = get_db

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

logger.info("Cortex backend API initialized successfully")
logger.info(f"Database: {DATABASE_URL}")
logger.info("Registered routers:")
logger.info("  - /api/import (import_router)")
logger.info("  - /api/import-history (import_history_router)")
logger.info("  - /api/unmatched-players (unmatched_players_router)")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
