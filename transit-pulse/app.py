"""Transit Pulse: Transit reliability scores from real-time BART data."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.bart_client import (
    fetch_stations,
    fetch_departures,
    fetch_all_departures,
    compute_reliability,
)

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app, templates = create_app(
    title="Transit Pulse",
    app_dir=APP_DIR,
    description="Transit reliability scores from real-time BART data",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": MAPBOX_TOKEN,
    })


@app.get("/api/stations")
async def get_stations():
    """Get all BART stations with coordinates."""
    try:
        stations = await fetch_stations()
        return {"stations": stations, "count": len(stations)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/departures/{station}")
async def get_departures(station: str):
    """Get estimated departures for a station."""
    try:
        departures = await fetch_departures(station.upper())
        return {"station": station.upper(), "departures": departures}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/reliability")
async def get_reliability():
    """Get system-wide reliability scores computed from current departures."""
    try:
        all_deps = await fetch_all_departures()
        reliability = compute_reliability(all_deps)
        return reliability
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/dashboard")
async def get_dashboard():
    """Get a combined dashboard view: stations, departures sample, and reliability."""
    errors = []
    stations = []
    sample_deps = {}
    reliability = {}

    try:
        stations = await fetch_stations()
    except Exception as e:
        errors.append(f"stations: {e}")

    try:
        all_deps = await fetch_all_departures()
        reliability = compute_reliability(all_deps)
        # Include a sample of departures per station (top 5)
        for abbr, deps in all_deps.items():
            sample_deps[abbr] = deps[:5]
    except Exception as e:
        errors.append(f"departures: {e}")

    return {
        "stations": stations,
        "sample_departures": sample_deps,
        "reliability": reliability,
        "errors": errors,
    }


if __name__ == "__main__":
    run_app(app, default_port=8017)
