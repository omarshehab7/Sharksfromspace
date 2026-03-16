"""
routes_ocean.py — Ocean Data API Endpoints
============================================

Provides endpoints for querying raw ocean parameter data
at a specific geographic location.

Endpoints:
    GET /ocean-data - Get ocean parameters (SST, chlorophyll, etc.) for a location
"""

from fastapi import APIRouter, Query
from models.schemas import OceanDataResponse

router = APIRouter()


@router.get("/ocean-data", response_model=OceanDataResponse)
async def get_ocean_data(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Retrieve ocean condition data for a specific latitude/longitude.

    Returns:
    - Sea Surface Temperature (SST) in °C
    - Chlorophyll-a concentration in mg/m³
    - Water depth in meters
    - Ocean current speed in m/s and direction in degrees
    - Salinity in PSU

    Data is sourced from NASA satellite products (MODIS, GHRSST)
    and interpolated to the requested location.
    """
    # TODO: Query the latest processed ocean data from the database
    # TODO: Interpolate values for the exact lat/lon if between grid points
    # TODO: Return structured ocean parameter response

    # Placeholder response for scaffolding
    return OceanDataResponse(
        latitude=lat,
        longitude=lon,
        sst=24.5,
        chlorophyll=0.35,
        depth=150.0,
        current_speed=0.45,
        current_direction=180.0,
        salinity=35.2,
        timestamp="2024-01-01T00:00:00Z",
    )
