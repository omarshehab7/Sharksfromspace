"""
main.py — FastAPI Application Entrypoint
==========================================

Sharks From Space API v1. Mounts all routes, configures CORS,
initializes the DB and ML model on startup.

Endpoints:
  GET /api/v1/predict      → Shark activity hotspots
  GET /api/v1/environment  → Ocean conditions per location
  GET /api/v1/forecast     → 7-day shark activity forecast
  GET /api/v1/health       → Service health check
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from config import settings
from api.routes_predict      import router as predict_router
from api.routes_environment  import router as environment_router
from api.routes_forecast     import router as forecast_router
from api.routes_health       import router as health_router
from utils.logging_config import setup_logging

logger = structlog.get_logger(__name__)


# ---- Lifespan ----

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle handler."""
    setup_logging()

    # Initialize PostgreSQL + PostGIS
    try:
        from database import init_db
        await init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.warning("Database init failed (running without DB)", error=str(e))

    # Load ML model into app state
    try:
        from models.ml_model import SharkPredictionModel
        model = SharkPredictionModel()
        model.load()
        app.state.model = model
        logger.info("Prediction model loaded")
    except Exception as e:
        logger.warning("ML model load failed (using heuristic)", error=str(e))
        app.state.model = None

    logger.info(
        "🦈 Sharks From Space API started",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        debug=settings.DEBUG,
    )

    yield

    # Shutdown
    try:
        from database import close_db
        await close_db()
    except Exception:
        pass
    logger.info("🛑 Sharks From Space API shutdown complete")


# ---- App ----

app = FastAPI(
    title="Sharks From Space API",
    description=(
        "Predicts shark activity hotspots using NASA satellite ocean data. "
        "Powered by PACE, GHRSST MUR SST, and SWOT satellite missions."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- CORS ----

ALLOWED_ORIGINS = (
    settings.ALLOWED_ORIGINS.split(",")
    if hasattr(settings, "ALLOWED_ORIGINS") and settings.ALLOWED_ORIGINS
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# ---- Routers ----

API_PREFIX = "/api/v1"

app.include_router(health_router,      prefix=API_PREFIX, tags=["Health"])
app.include_router(predict_router,     prefix=API_PREFIX, tags=["Predictions"])
app.include_router(environment_router, prefix=API_PREFIX, tags=["Environment"])
app.include_router(forecast_router,    prefix=API_PREFIX, tags=["Forecast"])

# Convenience aliases without /v1 (for mobile app backward compat)
app.include_router(predict_router,     prefix="/api",     tags=["Predictions (v0)"], include_in_schema=False)
app.include_router(environment_router, prefix="/api",     tags=["Environment (v0)"],  include_in_schema=False)
app.include_router(forecast_router,    prefix="/api",     tags=["Forecast (v0)"],     include_in_schema=False)


# ---- Root ----

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Sharks From Space API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }
