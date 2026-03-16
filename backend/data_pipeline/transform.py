"""
transform.py — Satellite Grid Preprocessing (Pipeline Step 2)
================================================================

Preprocesses raw satellite arrays from CombinedOceanDataset:

1. Quality filtering — mask invalid/flagged pixels
2. Regridding — resample all datasets to a common 4 km resolution grid
3. Unit conversion — SST Kelvin → Celsius, chlorophyll log-transform
4. NaN interpolation — fill small gaps with spatial interpolation
5. Temporal compositing — multi-day mean to reduce cloud gaps

All operations use xarray + numpy for efficient array processing.
"""

from __future__ import annotations

import numpy as np
import xarray as xr
from scipy.ndimage import uniform_filter, generic_filter
from scipy.interpolate import griddata
import structlog

logger = structlog.get_logger(__name__)


# ============================================================
# Quality Filtering
# ============================================================

def mask_invalid_pixels(
    data: np.ndarray,
    valid_range: tuple[float, float] | None = None,
) -> np.ndarray:
    """
    Set invalid pixels to NaN.

    Args:
        data: 2D array of values
        valid_range: (min, max) valid range; values outside are NaN'd

    Returns:
        Cleaned array with NaN for invalid pixels
    """
    cleaned = data.astype(np.float32).copy()

    # Mask infinities
    cleaned[~np.isfinite(cleaned)] = np.nan

    # Mask out-of-range
    if valid_range is not None:
        lo, hi = valid_range
        cleaned[(cleaned < lo) | (cleaned > hi)] = np.nan

    return cleaned


def quality_filter_sst(sst: np.ndarray) -> np.ndarray:
    """
    Apply quality filtering to SST data.

    Valid ocean SST range: -2°C (sea ice interface) to 35°C (tropical maximum).
    """
    return mask_invalid_pixels(sst, valid_range=(-2.0, 35.0))


def quality_filter_chlorophyll(chlor: np.ndarray) -> np.ndarray:
    """
    Apply quality filtering to chlorophyll-a data.

    Valid range: 0.001 – 100 mg/m³.
    Negative values are physically impossible; >100 is highly suspect.
    """
    return mask_invalid_pixels(chlor, valid_range=(0.001, 100.0))


def quality_filter_ssh(ssh: np.ndarray) -> np.ndarray:
    """Apply quality filtering to sea surface height data."""
    return mask_invalid_pixels(ssh, valid_range=(-150.0, 150.0))


# ============================================================
# Unit Conversions
# ============================================================

def kelvin_to_celsius(sst_k: np.ndarray) -> np.ndarray:
    """
    Convert SST from Kelvin to Celsius if needed.

    Detects units automatically: if median > 200, assumes Kelvin.
    """
    median_val = np.nanmedian(sst_k)
    if median_val > 200:
        logger.info("Converting SST from Kelvin to Celsius", median_k=float(median_val))
        return sst_k - 273.15
    return sst_k


def log_transform_chlorophyll(chlor: np.ndarray) -> np.ndarray:
    """
    Apply log10 transform to chlorophyll-a.

    Chlorophyll spans 3+ orders of magnitude (0.01 – 50 mg/m³).
    Log-transform makes the distribution more Gaussian for ML models.
    """
    # Ensure positive values before log
    valid = chlor.copy()
    valid[valid <= 0] = np.nan
    return np.log10(valid)


# ============================================================
# Spatial Regridding
# ============================================================

def regrid_to_common_grid(
    data: np.ndarray,
    src_lat: np.ndarray,
    src_lon: np.ndarray,
    target_lat: np.ndarray,
    target_lon: np.ndarray,
    method: str = "linear",
) -> np.ndarray:
    """
    Regrid a 2D array from source to target lat/lon grid.

    Uses scipy.interpolate.griddata for irregular → regular regridding.
    This handles the case where PACE (4 km) and MUR SST (1 km) are
    on different grids by resampling to a common resolution.

    Args:
        data: 2D source data array
        src_lat: 1D source latitude array
        src_lon: 1D source longitude array
        target_lat: 1D target latitude array
        target_lon: 1D target longitude array
        method: Interpolation method ("linear", "nearest", "cubic")

    Returns:
        2D array on the target grid
    """
    # Build source meshgrid points
    src_lat_g, src_lon_g = np.meshgrid(src_lat, src_lon, indexing="ij")
    src_points = np.column_stack([src_lat_g.ravel(), src_lon_g.ravel()])
    src_values = data.ravel()

    # Remove NaN source points
    valid = np.isfinite(src_values)
    src_points = src_points[valid]
    src_values = src_values[valid]

    if len(src_values) == 0:
        logger.warning("No valid data points for regridding")
        return np.full((len(target_lat), len(target_lon)), np.nan, dtype=np.float32)

    # Build target meshgrid
    tgt_lat_g, tgt_lon_g = np.meshgrid(target_lat, target_lon, indexing="ij")
    tgt_points = np.column_stack([tgt_lat_g.ravel(), tgt_lon_g.ravel()])

    # Interpolate
    regridded = griddata(src_points, src_values, tgt_points, method=method, fill_value=np.nan)
    return regridded.reshape(len(target_lat), len(target_lon)).astype(np.float32)


