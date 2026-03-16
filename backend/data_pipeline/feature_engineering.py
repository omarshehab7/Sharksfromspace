"""
feature_engineering.py — ML Feature Extraction (Pipeline Step 3+)
===================================================================

Extracts machine learning features from all preprocessed satellite grids.
Combines outputs from transform, ocean_fronts, eddy_detection, and
productivity_index into a single feature DataFrame.

Each row in the output DataFrame represents one ocean grid cell with
all features needed by the shark habitat prediction model.

Feature set:
  ├── SST (°C)                 — thermal habitat preference
  ├── SST anomaly (°C)         — unusual conditions
  ├── SST gradient             — raw thermal gradient
  ├── Chlorophyll-a (mg/m³)    — prey availability proxy
  ├── Chlorophyll-a log10      — log-transformed for ML
  ├── Front intensity [0,1]    — ocean front strength
  ├── Eddy proximity [0,1]     — distance to mesoscale eddies
  ├── Productivity index [0,1] — composite ecosystem productivity
  ├── Depth (m)                — bathymetry (if available)
  ├── Distance to coast (km)   — coastal proximity (if available)
  ├── Day of year              — seasonal signal
  └── Month                    — seasonal signal
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import structlog

logger = structlog.get_logger(__name__)


def extract_full_features(
    lat: np.ndarray,
    lon: np.ndarray,
    sst: np.ndarray,
    chlorophyll: np.ndarray,
    sst_anomaly: np.ndarray | None = None,
    sst_gradient: np.ndarray | None = None,
    chlorophyll_log: np.ndarray | None = None,
    front_intensity: np.ndarray | None = None,
    eddy_proximity_score: np.ndarray | None = None,
    productivity_index: np.ndarray | None = None,
    depth: np.ndarray | None = None,
    distance_to_coast: np.ndarray | None = None,
    day_of_year: int | None = None,
    month: int | None = None,
) -> pd.DataFrame:
    """
    Build a complete feature DataFrame from all satellite-derived grids.

    All 2D arrays should have shape (len(lat), len(lon)).
    Rows with NaN in SST or chlorophyll are dropped (land/missing).

    Args:
        lat: 1D latitude array
        lon: 1D longitude array
        sst: 2D SST array (°C)
        chlorophyll: 2D chlorophyll-a array (mg/m³)
        sst_anomaly: 2D SST anomaly (°C)
        sst_gradient: 2D SST gradient magnitude
        chlorophyll_log: 2D log10(chlorophyll)
        front_intensity: 2D front intensity [0,1]
        eddy_proximity_score: 2D eddy proximity [0,1]
        productivity_index: 2D productivity index [0,1]
        depth: 2D depth array (m)
        distance_to_coast: 2D distance to coast (km)
        day_of_year: Julian day (1-366)
        month: Calendar month (1-12)

    Returns:
        DataFrame with one row per valid ocean grid cell
    """
    lat_grid, lon_grid = np.meshgrid(lat, lon, indexing="ij")

    features = {
        "lat": lat_grid.ravel().astype(np.float32),
        "lon": lon_grid.ravel().astype(np.float32),
        "sst": sst.ravel().astype(np.float32),
        "chlorophyll": chlorophyll.ravel().astype(np.float32),
    }

    # Optional features — add as available
    _add_if_available(features, "sst_anomaly", sst_anomaly)
    _add_if_available(features, "sst_gradient", sst_gradient)
    _add_if_available(features, "chlorophyll_log", chlorophyll_log)
    _add_if_available(features, "front_intensity", front_intensity)
    _add_if_available(features, "eddy_proximity", eddy_proximity_score)
    _add_if_available(features, "productivity_index", productivity_index)
    _add_if_available(features, "depth", depth)
    _add_if_available(features, "distance_to_coast_km", distance_to_coast)

    if day_of_year is not None:
        features["day_of_year"] = np.full(len(features["lat"]), day_of_year, dtype=np.int16)
    if month is not None:
        features["month"] = np.full(len(features["lat"]), month, dtype=np.int8)

    df = pd.DataFrame(features)

    # Drop land pixels (NaN in both SST and chlorophyll)
    n_before = len(df)
    df = df.dropna(subset=["sst", "chlorophyll"]).reset_index(drop=True)
    n_after = len(df)

    logger.info(
        "Feature extraction complete",
        total_cells=n_before,
        ocean_cells=n_after,
        land_masked=n_before - n_after,
        features=list(df.columns),
    )

    return df


def _add_if_available(features: dict, name: str, array: np.ndarray | None) -> None:
    """Add an array to the feature dictionary if it's not None."""
    if array is not None:
        features[name] = array.ravel().astype(np.float32)


def normalize_features(
    df: pd.DataFrame,
    feature_columns: list[str] | None = None,
    method: str = "minmax",
) -> tuple[pd.DataFrame, dict[str, tuple[float, float]]]:
    """
    Normalize feature columns for ML model input.

    Args:
        df: Input DataFrame
        feature_columns: Columns to normalize (default: all numeric except lat/lon)
        method: "minmax" (→ [0,1]) or "zscore" (→ mean=0, std=1)

    Returns:
        (normalized_df, scaler_params) — scaler_params stores min/max or mean/std
        for each column, so new data can be normalized consistently
    """
    if feature_columns is None:
        feature_columns = [
            c for c in df.select_dtypes(include=[np.number]).columns
            if c not in ("lat", "lon")
        ]

    df_norm = df.copy()
    scaler_params: dict[str, tuple[float, float]] = {}

    for col in feature_columns:
        if col not in df.columns:
            continue

        vals = df[col].values

        if method == "minmax":
            col_min = np.nanmin(vals)
            col_max = np.nanmax(vals)
            if col_max > col_min:
                df_norm[col] = (vals - col_min) / (col_max - col_min)
            else:
                df_norm[col] = 0.0
            scaler_params[col] = (float(col_min), float(col_max))

        elif method == "zscore":
            col_mean = np.nanmean(vals)
            col_std = np.nanstd(vals)
            if col_std > 0:
                df_norm[col] = (vals - col_mean) / col_std
            else:
                df_norm[col] = 0.0
            scaler_params[col] = (float(col_mean), float(col_std))

    logger.info("Features normalized", method=method, columns=len(feature_columns))
    return df_norm, scaler_params
