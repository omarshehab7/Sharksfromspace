"""
detect_eddies.py — Ruflo Task: Detect Eddy Structures (Step 5)
================================================================

Detects mesoscale eddies from SSHA and computes proximity scores.
"""

import os
import sys
import pickle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.eddy_detection import detect_eddies


def main():
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")

    grids_path = os.path.join(processed_dir, "preprocessed_grids.pkl")
    with open(grids_path, "rb") as f:
        grids = pickle.load(f)

    print("[detect_eddies] Running eddy detection")

    results = detect_eddies(
        ssha=grids.ssha,
        threshold_m=0.10,
        min_size_pixels=25,
    )

    output_path = os.path.join(processed_dir, "eddy_results.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(results, f)

    print(f"[detect_eddies] Eddies found: {results['n_eddies']}")
    print(f"[detect_eddies] Saved to {output_path}")


if __name__ == "__main__":
    main()
