"""
nasa_client.py — NASA Satellite Data Integration Layer
=======================================================

Unified client for retrieving oceanographic satellite data from three
NASA missions critical to shark activity prediction:

  1. PACE (Plankton, Aerosol, Cloud, ocean Ecosystem)
     ├── Chlorophyll-a concentration      [ocean productivity]
     ├── Phytoplankton absorption (aph)   [ecosystem health]
     └── Remote-sensing reflectance (Rrs) [ocean color]

  2. MODIS / GHRSST (Multi-scale Ultra-high Resolution SST)
     ├── Sea surface temperature (SST)    [thermal habitat]
     ├── SST anomaly                      [thermal anomalies]
     └── SST gradient (computed)          [thermal fronts]

  3. SWOT (Surface Water and Ocean Topography)
     ├── Sea surface height anomaly (SSHA)[mesoscale eddies]
     └── Significant wave height          [sea state]

All datasets are retrieved via:
  - NASA CMR API:  https://cmr.earthdata.nasa.gov/search/granules.json
  - OceanColor API: https://oceancolor.gsfc.nasa.gov/api/
  - Direct HTTPS / OPeNDAP downloads from Earthdata

NetCDF4 files are parsed with xarray, relevant variables extracted,
and a structured OceanDataset dataclass is returned per dataset type.

Authentication:
  Set NASA_EARTHDATA_BEARER_TOKEN (preferred) or
  NASA_EARTHDATA_USERNAME + NASA_EARTHDATA_PASSWORD in .env

References:
  - PACE OCI:   https://pace.gsfc.nasa.gov / https://oceancolor.gsfc.nasa.gov
  - GHRSST MUR: https://podaac.jpl.nasa.gov/MEaSUREs-MUR
  - SWOT:       https://swot.jpl.nasa.gov / https://podaac.jpl.nasa.gov/swot
  - CMR API:    https://cmr.earthdata.nasa.gov/search/
"""

from __future__ import annotations

import os
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import xarray as xr
import structlog

from config import settings

logger = structlog.get_logger(__name__)

# ============================================================
# CMR API endpoint
# ============================================================
CMR_GRANULES_URL = "https://cmr.earthdata.nasa.gov/search/granules.json"
CMR_COLLECTIONS_URL = "https://cmr.earthdata.nasa.gov/search/collections.json"

# OceanColor API (PACE / MODIS data search)
OCEANCOLOR_API_URL = "https://oceancolor.gsfc.nasa.gov/api"
OCEANCOLOR_OPENDAP_ROOT = "https://oceandata.sci.gsfc.nasa.gov/opendap"

# OPeNDAP base for PO.DAAC (MUR SST, SWOT)
PODAAC_OPENDAP_URL = "https://opendap.earthdata.nasa.gov"


# ============================================================
# CMR Collection IDs (verified 2026-03-15 against live CMR)
# ============================================================
class Collections:
    """
    Verified NASA CMR concept IDs for each satellite collection.
    These are stable identifiers independent of version strings.
    """

    # ------ PACE OCI (Ocean Color Instrument) ------
    # Provider: OB_CLOUD (NASA GSFC OB.DAAC)
    # Temporal coverage: 2024-03-05 onwards

    # Chlorophyll-a concentration — primary ecosystem productivity proxy
    # Variable: chlor_a (mg m⁻³)
    PACE_OCI_CHL = "C3620140256-OB_CLOUD"

    # Inherent Optical Properties — phytoplankton absorption (aph)
    # Variables: aph, a, bb, Kd, adg_442, bbp_442 (all in m⁻¹)
    PACE_OCI_IOP = "C3620140295-OB_CLOUD"

    # Remote-Sensing Reflectance — hyperspectral ocean color
    # Variable: Rrs_<wavelength> (sr⁻¹) at dozens of OCI bands
    PACE_OCI_RRS = "C3620140444-OB_CLOUD"

    # ------ GHRSST / MODIS MUR SST ------
    # Provider: POCLOUD (NASA JPL PO.DAAC)
    # Product: GHRSST Level 4 MUR Global Foundation SST v4.1
    # Temporal coverage: 2002-05-31 onwards
    # Resolution: 0.01° (~1 km), daily
    # Variables: analysed_sst, sst_anomaly (since 2019-07-23), dt_1km_data
    MUR_SST = "C1996881146-POCLOUD"

    # ------ SWOT (Surface Water and Ocean Topography) ------
    # Provider: POCLOUD (NASA JPL PO.DAAC)
    # Product: SWOT Level 2 KaRIn Low Rate SSH, Version C (2.0)
    # Temporal coverage: 2022-12-16 onwards (science phase: 2023-08+)
    # Swath width: 120 km (60 km each side of nadir), 2×2 km grid
    # Variables: sea_surface_height_above_geoid, ssha, sig0, wind_speed, swh
    SWOT_L2_LR_SSH = "C2799438306-POCLOUD"

    # SWOT simulated dataset (from GLORYS reanalysis) for development/testing
    # Useful when real SWOT data access is restricted
    SWOT_SIMULATED_GLORYS = "C2152045877-POCLOUD"


# ============================================================
# Data Structures
# ============================================================

