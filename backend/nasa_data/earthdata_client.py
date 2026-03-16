"""
earthdata_client.py — NASA Earthdata API Client
==================================================

Handles authentication and data discovery through NASA's
Common Metadata Repository (CMR) and OPeNDAP data access.

NASA Earthdata provides access to satellite-derived ocean data products
including sea surface temperature, ocean color, and bathymetry.

References:
    - CMR API: https://cmr.earthdata.nasa.gov/search/
    - Earthdata Login: https://urs.earthdata.nasa.gov/
"""

import httpx
import structlog
from config import settings

logger = structlog.get_logger(__name__)

# NASA Earthdata API endpoints
CMR_SEARCH_URL = "https://cmr.earthdata.nasa.gov/search"
OPENDAP_BASE_URL = "https://opendap.earthdata.nasa.gov"


class EarthdataClient:
    """
    Client for NASA Earthdata services.

    Handles:
    - Authentication via bearer token or username/password
    - Collection and granule search via CMR
    - Data download via OPeNDAP or direct HTTPS
    """

    def __init__(self):
        self.token = settings.NASA_EARTHDATA_BEARER_TOKEN
        self.username = settings.NASA_EARTHDATA_USERNAME
        self.password = settings.NASA_EARTHDATA_PASSWORD
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Lazily create an authenticated HTTP client."""
        if self._client is None:
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"

            self._client = httpx.AsyncClient(
                headers=headers,
                timeout=60.0,
                follow_redirects=True,
            )
        return self._client

    async def search_collections(
        self,
        keyword: str,
        provider: str = "PODAAC",
        page_size: int = 10,
    ) -> list[dict]:
        """
        Search NASA CMR for data collections matching a keyword.

        Args:
            keyword: Search term (e.g., "sea surface temperature")
            provider: Data provider (e.g., PODAAC, OB_DAAC)
            page_size: Number of results to return

        Returns:
            List of collection metadata dictionaries
        """
        client = await self._get_client()
        params = {
            "keyword": keyword,
            "provider": provider,
            "page_size": page_size,
            "sort_key": "-score",
        }
        response = await client.get(
            f"{CMR_SEARCH_URL}/collections.json", params=params
        )
        response.raise_for_status()
        data = response.json()
        return data.get("feed", {}).get("entry", [])

    async def search_granules(
        self,
        collection_id: str,
        bounding_box: tuple[float, float, float, float] | None = None,
        temporal: str | None = None,
        page_size: int = 10,
    ) -> list[dict]:
        """
        Search for data granules (files) within a collection.

        Args:
            collection_id: CMR collection concept ID
            bounding_box: (west, south, east, north) in degrees
            temporal: ISO 8601 temporal range (e.g., "2024-01-01,2024-01-31")
            page_size: Number of results

        Returns:
            List of granule metadata with download URLs
        """
        client = await self._get_client()
        params = {
            "collection_concept_id": collection_id,
            "page_size": page_size,
            "sort_key": "-start_date",
        }
        if bounding_box:
            params["bounding_box"] = ",".join(str(v) for v in bounding_box)
        if temporal:
            params["temporal"] = temporal

        response = await client.get(
            f"{CMR_SEARCH_URL}/granules.json", params=params
        )
        response.raise_for_status()
        data = response.json()
        return data.get("feed", {}).get("entry", [])

    async def download_granule(self, url: str, output_path: str) -> str:
        """
        Download a data file from NASA Earthdata.

        Args:
            url: Direct download URL for the granule
            output_path: Local path to save the downloaded file

        Returns:
            Path to the downloaded file
        """
        client = await self._get_client()
        logger.info("Downloading granule", url=url, output=output_path)

        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(output_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

        logger.info("Download complete", output=output_path)
        return output_path

    async def close(self):
        """Close the HTTP client connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
