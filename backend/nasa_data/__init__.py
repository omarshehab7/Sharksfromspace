# backend/nasa_data/__init__.py
"""
NASA Data Package
==================
Clients for fetching satellite ocean data from three NASA missions:

  - nasa_client:       Unified NASAClient facade (primary interface)
                       ├── PACEClient   — PACE OCI ocean color (chlor-a, IOP, Rrs)
                       ├── SSTClient    — GHRSST MUR SST + anomaly + gradient
                       └── SWOTClient   — SWOT KaRIn sea surface height + eddies

  - earthdata_client:  Low-level CMR search + OPeNDAP download helper
  - modis_fetcher:     Legacy MODIS SST & chlorophyll (pre-PACE missions)
  - ghrsst_fetcher:    GHRSST Level 4 SST downloader

Typical usage:
    from nasa_data.nasa_client import NASAClient

    async with NASAClient() as client:
        dataset = await client.fetch_all(
            bounding_box=(-80, 20, -60, 35),
            temporal="2024-06-01,2024-06-07",
            output_dir="./data/raw",
        )
"""

from nasa_data.nasa_client import (
    NASAClient,
    PACEClient,
    SSTClient,
    SWOTClient,
    CMRClient,
    Collections,
    CombinedOceanDataset,
    PACEOceanDataset,
    SSTDataset,
    SWOTDataset,
    GranuleInfo,
)

__all__ = [
    "NASAClient",
    "PACEClient",
    "SSTClient",
    "SWOTClient",
    "CMRClient",
    "Collections",
    "CombinedOceanDataset",
    "PACEOceanDataset",
    "SSTDataset",
    "SWOTDataset",
    "GranuleInfo",
]
