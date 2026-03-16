"""
routes_predict.py — GET /api/predict
======================================

Returns shark activity hotspot predictions for a region.
Uses the habitat scoring model with a grid-based fallback.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse

from models.schemas import PredictionResponse, HotspotFeature, OceanConditions
from services.prediction_service import generate_regional_predictions
from config import settings

router = APIRouter()


@router.get(
    "/predict",
    response_model=PredictionResponse,
    summary="Predict shark activity hotspots",
    description=(
        "Returns predicted shark activity hotspots within the requested radius. "
        "Each hotspot includes a risk score [0-1], risk level, likely species, "
        "and the ocean conditions that drove the prediction."
    ),
)
async def predict_hotspots(
    lat:        float = Query(..., ge=-90,  le=90,  description="Center latitude"),
    lon:        float = Query(..., ge=-180, le=180, description="Center longitude"),
    radius_km:  float = Query(500, ge=10, le=5000,  description="Search radius in km"),
    risk_level: Optional[str] = Query(None, pattern="^(low|medium|high)$", description="Filter by risk level"),
    limit:      int   = Query(50, ge=1, le=200, description="Max hotspots to return"),
):
    """
    Predict shark activity hotspots within a geographic region.

    Pipeline:
    1. Attempt to load from cached DB predictions
    2. Fall back to real-time generation (heuristic + synthetic ocean data)
    3. Filter, sort, and return top N results
    """
    try:
        raw = generate_regional_predictions(
            center_lat=lat,
            center_lon=lon,
            radius_km=radius_km,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    # Apply risk_level filter
    if risk_level:
        raw = [h for h in raw if h["risk_level"] == risk_level]

    # Limit
    raw = raw[:limit]

    # Serialize
    hotspots = [
        HotspotFeature(
            id=h["id"],
            latitude=h["latitude"],
            longitude=h["longitude"],
            probability_of_shark_activity=h["probability_of_shark_activity"],
            risk_score=h["risk_score"],
            risk_level=h["risk_level"],
            species=h["species"],
            predicted_at=h["predicted_at"],
            conditions=OceanConditions(**h["conditions"]),
        )
        for h in raw
    ]

    return PredictionResponse(
        hotspots=hotspots,
        total=len(hotspots),
        last_updated=datetime.utcnow(),
    )
