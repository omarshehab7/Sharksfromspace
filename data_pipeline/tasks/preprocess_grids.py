"""
preprocess_grids.py — Ruflo Task: Preprocess Satellite Grids (Step 2)
=====================================================================

Loads the CombinedOceanDataset from Step 1, runs the preprocessing
pipeline (quality filtering, regridding, NaN interpolation), and
saves PreprocessedGrids for downstream tasks.
"""

import os
import sys
import pickle
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.transform import preprocess_satellite_data


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    return (parts[0], parts[1], parts[2], parts[3])


def main():
    raw_dir = os.environ.get("DATA_RAW_DIR", "./data/raw")
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")
    bbox = parse_bbox(os.environ.get("BOUNDING_BOX", "-80,20,-60,35"))
    resolution = float(os.environ.get("RESOLUTION_DEG", "0.04"))

    os.makedirs(processed_dir, exist_ok=True)

    # Load dataset from Step 1
    dataset_path = os.path.join(raw_dir, "combined_dataset.pkl")
    with open(dataset_path, "rb") as f:
        dataset = pickle.load(f)

    print(f"[preprocess] Running grid preprocessing at {resolution}° resolution")

    grids = preprocess_satellite_data(
        pace_data=dataset.pace,
        sst_data=dataset.sst,
        swot_data=dataset.swot,
        bounding_box=bbox,
        resolution_deg=resolution,
    )

    # Save preprocessed grids
    output_path = os.path.join(processed_dir, "preprocessed_grids.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(grids, f)

    print(f"[preprocess] Grid shape: ({len(grids.lat)}, {len(grids.lon)})")
    print(f"[preprocess] SST valid: {np.isfinite(grids.sst).sum()}")
    print(f"[preprocess] Chlor valid: {np.isfinite(grids.chlorophyll).sum()}")
    print(f"[preprocess] Saved to {output_path}")


if __name__ == "__main__":
    main()
