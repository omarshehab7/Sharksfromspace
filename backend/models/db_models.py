"""
db_models.py — SQLAlchemy ORM Models with PostGIS
====================================================

Database models for persisting shark hotspot predictions
and ocean data. Uses GeoAlchemy2 for PostGIS geometry columns.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.orm import DeclarativeBase
from geoalchemy2 import Geometry


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


class Hotspot(Base):
    """
    Predicted shark activity hotspot.

    Each hotspot represents a geographic area where the ML model
    predicts elevated shark activity based on ocean conditions.
    """
    __tablename__ = "hotspots"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Geospatial location (PostGIS Point)
    location = Column(
        Geometry("POINT", srid=4326),
        nullable=False,
        index=True,
        comment="Hotspot center point (WGS84)",
    )

    # Risk assessment
    risk_score = Column(Float, nullable=False, comment="ML prediction score (0-1)")
    risk_level = Column(
        String(10),
        nullable=False,
        comment="Categorical risk: low, medium, high",
    )

    # Ocean parameters at prediction time
    sst = Column(Float, comment="Sea surface temperature (°C)")
    sst_anomaly = Column(Float, comment="SST deviation from climatology (°C)")
    chlorophyll = Column(Float, comment="Chlorophyll-a concentration (mg/m³)")
    depth = Column(Float, comment="Water depth (meters)")
    current_speed = Column(Float, comment="Ocean current speed (m/s)")

    # Predicted species (stored as JSON array)
    species = Column(JSON, default=list, comment="List of likely shark species")

    # Metadata
    predicted_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    data_source = Column(String(50), comment="Source satellite product")
    model_version = Column(String(20), comment="ML model version used")

    def __repr__(self):
        return f"<Hotspot(id={self.id}, risk={self.risk_level}, score={self.risk_score:.2f})>"


class OceanDataTile(Base):
    """
    Processed ocean data tile from satellite observations.

    Stores gridded ocean parameter values for a geographic region,
    used for API queries and as input to the prediction model.
    """
    __tablename__ = "ocean_data_tiles"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Geospatial coverage (PostGIS Polygon)
    bounds = Column(
        Geometry("POLYGON", srid=4326),
        nullable=False,
        index=True,
        comment="Geographic bounds of this tile",
    )

    # Data point location
    center = Column(
        Geometry("POINT", srid=4326),
        nullable=False,
        comment="Center point of the tile",
    )

    # Ocean parameters
    sst = Column(Float, comment="Sea surface temperature (°C)")
    chlorophyll = Column(Float, comment="Chlorophyll-a (mg/m³)")
    salinity = Column(Float, comment="Salinity (PSU)")
    current_speed = Column(Float, comment="Current speed (m/s)")
    current_direction = Column(Float, comment="Current direction (degrees)")
    depth = Column(Float, comment="Bathymetric depth (meters)")

    # Metadata
    observed_at = Column(DateTime, nullable=False, comment="Observation timestamp")
    source = Column(String(50), comment="Data source (MODIS, GHRSST, etc.)")
    resolution_km = Column(Float, comment="Spatial resolution in km")
    ingested_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OceanDataTile(id={self.id}, source={self.source}, observed={self.observed_at})>"
