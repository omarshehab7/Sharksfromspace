"""
ocean_fronts.py — Ocean Front Detection (Pipeline Step 4)
============================================================

Detects thermal and productivity fronts in satellite data.

Thermal fronts — sharp SST boundaries — are critical for shark
prediction because they:
  • Concentrate plankton and small fish at the convergence zone
  • Create "walls" that guide shark migration corridors
  • Are the primary foraging habitat for pelagic predators

Methods:
  • Sobel gradient magnitude (primary)
  • Canny edge detection for sharp front boundaries
  • Front intensity scoring based on gradient percentiles
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import sobel, gaussian_filter, generic_filter
import structlog

logger = structlog.get_logger(__name__)


def compute_sobel_gradient(data: np.ndarray) -> np.ndarray:
    """
    Compute the Sobel gradient magnitude of a 2D field.

    The Sobel operator approximates the gradient using a 3×3 kernel:
      Gx = [[-1, 0, +1], [-2, 0, +2], [-1, 0, +1]]
      Gy = [[-1, -2, -1], [0, 0, 0], [+1, +2, +1]]
      magnitude = sqrt(Gx² + Gy²)

    Args:
        data: 2D array (e.g. SST or chlorophyll)

    Returns:
        2D gradient magnitude array
    """
    # Fill NaN with local mean for stable gradient computation
    filled = data.copy()
    nan_mask = np.isnan(filled)
    if nan_mask.any():
        filled[nan_mask] = np.nanmean(filled)

    gx = sobel(filled, axis=1)  # dT/dx
    gy = sobel(filled, axis=0)  # dT/dy
    magnitude = np.sqrt(gx ** 2 + gy ** 2).astype(np.float32)

    # Restore NaN where original was NaN
    magnitude[nan_mask] = np.nan

    return magnitude


def detect_canny_edges(
    gradient: np.ndarray,
    low_threshold_pct: float = 70,
    high_threshold_pct: float = 90,
) -> np.ndarray:
    """
    Simple Canny-like edge detection using gradient magnitude thresholding.

    Identifies sharp frontal boundaries as a binary mask.
    Uses percentile-based thresholds (adaptive to the data).

    Args:
        gradient: 2D gradient magnitude array
        low_threshold_pct: Percentile for lower hysteresis threshold
        high_threshold_pct: Percentile for upper hysteresis threshold

    Returns:
        Binary mask (True = front edge pixel)
    """
    valid = gradient[np.isfinite(gradient)]
    if len(valid) == 0:
        return np.zeros(gradient.shape, dtype=bool)

    low_thresh = np.percentile(valid, low_threshold_pct)
    high_thresh = np.percentile(valid, high_threshold_pct)

    strong = gradient >= high_thresh
    weak = (gradient >= low_thresh) & (gradient < high_thresh)

    # Hysteresis: weak edges connected to strong edges are kept
    edges = strong.copy()

    # Dilate strong edges by 1 pixel and intersect with weak
    from scipy.ndimage import binary_dilation

    dilated = binary_dilation(strong, iterations=1)
    edges = edges | (weak & dilated)

    return edges


def compute_front_intensity(
    sst_gradient: np.ndarray,
    chlor_gradient: np.ndarray | None = None,
    sst_weight: float = 0.7,
    chlor_weight: float = 0.3,
) -> np.ndarray:
    """
    Compute a composite front intensity score (0 to 1).

    Combines SST gradient (thermal fronts) with chlorophyll gradient
    (productivity fronts). The combined score indicates the overall
    ecological importance of the front.

    Used as a direct feature in the shark habitat model:
      HabitatScore += front_weight × front_intensity

    Args:
        sst_gradient: 2D SST gradient magnitude
        chlor_gradient: 2D chlorophyll gradient magnitude (optional)
        sst_weight: Weight for SST gradient (default 0.7)
        chlor_weight: Weight for chlorophyll gradient (default 0.3)

    Returns:
        2D front intensity array, normalized to [0, 1]
    """
    # Normalize SST gradient to [0, 1] using robust percentile scaling
    sst_norm = _percentile_normalize(sst_gradient)

    if chlor_gradient is not None:
        chlor_norm = _percentile_normalize(chlor_gradient)
        intensity = sst_weight * sst_norm + chlor_weight * chlor_norm
    else:
        intensity = sst_norm

    return np.clip(intensity, 0, 1).astype(np.float32)


def _percentile_normalize(data: np.ndarray, pmin: float = 2, pmax: float = 98) -> np.ndarray:
    """
    Normalize array to [0, 1] using percentile-based min/max.

    Robust to outliers (uses 2nd and 98th percentiles).
    """
    valid = data[np.isfinite(data)]
    if len(valid) == 0:
        return np.zeros_like(data, dtype=np.float32)

    lo = np.percentile(valid, pmin)
    hi = np.percentile(valid, pmax)

    if hi <= lo:
        return np.zeros_like(data, dtype=np.float32)

    normalized = (data - lo) / (hi - lo)
    return np.clip(normalized, 0, 1).astype(np.float32)


def detect_fronts(
    sst: np.ndarray,
    chlorophyll: np.ndarray | None = None,
    smooth_sigma: float = 1.0,
) -> dict[str, np.ndarray]:
    """
    Full ocean front detection pipeline.

    Args:
        sst: 2D SST array on the common grid
        chlorophyll: 2D chlorophyll array on the common grid (optional)
        smooth_sigma: Gaussian smoothing σ before gradient (reduces noise)

    Returns:
        Dict with keys:
          - "sst_gradient": Sobel gradient of SST
          - "chlor_gradient": Sobel gradient of chlorophyll (or None)
          - "front_intensity": Composite front score [0, 1]
          - "front_edges": Binary mask of sharp front boundaries
    """
    logger.info("Running front detection", smooth_sigma=smooth_sigma)

    # Smooth before gradient to reduce sensor noise
    sst_smooth = sst.copy()
    valid = np.isfinite(sst_smooth)
    if valid.any():
        sst_filled = np.where(valid, sst_smooth, np.nanmean(sst_smooth))
        sst_smooth = gaussian_filter(sst_filled, sigma=smooth_sigma)
        sst_smooth[~valid] = np.nan

    sst_gradient = compute_sobel_gradient(sst_smooth)

    chlor_gradient = None
    if chlorophyll is not None:
        chlor_smooth = chlorophyll.copy()
        valid_c = np.isfinite(chlor_smooth)
        if valid_c.any():
            chlor_filled = np.where(valid_c, chlor_smooth, np.nanmean(chlor_smooth))
            chlor_smooth = gaussian_filter(chlor_filled, sigma=smooth_sigma)
            chlor_smooth[~valid_c] = np.nan
        chlor_gradient = compute_sobel_gradient(chlor_smooth)

    front_intensity = compute_front_intensity(sst_gradient, chlor_gradient)
    front_edges = detect_canny_edges(sst_gradient)

    logger.info(
        "Front detection complete",
        front_pixels=int(front_edges.sum()),
        mean_intensity=float(np.nanmean(front_intensity)),
    )

    return {
        "sst_gradient": sst_gradient,
        "chlor_gradient": chlor_gradient,
        "front_intensity": front_intensity,
        "front_edges": front_edges,
    }
