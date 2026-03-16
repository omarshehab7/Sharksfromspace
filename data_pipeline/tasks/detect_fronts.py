"""
detect_fronts.py — Ruflo Task: Detect Ocean Fronts (Step 4)
=============================================================

Runs Sobel gradient and Canny edge front detection on
preprocessed SST and chlorophyll grids.
"""

import os
import sys
import pickle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.ocean_fronts import detect_fronts


def main():
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")

    # Load preprocessed grids
    grids_path = os.path.join(processed_dir, "preprocessed_grids.pkl")
    with open(grids_path, "rb") as f:
        grids = pickle.load(f)

    print("[detect_fronts] Running ocean front detection")

    results = detect_fronts(
        sst=grids.sst,
        chlorophyll=grids.chlorophyll,
        smooth_sigma=1.0,
    )

    # Save front results
    output_path = os.path.join(processed_dir, "front_results.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(results, f)

    print(f"[detect_fronts] Front pixels: {results['front_edges'].sum()}")
    print(f"[detect_fronts] Saved to {output_path}")


if __name__ == "__main__":
    main()