@dataclass
class GranuleInfo:
    """Metadata about a single downloadable satellite granule (file)."""
    granule_id: str
    title: str
    collection_id: str
    time_start: str
    time_end: str
    download_url: str
    opendap_url: str | None
    size_mb: float | None


@dataclass
class PACEOceanDataset:
    """
    Processed PACE OCI ocean color data for a region.
    All arrays share the same lat/lon grid.
    """
    # Grid coordinates
    lat: np.ndarray          # 1D latitude array (degrees)
    lon: np.ndarray          # 1D longitude array (degrees)

    # Ocean Color Products (Level-3 mapped, daily composite)
    chlor_a: np.ndarray      # Chlorophyll-a (mg m⁻³) — primary productivity proxy
    aph: np.ndarray | None   # Phytoplankton absorption at 443 nm (m⁻¹)
    Kd_490: np.ndarray | None  # Diffuse attenuation at 490 nm (m⁻¹) — water clarity
    Rrs_443: np.ndarray | None  # Remote-sensing reflectance at 443 nm (sr⁻¹)
    Rrs_555: np.ndarray | None  # Remote-sensing reflectance at 555 nm (sr⁻¹)

    # Metadata
    source_file: str
    observation_date: str
    mission: str = "PACE OCI"
    resolution_km: float = 4.0


@dataclass
class SSTDataset:
    """
    Processed GHRSST MUR sea surface temperature data for a region.
    """
    # Grid coordinates
    lat: np.ndarray          # 1D latitude array (degrees)
    lon: np.ndarray          # 1D longitude array (degrees)

    # Temperature Products
    sst: np.ndarray          # Sea surface temperature (°C) — converted from Kelvin
    sst_anomaly: np.ndarray | None  # SST anomaly from MUR climatology (°C)
    sst_gradient: np.ndarray | None  # SST spatial gradient magnitude (computed)

    # Data quality
    analysis_error: np.ndarray | None  # Estimated analysis error (°C)

    # Metadata
    source_file: str
    observation_date: str
    mission: str = "GHRSST MUR"
    resolution_km: float = 1.0


@dataclass
class SWOTDataset:
    """
    Processed SWOT sea surface height data for a region.
    SWOT uses a swath geometry — not a regular lat/lon grid.
    """
    # Swath coordinates (2D arrays, not regular grids)
    lat: np.ndarray          # 2D latitude array (num_lines x num_pixels)
    lon: np.ndarray          # 2D longitude array (num_lines x num_pixels)

    # SSH Products
    ssh: np.ndarray          # Sea surface height above geoid (m)
    ssha: np.ndarray | None  # Sea surface height anomaly (m) — mesoscale signal
    swh: np.ndarray | None   # Significant wave height (m)
    wind_speed: np.ndarray | None  # Wind speed (m/s)

    # Derived Products
    eddy_mask: np.ndarray | None  # Boolean mask of detected mesoscale eddies (computed)

    # Metadata
    source_file: str
    observation_date: str
    pass_number: str | None
    mission: str = "SWOT KaRIn"
    resolution_km: float = 2.0


@dataclass
class CombinedOceanDataset:
    """
    All three satellite datasets merged for a region/period.
    Used as the final input to the shark activity prediction model.
    """
    pace: PACEOceanDataset | None = None
    sst: SSTDataset | None = None
    swot: SWOTDataset | None = None
    bounding_box: tuple[float, float, float, float] | None = None  # W, S, E, N
    date_range: tuple[str, str] | None = None  # start, end ISO dates


# ============================================================
# HTTP Client Helper
# ============================================================

class _EarthdataHTTPClient:
    """
    Shared authenticated HTTPS client for NASA Earthdata.

    Handles Bearer token and Basic auth modes. Uses streaming
    for large file downloads to avoid memory issues.
    """

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    def _build_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {
            "User-Agent": "SharkFromSpace/1.0 (https://github.com/sharksfromspace)",
        }
        token = settings.NASA_EARTHDATA_BEARER_TOKEN
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _get_auth(self) -> httpx.BasicAuth | None:
        if settings.NASA_EARTHDATA_USERNAME and settings.NASA_EARTHDATA_PASSWORD:
            return httpx.BasicAuth(
                settings.NASA_EARTHDATA_USERNAME,
                settings.NASA_EARTHDATA_PASSWORD,
            )
        return None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self._build_headers(),
                auth=self._get_auth(),
                timeout=httpx.Timeout(connect=30.0, read=120.0, write=60.0, pool=30.0),
                follow_redirects=True,
            )
        return self._client

    async def get_json(self, url: str, params: dict | None = None) -> dict:
        """GET request returning parsed JSON."""
        client = await self.get_client()
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def download_stream(self, url: str, output_path: str) -> str:
        """
        Stream-download a remote file to disk.

        Returns the local file path after download completes.
        """
        client = await self.get_client()
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        logger.info("Downloading dataset", url=url, target=output_path)

        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            received = 0
            with open(output, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=65536):  # 64 KB chunks
                    f.write(chunk)
                    received += len(chunk)
                    if total:
                        pct = (received / total) * 100
                        logger.debug("Download progress", pct=f"{pct:.1f}%", path=output_path)

        logger.info("Download complete", path=output_path, size_bytes=output.stat().st_size)
        return output_path

    async def close(self):
        if self._client:
            await self._client.aclose()


# ============================================================
# CMR Granule Search
# ============================================================

