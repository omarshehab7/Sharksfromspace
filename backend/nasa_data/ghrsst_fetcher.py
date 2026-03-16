"""
ghrsst_fetcher.py — GHRSST L4 SST Data Fetcher
==================================================

Downloads Group for High Resolution Sea Surface Temperature (GHRSST)
Level 4 data products. L4 products are gap-free, gridded SST fields
produced by blending multiple satellite and in-situ observations.

GHRSST L4 is preferred over single-sensor SST for shark prediction
because it provides complete spatial coverage without cloud gaps.

Reference:
    https://podaac.jpl.nasa.gov/GHRSST
"""

import structlog
from nasa_data.earthdata_client import EarthdataClient

logger = structlog.get_logger(__name__)

# GHRSST L4 Collection IDs in CMR (PO.DAAC)
GHRSST_COLLECTIONS = {
    "mur_sst": "C1996881146-PODAAC",  # MUR SST (Multi-scale Ultra-high Resolution)
}


class GHRSSTFetcher:
    """
    Fetches GHRSST Level 4 sea surface temperature data.

    The MUR SST product provides daily global SST at 1km resolution,
    which is ideal for identifying fine-scale thermal fronts that
    attract sharks and their prey.
    """

    def __init__(self, earthdata_client: EarthdataClient):
        self.client = earthdata_client

    async def fetch_mur_sst(
        self,
        bounding_box: tuple[float, float, float, float],
        date_range: str,
        output_dir: str,
    ) -> list[str]:
        """
        Download MUR SST data for a region and time range.

        MUR (Multi-scale Ultra-high Resolution) SST blends data from
        multiple satellites and in-situ sensors to produce a gap-free
        daily SST field at ~1km resolution.

        Args:
            bounding_box: (west, south, east, north) degrees
            date_range: ISO 8601 range, e.g. "2024-01-01,2024-01-07"
            output_dir: Directory to save downloaded files

        Returns:
            List of paths to downloaded netCDF4 files
        """
        logger.info("Fetching GHRSST MUR SST", bbox=bounding_box, dates=date_range)

        granules = await self.client.search_granules(
            collection_id=GHRSST_COLLECTIONS["mur_sst"],
            bounding_box=bounding_box,
            temporal=date_range,
        )

        downloaded = []
        for granule in granules:
            links = granule.get("links", [])
            # Prefer OPeNDAP access for subsetting, fall back to direct download
            opendap_url = next(
                (l["href"] for l in links if "opendap" in l.get("href", "").lower()),
                None,
            )
            data_url = opendap_url or next(
                (l["href"] for l in links if l.get("rel") == "http://esipfed.org/ns/fedsearch/1.1/data#"),
                None,
            )
            if data_url:
                filename = f"{output_dir}/ghrsst_mur_{granule['id']}.nc"
                path = await self.client.download_granule(data_url, filename)
                downloaded.append(path)

        logger.info("GHRSST MUR download complete", files=len(downloaded))
        return downloaded
