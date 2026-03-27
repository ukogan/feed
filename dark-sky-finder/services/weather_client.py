"""Open-Meteo weather client for cloud cover forecasts."""

import httpx

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


async def get_cloud_cover(lat: float, lng: float, forecast_days: int = 1) -> dict:
    """Fetch hourly cloud cover for a location.

    Returns dict with keys: latitude, longitude, hours (list of {time, cloud_cover}).
    """
    params = {
        "latitude": lat,
        "longitude": lng,
        "hourly": "cloud_cover",
        "forecast_days": forecast_days,
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(OPEN_METEO_BASE, params=params)
        resp.raise_for_status()
        data = resp.json()

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    covers = hourly.get("cloud_cover", [])

    hours = [{"time": t, "cloud_cover": c} for t, c in zip(times, covers)]

    return {
        "latitude": data.get("latitude", lat),
        "longitude": data.get("longitude", lng),
        "hours": hours,
    }


async def get_cloud_cover_grid(
    lat_min: float,
    lat_max: float,
    lng_min: float,
    lng_max: float,
    step: float = 2.0,
) -> list[dict]:
    """Fetch cloud cover for a grid of points across a bounding box.

    Returns list of {lat, lng, cloud_cover} for the current hour.
    """
    import asyncio

    lats = []
    lat = lat_min
    while lat <= lat_max:
        lats.append(round(lat, 2))
        lat += step
    lngs = []
    lng = lng_min
    while lng <= lng_max:
        lngs.append(round(lng, 2))
        lng += step

    async def _fetch_point(la: float, lo: float) -> dict | None:
        try:
            result = await get_cloud_cover(la, lo, forecast_days=1)
            if result["hours"]:
                # Return the nearest-future hour's cloud cover
                return {"lat": la, "lng": lo, "cloud_cover": result["hours"][0]["cloud_cover"]}
        except Exception:
            pass
        return None

    tasks = [_fetch_point(la, lo) for la in lats for lo in lngs]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
