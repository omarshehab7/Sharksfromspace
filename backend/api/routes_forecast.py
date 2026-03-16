"""
routes_forecast.py — GET /api/forecast
========================================

Returns a 7-day shark activity forecast for a location.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException

from models.schemas import ForecastResponse, ForecastDay
from services.prediction_service import generate_forecast

router = APIRouter()


@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="7-day shark activity forecast",
    description=(
        "Returns a 7-day forward prediction of shark activity likelihood. "
        "Each day includes predicted risk level, ocean conditions, likely species, "
        "and a confidence score (decreases further from today)."
    ),
)
async def get_forecast(
    lat:  float = Query(..., ge=-90,  le=90,  description="Latitude"),
    lon:  float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int   = Query(7,   ge=1,   le=14,  description="Number of forecast days"),
):
    """
    Generate a multi-day shark activity forecast.

    The forecast model uses:
    - Current satellite observations as the baseline
    - Historical seasonal patterns for trend extrapolation
    - Day-to-day environmental variability (simulated via stochastic model)
    - Decreasing confidence for days further in the future
    """
    try:
        raw_days = generate_forecast(lat=lat, lon=lon, days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast generation failed: {str(e)}")

    forecast_days = [
        ForecastDay(**d)
        for d in raw_days
    ]

    return ForecastResponse(
        latitude=lat,
        longitude=lon,
        days=forecast_days,
        generated_at=datetime.utcnow(),
    )
