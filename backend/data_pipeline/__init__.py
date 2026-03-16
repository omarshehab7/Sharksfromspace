# backend/data_pipeline/__init__.py
"""
Data Pipeline Package
======================
8-stage ocean data processing pipeline:

  1. ingest             → Fetch NASA datasets (PACE, SST, SWOT)
  2. transform          → Preprocess grids (quality filter, regrid, unit convert)
  3. feature_engineering → Extract ML features
  4. ocean_fronts       → Detect thermal/productivity fronts
  5. eddy_detection     → Detect mesoscale eddies from SSHA
  6. productivity_index → Composite marine productivity index
  7. ml_model (models/) → Shark habitat prediction model
  8. spatial_analysis   → GeoJSON hotspots + GeoTIFF heatmaps
"""
