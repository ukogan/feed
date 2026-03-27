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


if __name__ == "__main__":
    run_app(app, default_port=8012)
