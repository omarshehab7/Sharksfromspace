"""
fetch_data.py — Ruflo Task: Fetch NASA Satellite Datasets (Step 1)
===================================================================

Downloads PACE ocean color, GHRSST MUR SST, and SWOT SSH data
using the NASAClient. Saves raw netCDF4 files and pickles the
CombinedOceanDataset for downstream tasks.
"""

import os
import sys
import asyncio
import pickle
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from data_pipeline.ingest import ingest_ocean_data


def parse_bbox(bbox_str: str) -> tuple[float, float, float, float]:
    """Parse "west,south,east,north" string to tuple."""
    parts = [float(x.strip()) for x in bbox_str.split(",")]
    return (parts[0], parts[1], parts[2], parts[3])


def auto_date_range() -> str:
    """Generate date range for the last 7 days."""
    end = datetime.utcnow()
    start = end - timedelta(days=7)
    return f"{start.strftime('%Y-%m-%d')},{end.strftime('%Y-%m-%d')}"


async def main():
    bbox_str = os.environ.get("BOUNDING_BOX", "-80,20,-60,35")
    date_str = os.environ.get("DATE_RANGE", "auto")
    fetch_pace = os.environ.get("FETCH_PACE", "true").lower() == "true"
    fetch_sst = os.environ.get("FETCH_SST", "true").lower() == "true"
    fetch_swot = os.environ.get("FETCH_SWOT", "true").lower() == "true"

    bbox = parse_bbox(bbox_str)
    dates = auto_date_range() if date_str == "auto" else date_str
    output_dir = os.environ.get("DATA_RAW_DIR", "./data/raw")

    print(f"[fetch_data] bbox={bbox}, dates={dates}")

    dataset = await ingest_ocean_data(
        bounding_box=bbox,
        date_range=dates,
        output_dir=output_dir,
        fetch_pace=fetch_pace,
        fetch_sst=fetch_sst,
        fetch_swot=fetch_swot,
    )

    # Serialize dataset for downstream tasks
    cache_path = os.path.join(output_dir, "combined_dataset.pkl")
    with open(cache_path, "wb") as f:
        pickle.dump(dataset, f)

    print(f"[fetch_data] Dataset saved to {cache_path}")
    print(f"[fetch_data] PACE={dataset.pace is not None}, SST={dataset.sst is not None}, SWOT={dataset.swot is not None}")


if __name__ == "__main__":
    asyncio.run(main())
