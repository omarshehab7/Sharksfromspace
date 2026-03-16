"""
process_netcdf.py — Process Raw NetCDF4 Data
===============================================

Ruflo task that processes downloaded netCDF4 satellite files:
- Opens datasets with xarray
- Applies quality flags to filter bad data
- Subsets to the region of interest
- Regrids to a common resolution
- Saves processed data to the processed directory

Usage: ruflo run --task process_netcdf
"""

import os
import glob
import xarray as xr
import numpy as np
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)


def process_sst_files(raw_dir: str, processed_dir: str) -> list[str]:
    """Process raw SST netCDF4 files."""
    sst_files = glob.glob(os.path.join(raw_dir, "ghrsst_mur_*.nc")) + \
                glob.glob(os.path.join(raw_dir, "modis_sst_*.nc"))

    processed = []
    for filepath in sst_files:
        logger.info("Processing SST file", path=filepath)
        try:
            ds = xr.open_dataset(filepath, engine="netcdf4")

            # TODO: Apply quality flags
            # TODO: Subset to region of interest
            # TODO: Regrid if needed

            output_path = os.path.join(
                processed_dir,
                f"processed_{os.path.basename(filepath)}"
            )
            ds.to_netcdf(output_path)
            processed.append(output_path)
            ds.close()
        except Exception as e:
            logger.error("Failed to process SST file", path=filepath, error=str(e))

    return processed


def process_chlorophyll_files(raw_dir: str, processed_dir: str) -> list[str]:
    """Process raw chlorophyll netCDF4 files."""
    chlor_files = glob.glob(os.path.join(raw_dir, "modis_chlor_*.nc"))

    processed = []
    for filepath in chlor_files:
        logger.info("Processing chlorophyll file", path=filepath)
        try:
            ds = xr.open_dataset(filepath, engine="netcdf4")

            # TODO: Apply quality flags, log-transform chlorophyll
            output_path = os.path.join(
                processed_dir,
                f"processed_{os.path.basename(filepath)}"
            )
            ds.to_netcdf(output_path)
            processed.append(output_path)
            ds.close()
        except Exception as e:
            logger.error("Failed to process chlorophyll file", path=filepath, error=str(e))

    return processed


def main():
    """Process all raw netCDF4 data files."""
    raw_dir = os.environ.get("DATA_RAW_DIR", "./data/raw")
    processed_dir = os.environ.get("DATA_PROCESSED_DIR", "./data/processed")
    os.makedirs(processed_dir, exist_ok=True)

    logger.info("Starting netCDF4 processing", raw_dir=raw_dir)

    sst_files = process_sst_files(raw_dir, processed_dir)
    chlor_files = process_chlorophyll_files(raw_dir, processed_dir)

    logger.info(
        "NetCDF4 processing complete",
        sst_files=len(sst_files),
        chlor_files=len(chlor_files),
    )


if __name__ == "__main__":
    main()
