"""
productivity_index.py — Marine Productivity Index (Pipeline Step 6)
=====================================================================

Computes a composite marine ecosystem productivity index that estimates
the overall biological productivity of each ocean grid cell.

Higher productivity → more prey → more sharks.

Components:
  • Chlorophyll-a concentration — proxy for phytoplankton biomass
  • Phytoplankton absorption (aph) — direct measure from PACE OCI
  • SST anomaly — warm anomalies can trigger bloom events
  • Front intensity — fronts concentrate nutrients and plankton

The composite index is used as a direct feature in the shark model:
  HabitatScore += productivity_weight × productivity_index
"""

from __future__ import annotations

import numpy as np
import structlog

logger = structlog.get_logger(__name__)


def compute_productivity_index(
    chlorophyll: np.ndarray,
    aph: np.ndarray | None = None,
    sst_anomaly: np.ndarray | None = None,
    front_intensity: np.ndarray | None = None,
    chlor_weight: float = 0.40,
    aph_weight: float = 0.20,
    sst_anomaly_weight: float = 0.15,
    front_weight: float = 0.25,
) -> np.ndarray:
    """
    Compute composite marine productivity index (0 to 1).

    The index blends multiple indicators of ecosystem productivity.
    Each component is independently normalized to [0, 1] and then
    combined using configurable weights.

    Args:
        chlorophyll: 2D chlorophyll-a array (mg/m³) — primary indicator
        aph: 2D phytoplankton absorption array (m⁻¹) — optional PACE product
        sst_anomaly: 2D SST anomaly array (°C) — optional
        front_intensity: 2D front intensity score [0,1] — optional
        chlor_weight: Weight for chlorophyll (default 0.40)
        aph_weight: Weight for phytoplankton absorption (default 0.20)
        sst_anomaly_weight: Weight for SST anomaly (default 0.15)
        front_weight: Weight for front intensity (default 0.25)

    Returns:
        2D productivity index array, normalized to [0, 1]
    """
    shape = chlorophyll.shape
    index = np.zeros(shape, dtype=np.float32)
    total_weight = 0.0

    # ---- Chlorophyll-a ----
    # Optimal range for prey concentration: 0.2 – 5.0 mg/m³
    # Very low = oligotrophic (low prey), very high = potentially harmful bloom
    chlor_score = _sigmoid_score(chlorophyll, center=1.0, width=2.0)
    index += chlor_weight * chlor_score
    total_weight += chlor_weight

    # ---- Phytoplankton absorption (PACE aph) ----
    if aph is not None:
        aph_score = _percentile_normalize(aph)
        index += aph_weight * aph_score
        total_weight += aph_weight

    # ---- SST anomaly ----
    # Moderate warm anomalies (+0.5 to +2°C) often indicate enhanced productivity
    # Strong anomalies (>3°C) can cause marine heatwaves — negative for ecosystem
    if sst_anomaly is not None:
        # Optimal anomaly: slight positive (+0.5 to +1.5°C)
        anom_score = np.exp(-0.5 * ((sst_anomaly - 1.0) / 1.5) ** 2).astype(np.float32)
        anom_score[np.isnan(sst_anomaly)] = 0.0
        index += sst_anomaly_weight * anom_score
        total_weight += sst_anomaly_weight

    # ---- Front intensity ----
    # Already normalized [0, 1] from ocean_fronts module
    if front_intensity is not None:
        index += front_weight * front_intensity
        total_weight += front_weight

    # Normalize by actual weight used
    if total_weight > 0:
        index /= total_weight

    index = np.clip(index, 0, 1)

    logger.info(
        "Productivity index computed",
        mean=float(np.nanmean(index)),
        p90=float(np.nanpercentile(index[np.isfinite(index)], 90))
        if np.isfinite(index).any() else 0.0,
    )

    return index


def _sigmoid_score(
    data: np.ndarray,
    center: float = 1.0,
    width: float = 2.0,
) -> np.ndarray:
    """
    Apply a sigmoid-like scoring function.

    Peaks at `center`, with soft falloff controlled by `width`.
    Values at center → score ≈ 1, far from center → score → 0.

    Uses a Gaussian envelope: score = exp(-0.5 * ((x - center) / width)²)
    """
    score = np.exp(-0.5 * ((data - center) / width) ** 2).astype(np.float32)
    score[np.isnan(data)] = 0.0
    return score


def _percentile_normalize(data: np.ndarray, pmin: float = 2, pmax: float = 98) -> np.ndarray:
    """Normalize to [0, 1] using robust percentile scaling."""
    valid = data[np.isfinite(data)]
    if len(valid) == 0:
        return np.zeros_like(data, dtype=np.float32)

    lo = np.percentile(valid, pmin)
    hi = np.percentile(valid, pmax)

    if hi <= lo:
        return np.zeros_like(data, dtype=np.float32)

    normalized = (data - lo) / (hi - lo)
    return np.clip(normalized, 0, 1).astype(np.float32)
