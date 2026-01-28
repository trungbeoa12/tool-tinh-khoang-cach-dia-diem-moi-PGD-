"""Haversine distance utilities (km)."""

import math
import numpy as np


EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute great-circle distance between two lat/lng pairs in km."""
    lat1_rad, lon1_rad = math.radians(lat1), math.radians(lon1)
    lat2_rad, lon2_rad = math.radians(lat2), math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return EARTH_RADIUS_KM * c


def haversine_vectorized(origin_lat: float, origin_lng: float, dest_lats: np.ndarray, dest_lngs: np.ndarray) -> np.ndarray:
    """Vectorized haversine distances from one origin to many destinations."""
    lat1 = np.radians(origin_lat)
    lon1 = np.radians(origin_lng)
    lat2 = np.radians(dest_lats.astype(float))
    lon2 = np.radians(dest_lngs.astype(float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.minimum(1.0, np.sqrt(a)))
    return EARTH_RADIUS_KM * c

