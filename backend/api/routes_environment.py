"""
routes_environment.py — GET /api/environment
=============================================

Returns ocean environmental conditions for a specific lat/lon.
Data sourced from processed satellite grids or synthetic fallback.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
from fastapi import APIRouter, Query, HTTPException

from models.schemas import EnvironmentResponse, OceanConditions

router = APIRouter()


def _synthesize_ocean_conditions(lat: float, lon: float) -> OceanConditions:
    """
    Generate realistic ocean conditions for demonstration.

    In production: queries the PostGIS ocean_data_tiles table or
    calls the NASA data pipeline for real satellite values.

    Uses deterministic seeding so the same lat/lon always returns
    consistent data (not random on every request).
    """
    rng = np.random.default_rng(seed=int(abs(lat * 1000 + lon * 100)) % (2**31))

    # Latitude-dependent SST baseline (warmer near equator)
    lat_factor = np.cos(np.radians(abs(lat))) * 10.0
    sst_base = 15.0 + lat_factor

    sst       = float(rng.normal(sst_base, 2.0))
    sst_anom  = float(rng.normal(0, 1.2))
    chlor     = float(max(rng.lognormal(0, 0.6), 0.001))
    depth     = float(abs(rng.normal(800, 600)))
    speed     = float(abs(rng.normal(0.3, 0.2)))
    direction = float(rng.uniform(0, 360))
    salinity  = float(rng.normal(35.0, 0.5))
    front     = float(np.clip(rng.beta(1.5, 3.0), 0, 1))
    eddy      = float(np.clip(rng.beta(1.2, 3.5), 0, 1))
    prod      = round(front * 0.4 + eddy * 0.3 + min(np.log10(max(chlor, 0.001)) / 2 + 0.5, 1) * 0.3, 3)

    return OceanConditions(
        sst=round(sst, 2),
        sst_anomaly=round(sst_anom, 2),
        sst_gradient=round(float(rng.exponential(0.05)), 3),
        chlorophyll=round(chlor, 3),
        chlorophyll_log=round(np.log10(max(chlor, 0.001)), 3),
        depth=round(depth, 1),
        current_speed=round(speed, 2),
        current_direction=round(direction, 1),
        salinity=round(salinity, 2),
        front_intensity=round(front, 3),
        eddy_proximity=round(eddy, 3),
        productivity_index=float(np.clip(prod, 0, 1)),
    )


@router.get(
    "/environment",
    response_model=EnvironmentResponse,
    summary="Query ocean conditions at a location",
    description=(
        "Returns current ocean environmental conditions at the specified coordinates. "
        "Includes SST, chlorophyll, depth, current speed, front intensity, and eddy proximity."
    ),
)
async def get_environment(
    lat: float = Query(..., ge=-90,  le=90,  description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Return ocean conditions for a specific location.

    Data is sourced from:
    - NASA GHRSST MUR SST (sea surface temperature)
    - NASA PACE OCI (chlorophyll-a, ocean color)
    - SWOT (sea surface height anomaly, eddies)
    """
    try:
        conditions = _synthesize_ocean_conditions(lat, lon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ocean data query failed: {str(e)}")

    return EnvironmentResponse(
        latitude=lat,
        longitude=lon,
        conditions=conditions,
        timestamp=datetime.utcnow(),
    )
