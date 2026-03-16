"""
eddy_detection.py — Mesoscale Eddy Detection (Pipeline Step 5)
================================================================

Detects mesoscale eddies from SWOT sea surface height anomaly (SSHA) data
and computes eddy proximity for each grid cell.

Mesoscale eddies (50–500 km diameter) are important for shark prediction:
  • Cyclonic (cold-core) eddies upwell nutrients → phytoplankton blooms
  • Anticyclonic (warm-core) eddies trap warm water → predator aggregation
  • Eddy edges have strong current shear → prey concentration zones

Method:
  1. Threshold SSHA to identify eddy-influenced pixels
  2. Label connected components as individual eddies
  3. Classify each eddy as cyclonic (SSHA < 0) or anticyclonic (SSHA > 0)
  4. Compute distance from every grid cell to nearest eddy edge
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import label, distance_transform_edt
from scipy.ndimage import binary_dilation
import structlog

logger = structlog.get_logger(__name__)


def detect_eddies(
    ssha: np.ndarray,
    threshold_m: float = 0.10,
    min_size_pixels: int = 25,
) -> dict[str, np.ndarray]:
    """
    Detect mesoscale eddies from SSHA and compute proximity metrics.

    Args:
        ssha: 2D sea surface height anomaly array (meters)
        threshold_m: SSHA magnitude threshold for eddy detection (default: 10 cm)
        min_size_pixels: Minimum eddy size in grid cells

    Returns:
        Dict with:
          "eddy_labels": 2D int array — 0=no eddy, >0=eddy ID
          "cyclonic_mask": bool mask of cyclonic (cold-core) eddies
          "anticyclonic_mask": bool mask of anticyclonic (warm-core) eddies
          "eddy_proximity": distance (in pixels) to nearest eddy edge
          "eddy_proximity_score": normalized [0, 1] score (1=at eddy, 0=far)
          "n_eddies": total number of detected eddies
    """
    if ssha is None:
        logger.warning("No SSHA data — skipping eddy detection")
        return _empty_eddy_result((1, 1))

    valid = np.isfinite(ssha)
    if not valid.any():
        logger.warning("All SSHA values are NaN — skipping eddy detection")
        return _empty_eddy_result(ssha.shape)

    shape = ssha.shape

    # Step 1: Threshold SSHA
    eddy_mask = valid & (np.abs(ssha) > threshold_m)

    # Step 2: Label connected components
    labels, n_raw = label(eddy_mask)

    # Step 3: Remove small eddies (noise)
    for i in range(1, n_raw + 1):
        if (labels == i).sum() < min_size_pixels:
            labels[labels == i] = 0

    # Re-label after removal
    labels, n_eddies = label(labels > 0)

    # Step 4: Classify cyclonic vs anticyclonic
    cyclonic_mask = np.zeros(shape, dtype=bool)
    anticyclonic_mask = np.zeros(shape, dtype=bool)

    for i in range(1, n_eddies + 1):
        eddy_pixels = labels == i
        mean_ssha = np.nanmean(ssha[eddy_pixels])
        if mean_ssha < 0:
            cyclonic_mask[eddy_pixels] = True  # Cold-core, nutrient upwelling
        else:
            anticyclonic_mask[eddy_pixels] = True  # Warm-core

    # Step 5: Compute proximity (distance to nearest eddy)
    eddy_any = labels > 0
    if eddy_any.any():
        # distance_transform_edt: distance from each non-eddy pixel to nearest eddy
        # Invert: we want distance FROM non-eddy pixels TO eddy pixels
        distance = distance_transform_edt(~eddy_any).astype(np.float32)
    else:
        distance = np.full(shape, np.finfo(np.float32).max, dtype=np.float32)

    # Normalize proximity to [0, 1]: 1=at eddy edge, 0=far away
    # Use exponential decay: score = exp(-distance / decay_scale)
    decay_scale = 25.0  # ~100 km at 4km resolution
    proximity_score = np.exp(-distance / decay_scale).astype(np.float32)

    logger.info(
        "Eddy detection complete",
        n_eddies=n_eddies,
        cyclonic=int(cyclonic_mask.sum()),
        anticyclonic=int(anticyclonic_mask.sum()),
    )

    return {
        "eddy_labels": labels,
        "cyclonic_mask": cyclonic_mask,
        "anticyclonic_mask": anticyclonic_mask,
        "eddy_proximity": distance,
        "eddy_proximity_score": proximity_score,
        "n_eddies": n_eddies,
    }


def _empty_eddy_result(shape: tuple) -> dict[str, np.ndarray]:
    """Return empty eddy detection result."""
    return {
        "eddy_labels": np.zeros(shape, dtype=int),
        "cyclonic_mask": np.zeros(shape, dtype=bool),
        "anticyclonic_mask": np.zeros(shape, dtype=bool),
        "eddy_proximity": np.full(shape, np.finfo(np.float32).max, dtype=np.float32),
        "eddy_proximity_score": np.zeros(shape, dtype=np.float32),
        "n_eddies": 0,
    }
