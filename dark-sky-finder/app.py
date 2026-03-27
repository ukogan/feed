"""Dark Sky Finder -- Where should I stargaze tonight?"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

import os

from fastapi import FastAPI, Query, Request
from _shared.server import create_app, run_app

from services.dark_sky_data import DARK_SKY_LOCATIONS, BRIGHT_CITIES
from services.weather_client import get_cloud_cover, get_cloud_cover_grid

APP_DIR = Path(__file__).resolve().parent

app, templates = create_app(
    title="Dark Sky Finder",
    app_dir=APP_DIR,
    description="Where should I stargaze tonight?",
)

MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")


def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Return distance in miles between two lat/lng points."""
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": MAPBOX_TOKEN,
    })


@app.get("/api/locations")
async def api_locations():
    """Return all dark sky locations and bright cities."""
    return {
        "dark_sky": DARK_SKY_LOCATIONS,
        "cities": BRIGHT_CITIES,
    }


@app.get("/api/nearest")
async def api_nearest(
    lat: float = Query(...),
    lng: float = Query(...),
    limit: int = Query(5, ge=1, le=20),
):
    """Find nearest dark sky locations to a given point."""
    scored = []
    for loc in DARK_SKY_LOCATIONS:
        dist = _haversine(lat, lng, loc["lat"], loc["lng"])
        scored.append({**loc, "distance_miles": round(dist, 1)})
    scored.sort(key=lambda x: x["distance_miles"])
    return {"results": scored[:limit]}


@app.get("/api/cloud-cover")
async def api_cloud_cover(
    lat: float = Query(...),
    lng: float = Query(...),
):
    """Fetch cloud cover forecast for a single point."""
    data = await get_cloud_cover(lat, lng)
    return data


@app.get("/api/cloud-grid")
async def api_cloud_grid(
    lat_min: float = Query(25.0),
    lat_max: float = Query(50.0),
    lng_min: float = Query(-125.0),
    lng_max: float = Query(-66.0),
    step: float = Query(3.0),
):
    """Fetch cloud cover for a grid of points (for overlay)."""
    grid = await get_cloud_cover_grid(lat_min, lat_max, lng_min, lng_max, step)
    return {"grid": grid}


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Dark Sky Finder",
        "app_description": "Find the best stargazing locations near you. Combines dark sky locations, cloud cover forecasts, and moon phase to recommend optimal viewing conditions.",
        "vision_assessment": "The Open-Meteo cloud cover integration works and the 50 hardcoded IDA locations provide a starting point. But 50 points on a US map is sparse -- the app feels more like a curated list than a discovery tool. The fundamental missing piece is actual light pollution data. Without it, the app can only tell you 'go to these known dark spots' rather than 'here is an undiscovered dark spot 20 minutes from your house.' Uses a standalone template without shared nav.",
        "killer_feature": "Tonight's sky score -- a single 0-100 rating for any location that combines real-time cloud cover forecast, moon phase and position, light pollution from satellite data, and atmospheric transparency. Push notifications when conditions align for exceptional stargazing at your saved locations. 'Your backyard is a 34 tonight, but drive 45 minutes to [location] for a 91.'",
        "data_gaps": [
            "No actual light pollution data layer -- only 50 hardcoded point locations",
            "Standalone template without shared navigation (inconsistent with other apps)",
            "No satellite pass predictions (ISS, Starlink, etc.)",
            "No aurora visibility forecasts",
            "No atmospheric transparency or seeing conditions data",
            "Bortle class ratings are estimates, not measured values",
            "No user-contributed dark sky locations",
        ],
        "related_apis": [
            {"name": "NASA Black Marble (VNP46)", "url": "https://blackmarble.gsfc.nasa.gov/", "description": "Satellite-measured nighttime light emissions. The actual light pollution data layer needed to turn this from a curated list into a discovery tool.", "free": True},
            {"name": "NOAA SWPC Aurora", "url": "https://services.swpc.noaa.gov/", "description": "Space Weather Prediction Center aurora forecasts. Kp index and ovation model for aurora visibility predictions.", "free": True},
            {"name": "Heavens-Above / CelesTrak", "url": "https://celestrak.org/", "description": "Satellite pass predictions including ISS and Starlink trains. TLE orbital elements for computing visible passes.", "free": True},
            {"name": "Clear Outside", "url": "https://clearoutside.com/", "description": "Astronomy-specific weather forecasts including seeing, transparency, and dew point. Purpose-built for stargazers.", "free": True},
        ],
        "data_sources": [
            {
                "name": "Open-Meteo Weather API",
                "url": "https://api.open-meteo.com/",
                "provider": "Open-Meteo",
                "coverage": "Global",
                "granularity": "Hourly forecast per coordinate",
                "update_frequency": "Hourly forecast updates",
                "authentication": "Free, no key required",
                "rate_limits": "10,000 calls/day",
                "history": "Forecast data only (not historical)",
                "key_fields": ["cloud_cover (%)", "cloud_cover_low", "cloud_cover_mid", "cloud_cover_high", "temperature", "humidity"],
                "caveats": "Cloud cover forecasts decrease in accuracy beyond 48 hours. Resolution varies by region.",
            },
            {
                "name": "IDA Dark Sky Places",
                "url": "",
                "provider": "International Dark-Sky Association (hardcoded dataset)",
                "coverage": "~50 certified dark sky locations worldwide",
                "granularity": "Per location with Bortle class rating",
                "update_frequency": "Static (updated manually in source code)",
                "authentication": "N/A (embedded data)",
                "rate_limits": "N/A",
                "history": "Current certified locations",
                "key_fields": ["name", "lat", "lng", "bortle_class", "designation"],
                "caveats": "Only 50 locations -- sparse coverage. List may not include the most recently certified sites. Bortle class ratings are estimates.",
            },
            {
                "name": "Moon Phase (computed)",
                "url": "",
                "provider": "Client-side computation",
                "coverage": "Global (astronomical calculation)",
                "granularity": "Daily",
                "update_frequency": "Computed on each page load",
                "authentication": "N/A",
                "rate_limits": "N/A",
                "history": "Any date (algorithmic)",
                "key_fields": ["phase", "illumination (%)", "age (days)"],
                "caveats": "Computed from a known new moon reference date. Accurate to within a few hours for illumination percentage.",
            },
        ],
        "data_freshness": "Cloud cover forecasts are fetched in real-time from Open-Meteo. Dark sky locations are a static embedded dataset of ~50 IDA-certified places. Moon phase is computed client-side from astronomical algorithms, requiring no API call.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8012)