class CMRClient:
    """
    Searches NASA's Common Metadata Repository for satellite granules.
    """

    def __init__(self, http: _EarthdataHTTPClient):
        self._http = http

    async def search_granules(
        self,
        collection_id: str,
        bounding_box: tuple[float, float, float, float] | None = None,
        temporal: str | None = None,
        page_size: int = 20,
        sort_key: str = "-start_date",
    ) -> list[GranuleInfo]:
        """
        Search CMR for granules matching a collection and optional filters.

        Args:
            collection_id: CMR concept ID (e.g. "C3620140256-OB_CLOUD")
            bounding_box: (west, south, east, north) in decimal degrees
            temporal: ISO 8601 range, e.g. "2024-01-01T00:00:00Z,2024-01-07T23:59:59Z"
            page_size: Number of granules to retrieve (max 200)
            sort_key: CMR sort key (default: most recent first)

        Returns:
            List of GranuleInfo objects with download/OPeNDAP URLs
        """
        params: dict[str, Any] = {
            "collection_concept_id": collection_id,
            "page_size": min(page_size, 200),
            "sort_key": sort_key,
        }

        if bounding_box:
            west, south, east, north = bounding_box
            params["bounding_box"] = f"{west},{south},{east},{north}"

        if temporal:
            params["temporal"] = temporal

        logger.info(
            "CMR granule search",
            collection=collection_id,
            bbox=bounding_box,
            temporal=temporal,
        )

        data = await self._http.get_json(CMR_GRANULES_URL, params=params)
        raw_entries: list[dict] = data.get("feed", {}).get("entry", [])

        granules: list[GranuleInfo] = []
        for entry in raw_entries:
            links = entry.get("links", [])

            # Prefer OPeNDAP URL for subsetting, fall back to direct data download
            opendap_url = next(
                (
                    lnk["href"]
                    for lnk in links
                    if "opendap" in lnk.get("href", "").lower()
                    and lnk.get("href", "").endswith(".nc")
                ),
                None,
            )
            data_url = next(
                (
                    lnk["href"]
                    for lnk in links
                    if lnk.get("rel") == "http://esipfed.org/ns/fedsearch/1.1/data#"
                    and lnk.get("href", "").endswith(".nc")
                ),
                None,
            )
            # Some providers have .nc4 extension
            if not data_url:
                data_url = next(
                    (
                        lnk["href"]
                        for lnk in links
                        if lnk.get("rel") == "http://esipfed.org/ns/fedsearch/1.1/data#"
                        and ".nc" in lnk.get("href", "")
                    ),
                    None,
                )

            # Try to parse size
            size_mb = None
            for lnk in links:
                if "length" in lnk and lnk.get("rel", "").endswith("data#"):
                    try:
                        raw = lnk["length"].replace("MB", "").replace("GB", "000").strip()
                        size_mb = float(raw)
                    except (ValueError, AttributeError):
                        pass

            if data_url or opendap_url:
                granules.append(
                    GranuleInfo(
                        granule_id=entry.get("id", ""),
                        title=entry.get("title", ""),
                        collection_id=collection_id,
                        time_start=entry.get("time_start", ""),
                        time_end=entry.get("time_end", ""),
                        download_url=data_url or opendap_url or "",
                        opendap_url=opendap_url,
                        size_mb=size_mb,
                    )
                )

        logger.info("CMR search complete", collection=collection_id, granules=len(granules))
        return granules


# ============================================================
# PACE Ocean Color Client
# ============================================================

