"""
compute_productivity.py — Ruflo Task: Compute Productivity Index (Step 6)
===========================================================================

Computes the composite marine ecosystem productivity index.
"""

import os
import sys
import pickle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.productivity_index import compute_productivity_index


def main():
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")

    # Load preprocessed grids
    grids_path = os.path.join(processed_dir, "preprocessed_grids.pkl")
    with open(grids_path, "rb") as f:
        grids = pickle.load(f)

    # Load front results (front_intensity is an input)
    front_path = os.path.join(processed_dir, "front_results.pkl")
    front_intensity = None
    if os.path.exists(front_path):
        with open(front_path, "rb") as f:
            front_results = pickle.load(f)
            front_intensity = front_results.get("front_intensity")

    print("[compute_productivity] Computing productivity index")

    productivity = compute_productivity_index(
        chlorophyll=grids.chlorophyll,
        aph=grids.aph,
        sst_anomaly=grids.sst_anomaly,
        front_intensity=front_intensity,
    )

    output_path = os.path.join(processed_dir, "productivity_index.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(productivity, f)

    import numpy as np
    print(f"[compute_productivity] Mean index: {np.nanmean(productivity):.3f}")
    print(f"[compute_productivity] Saved to {output_path}")


if __name__ == "__main__":
    main()
