"""
compute_features.py — Build ML Features
==========================================

Ruflo task that extracts machine learning features from
processed ocean data files. Outputs a feature matrix
ready for the prediction model.

Features extracted:
- SST (absolute and anomaly)
- SST gradient (thermal fronts)
- Chlorophyll-a concentration
- Bathymetry (depth)
- Day of year, month (seasonal signal)

Usage: ruflo run --task compute_features
"""

import os
import glob
import pandas as pd
import xarray as xr
import numpy as np
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)


def main():
    """Compute ML features from processed ocean data."""
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")
    output_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")

    logger.info("Starting feature computation", source_dir=processed_dir)

    # TODO: Load processed SST, chlorophyll, and bathymetry data
    # TODO: Compute SST anomaly from climatology
    # TODO: Compute SST gradient magnitude
    # TODO: Merge all variables onto common grid
    # TODO: Extract feature DataFrame
    # TODO: Save feature matrix as parquet

    output_path = os.path.join(output_dir, "features.parquet")

    # Placeholder feature matrix
    features = pd.DataFrame(columns=[
        "lat", "lon",
        "sst", "sst_anomaly", "sst_gradient",
        "chlorophyll", "depth",
        "distance_to_coast_km",
        "day_of_year", "month",
    ])

    features.to_parquet(output_path, index=False)
    logger.info("Feature computation complete", output=output_path, rows=len(features))


if __name__ == "__main__":
    main()
