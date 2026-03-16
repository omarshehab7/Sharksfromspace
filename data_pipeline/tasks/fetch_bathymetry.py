"""
fetch_bathymetry.py — Download Bathymetry Data
=================================================

Ruflo task that downloads global bathymetry (ocean depth) data.
Uses ETOPO 2022 from NOAA.

Bathymetry is static data — this task only runs if the local
cache is missing. Sharks prefer specific depth ranges, making
bathymetry an important prediction feature.

Usage: ruflo run --task fetch_bathymetry
"""

import os
import yaml
import asyncio
import structlog
from dotenv import load_dotenv

load_dotenv()
logger = structlog.get_logger(__name__)


async def main():
    """Fetch bathymetry data (if not already cached)."""
    with open("config/sources.yaml") as f:
        config = yaml.safe_load(f)

    source = config["sources"]["etopo_bathymetry"]
    output_dir = os.environ.get("DATA_RAW_DIR", "./data/raw")
    output_file = os.path.join(output_dir, "bathymetry.nc")

    if os.path.exists(output_file):
        logger.info("Bathymetry data already cached, skipping download")
        return

    os.makedirs(output_dir, exist_ok=True)

    logger.info("Downloading bathymetry data", url=source["url"])

    # TODO: Download ETOPO data via OPeNDAP or direct HTTPS
    # This is a large file (~1GB) — download with streaming
    logger.info("Bathymetry fetch complete (placeholder)")


if __name__ == "__main__":
    asyncio.run(main())
