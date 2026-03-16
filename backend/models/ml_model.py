"""
ml_model.py — Shark Habitat Prediction Model (Pipeline Step 7)
================================================================

Predicts probability of shark activity at each ocean grid cell
using a weighted habitat suitability model.

The model implements the core formula:

  HabitatScore = temperature_weight × SST_score
               + productivity_weight × chlorophyll_score
               + front_weight × front_intensity
               + eddy_weight × eddy_proximity

When a trained scikit-learn GradientBoostingClassifier is available,
it replaces the heuristic formula with a data-driven prediction.

Outputs:
  • probability_of_shark_activity (0–1)
  • risk_level: low / medium / high
  • likely_species: list based on SST preference ranges
"""

from __future__ import annotations

import os
import numpy as np
import pandas as pd
import joblib
import structlog
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score
from config import settings

logger = structlog.get_logger(__name__)


# ============================================================
# Constants
# ============================================================

RISK_THRESHOLDS = {
    "low": (0.0, 0.3),
    "medium": (0.3, 0.6),
    "high": (0.6, 1.0),
}

# Shark species → preferred SST range (°C)
SPECIES_SST_RANGES = {
    "Great White Shark": (12, 24),
    "Tiger Shark": (20, 30),
    "Hammerhead Shark": (18, 28),
    "Bull Shark": (20, 32),
    "Whale Shark": (21, 30),
    "Mako Shark": (15, 25),
    "Blue Shark": (10, 22),
}

# Habitat model weights (used when no trained model is available)
HABITAT_WEIGHTS = {
    "temperature": 0.30,
    "productivity": 0.25,
    "front": 0.25,
    "eddy": 0.20,
}

# Features used by the ML model
FEATURE_COLUMNS = [
    "sst",
    "sst_anomaly",
    "sst_gradient",
    "chlorophyll",
    "chlorophyll_log",
    "front_intensity",
    "eddy_proximity",
    "productivity_index",
    "depth",
    "distance_to_coast_km",
    "day_of_year",
    "month",
]


# ============================================================
# Habitat Score Functions
# ============================================================

def compute_sst_score(sst: np.ndarray) -> np.ndarray:
    """
    Score SST for shark habitat suitability.

    Most shark species prefer 18–28°C. The score uses a Gaussian
    envelope centered at 23°C with σ = 5°C.

    Args:
        sst: 1D array of SST values (°C)

    Returns:
        1D array of scores in [0, 1]
    """
    optimal_temp = 23.0
    sigma = 5.0
    score = np.exp(-0.5 * ((sst - optimal_temp) / sigma) ** 2)
    return np.clip(score, 0, 1).astype(np.float32)


def compute_chlorophyll_score(chlor: np.ndarray) -> np.ndarray:
    """
    Score chlorophyll-a for prey availability.

    Moderate chlorophyll (0.3–3.0 mg/m³) = productive waters with prey.
    Very low = oligotrophic desert. Very high = possible harmful bloom.

    Uses a log-normal distribution centered at log10(1.0) = 0.

    Args:
        chlor: 1D array of chlorophyll values (mg/m³)

    Returns:
        1D array of scores in [0, 1]
    """
    # Avoid log of zero/negative
    safe = np.clip(chlor, 0.001, 100.0)
    log_chlor = np.log10(safe)
    optimal_log = 0.0  # log10(1.0 mg/m³)
    sigma = 0.8
    score = np.exp(-0.5 * ((log_chlor - optimal_log) / sigma) ** 2)
    return np.clip(score, 0, 1).astype(np.float32)


def compute_habitat_score(features: pd.DataFrame) -> np.ndarray:
    """
    Compute the weighted habitat suitability score.

    Implements:
      HabitatScore = temperature_weight × SST_score
                   + productivity_weight × chlorophyll_score
                   + front_weight × front_intensity
                   + eddy_weight × eddy_proximity

    All components are individually scored to [0, 1] before weighting.

    Args:
        features: DataFrame with columns: sst, chlorophyll,
                  front_intensity, eddy_proximity

    Returns:
        1D array of habitat scores in [0, 1]
    """
    n = len(features)
    score = np.zeros(n, dtype=np.float32)

    w = HABITAT_WEIGHTS

    # Temperature component
    if "sst" in features.columns:
        sst_score = compute_sst_score(features["sst"].values)
        score += w["temperature"] * sst_score

    # Productivity component (use productivity_index if available, else chlorophyll)
    if "productivity_index" in features.columns:
        prod_score = np.clip(features["productivity_index"].fillna(0).values, 0, 1)
        score += w["productivity"] * prod_score
    elif "chlorophyll" in features.columns:
        chlor_score = compute_chlorophyll_score(features["chlorophyll"].values)
        score += w["productivity"] * chlor_score

    # Front component
    if "front_intensity" in features.columns:
        front_score = np.clip(features["front_intensity"].fillna(0).values, 0, 1)
        score += w["front"] * front_score

    # Eddy component
    if "eddy_proximity" in features.columns:
        eddy_score = np.clip(features["eddy_proximity"].fillna(0).values, 0, 1)
        score += w["eddy"] * eddy_score

    # Bonus: SST anomaly boost (warm anomalies slightly increase score)
    if "sst_anomaly" in features.columns:
        anomaly = features["sst_anomaly"].fillna(0).values
        anomaly_boost = np.clip(anomaly / 3.0, -0.1, 0.1)
        score += anomaly_boost

    # Bonus: Depth preference (continental shelf 20-200m)
    if "depth" in features.columns:
        depth = np.abs(features["depth"].fillna(0).values)
        depth_mask = (depth >= 20) & (depth <= 200)
        score[depth_mask] += 0.05

    return np.clip(score, 0.0, 1.0).astype(np.float32)