class PACEClient:
    """
    Downloads and processes PACE OCI Level-3 ocean color data.

    PACE (Plankton, Aerosol, Cloud, ocean Ecosystem) was launched in
    February 2024. Its Ocean Color Instrument (OCI) provides hyperspectral
    measurements from 340–890 nm, giving unprecedented ocean color detail.

    Level-3 Mapped (L3M) products are daily global grids at 4 km resolution.
    Data is distributed by NASA OB.DAAC via CMR.

    Key variables for shark prediction:
    - chlor_a:   Chlorophyll-a (mg m⁻³) — food web productivity
    - aph:       Phytoplankton absorption at 443 nm (m⁻¹)
    - Kd_490:    Water clarity — deeper Kd = more productive water
    - Rrs_443/555: Ocean color ratio — relates to phytoplankton community
    """

    # OceanColor API base for file search (alternative to CMR)
    _OCEANCOLOR_API = "https://oceancolor.gsfc.nasa.gov/api"

    def __init__(self, http: _EarthdataHTTPClient, cmr: CMRClient):
        self._http = http
        self._cmr = cmr

    async def fetch_chlorophyll(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
        output_dir: str,
        max_granules: int = 5,
    ) -> list[str]:
        """
        Download PACE OCI Level-3 chlorophyll-a files (daily composites).

        Args:
            bounding_box: (west, south, east, north) degrees
            temporal: ISO 8601 date range, e.g. "2024-06-01,2024-06-07"
            output_dir: Directory to save .nc files
            max_granules: Maximum number of daily files to download

        Returns:
            List of paths to downloaded netCDF4 files
        """
        granules = await self._cmr.search_granules(
            collection_id=Collections.PACE_OCI_CHL,
            bounding_box=bounding_box,
            temporal=temporal,
            page_size=max_granules,
        )

        paths = []
        for g in granules:
            fname = f"pace_chl_{g.granule_id}.nc"
            out = os.path.join(output_dir, fname)
            if not os.path.exists(out):
                path = await self._http.download_stream(g.download_url, out)
                paths.append(path)
            else:
                logger.info("PACE CHL already cached", path=out)
                paths.append(out)

        return paths

    async def fetch_inherent_optical_properties(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
        output_dir: str,
        max_granules: int = 5,
    ) -> list[str]:
        """
        Download PACE OCI Inherent Optical Properties (IOP) files.

        IOP includes phytoplankton absorption (aph), which is a direct
        measurement of phytoplankton biomass beyond simple chlorophyll.

        Args:
            bounding_box: (west, south, east, north) degrees
            temporal: ISO 8601 date range
            output_dir: Output directory
            max_granules: Maximum files to download

        Returns:
            List of paths to downloaded netCDF4 files
        """
        granules = await self._cmr.search_granules(
            collection_id=Collections.PACE_OCI_IOP,
            bounding_box=bounding_box,
            temporal=temporal,
            page_size=max_granules,
        )

        paths = []
        for g in granules:
            fname = f"pace_iop_{g.granule_id}.nc"
            out = os.path.join(output_dir, fname)
            if not os.path.exists(out):
                path = await self._http.download_stream(g.download_url, out)
                paths.append(path)
            else:
                logger.info("PACE IOP already cached", path=out)
                paths.append(out)

        return paths

    async def fetch_rrs(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
        output_dir: str,
        max_granules: int = 3,
    ) -> list[str]:
        """
        Download PACE OCI Remote-Sensing Reflectance (Rrs) files.

        Rrs is the foundation of all ocean color retrievals. The hyperspectral
        Rrs from PACE enables water-type classification and can indicate
        different phytoplankton communities.

        Args:
            bounding_box: (west, south, east, north) degrees
            temporal: ISO 8601 date range
            output_dir: Output directory
            max_granules: Maximum files to download

        Returns:
            List of paths to downloaded netCDF4 files
        """
        granules = await self._cmr.search_granules(
            collection_id=Collections.PACE_OCI_RRS,
            bounding_box=bounding_box,
            temporal=temporal,
            page_size=max_granules,
        )

        paths = []
        for g in granules:
            fname = f"pace_rrs_{g.granule_id}.nc"
            out = os.path.join(output_dir, fname)
            if not os.path.exists(out):
                path = await self._http.download_stream(g.download_url, out)
                paths.append(path)
            else:
                logger.info("PACE RRS already cached", path=out)
                paths.append(out)

        return paths

    @staticmethod
    def extract_variables(nc_path: str) -> PACEOceanDataset:
        """
        Open a downloaded PACE OCI netCDF4 file and extract
        relevant variables into a PACEOceanDataset.

        The Level-3 Mapped files use a simple lat/lon grid convention.
        Variables use a fill value for missing/flagged pixels.

        Args:
            nc_path: Path to a PACE OCI Level-3 netCDF4 file

        Returns:
            PACEOceanDataset with extracted arrays (masked NaN where invalid)
        """
        logger.info("Extracting PACE OCI variables", path=nc_path)
        ds = xr.open_dataset(nc_path, mask_and_scale=True, decode_cf=True)

        # Grid coordinates — PACE L3M uses 'lat' and 'lon' dimension names
        lat = ds["lat"].values if "lat" in ds.coords else ds["latitude"].values
        lon = ds["lon"].values if "lon" in ds.coords else ds["longitude"].values

        def _safe_values(var_name: str) -> np.ndarray | None:
            """Extract variable, applying fill-value masking → NaN."""
            if var_name not in ds:
                return None
            arr = ds[var_name].values.astype(np.float32)
            # xarray already handles _FillValue masking when mask_and_scale=True
            return arr

        # Extract date from filename (PACE_OCI.YYYYMMDD.L3m.*)
        basename = os.path.basename(nc_path)
        obs_date = "unknown"
        try:
            # Typical naming: PACE_OCI.20250101.L3m.DAY.CHL.V3_1.chlor_a.4km.nc
            parts = basename.split(".")
            if len(parts) > 1:
                obs_date = parts[1]  # e.g. "20250101"
        except (IndexError, ValueError):
            pass

        dataset = PACEOceanDataset(
            lat=lat,
            lon=lon,
            chlor_a=_safe_values("chlor_a") or np.full((len(lat), len(lon)), np.nan),
            aph=_safe_values("aph"),
            Kd_490=_safe_values("Kd_490"),
            Rrs_443=_safe_values("Rrs_443"),
            Rrs_555=_safe_values("Rrs_555"),
            source_file=nc_path,
            observation_date=obs_date,
        )

        ds.close()
        logger.info(
            "PACE extraction complete",
            lat_range=(lat.min(), lat.max()),
            lon_range=(lon.min(), lon.max()),
            shape=dataset.chlor_a.shape,
        )
        return dataset


# ============================================================
# SST Client (GHRSST / MUR)
# ============================================================

