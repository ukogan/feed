"""Geocoding and coordinate utilities."""

import math

import httpx


async def geocode_address(address: str, mapbox_token: str) -> tuple[float, float]:
    """Convert an address to (lat, lng) using Mapbox Geocoding API.

    Returns (latitude, longitude).
    Raises ValueError if address not found.
    """
    url = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{url}/{address}.json",
            params={"access_token": mapbox_token, "limit": 1},
        )
        response.raise_for_status()
        data = response.json()

    features = data.get("features", [])
    if not features:
        raise ValueError(f"Address not found: {address}")

    lng, lat = features[0]["center"]
    return lat, lng


def haversine_distance_nm(
    lat1: float, lng1: float, lat2: float, lng2: float
) -> float:
    """Calculate distance between two points in nautical miles."""
    R_NM = 3440.065  # Earth radius in nautical miles
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return R_NM * 2 * math.asin(math.sqrt(a))


def bounding_box(lat: float, lng: float, radius_nm: float) -> dict:
    """Get bounding box around a point. Returns {min_lat, max_lat, min_lng, max_lng}."""
    # 1 degree lat ≈ 60 NM
    dlat = radius_nm / 60.0
    dlng = radius_nm / (60.0 * math.cos(math.radians(lat)))
    return {
        "min_lat": lat - dlat,
        "max_lat": lat + dlat,
        "min_lng": lng - dlng,
        "max_lng": lng + dlng,
    }