def create_common_grid(
    bounding_box: tuple[float, float, float, float],
    resolution_deg: float = 0.04,  # ~4 km
) -> tuple[np.ndarray, np.ndarray]:
    """
    Create a regular lat/lon grid at the specified resolution.

    Args:
        bounding_box: (west, south, east, north) degrees
        resolution_deg: Grid spacing in degrees (default 0.04° ≈ 4 km)

    Returns:
        (lat_array, lon_array) as 1D numpy arrays
    """
    west, south, east, north = bounding_box
    lat = np.arange(south, north, resolution_deg).astype(np.float32)
    lon = np.arange(west, east, resolution_deg).astype(np.float32)
    logger.info("Common grid created", lat_pts=len(lat), lon_pts=len(lon), res_deg=resolution_deg)
    return lat, lon


# ============================================================
# NaN Interpolation
# ============================================================

def interpolate_nans(data: np.ndarray, max_gap_pixels: int = 5) -> np.ndarray:
    """
    Fill small NaN gaps using nearest-neighbor interpolation.

    Cloud-covered pixels in satellite data create small holes.
    This fills gaps up to max_gap_pixels wide, leaving large
    gaps (e.g. land) as NaN.

    Args:
        data: 2D array with NaN gaps
        max_gap_pixels: Maximum gap size to fill

    Returns:
        Array with small gaps filled
    """
    filled = data.copy()
    mask = np.isnan(filled)

    if not mask.any():
        return filled

    # Count NaN neighbors — only fill if surrounded by valid data
    valid_count = generic_filter(
        (~mask).astype(np.float32),
        np.sum,
        size=max_gap_pixels * 2 + 1,
        mode="constant",
        cval=0,
    )
    total_cells = (max_gap_pixels * 2 + 1) ** 2

    # Only fill where >50% of neighbors are valid (small gap, not land)
    fillable = mask & (valid_count > total_cells * 0.5)

    if fillable.any():
        # Use uniform filter (box blur) on the valid data to fill
        valid_data = np.where(mask, 0, filled)
        valid_weight = (~mask).astype(np.float32)

        blurred_data = uniform_filter(valid_data, size=max_gap_pixels)
        blurred_weight = uniform_filter(valid_weight, size=max_gap_pixels)
        blurred_weight[blurred_weight == 0] = 1  # Avoid division by zero

        interpolated = blurred_data / blurred_weight
        filled[fillable] = interpolated[fillable]

    n_filled = fillable.sum()
    if n_filled > 0:
        logger.debug("NaN interpolation", pixels_filled=int(n_filled))

    return filled


# ============================================================
# Full Preprocessing Pipeline
# ============================================================

class PreprocessedGrids:
    """
    Container for all preprocessed satellite grids on a common grid.
    All arrays share the same lat/lon axes.
    """

    def __init__(
        self,
        lat: np.ndarray,
        lon: np.ndarray,
        sst: np.ndarray,
        sst_anomaly: np.ndarray | None,
        sst_gradient: np.ndarray | None,
        chlorophyll: np.ndarray,
        chlorophyll_log: np.ndarray,
        ssh: np.ndarray | None,
        ssha: np.ndarray | None,
        aph: np.ndarray | None,
    ):
        self.lat = lat
        self.lon = lon
        self.sst = sst
        self.sst_anomaly = sst_anomaly
        self.sst_gradient = sst_gradient
        self.chlorophyll = chlorophyll
        self.chlorophyll_log = chlorophyll_log
        self.ssh = ssh
        self.ssha = ssha
        self.aph = aph