class SSTClient:
    """
    Downloads and processes GHRSST MUR Level-4 sea surface temperature data.

    The Multi-scale Ultra-high Resolution (MUR) SST product provides:
    - Gap-free, daily global SST at 1 km resolution
    - Blended from MODIS Aqua & Terra, AMSR-E/2, AVHRR, WindSat
    - Built-in SST anomaly (deviation from 11-year MUR climatology)
    - Analysis error estimate per pixel

    Available from 2002-05-31 onwards (MODIS Aqua launch date).
    The `sst_anomaly` variable is available from 2019-07-23 onwards.

    Key variables for shark prediction:
    - analysed_sst:  Absolute SST (K → converted to °C in extraction)
    - sst_anomaly:   Deviation from climatological mean (°C)
    - SST gradient:  Computed from spatial derivatives — identifies thermal fronts
    """

    def __init__(self, http: _EarthdataHTTPClient, cmr: CMRClient):
        self._http = http
        self._cmr = cmr

    async def fetch_sst(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
        output_dir: str,
        max_granules: int = 7,
    ) -> list[str]:
        """
        Download MUR SST daily files for a region and time range.

        Each file covers the full globe (~300 MB when subsetted).
        Files are cached locally to avoid redundant downloads.

        Args:
            bounding_box: (west, south, east, north) degrees
            temporal: ISO 8601 range, e.g. "2024-06-01,2024-06-07"
            output_dir: Directory to save .nc files
            max_granules: Max daily files to retrieve

        Returns:
            List of paths to downloaded netCDF4 files
        """
        granules = await self._cmr.search_granules(
            collection_id=Collections.MUR_SST,
            bounding_box=bounding_box,
            temporal=temporal,
            page_size=max_granules,
        )

        paths = []
        for g in granules:
            fname = f"mur_sst_{g.granule_id}.nc"
            out = os.path.join(output_dir, fname)
            if not os.path.exists(out):
                # Prefer OPeNDAP URL for spatial subsetting
                url = g.opendap_url or g.download_url
                if g.opendap_url:
                    # Append subsetting parameters to OPeNDAP URL
                    url = self._build_opendap_url(g.opendap_url, bounding_box)
                path = await self._http.download_stream(url, out)
                paths.append(path)
            else:
                logger.info("MUR SST already cached", path=out)
                paths.append(out)

        return paths

    @staticmethod
    def _build_opendap_url(
        base_url: str,
        bounding_box: tuple[float, float, float, float],
    ) -> str:
        """
        Append OPeNDAP constraint expression to subset the global file
        to the bounding box of interest.

        This avoids downloading the full ~2GB global file when only
        a regional subset is needed.

        Args:
            base_url: Base OPeNDAP dataset URL
            bounding_box: (west, south, east, north) degrees

        Returns:
            URL with constraint expression appended
        """
        west, south, east, north = bounding_box
        # OPeNDAP constraint: select lat[south:north], lon[west:east]
        # Exact index calculation depends on the dataset resolution (0.01° for MUR)
        resolution = 0.01  # degrees per pixel for MUR v4.1
        lat_start = int((south + 90) / resolution)
        lat_end = int((north + 90) / resolution)
        lon_start = int((west + 180) / resolution)
        lon_end = int((east + 180) / resolution)

        constraint = (
            f"?analysed_sst[0][{lat_start}:{lat_end}][{lon_start}:{lon_end}]"
            f",sst_anomaly[0][{lat_start}:{lat_end}][{lon_start}:{lon_end}]"
            f",analysis_error[0][{lat_start}:{lat_end}][{lon_start}:{lon_end}]"
            f",lat[{lat_start}:{lat_end}]"
            f",lon[{lon_start}:{lon_end}]"
        )
        return base_url + constraint

    @staticmethod
    def extract_variables(nc_path: str) -> SSTDataset:
        """
        Open a downloaded MUR SST netCDF4 file and extract
        temperature variables into a SSTDataset.

        Converts SST from Kelvin to Celsius and computes the
        SST spatial gradient (identifies thermal fronts).

        Args:
            nc_path: Path to a MUR SST netCDF4 file

        Returns:
            SSTDataset with extracted and processed arrays
        """
        logger.info("Extracting MUR SST variables", path=nc_path)
        ds = xr.open_dataset(nc_path, mask_and_scale=True, decode_cf=True)

        lat = ds["lat"].values
        lon = ds["lon"].values

        # ---- SST (convert Kelvin → Celsius if needed) ----
        sst_da = ds["analysed_sst"]
        sst = sst_da.values.astype(np.float32)
        # MUR stores in Kelvin (300 K ≈ 27 °C); convert if > 200
        if np.nanmedian(sst) > 200:
            sst = sst - 273.15
        # Handle time dimension (squeeze to 2D)
        if sst.ndim == 3:
            sst = sst.squeeze(axis=0)

        # ---- SST Anomaly (available 2019-07-23+) ----
        sst_anomaly = None
        if "sst_anomaly" in ds:
            sst_anomaly = ds["sst_anomaly"].values.astype(np.float32)
            if sst_anomaly.ndim == 3:
                sst_anomaly = sst_anomaly.squeeze(axis=0)

        # ---- Analysis Error ----
        analysis_error = None
        if "analysis_error" in ds:
            analysis_error = ds["analysis_error"].values.astype(np.float32)
            if analysis_error.ndim == 3:
                analysis_error = analysis_error.squeeze(axis=0)

        # ---- Compute SST gradient (thermal fronts) ----
        # Gradient is computed on a 2D field using numpy gradient
        sst_gradient = SSTClient._compute_sst_gradient(sst, lat, lon)

        # Extract date from MUR filename (YYYYMMDD090000-JPL-L4_GHRSST...)
        basename = os.path.basename(nc_path)
        obs_date = "unknown"
        try:
            # Typical MUR naming: 20250101090000-JPL-L4_GHRSST-SSTfnd-MUR-GLOB-v02.0-fv04.1.nc
            obs_date = basename[:8]  # YYYYMMDD
        except (IndexError, ValueError):
            pass

        dataset = SSTDataset(
            lat=lat,
            lon=lon,
            sst=sst,
            sst_anomaly=sst_anomaly,
            sst_gradient=sst_gradient,
            analysis_error=analysis_error,
            source_file=nc_path,
            observation_date=obs_date,
        )

        ds.close()
        logger.info(
            "SST extraction complete",
            shape=sst.shape,
            sst_range=(float(np.nanmin(sst)), float(np.nanmax(sst))),
            has_anomaly=sst_anomaly is not None,
            has_gradient=sst_gradient is not None,
        )
        return dataset

    @staticmethod
    def _compute_sst_gradient(
        sst: np.ndarray,
        lat: np.ndarray,
        lon: np.ndarray,
    ) -> np.ndarray:
        """
        Compute the magnitude of the SST spatial gradient.

        Strong gradients indicate thermal fronts — boundaries between
        warm and cold water masses where prey aggregates and sharks hunt.

        Uses numpy.gradient for finite difference approximation.
        Gradient units: °C per degree of latitude/longitude.

        Args:
            sst: 2D SST array (lat × lon), NaN where invalid
            lat: 1D latitude array
            lon: 1D longitude array

        Returns:
            2D gradient magnitude array (same shape as sst)
        """
        # Approximate spacing in degrees
        dlat = np.abs(np.mean(np.diff(lat))) if len(lat) > 1 else 1.0
        dlon = np.abs(np.mean(np.diff(lon))) if len(lon) > 1 else 1.0

        # numpy.gradient handles NaN gracefully (NaN propagates)
        grad_lat, grad_lon = np.gradient(sst, dlat, dlon)
        gradient_magnitude = np.sqrt(grad_lat ** 2 + grad_lon ** 2)

        return gradient_magnitude.astype(np.float32)


