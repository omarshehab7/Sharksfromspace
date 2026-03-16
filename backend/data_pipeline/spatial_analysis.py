"""
spatial_analysis.py — Geospatial Output Generation (Pipeline Step 8)
======================================================================

Converts prediction results into geospatial formats:

  • GeoJSON hotspot layers — polygonal hotspot regions for the mobile app
  • Heatmap rasters — GeoTIFF probability grids for Mapbox overlay
  • GeoDataFrame operations — point-to-polygon conversion, buffering, etc.

These outputs are the final product of the pipeline, consumed directly
by the mobile app's map layers and the backend API endpoints.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_bounds
from shapely.geometry import Point, mapping
import structlog

logger = structlog.get_logger(__name__)


# ============================================================
# Grid → GeoDataFrame
# ============================================================

def predictions_to_geodataframe(
    predictions: pd.DataFrame,
    crs: str = "EPSG:4326",
) -> gpd.GeoDataFrame:
    """
    Convert a predictions DataFrame (with lat/lon columns) to a GeoDataFrame.

    Args:
        predictions: DataFrame with columns including "lat", "lon", "risk_score"
        crs: Coordinate reference system (default WGS84)

    Returns:
        GeoDataFrame with Point geometries
    """
    geometry = [Point(lon, lat) for lat, lon in zip(predictions["lat"], predictions["lon"])]
    gdf = gpd.GeoDataFrame(predictions, geometry=geometry, crs=crs)
    logger.info("Created prediction GeoDataFrame", points=len(gdf))
    return gdf


# ============================================================
# GeoJSON Hotspot Layers
# ============================================================

def generate_hotspot_geojson(
    predictions: pd.DataFrame,
    output_path: str,
    risk_threshold: float = 0.5,
    buffer_km: float = 10.0,
    simplify_tolerance: float = 0.01,
) -> str:
    """
    Generate a GeoJSON file containing shark activity hotspot polygons.

    Steps:
    1. Filter predictions to high-risk cells
    2. Buffer each point by buffer_km
    3. Merge overlapping buffers into hotspot polygons
    4. Add aggregated metadata (mean risk, species, etc.)
    5. Write GeoJSON

    Args:
        predictions: DataFrame with lat, lon, risk_score, risk_level, species
        output_path: Path to write the .geojson file
        risk_threshold: Minimum risk_score to include
        buffer_km: Buffer radius in km around each prediction point
        simplify_tolerance: Simplification tolerance in degrees (for smaller files)

    Returns:
        Path to the written GeoJSON file
    """
    # Filter to high-risk predictions
    high_risk = predictions[predictions["risk_score"] >= risk_threshold].copy()

    if len(high_risk) == 0:
        logger.info("No hotspots above threshold", threshold=risk_threshold)
        _write_empty_geojson(output_path)
        return output_path

    # Create point GeoDataFrame
    gdf = predictions_to_geodataframe(high_risk)

    # Project to metric CRS for accurate buffering
    gdf_proj = gdf.to_crs("EPSG:3857")
    gdf_proj["geometry"] = gdf_proj.geometry.buffer(buffer_km * 1000)

    # Dissolve overlapping buffers into merged polygons
    gdf_proj["cluster"] = 1  # All in one group for dissolve
    merged = gdf_proj.dissolve(by="cluster", aggfunc={
        "risk_score": "mean",
    })

    # Explode multipolygons into individual polygons
    hotspots = merged.explode(index_parts=False).reset_index(drop=True)

    # Simplify geometries for smaller file size
    hotspots = hotspots.to_crs("EPSG:4326")
    hotspots["geometry"] = hotspots.geometry.simplify(simplify_tolerance)

    # Assign risk levels to each polygon
    hotspots["risk_level"] = hotspots["risk_score"].apply(
        lambda s: "high" if s >= 0.6 else ("medium" if s >= 0.3 else "low")
    )

    # Add metadata
    hotspots["id"] = [f"hotspot-{i+1}" for i in range(len(hotspots))]
    hotspots["area_km2"] = hotspots.to_crs("EPSG:3857").geometry.area / 1e6

    # Write GeoJSON
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    hotspots.to_file(output_path, driver="GeoJSON")

    logger.info(
        "GeoJSON hotspots written",
        path=output_path,
        n_hotspots=len(hotspots),
        mean_risk=float(hotspots["risk_score"].mean()),
    )
    return output_path


def generate_point_geojson(
    predictions: pd.DataFrame,
    output_path: str,
    risk_threshold: float = 0.3,
) -> str:
    """
    Generate a GeoJSON file with individual prediction points.

    Lighter than polygon hotspots — used for point markers on the map.

    Args:
        predictions: DataFrame with lat, lon, risk_score columns
        output_path: Path to write .geojson file
        risk_threshold: Minimum risk_score to include

    Returns:
        Path to the written GeoJSON file
    """
    filtered = predictions[predictions["risk_score"] >= risk_threshold].copy()

    if len(filtered) == 0:
        _write_empty_geojson(output_path)
        return output_path

    # Build GeoJSON features manually for full control
    features = []
    for _, row in filtered.iterrows():
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(row["lon"]), float(row["lat"])],
            },
            "properties": {
                "risk_score": round(float(row["risk_score"]), 3),
                "risk_level": row.get("risk_level", "unknown"),
                "sst": round(float(row.get("sst", 0)), 1),
                "chlorophyll": round(float(row.get("chlorophyll", 0)), 3),
            },
        }
        if "species" in row.index:
            species = row["species"]
            if isinstance(species, list):
                feature["properties"]["species"] = species
            else:
                feature["properties"]["species"] = [str(species)]

        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features,
    }

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(geojson, f, indent=2)

    logger.info("Point GeoJSON written", path=output_path, points=len(features))
    return output_path


def _write_empty_geojson(path: str) -> None:
    """Write an empty GeoJSON FeatureCollection."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"type": "FeatureCollection", "features": []}, f)


