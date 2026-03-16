"""
fetch_sst.py — Download Sea Surface Temperature Data
======================================================

Ruflo task that downloads the latest GHRSST MUR SST data
from NASA Earthdata for the configured region of interest.

Usage: ruflo run --task fetch_sst
"""

import os
import yaml
import asyncio
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)


async def main():
    """Fetch latest SST data from NASA."""
    # Load source configuration
    with open("config/sources.yaml") as f:
        config = yaml.safe_load(f)

    source = config["sources"]["ghrsst_mur"]
    region = config["default_region"]["bounding_box"]
    days_back = config["fetch"]["days_back"]

    logger.info(
        "Starting SST fetch",
        source=source["description"],
        region=region,
        days_back=days_back,
    )

    # Import from backend (shared code)
    # In production, this would use the earthdata_client directly
    # For now, placeholder for the fetch logic

    output_dir = os.environ.get("DATA_RAW_DIR", "./data/raw")
    os.makedirs(output_dir, exist_ok=True)

    # TODO: Implement actual data fetching
    # client = EarthdataClient()
    # ghrsst = GHRSSTFetcher(client)
    # files = await ghrsst.fetch_mur_sst(
    #     bounding_box=(region["west"], region["south"], region["east"], region["north"]),
    #     date_range=get_date_range(days_back),
    #     output_dir=output_dir,
    # )

    logger.info("SST fetch complete (placeholder)")


if __name__ == "__main__":
    asyncio.run(main())
