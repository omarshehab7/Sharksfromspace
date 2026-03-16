"""
run_predictions.py — Ruflo Task: Run Shark Habitat Prediction (Step 7)
========================================================================

Loads the feature DataFrame and runs the shark prediction model.
Outputs probability_of_shark_activity for each ocean grid cell.
"""

import os
import sys
import pickle

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from models.ml_model import SharkPredictionModel


def main():
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")

    # Load features
    features_path = os.path.join(processed_dir, "features.pkl")
    with open(features_path, "rb") as f:
        features = pickle.load(f)

    print(f"[run_predictions] {len(features)} cells to predict")

    # Load and run model
    model = SharkPredictionModel()
    model.load()

    predictions = model.predict(features)

    # Save predictions
    output_path = os.path.join(processed_dir, "predictions.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(predictions, f)

    high = (predictions["risk_level"] == "high").sum()
    medium = (predictions["risk_level"] == "medium").sum()
    mean_prob = predictions["probability_of_shark_activity"].mean()

    print(f"[run_predictions] High risk: {high}, Medium: {medium}")
    print(f"[run_predictions] Mean probability: {mean_prob:.3f}")
    print(f"[run_predictions] Saved to {output_path}")


if __name__ == "__main__":
    main()
