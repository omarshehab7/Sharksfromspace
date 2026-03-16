"""
extract_features.py — Ruflo Task: Extract Environmental Features (Step 3)
===========================================================================

Combines all preprocessed grids and detection results into a single
ML feature DataFrame.
"""

import os
import sys
import pickle
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.feature_engineering import extract_full_features, normalize_features


def main():
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")

    # Load all intermediate results
    with open(os.path.join(processed_dir, "preprocessed_grids.pkl"), "rb") as f:
        grids = pickle.load(f)

    front_results = {}
    front_path = os.path.join(processed_dir, "front_results.pkl")
    if os.path.exists(front_path):
        with open(front_path, "rb") as f:
            front_results = pickle.load(f)

    eddy_results = {}
    eddy_path = os.path.join(processed_dir, "eddy_results.pkl")
    if os.path.exists(eddy_path):
        with open(eddy_path, "rb") as f:
            eddy_results = pickle.load(f)

    productivity = None
    prod_path = os.path.join(processed_dir, "productivity_index.pkl")
    if os.path.exists(prod_path):
        with open(prod_path, "rb") as f:
            productivity = pickle.load(f)

    now = datetime.utcnow()

    print("[extract_features] Building feature DataFrame")

    features_df = extract_full_features(
        lat=grids.lat,
        lon=grids.lon,
        sst=grids.sst,
        chlorophyll=grids.chlorophyll,
        sst_anomaly=grids.sst_anomaly,
        sst_gradient=grids.sst_gradient,
        chlorophyll_log=grids.chlorophyll_log,
        front_intensity=front_results.get("front_intensity"),
        eddy_proximity_score=eddy_results.get("eddy_proximity_score"),
        productivity_index=productivity,
        day_of_year=now.timetuple().tm_yday,
        month=now.month,
    )

    # Normalize features
    features_normalized, scaler_params = normalize_features(features_df)

    # Save
    features_path = os.path.join(processed_dir, "features.pkl")
    with open(features_path, "wb") as f:
        pickle.dump(features_normalized, f)

    scaler_path = os.path.join(processed_dir, "scaler_params.pkl")
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler_params, f)

    print(f"[extract_features] {len(features_normalized)} ocean cells, {len(features_normalized.columns)} features")
    print(f"[extract_features] Saved to {features_path}")


if __name__ == "__main__":
    main()