def preprocess_satellite_data(
    pace_data,
    sst_data,
    swot_data,
    bounding_box: tuple[float, float, float, float],
    resolution_deg: float = 0.04,
) -> PreprocessedGrids:
    """
    Full preprocessing pipeline for satellite data.

    Steps:
    1. Create a common grid at target resolution
    2. Quality-filter each dataset
    3. Convert units (Kelvin→°C, log-chlorophyll)
    4. Regrid all sources to the common grid
    5. Fill small NaN gaps

    Args:
        pace_data: PACEOceanDataset (or None)
        sst_data: SSTDataset (or None)
        swot_data: SWOTDataset (or None)
        bounding_box: (west, south, east, north) degrees
        resolution_deg: Target grid resolution (default ~4 km)

    Returns:
        PreprocessedGrids with all arrays on the common grid
    """
    logger.info("Starting grid preprocessing", bbox=bounding_box, res=resolution_deg)

    # Step 1: Common grid
    target_lat, target_lon = create_common_grid(bounding_box, resolution_deg)
    n_lat, n_lon = len(target_lat), len(target_lon)

    # Step 2–5: Process each dataset

    # ---- SST ----
    sst_grid = np.full((n_lat, n_lon), np.nan, dtype=np.float32)
    sst_anom_grid = None
    sst_grad_grid = None

    if sst_data is not None:
        raw_sst = kelvin_to_celsius(sst_data.sst)
        raw_sst = quality_filter_sst(raw_sst)
        sst_grid = regrid_to_common_grid(raw_sst, sst_data.lat, sst_data.lon, target_lat, target_lon)
        sst_grid = interpolate_nans(sst_grid)

        if sst_data.sst_anomaly is not None:
            sst_anom_grid = regrid_to_common_grid(
                sst_data.sst_anomaly, sst_data.lat, sst_data.lon, target_lat, target_lon,
            )
            sst_anom_grid = interpolate_nans(sst_anom_grid)

        if sst_data.sst_gradient is not None:
            sst_grad_grid = regrid_to_common_grid(
                sst_data.sst_gradient, sst_data.lat, sst_data.lon, target_lat, target_lon,
            )

    # ---- Chlorophyll (PACE) ----
    chlor_grid = np.full((n_lat, n_lon), np.nan, dtype=np.float32)
    chlor_log_grid = np.full((n_lat, n_lon), np.nan, dtype=np.float32)
    aph_grid = None

    if pace_data is not None:
        raw_chlor = quality_filter_chlorophyll(pace_data.chlor_a)
        chlor_grid = regrid_to_common_grid(raw_chlor, pace_data.lat, pace_data.lon, target_lat, target_lon)
        chlor_grid = interpolate_nans(chlor_grid)
        chlor_log_grid = log_transform_chlorophyll(chlor_grid)

        if pace_data.aph is not None:
            aph_grid = regrid_to_common_grid(pace_data.aph, pace_data.lat, pace_data.lon, target_lat, target_lon)

    # ---- SSH / SSHA (SWOT) ----
    ssh_grid = None
    ssha_grid = None

    if swot_data is not None and swot_data.ssha is not None:
        # SWOT uses swath geometry (2D lat/lon) — need to handle differently
        # For swath→grid conversion, we use nearest-neighbor on the irregular points
        swot_lat_flat = swot_data.lat.ravel()
        swot_lon_flat = swot_data.lon.ravel()
        swot_valid = np.isfinite(swot_lat_flat) & np.isfinite(swot_lon_flat)

        if swot_valid.any():
            ssh_flat = quality_filter_ssh(swot_data.ssh.ravel())
            ssha_flat = swot_data.ssha.ravel()

            src_points = np.column_stack([swot_lat_flat[swot_valid], swot_lon_flat[swot_valid]])
            tgt_lat_g, tgt_lon_g = np.meshgrid(target_lat, target_lon, indexing="ij")
            tgt_points = np.column_stack([tgt_lat_g.ravel(), tgt_lon_g.ravel()])

            from scipy.interpolate import griddata as gd

            ssh_vals = ssh_flat[swot_valid]
            ssh_valid2 = np.isfinite(ssh_vals)
            if ssh_valid2.any():
                ssh_grid = gd(
                    src_points[ssh_valid2], ssh_vals[ssh_valid2], tgt_points,
                    method="nearest", fill_value=np.nan,
                ).reshape(n_lat, n_lon).astype(np.float32)

            ssha_vals = ssha_flat[swot_valid]
            ssha_valid2 = np.isfinite(ssha_vals)
            if ssha_valid2.any():
                ssha_grid = gd(
                    src_points[ssha_valid2], ssha_vals[ssha_valid2], tgt_points,
                    method="nearest", fill_value=np.nan,
                ).reshape(n_lat, n_lon).astype(np.float32)

    logger.info(
        "Preprocessing complete",
        grid_shape=(n_lat, n_lon),
        sst_valid=int(np.isfinite(sst_grid).sum()),
        chlor_valid=int(np.isfinite(chlor_grid).sum()),
        has_ssha=ssha_grid is not None,
    )

    return PreprocessedGrids(
        lat=target_lat,
        lon=target_lon,
        sst=sst_grid,
        sst_anomaly=sst_anom_grid,
        sst_gradient=sst_grad_grid,
        chlorophyll=chlor_grid,
        chlorophyll_log=chlor_log_grid,
        ssh=ssh_grid,
        ssha=ssha_grid,
        aph=aph_grid,
    )
