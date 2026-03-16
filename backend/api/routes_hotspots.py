"""
routes_hotspots.py — Shark Hotspot API Endpoints
==================================================

Provides endpoints for querying predicted shark activity hotspots.
Hotspots are computed by the ML prediction service and stored in PostGIS.

Endpoints:
    GET /hotspots          - List hotspots within a bounding box
    GET /hotspots/{id}     - Get detailed info for a specific hotspot
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from models.schemas import HotspotResponse, HotspotListResponse

router = APIRouter()


@router.get("/hotspots", response_model=HotspotListResponse)
async def list_hotspots(
    min_lat: Optional[float] = Query(None, ge=-90, le=90, description="Minimum latitude"),
    max_lat: Optional[float] = Query(None, ge=-90, le=90, description="Maximum latitude"),
    min_lon: Optional[float] = Query(None, ge=-180, le=180, description="Minimum longitude"),
    max_lon: Optional[float] = Query(None, ge=-180, le=180, description="Maximum longitude"),
    risk_level: Optional[str] = Query(None, regex="^(low|medium|high)$", description="Filter by risk level"),
    limit: int = Query(50, ge=1, le=200, description="Max results to return"),
):
    """
    Retrieve predicted shark activity hotspots.

    If bounding box coordinates are provided, only hotspots within that
    geographic area are returned. Otherwise, returns global hotspots.

    Results are ordered by risk score (highest first).
    """
    # TODO: Query PostGIS database for hotspots within bounding box
    # TODO: Apply risk_level filter if specified
    # TODO: Return serialized hotspot data

    # Placeholder response for scaffolding
    return HotspotListResponse(
        hotspots=[],
        total=0,
        last_updated="2024-01-01T00:00:00Z",
    )


@router.get("/hotspots/{hotspot_id}", response_model=HotspotResponse)
async def get_hotspot(hotspot_id: str):
    """
    Retrieve detailed information for a specific hotspot.

    Returns ocean parameters, predicted species, risk assessment,
    and the timestamp of the prediction.
    """
    # TODO: Query database for hotspot by ID
    # TODO: Enrich with ocean data and species predictions

    raise HTTPException(status_code=404, detail="Hotspot not found")
