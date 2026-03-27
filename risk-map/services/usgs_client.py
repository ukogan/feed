"""USGS Earthquake API client for California."""

from datetime import datetime, timedelta

import httpx

USGS_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/query"

# California bounding box
CA_BOUNDS = {
    "minlatitude": 32,
    "maxlatitude": 42,
    "minlongitude": -125,
    "maxlongitude": -114,
}


async def fetch_earthquakes(days_back: int = 365, min_magnitude: float = 1.0) -> list[dict]:
    """Fetch recent earthquakes in California from the USGS API.

    Returns list of dicts with: id, lat, lng, magnitude, depth, place, time, url.
    """
    start_time = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    params = {
        "format": "geojson",
        "starttime": start_time,
        "minmagnitude": min_magnitude,
        **CA_BOUNDS,
        "orderby": "time",
        "limit": 2000,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(USGS_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    results = []
    for f in features:
        props = f["properties"]
        coords = f["geometry"]["coordinates"]
        results.append({
            "id": f["id"],
            "lng": coords[0],
            "lat": coords[1],
            "depth": coords[2],
            "magnitude": props.get("mag", 0),
            "place": props.get("place", ""),
            "time": props.get("time", 0),
            "url": props.get("url", ""),
            "type": props.get("type", "earthquake"),
        })

    return results


async def fetch_earthquake_stats() -> dict:
    """Get summary stats: count by magnitude range for the last year."""
    quakes = await fetch_earthquakes(days_back=365, min_magnitude=0.5)

    ranges = {"0-2": 0, "2-3": 0, "3-4": 0, "4-5": 0, "5+": 0}
    for q in quakes:
        mag = q["magnitude"]
        if mag < 2:
            ranges["0-2"] += 1
        elif mag < 3:
            ranges["2-3"] += 1
        elif mag < 4:
            ranges["3-4"] += 1
        elif mag < 5:
            ranges["4-5"] += 1
        else:
            ranges["5+"] += 1

    return {
        "total": len(quakes),
        "ranges": ranges,
        "max_magnitude": max((q["magnitude"] for q in quakes), default=0),
    }
