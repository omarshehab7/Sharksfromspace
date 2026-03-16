"""
fetch_chlorophyll.py — Download Chlorophyll-a Data
====================================================

Ruflo task that downloads MODIS chlorophyll-a concentration
data from NASA for the configured region of interest.

Chlorophyll-a is a key indicator of phytoplankton abundance,
which drives the marine food chain and attracts sharks.

Usage: ruflo run --task fetch_chlorophyll
"""

import os
import yaml
import asyncio
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)


async def main():
    """Fetch latest chlorophyll-a data from NASA."""
    with open("config/sources.yaml") as f:
        config = yaml.safe_load(f)

    source = config["sources"]["modis_chlorophyll"]
    region = config["default_region"]["bounding_box"]
    days_back = config["fetch"]["days_back"]

    logger.info(
        "Starting chlorophyll fetch",
        source=source["description"],
        region=region,
    )

    output_dir = os.environ.get("DATA_RAW_DIR", "./data/raw")
    os.makedirs(output_dir, exist_ok=True)

    # TODO: Implement actual MODIS chlorophyll data fetching
    logger.info("Chlorophyll fetch complete (placeholder)")


if __name__ == "__main__":
    asyncio.run(main())
