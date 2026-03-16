"""
modis_fetcher.py — MODIS Ocean Data Fetcher
==============================================

Downloads and processes MODIS (Moderate Resolution Imaging Spectroradiometer)
satellite data products:

- **MODIS SST**: Sea Surface Temperature (11μm, day/night)
- **MODIS Ocean Color**: Chlorophyll-a, Kd490 (diffuse attenuation)

MODIS data is available from both Terra (since 2000) and Aqua (since 2002)
satellites, provided by NASA's Ocean Biology Processing Group (OB_DAAC).

Reference:
    https://oceancolor.gsfc.nasa.gov/
"""

import structlog
from nasa_data.earthdata_client import EarthdataClient

logger = structlog.get_logger(__name__)

# MODIS Collection IDs in CMR
MODIS_COLLECTIONS = {
    "sst_daily": "C1664741463-OB_DAAC",       # MODIS Aqua SST daily
    "chlor_a_daily": "C1664741464-OB_DAAC",   # MODIS Aqua Chlorophyll daily
}


class MODISFetcher:
    """
    Fetches MODIS satellite data products from NASA.

    Handles searching for available granules, downloading netCDF4 files,
    and providing metadata about available data coverage.
    """

    def __init__(self, earthdata_client: EarthdataClient):
        self.client = earthdata_client

    async def fetch_sst(
        self,
        bounding_box: tuple[float, float, float, float],
        date_range: str,
        output_dir: str,
    ) -> list[str]:
        """
        Download MODIS sea surface temperature data.

        Args:
            bounding_box: (west, south, east, north) degrees
            date_range: ISO 8601 range, e.g. "2024-01-01,2024-01-07"
            output_dir: Directory to save downloaded files

        Returns:
            List of paths to downloaded netCDF4 files
        """
        logger.info("Fetching MODIS SST", bbox=bounding_box, dates=date_range)

        granules = await self.client.search_granules(
            collection_id=MODIS_COLLECTIONS["sst_daily"],
            bounding_box=bounding_box,
            temporal=date_range,
        )

        downloaded = []
        for granule in granules:
            # Extract download URL from granule links
            links = granule.get("links", [])
            data_url = next(
                (l["href"] for l in links if l.get("rel") == "http://esipfed.org/ns/fedsearch/1.1/data#"),
                None,
            )
            if data_url:
                filename = f"{output_dir}/modis_sst_{granule['id']}.nc"
                path = await self.client.download_granule(data_url, filename)
                downloaded.append(path)

        logger.info("MODIS SST download complete", files=len(downloaded))
        return downloaded

    async def fetch_chlorophyll(
        self,
        bounding_box: tuple[float, float, float, float],
        date_range: str,
        output_dir: str,
    ) -> list[str]:
        """
        Download MODIS chlorophyll-a concentration data.

        Args:
            bounding_box: (west, south, east, north) degrees
            date_range: ISO 8601 range
            output_dir: Directory to save downloaded files

        Returns:
            List of paths to downloaded netCDF4 files
        """
        logger.info("Fetching MODIS Chlorophyll", bbox=bounding_box, dates=date_range)

        granules = await self.client.search_granules(
            collection_id=MODIS_COLLECTIONS["chlor_a_daily"],
            bounding_box=bounding_box,
            temporal=date_range,
        )

        downloaded = []
        for granule in granules:
            links = granule.get("links", [])
            data_url = next(
                (l["href"] for l in links if l.get("rel") == "http://esipfed.org/ns/fedsearch/1.1/data#"),
                None,
            )
            if data_url:
                filename = f"{output_dir}/modis_chlor_{granule['id']}.nc"
                path = await self.client.download_granule(data_url, filename)
                downloaded.append(path)

        logger.info("MODIS Chlorophyll download complete", files=len(downloaded))
        return downloaded