# ============================================================
# SWOT Ocean Circulation Client
# ============================================================

class SWOTClient:
    """
    Downloads and processes SWOT KaRIn Level-2 sea surface height data.

    The Surface Water and Ocean Topography (SWOT) mission (launched Dec 2022)
    is the first satellite to measure sea surface height with 2D swath
    coverage rather than point nadir measurements.

    Key oceanographic features derivable from SWOT:
    - Sea Surface Height Anomaly (SSHA): reveals mesoscale eddies (50–500 km),
      sub-mesoscale fronts, and current jets
    - Mesoscale eddies are critical foraging habitats — their convergence
      zones concentrate prey fish, attracting sharks

    Data format:
    - Level-2 Low Rate (LR): 2×2 km grid, swath width ~120 km
    - One file per half-orbit pass
    - Contains: ssh, ssha, swh (significant wave height), sig0 (backscatter),
      wind_speed
    """

    def __init__(self, http: _EarthdataHTTPClient, cmr: CMRClient):
        self._http = http
        self._cmr = cmr

    async def fetch_ssh(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
        output_dir: str,
        max_granules: int = 10,
        use_simulated: bool = False,
    ) -> list[str]:
        """
        Download SWOT L2 KaRIn Low Rate SSH files.

        SWOT has a 21-day orbit repeat cycle (science phase from Aug 2023).
        Each file covers a single ascending/descending pass (~24 min).

        Args:
            bounding_box: (west, south, east, north) degrees
            temporal: ISO 8601 date range
            output_dir: Output directory for .nc files
            max_granules: Max files to download (each ~2 GB)
            use_simulated: Use GLORYS-simulated SWOT data (useful for testing)

        Returns:
            List of paths to downloaded netCDF4 files
        """
        collection_id = (
            Collections.SWOT_SIMULATED_GLORYS
            if use_simulated
            else Collections.SWOT_L2_LR_SSH
        )

        granules = await self._cmr.search_granules(
            collection_id=collection_id,
            bounding_box=bounding_box,
            temporal=temporal,
            page_size=max_granules,
        )

        if not granules:
            logger.warning(
                "No SWOT granules found",
                bbox=bounding_box,
                temporal=temporal,
                simulated=use_simulated,
            )
            return []

        paths = []
        for g in granules:
            fname = f"swot_ssh_{g.granule_id}.nc"
            out = os.path.join(output_dir, fname)
            if not os.path.exists(out):
                path = await self._http.download_stream(g.download_url, out)
                paths.append(path)
            else:
                logger.info("SWOT SSH already cached", path=out)
                paths.append(out)

        return paths

    @staticmethod
    def extract_variables(nc_path: str) -> SWOTDataset:
        """
        Open a downloaded SWOT L2 SSH netCDF4 file and extract
        SSH-related variables into a SWOTDataset.

        SWOT files use a swath geometry:
        - Dimensions: num_lines (along-track) × num_pixels (cross-track)
        - The left and right swaths are stored as separate groups or arrays

        Args:
            nc_path: Path to a SWOT L2 LR SSH netCDF4 file

        Returns:
            SWOTDataset with SSH, SSHA, wave height, and eddy mask
        """
        logger.info("Extracting SWOT SSH variables", path=nc_path)

        # SWOT L2 LR files often have groups (Basic, Expert, etc.)
        # Try opening the root dataset first
        try:
            ds = xr.open_dataset(nc_path, mask_and_scale=True, decode_cf=True)
        except Exception:
            # Some SWOT files require group access
            ds = xr.open_dataset(nc_path, group="basic", mask_and_scale=True)

        def _safe_2d(var: str) -> np.ndarray | None:
            if var not in ds:
                return None
            arr = ds[var].values.astype(np.float32)
            return arr

        lat = _safe_2d("latitude") or _safe_2d("lat")
        lon = _safe_2d("longitude") or _safe_2d("lon")

        if lat is None or lon is None:
            raise ValueError(f"Latitude/longitude not found in SWOT file: {nc_path}")

        ssh = _safe_2d("sea_surface_height_above_geoid") or _safe_2d("ssh_karin")
        if ssh is None:
            raise ValueError(f"SSH variable not found in SWOT file: {nc_path}")

        ssha = _safe_2d("ssha") or _safe_2d("sea_surface_height_anomaly")
        swh = _safe_2d("swh") or _safe_2d("sig_wave_height")
        wind_speed = _safe_2d("wind_speed")

        # Detect mesoscale eddies from SSHA
        eddy_mask = None
        if ssha is not None:
            eddy_mask = SWOTClient._detect_mesoscale_eddies(ssha)

        # Extract pass number from filename or attributes
        pass_number = ds.attrs.get("pass_number", None) or ds.attrs.get("pass", None)

        basename = os.path.basename(nc_path)
        obs_date = "unknown"
        try:
            # SWOT filenames: SWOT_L2_LR_SSH_Basic_2.0_YYYYMMDDTHHMMSS_*.nc
            parts = basename.split("_")
            for part in parts:
                if len(part) == 15 and "T" in part:  # YYYYMMDDTHHMMSS
                    obs_date = part[:8]
                    break
        except (IndexError, ValueError):
            pass

        dataset = SWOTDataset(
            lat=lat,
            lon=lon,
            ssh=ssh,
            ssha=ssha,
            swh=swh,
            wind_speed=wind_speed,
            eddy_mask=eddy_mask,
            source_file=nc_path,
            observation_date=obs_date,
            pass_number=str(pass_number) if pass_number else None,
        )

        ds.close()
        logger.info(
            "SWOT extraction complete",
            shape=ssh.shape,
            has_ssha=ssha is not None,
            eddies_detected=int(eddy_mask.sum()) if eddy_mask is not None else None,
        )
        return dataset

    @staticmethod
    def _detect_mesoscale_eddies(ssha: np.ndarray, threshold_m: float = 0.1) -> np.ndarray:
        """
        Simple threshold-based mesoscale eddy detection from SSHA.

        Pixels with |SSHA| > threshold are considered eddy-influenced.
        A full eddy detection algorithm (e.g., py-eddy-tracker) should be
        used for production applications.

        Args:
            ssha: 2D sea surface height anomaly array (meters)
            threshold_m: SSHA magnitude threshold for eddy detection (default: 10 cm)

        Returns:
            2D boolean mask (True = eddy-influenced pixel)
        """
        valid = ~np.isnan(ssha)
        eddy_mask = np.zeros(ssha.shape, dtype=bool)
        eddy_mask[valid] = np.abs(ssha[valid]) > threshold_m
        return eddy_mask


