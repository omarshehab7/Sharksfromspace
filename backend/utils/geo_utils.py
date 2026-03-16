"""
geo_utils.py — Geospatial Utility Functions
==============================================

Helper functions for coordinate transformations,
bounding box calculations, and distance computations.
"""

import math
from typing import NamedTuple


class BoundingBox(NamedTuple):
    """Geographic bounding box (west, south, east, north)."""
    west: float
    south: float
    east: float
    north: float


def point_to_bounding_box(
    lat: float,
    lon: float,
    radius_km: float,
) -> BoundingBox:
    """
    Create a bounding box around a point with a given radius.

    Args:
        lat: Center latitude (degrees)
        lon: Center longitude (degrees)
        radius_km: Radius in kilometers

    Returns:
        BoundingBox (west, south, east, north)
    """
    # Approximate degrees per km at the given latitude
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat))

    delta_lat = radius_km / km_per_deg_lat
    delta_lon = radius_km / km_per_deg_lon if km_per_deg_lon > 0 else radius_km / 111.32

    return BoundingBox(
        west=lon - delta_lon,
        south=lat - delta_lat,
        east=lon + delta_lon,
        north=lat + delta_lat,
    )


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Calculate the great-circle distance between two points in km.

    Args:
        lat1, lon1: First point coordinates (degrees)
        lat2, lon2: Second point coordinates (degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth's radius in km

    lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
    lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def validate_coordinates(lat: float, lon: float) -> bool:
    """Validate that coordinates are within valid ranges."""
    return -90 <= lat <= 90 and -180 <= lon <= 180
