"""
prediction_service.py — Prediction Service Layer
=================================================

Bridges the API layer to the ML pipeline.
Handles caching, fallback data, DB persistence, and
coordinates between the ML model and ocean data sources.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta
from typing import Optional, List

import numpy as np
import structlog

from config import settings

logger = structlog.get_logger(__name__)


# ---- Species/SST mapping ----
SPECIES_SST_RANGES: dict[str, tuple[float, float]] = {
    "Great White Shark":   (12, 24),
    "Tiger Shark":         (20, 30),
    "Hammerhead Shark":    (18, 28),
    "Bull Shark":          (20, 32),
    "Whale Shark":         (21, 30),
    "Mako Shark":          (15, 25),
    "Blue Shark":          (10, 22),
}

# ---- Habitat weights ----
W_SST        = 0.30
W_CHLOR      = 0.25
W_FRONT      = 0.25
W_EDDY       = 0.20


def _sst_score(sst: float) -> float:
    """Gaussian score centered at 23°C, σ=5."""
    return float(np.exp(-0.5 * ((sst - 23.0) / 5.0) ** 2))


def _chlor_score(chlor: float) -> float:
    """Log-normal score centered at 1 mg/m³."""
    chlor = max(chlor, 0.001)
    log_c = np.log10(chlor)
    return float(np.exp(-0.5 * ((log_c - 0.0) / 0.8) ** 2))


def compute_habitat_score(
    sst:              float,
    chlorophyll:      float,
    front_intensity:  float = 0.0,
    eddy_proximity:   float = 0.0,
    sst_anomaly:      float = 0.0,
    depth:            Optional[float] = None,
) -> float:
    """
    Compute the weighted habitat suitability score.

      HabitatScore = W_SST×SST_score
                   + W_CHLOR×chlor_score
                   + W_FRONT×front_intensity
                   + W_EDDY×eddy_proximity
    """
    score = (
        W_SST   * _sst_score(sst)
        + W_CHLOR * _chlor_score(chlorophyll)
        + W_FRONT * np.clip(front_intensity, 0, 1)
        + W_EDDY  * np.clip(eddy_proximity, 0, 1)
    )
    # SST anomaly bonus (±0.1)
    score += np.clip(sst_anomaly / 3.0, -0.1, 0.1)
    # Depth bonus for continental shelf (20-200m)
    if depth is not None and 20 <= abs(depth) <= 200:
        score += 0.05
    return float(np.clip(score, 0.0, 1.0))


def classify_risk(score: float) -> str:
    if score >= 0.6:
        return "high"
    if score >= 0.3:
        return "medium"
    return "low"


def predict_species(sst: float) -> List[str]:
    return [sp for sp, (lo, hi) in SPECIES_SST_RANGES.items() if lo <= sst <= hi] or ["Unknown"]


# ---- Grid-based prediction around a point ----

def generate_regional_predictions(
    center_lat:  float,
    center_lon:  float,
    radius_km:   float = 500,
    grid_deg:    float = 0.5,
) -> List[dict]:
    """
    Generate synthetic grid predictions around a center point.

    In production this is replaced by actual satellite data from
    the pipeline. Used as a fallback when no DB data exists.
    """
    # Convert radius to rough degrees
    deg_span = radius_km / 111.0
    step = grid_deg

    lats = np.arange(center_lat - deg_span, center_lat + deg_span, step)
    lons = np.arange(center_lon - deg_span, center_lon + deg_span, step)

    predictions = []
    rng = np.random.default_rng(seed=int(abs(center_lat * 1000 + center_lon)))

    for lat in lats:
        for lon in lons:
            if abs(lat) > 90 or abs(lon) > 180:
                continue

            # Synthetic ocean conditions with realistic spatial variation
            sst       = rng.normal(22.0, 4.0)
            chlor     = rng.lognormal(0, 0.6)
            sst_anom  = rng.normal(0, 1.5)
            front     = float(rng.beta(1.5, 3.0))
            eddy      = float(rng.beta(1.2, 3.5))
            depth     = float(rng.uniform(50, 2000))

            score = compute_habitat_score(
                sst=sst, chlorophyll=chlor,
                front_intensity=front, eddy_proximity=eddy,
                sst_anomaly=sst_anom, depth=depth,
            )

            # Only include cells with detectable activity (score > 0.1)
            if score < 0.1:
                continue

            predictions.append({
                "id":                           str(uuid.uuid4()),
                "latitude":                     round(float(lat), 4),
                "longitude":                    round(float(lon), 4),
                "probability_of_shark_activity": round(score, 3),
                "risk_score":                   round(score, 3),
                "risk_level":                   classify_risk(score),
                "species":                      predict_species(sst),
                "predicted_at":                 datetime.utcnow(),
                "conditions": {
                    "sst":                sst,
                    "sst_anomaly":        sst_anom,
                    "chlorophyll":        round(max(chlor, 0.001), 3),
                    "front_intensity":    round(front, 3),
                    "eddy_proximity":     round(eddy, 3),
                    "productivity_index": round((front * 0.4 + eddy * 0.3 + _chlor_score(chlor) * 0.3), 3),
                    "depth":              round(depth, 1),
                },
            })

    # Sort by score descending
    predictions.sort(key=lambda x: x["risk_score"], reverse=True)
    logger.info("Generated regional predictions", count=len(predictions), center=(center_lat, center_lon))
    return predictions


def generate_forecast(
    lat: float,
    lon: float,
    days: int = 7,
) -> List[dict]:
    """
    Generate a 7-day forecast using trend extrapolation.

    In production this uses a time-series model on the satellite data cadence.
    """
    from datetime import date

    rng = np.random.default_rng(seed=int(abs(lat * 100 + lon)))

    # Base conditions
    base_sst   = rng.normal(22.0, 3.0)
    base_chlor = rng.lognormal(0, 0.5)
    base_front = float(rng.beta(1.5, 3.0))

    day_labels = ["Today", "Tomorrow", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    forecast_days = []
    today = date.today()

    for i in range(days):
        # Add day-to-day variation
        sst   = base_sst + rng.normal(0, 0.5)
        chlor = max(base_chlor + rng.normal(0, 0.2), 0.01)
        front = float(np.clip(base_front + rng.normal(0, 0.08), 0, 1))
        eddy  = float(rng.beta(1.2, 3.5))

        score = compute_habitat_score(sst=sst, chlorophyll=chlor, front_intensity=front, eddy_proximity=eddy)
        confidence = max(0.3, 0.95 - i * 0.08)  # Confidence decreases further out

        forecast_days.append({
            "date":                      str(today + timedelta(days=i)),
            "day_label":                 day_labels[i] if i < len(day_labels) else str(today + timedelta(days=i)),
            "risk_level":               classify_risk(score),
            "risk_score":               round(score, 3),
            "predicted_sst":            round(sst, 1),
            "predicted_chlorophyll":    round(chlor, 3),
            "predicted_front_intensity": round(front, 3),
            "confidence":               round(confidence, 2),
            "likely_species":           predict_species(sst),
        })

    return forecast_days