# ============================================================
# Heatmap Raster Layers (GeoTIFF)
# ============================================================

def generate_heatmap_raster(
    lat: np.ndarray,
    lon: np.ndarray,
    risk_scores: np.ndarray,
    output_path: str,
    nodata: float = -9999.0,
) -> str:
    """
    Write a 2D risk score grid as a GeoTIFF raster file.

    Produces a single-band GeoTIFF with probability_of_shark_activity
    values in [0, 1]. Can be served as a Mapbox raster tile source.

    Args:
        lat: 1D latitude array (south to north)
        lon: 1D longitude array (west to east)
        risk_scores: 2D array of risk scores, shape (len(lat), len(lon))
        output_path: Path to write the .tif file
        nodata: NoData value for invalid pixels

    Returns:
        Path to the written GeoTIFF file
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Replace NaN with nodata
    data = risk_scores.copy()
    data[np.isnan(data)] = nodata

    # Compute geotransform from lat/lon arrays
    west = float(lon.min())
    east = float(lon.max())
    south = float(lat.min())
    north = float(lat.max())

    n_rows = len(lat)
    n_cols = len(lon)

    transform = from_bounds(west, south, east, north, n_cols, n_rows)

    # Rasterio expects data in (bands, rows, cols) with north-up orientation
    # If lat is ascending (south→north), flip vertically for GeoTIFF (north→south)
    if len(lat) > 1 and lat[0] < lat[-1]:
        data = np.flipud(data)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=n_rows,
        width=n_cols,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        dst.write(data.astype(np.float32), 1)
        dst.update_tags(
            DESCRIPTION="Sharks From Space - Probability of Shark Activity",
            UNITS="probability [0, 1]",
        )

    logger.info(
        "Heatmap raster written",
        path=output_path,
        shape=(n_rows, n_cols),
        bounds=(west, south, east, north),
    )
    return output_path


def generate_multi_band_raster(
    lat: np.ndarray,
    lon: np.ndarray,
    bands: dict[str, np.ndarray],
    output_path: str,
    nodata: float = -9999.0,
) -> str:
    """
    Write multiple 2D arrays as a multi-band GeoTIFF.

    Useful for storing SST, chlorophyll, risk score, etc. in a single file.

    Args:
        lat: 1D latitude array
        lon: 1D longitude array
        bands: Dict mapping band name to 2D array
        output_path: Path to write .tif
        nodata: NoData fill value

    Returns:
        Path to the written GeoTIFF
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    n_bands = len(bands)
    n_rows = len(lat)
    n_cols = len(lon)

    west, east = float(lon.min()), float(lon.max())
    south, north = float(lat.min()), float(lat.max())

    transform = from_bounds(west, south, east, north, n_cols, n_rows)

    with rasterio.open(
        output_path,
        "w",
        driver="GTiff",
        height=n_rows,
        width=n_cols,
        count=n_bands,
        dtype="float32",
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
        compress="deflate",
    ) as dst:
        for i, (name, data) in enumerate(bands.items(), 1):
            band_data = data.copy()
            band_data[np.isnan(band_data)] = nodata
            if len(lat) > 1 and lat[0] < lat[-1]:
                band_data = np.flipud(band_data)
            dst.write(band_data.astype(np.float32), i)
            dst.set_band_description(i, name)

    logger.info("Multi-band raster written", path=output_path, bands=list(bands.keys()))
    return output_path