# ============================================================
# Species Prediction
# ============================================================

def predict_species(sst: float) -> list[str]:
    """
    Predict likely shark species based on SST.

    Args:
        sst: Sea surface temperature (°C)

    Returns:
        List of species names that prefer this temperature range
    """
    if np.isnan(sst):
        return ["Unknown"]

    species = []
    for name, (min_t, max_t) in SPECIES_SST_RANGES.items():
        if min_t <= sst <= max_t:
            species.append(name)

    return species if species else ["Unknown"]


def score_to_risk_level(score: float) -> str:
    """Convert numeric risk score to categorical level."""
    if score >= 0.6:
        return "high"
    elif score >= 0.3:
        return "medium"
    return "low"


# ============================================================
# Main Prediction Model
# ============================================================

class SharkPredictionModel:
    """
    Shark habitat prediction model.

    Primary interface for the pipeline. Supports two modes:
    1. Heuristic formula (when no trained model file exists)
    2. Trained GradientBoosting classifier (loaded from disk)

    Usage:
        model = SharkPredictionModel()
        model.load()
        predictions = model.predict(features_df)
    """

    def __init__(self):
        self.model: GradientBoostingClassifier | None = None
        self.model_path = settings.MODEL_PATH
        self.threshold = settings.PREDICTION_THRESHOLD

    def load(self) -> None:
        """Load a trained model from disk if available."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            logger.info("Trained ML model loaded", path=self.model_path)
        else:
            logger.info(
                "No trained model found — using heuristic habitat scoring",
                path=self.model_path,
            )

    def predict(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Generate shark activity predictions for all grid cells.

        Output columns added:
          - probability_of_shark_activity (float, 0–1)
          - risk_score (alias for probability)
          - risk_level ("low" / "medium" / "high")
          - species (list of likely shark species)

        Args:
            features: DataFrame with ocean condition features

        Returns:
            DataFrame with prediction columns added
        """
        result = features.copy()

        if self.model is not None:
            # ---- Trained model inference ----
            X = self._prepare_features(features)
            probabilities = self.model.predict_proba(X)[:, 1]
            result["probability_of_shark_activity"] = probabilities
        else:
            # ---- Heuristic habitat score ----
            result["probability_of_shark_activity"] = compute_habitat_score(features)

        # Alias for backward compatibility
        result["risk_score"] = result["probability_of_shark_activity"]

        # Risk levels
        result["risk_level"] = result["risk_score"].apply(score_to_risk_level)

        # Species prediction
        if "sst" in result.columns:
            result["species"] = result["sst"].apply(predict_species)
        else:
            result["species"] = [["Unknown"]] * len(result)

        logger.info(
            "Predictions generated",
            n_cells=len(result),
            high_risk=int((result["risk_level"] == "high").sum()),
            medium_risk=int((result["risk_level"] == "medium").sum()),
            mean_probability=float(result["probability_of_shark_activity"].mean()),
        )

        return result

    def _prepare_features(self, features: pd.DataFrame) -> pd.DataFrame:
        """Prepare feature matrix for the trained model."""
        available = [c for c in FEATURE_COLUMNS if c in features.columns]
        X = features[available].fillna(0).copy()

        # Add missing columns as zeros
        for col in FEATURE_COLUMNS:
            if col not in X.columns:
                X[col] = 0.0

        return X[FEATURE_COLUMNS]

    # ============================================================
    # Training
    # ============================================================

    def train(
        self,
        features: pd.DataFrame,
        labels: np.ndarray,
        test_size: float = 0.2,
    ) -> dict:
        """
        Train a GradientBoosting classifier on labeled data.

        Args:
            features: DataFrame with FEATURE_COLUMNS
            labels: Binary labels (1=shark activity, 0=no activity)
            test_size: Fraction reserved for validation

        Returns:
            Dict with training metrics (accuracy, AUC, classification report)
        """
        logger.info("Training shark prediction model", samples=len(features))

        X = self._prepare_features(features)
        y = labels

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y,
        )

        self.model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            min_samples_leaf=10,
            subsample=0.8,
            random_state=42,
        )
        self.model.fit(X_train, y_train)

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_proba = self.model.predict_proba(X_test)[:, 1]

        auc_score = roc_auc_score(y_test, y_proba)
        report = classification_report(y_test, y_pred, output_dict=True)

        # Feature importance
        importance = dict(zip(FEATURE_COLUMNS, self.model.feature_importances_))

        metrics = {
            "auc": auc_score,
            "accuracy": report["accuracy"],
            "classification_report": report,
            "feature_importance": importance,
        }

        logger.info(
            "Model training complete",
            auc=round(auc_score, 4),
            accuracy=round(metrics["accuracy"], 4),
        )

        return metrics

    def save(self, path: str | None = None) -> str:
        """Save the trained model to disk."""
        save_path = path or self.model_path
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        joblib.dump(self.model, save_path)
        logger.info("Model saved", path=save_path)
        return save_path