# ============================================================
# Main NASAClient — Unified Facade
# ============================================================

class NASAClient:
    """
    Unified NASA satellite data client for Sharks From Space.

    This is the primary interface for the rest of the application.
    It combines PACE, SST, and SWOT data into a single
    CombinedOceanDataset, which is then used by the ML prediction model.

    Usage:
        async with NASAClient() as client:
            dataset = await client.fetch_all(
                bounding_box=(-80, 20, -60, 35),      # Caribbean + Gulf Stream
                temporal="2024-06-01,2024-06-07",
                output_dir="./data/raw",
            )
            # dataset.pace.chlor_a — PACE chlorophyll
            # dataset.sst.sst      — MUR sea surface temperature
            # dataset.swot.ssha    — SWOT sea surface height anomaly

    Configuration:
        Required env variables (see .env.example):
        - NASA_EARTHDATA_BEARER_TOKEN  (preferred)
          or
        - NASA_EARTHDATA_USERNAME + NASA_EARTHDATA_PASSWORD
    """

    def __init__(self):
        self._http = _EarthdataHTTPClient()
        self._cmr = CMRClient(self._http)
        self.pace = PACEClient(self._http, self._cmr)
        self.sst = SSTClient(self._http, self._cmr)
        self.swot = SWOTClient(self._http, self._cmr)

    async def __aenter__(self) -> "NASAClient":
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def close(self):
        """Close the underlying HTTP client."""
        await self._http.close()

    async def fetch_all(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
        output_dir: str,
        fetch_pace: bool = True,
        fetch_sst: bool = True,
        fetch_swot: bool = True,
        swot_simulated: bool = False,
        max_granules_per_source: int = 7,
    ) -> CombinedOceanDataset:
        """
        Fetch, download, and extract all three satellite datasets concurrently.

        Runs PACE, SST, and SWOT downloads in parallel using asyncio.gather.
        Extracts variables from the most recent granule of each type.

        Args:
            bounding_box: Geographic AOI as (west, south, east, north) degrees
            temporal: ISO 8601 date range, e.g. "2024-06-01,2024-06-07"
            output_dir: Base directory for downloaded files
            fetch_pace: Whether to fetch PACE ocean color data
            fetch_sst: Whether to fetch GHRSST/MUR SST data
            fetch_swot: Whether to fetch SWOT SSH data
            swot_simulated: Use simulated SWOT data (for development)
            max_granules_per_source: Maximum granules per dataset

        Returns:
            CombinedOceanDataset with pace, sst, and swot sub-datasets
        """
        os.makedirs(output_dir, exist_ok=True)

        pace_dir = os.path.join(output_dir, "pace")
        sst_dir = os.path.join(output_dir, "sst")
        swot_dir = os.path.join(output_dir, "swot")
        for d in [pace_dir, sst_dir, swot_dir]:
            os.makedirs(d, exist_ok=True)

        logger.info(
            "Fetching all satellite data",
            bbox=bounding_box,
            temporal=temporal,
            pace=fetch_pace,
            sst=fetch_sst,
            swot=fetch_swot,
        )

        start_dt = datetime.utcnow()

        # ---- Run downloads concurrently ----
        tasks = []
        labels = []

        if fetch_pace:
            tasks.append(
                self.pace.fetch_chlorophyll(bounding_box, temporal, pace_dir, max_granules_per_source)
            )
            labels.append("pace_chl")
            tasks.append(
                self.pace.fetch_inherent_optical_properties(bounding_box, temporal, pace_dir, max_granules_per_source)
            )
            labels.append("pace_iop")

        if fetch_sst:
            tasks.append(
                self.sst.fetch_sst(bounding_box, temporal, sst_dir, max_granules_per_source)
            )
            labels.append("sst")

        if fetch_swot:
            tasks.append(
                self.swot.fetch_ssh(bounding_box, temporal, swot_dir, max_granules_per_source, use_simulated=swot_simulated)
            )
            labels.append("swot")

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Map results back
        result_map: dict[str, list[str]] = {}
        for label, result in zip(labels, results):
            if isinstance(result, Exception):
                logger.error("Dataset fetch failed", source=label, error=str(result))
                result_map[label] = []
            else:
                result_map[label] = result

        # ---- Extract variables from downloaded files ----
        pace_dataset = None
        if fetch_pace and result_map.get("pace_chl"):
            try:
                # Use the most recent CHL file; merge IOP if available
                latest_chl = result_map["pace_chl"][-1]
                pace_dataset = PACEClient.extract_variables(latest_chl)
            except Exception as e:
                logger.error("PACE extraction failed", error=str(e))

        sst_dataset = None
        if fetch_sst and result_map.get("sst"):
            try:
                latest_sst = result_map["sst"][-1]
                sst_dataset = SSTClient.extract_variables(latest_sst)
            except Exception as e:
                logger.error("SST extraction failed", error=str(e))

        swot_dataset = None
        if fetch_swot and result_map.get("swot"):
            try:
                latest_swot = result_map["swot"][-1]
                swot_dataset = SWOTClient.extract_variables(latest_swot)
            except Exception as e:
                logger.error("SWOT extraction failed", error=str(e))

        elapsed = (datetime.utcnow() - start_dt).total_seconds()
        logger.info(
            "All datasets ready",
            elapsed_s=round(elapsed, 1),
            pace=pace_dataset is not None,
            sst=sst_dataset is not None,
            swot=swot_dataset is not None,
        )

        return CombinedOceanDataset(
            pace=pace_dataset,
            sst=sst_dataset,
            swot=swot_dataset,
            bounding_box=bounding_box,
            date_range=tuple(temporal.split(",")) if "," in temporal else (temporal, temporal),  # type: ignore
        )

    async def search_available_granules(
        self,
        bounding_box: tuple[float, float, float, float],
        temporal: str,
    ) -> dict[str, list[GranuleInfo]]:
        """
        Search all three collections for available granules without downloading.

        Useful for previewing what data is available before committing to
        potentially large downloads.

        Args:
            bounding_box: (west, south, east, north) degrees
            temporal: ISO 8601 date range

        Returns:
            Dict with keys "pace_chl", "pace_iop", "pace_rrs", "sst", "swot"
            and values of GranuleInfo lists
        """
        searches = await asyncio.gather(
            self._cmr.search_granules(Collections.PACE_OCI_CHL, bounding_box, temporal),
            self._cmr.search_granules(Collections.PACE_OCI_IOP, bounding_box, temporal),
            self._cmr.search_granules(Collections.PACE_OCI_RRS, bounding_box, temporal),
            self._cmr.search_granules(Collections.MUR_SST, bounding_box, temporal),
            self._cmr.search_granules(Collections.SWOT_L2_LR_SSH, bounding_box, temporal),
        )

        return {
            "pace_chl": searches[0],
            "pace_iop": searches[1],
            "pace_rrs": searches[2],
            "sst": searches[3],
            "swot": searches[4],
        }
