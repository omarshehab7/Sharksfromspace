"""
ingest.py — Satellite Data Ingestion (Pipeline Step 1)
========================================================

Fetches raw ocean datasets from NASA using the unified NASAClient.
Downloads PACE, GHRSST MUR SST, and SWOT data concurrently
and returns a CombinedOceanDataset with extracted variables.

This is the entry point of the data pipeline — all downstream
modules consume the output of this module.

Usage:
    dataset = await ingest_ocean_data(
        bounding_box=(-80, 20, -60, 35),
        date_range="2024-06-01,2024-06-07",
    )
"""

from __future__ import annotations

import os
import structlog
from config import settings
from nasa_data.nasa_client import NASAClient, CombinedOceanDataset

logger = structlog.get_logger(__name__)


async def ingest_ocean_data(
    bounding_box: tuple[float, float, float, float],
    date_range: str,
    output_dir: str | None = None,
    fetch_pace: bool = True,
    fetch_sst: bool = True,
    fetch_swot: bool = True,
    swot_simulated: bool = False,
    max_granules: int = 7,
) -> CombinedOceanDataset:
    """
    Download and extract all satellite data for a region and time window.

    Runs PACE, MUR SST, and SWOT downloads concurrently.
    Automatically extracts netCDF variables into numpy arrays.

    Args:
        bounding_box: (west, south, east, north) degrees
        date_range: ISO 8601 temporal range, e.g. "2024-06-01,2024-06-07"
        output_dir: Override raw data directory (default: settings.DATA_RAW_DIR)
        fetch_pace: Whether to fetch PACE ocean color
        fetch_sst: Whether to fetch MUR SST
        fetch_swot: Whether to fetch SWOT SSH
        swot_simulated: Use simulated SWOT data for development
        max_granules: Max granules per data source

    Returns:
        CombinedOceanDataset with pace, sst, swot sub-datasets
    """
    raw_dir = output_dir or settings.DATA_RAW_DIR
    os.makedirs(raw_dir, exist_ok=True)

    logger.info(
        "Starting data ingestion",
        bbox=bounding_box,
        dates=date_range,
        output=raw_dir,
    )

    async with NASAClient() as client:
        dataset = await client.fetch_all(
            bounding_box=bounding_box,
            temporal=date_range,
            output_dir=raw_dir,
            fetch_pace=fetch_pace,
            fetch_sst=fetch_sst,
            fetch_swot=fetch_swot,
            swot_simulated=swot_simulated,
            max_granules_per_source=max_granules,
        )

    logger.info(
        "Ingestion complete",
        has_pace=dataset.pace is not None,
        has_sst=dataset.sst is not None,
        has_swot=dataset.swot is not None,
    )
    return dataset
