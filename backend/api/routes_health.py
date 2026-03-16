"""
routes_health.py — Service Health Check
=========================================
"""

from fastapi import APIRouter
from models.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health():
    """Returns API operational status."""
    return HealthResponse(
        status="ok",
        version="1.0.0",
        services={
            "api": "ok",
            "model": "heuristic",
        },
    )
