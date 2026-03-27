"""NIFC Wildland Fire and NWS Fire Weather API clients."""

import httpx

NIFC_PERIMETERS_URL = (
    "https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services/"
    "NIFC_WildlandFire_Perimeters/FeatureServer/0/query"
)

NWS_ALERTS_URL = "https://api.weather.gov/alerts/active"


async def fetch_fire_perimeters() -> list[dict]:
    """Fetch active wildland fire perimeters in/near California from NIFC.

    Returns list of dicts with: name, acres, containment, geometry (GeoJSON polygon),
    start_date, and centroid lat/lng.
    """
    params = {
        "where": "1=1",
        "outFields": (
            "IncidentName,GISAcres,PercentContained,"
            "FireDiscoveryDateTime,POOState"
        ),
        "f": "geojson",
        "geometry": "-125,32,-114,42",
        "geometryType": "esriGeometryEnvelope",
        "spatialRel": "esriSpatialRelIntersects",
        "resultRecordCount": 200,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(NIFC_PERIMETERS_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    results = []
    for f in features:
        props = f.get("properties", {})
        geometry = f.get("geometry", {})

        # Compute centroid from first coordinate ring
        centroid = _compute_centroid(geometry)

        results.append({
            "name": props.get("IncidentName", "Unknown"),
            "acres": props.get("GISAcres", 0),
            "containment": props.get("PercentContained", 0),
            "start_date": props.get("FireDiscoveryDateTime"),
            "state": props.get("POOState", ""),
            "geometry": geometry,
            "centroid_lat": centroid[1],
            "centroid_lng": centroid[0],
        })

    return results


def _compute_centroid(geometry: dict) -> tuple[float, float]:
    """Compute a rough centroid from a GeoJSON geometry."""
    coords = geometry.get("coordinates", [])
    if not coords:
        return (0, 0)

    geo_type = geometry.get("type", "")

    all_points = []
    if geo_type == "Polygon" and coords:
        all_points = coords[0]
    elif geo_type == "MultiPolygon" and coords:
        for polygon in coords:
            if polygon:
                all_points.extend(polygon[0])

    if not all_points:
        return (0, 0)

    avg_lng = sum(p[0] for p in all_points) / len(all_points)
    avg_lat = sum(p[1] for p in all_points) / len(all_points)
    return (avg_lng, avg_lat)


async def fetch_fire_weather_alerts() -> list[dict]:
    """Fetch active fire weather alerts for California from NWS.

    Returns list of dicts with: headline, severity, description, areas, onset, expires.
    """
    params = {
        "area": "CA",
        "event": "Fire Weather Watch",
    }
    headers = {
        "User-Agent": "risk-map-poc/1.0 (feed-monorepo)",
        "Accept": "application/geo+json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(NWS_ALERTS_URL, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    results = []
    for f in features:
        props = f.get("properties", {})
        results.append({
            "headline": props.get("headline", ""),
            "severity": props.get("severity", ""),
            "description": props.get("description", ""),
            "areas": props.get("areaDesc", ""),
            "onset": props.get("onset"),
            "expires": props.get("expires"),
            "event": props.get("event", ""),
        })

    # Also fetch Red Flag Warnings
    params_rfw = {
        "area": "CA",
        "event": "Red Flag Warning",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(NWS_ALERTS_URL, params=params_rfw, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        for f in data.get("features", []):
            props = f.get("properties", {})
            results.append({
                "headline": props.get("headline", ""),
                "severity": props.get("severity", ""),
                "description": props.get("description", ""),
                "areas": props.get("areaDesc", ""),
                "onset": props.get("onset"),
                "expires": props.get("expires"),
                "event": props.get("event", ""),
            })
    except Exception:
        pass  # Red Flag Warnings are supplementary

    return results
