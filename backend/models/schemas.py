"""
schemas.py — Pydantic API Schemas (v2)
=======================================
Complete request/response contracts for all three API endpoints:

  GET /api/predict      → PredictionResponse
  GET /api/environment  → EnvironmentResponse
  GET /api/forecast     → ForecastResponse
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ============================================================
# Shared sub-models
# ============================================================

class OceanConditions(BaseModel):
    """Ocean environmental conditions at a point in time and space."""
    sst: float                          = Field(..., description="Sea surface temperature (°C)")
    sst_anomaly: Optional[float]        = Field(None, description="SST anomaly from climatology (°C)")
    sst_gradient: Optional[float]       = Field(None, description="SST gradient magnitude")
    chlorophyll: float                  = Field(..., description="Chlorophyll-a (mg/m³)")
    chlorophyll_log: Optional[float]    = Field(None, description="log10(chlorophyll)")
    depth: Optional[float]              = Field(None, description="Water depth (m)")
    current_speed: Optional[float]      = Field(None, description="Current speed (m/s)")
    current_direction: Optional[float]  = Field(None, description="Current direction (degrees)")
    salinity: Optional[float]           = Field(None, description="Salinity (PSU)")
    front_intensity: Optional[float]    = Field(None, ge=0, le=1, description="Ocean front intensity [0,1]")
    eddy_proximity: Optional[float]     = Field(None, ge=0, le=1, description="Eddy proximity score [0,1]")
    productivity_index: Optional[float] = Field(None, ge=0, le=1, description="Marine productivity index [0,1]")

    class Config:
        from_attributes = True


# ============================================================
# GET /api/predict  — Shark Activity Prediction
# ============================================================

class HotspotFeature(BaseModel):
    """A single GeoJSON-compatible hotspot prediction point."""
    id: str
    latitude:  float = Field(..., ge=-90,  le=90)
    longitude: float = Field(..., ge=-180, le=180)

    probability_of_shark_activity: float = Field(..., ge=0, le=1)
    risk_score:  float  = Field(..., ge=0, le=1)
    risk_level:  str    = Field(..., pattern="^(low|medium|high)$")
    species:     List[str] = Field(default_factory=list)

    conditions: OceanConditions
    predicted_at: datetime

    class Config:
        from_attributes = True


class PredictionRequest(BaseModel):
    """Query parameters for GET /api/predict."""
    lat:          float = Field(..., ge=-90,  le=90,  description="Center latitude")
    lon:          float = Field(..., ge=-180, le=180, description="Center longitude")
    radius_km:    float = Field(500, ge=10, le=5000,  description="Search radius (km)")
    risk_level:   Optional[str] = Field(None, pattern="^(low|medium|high)$")
    limit:        int   = Field(50,  ge=1,  le=200)


class PredictionResponse(BaseModel):
    """Response for GET /api/predict."""
    hotspots:     List[HotspotFeature]
    total:        int
    last_updated: datetime
    model_version: str = "1.0-heuristic"
    data_sources: List[str] = Field(
        default_factory=lambda: ["NASA PACE", "GHRSST MUR SST", "SWOT"]
    )


# ============================================================
# GET /api/environment  — Ocean Parameter Query
# ============================================================

class EnvironmentRequest(BaseModel):
    """Query parameters for GET /api/environment."""
    lat: float = Field(..., ge=-90,  le=90)
    lon: float = Field(..., ge=-180, le=180)


class EnvironmentResponse(BaseModel):
    """Response for GET /api/environment."""
    latitude:  float
    longitude: float
    conditions: OceanConditions
    timestamp: datetime


# ============================================================
# GET /api/forecast  — 7-Day Forecast
# ============================================================

class ForecastDay(BaseModel):
    """Predicted conditions for a single forecast day."""
    date:                        str
    day_label:                   str   # e.g. "Tomorrow", "Wednesday"
    risk_level:                  str   = Field(..., pattern="^(low|medium|high)$")
    risk_score:                  float = Field(..., ge=0, le=1)
    predicted_sst:               float
    predicted_chlorophyll:       float
    predicted_front_intensity:   float = Field(..., ge=0, le=1)
    confidence:                  float = Field(..., ge=0, le=1, description="Forecast confidence")
    likely_species:              List[str] = Field(default_factory=list)


class ForecastResponse(BaseModel):
    """Response for GET /api/forecast."""
    latitude:  float
    longitude: float
    days:      List[ForecastDay]
    generated_at: datetime


# ============================================================
# Shared error/health schemas
# ============================================================

class HealthResponse(BaseModel):
    status: str
    version: str
    services: dict


class ErrorResponse(BaseModel):
    detail: str
    code:   Optional[str] = None
