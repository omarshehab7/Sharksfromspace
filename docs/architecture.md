# Architecture Overview

## System Architecture

```
┌─────────────────────┐     ┌──────────────────────┐     ┌────────────────────┐
│    Mobile App        │     │    Backend API        │     │   Data Pipeline    │
│  (React Native/Expo) │────▶│  (FastAPI/Python)     │◀────│   (Ruflo/Python)   │
│                      │     │                       │     │                    │
│  • Mapbox Maps       │     │  • /hotspots          │     │  • Fetch NASA data │
│  • TanStack Query    │     │  • /ocean-data        │     │  • Process netCDF4 │
│  • NativeWind        │     │  • ML Predictions     │     │  • Extract features│
└─────────────────────┘     └───────┬───────────────┘     │  • Run predictions │
                                    │                      └────────┬───────────┘
                                    ▼                               │
                            ┌───────────────┐                       │
                            │  PostgreSQL    │◀──────────────────────┘
                            │  + PostGIS     │
                            │               │
                            │  Redis Cache   │
                            └───────────────┘
```

## Data Flow

1. **Ruflo pipeline** runs every 6 hours:
   - Downloads SST, chlorophyll, and bathymetry data from NASA Earthdata
   - Processes netCDF4 files with xarray/numpy
   - Extracts ML features (SST gradient, anomaly, depth, etc.)
   - Runs the shark prediction model
   - Stores predicted hotspots in PostGIS

2. **FastAPI backend** serves the mobile app:
   - Queries PostGIS for hotspots within a bounding box
   - Returns ocean parameter data for specific locations
   - Caches frequent queries with Redis

3. **React Native app** displays results:
   - Mapbox heatmap and marker layers show hotspots
   - TanStack Query manages server state with auto-refresh
   - Educational content explains the science

## Technology Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Map SDK | Mapbox React Native | Rich heatmap/vector layers, dark theme, offline support |
| Server state | TanStack Query | Automatic caching, refetching, and error handling |
| Styling | NativeWind | Tailwind-style utility classes for React Native |
| Backend | FastAPI | Async Python, auto-docs, Pydantic validation |
| Spatial DB | PostGIS | Industry-standard geospatial queries (ST_Within, etc.) |
| ML Pipeline | Ruflo | Declarative workflow orchestration with task dependencies |
| SST Data | GHRSST MUR | Gap-free, 1km resolution, blended from multiple satellites |

## Key Ocean Data Products

| Product | Source | Resolution | Use |
|---|---|---|---|
| MUR SST | GHRSST / PO.DAAC | 1 km, daily | Sea surface temperature (primary) |
| Chlorophyll-a | MODIS Aqua / OB_DAAC | 4 km, daily | Plankton abundance → prey availability |
| ETOPO 2022 | NOAA | 1 arc-min | Bathymetry (water depth) |
