"""
generate_outputs.py — Ruflo Task: Generate Geospatial Outputs (Step 8)
========================================================================

Creates the final output layers consumed by the mobile app:
  • GeoJSON hotspot polygons (buffered + merged high-risk zones)
  • GeoJSON prediction points (individual scored locations)
  • GeoTIFF heatmap raster (probability_of_shark_activity grid)
  • Multi-band GeoTIFF (SST + chlorophyll + risk in one file)
"""

import os
import sys
import pickle
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.spatial_analysis import (
    generate_hotspot_geojson,
    generate_point_geojson,
    generate_heatmap_raster,
    generate_multi_band_raster,
)


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    return (parts[0], parts[1], parts[2], parts[3])


def main():
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")
    output_dir = os.environ.get("OUTPUT_DIR", "./data/output")
    risk_threshold = float(os.environ.get("RISK_THRESHOLD", "0.5"))
    bbox = parse_bbox(os.environ.get("BOUNDING_BOX", "-80,20,-60,35"))
    resolution = float(os.environ.get("RESOLUTION_DEG", "0.04"))

    os.makedirs(output_dir, exist_ok=True)

    # Load predictions
    with open(os.path.join(processed_dir, "predictions.pkl"), "rb") as f:
        predictions = pickle.load(f)

    # Load grid info
    with open(os.path.join(processed_dir, "preprocessed_grids.pkl"), "rb") as f:
        grids = pickle.load(f)

    print(f"[generate_outputs] {len(predictions)} predictions, threshold={risk_threshold}")

    # ---- GeoJSON Hotspot Polygons ----
    hotspot_path = generate_hotspot_geojson(
        predictions=predictions,
        output_path=os.path.join(output_dir, "hotspots.geojson"),
        risk_threshold=risk_threshold,
        buffer_km=10.0,
    )
    print(f"[generate_outputs] Hotspot GeoJSON: {hotspot_path}")

    # ---- GeoJSON Points ----
    points_path = generate_point_geojson(
        predictions=predictions,
        output_path=os.path.join(output_dir, "prediction_points.geojson"),
        risk_threshold=0.3,
    )
    print(f"[generate_outputs] Point GeoJSON: {points_path}")

    # ---- Heatmap Raster ----
    # Reconstruct the risk score grid from the predictions DataFrame
    lat = grids.lat
    lon = grids.lon
    risk_grid = np.full((len(lat), len(lon)), np.nan, dtype=np.float32)

    for _, row in predictions.iterrows():
        lat_idx = np.argmin(np.abs(lat - row["lat"]))
        lon_idx = np.argmin(np.abs(lon - row["lon"]))
        risk_grid[lat_idx, lon_idx] = row["probability_of_shark_activity"]

    heatmap_path = generate_heatmap_raster(
        lat=lat,
        lon=lon,
        risk_scores=risk_grid,
        output_path=os.path.join(output_dir, "shark_activity_heatmap.tif"),
    )
    print(f"[generate_outputs] Heatmap raster: {heatmap_path}")

    # ---- Multi-band diagnostic raster ----
    bands = {"risk_score": risk_grid}
    if hasattr(grids, "sst"):
        bands["sst"] = grids.sst
    if hasattr(grids, "chlorophyll"):
        bands["chlorophyll"] = grids.chlorophyll

    multi_path = generate_multi_band_raster(
        lat=lat,
        lon=lon,
        bands=bands,
        output_path=os.path.join(output_dir, "ocean_layers.tif"),
    )
    print(f"[generate_outputs] Multi-band raster: {multi_path}")
    print("[generate_outputs] All outputs generated successfully")


if __name__ == "__main__":
    main()
