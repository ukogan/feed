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


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Transit Pulse",
        "app_description": "Transit reliability scores from real-time BART data. Monitors station departures across the Bay Area Rapid Transit system and computes reliability metrics.",
        "vision_assessment": "The BART API works with its public key and returns departure estimates for all stations. The reliability score computation is functional. The fundamental limitation is that each page load captures a single point-in-time snapshot -- there's no accumulated historical reliability data, so you can't answer 'is the Pittsburg line usually late at 5pm?' The departure estimates also don't tell you where trains actually are between stations.",
        "killer_feature": "BART reliability report card -- continuously poll the API (every 2 minutes) and accumulate a database of actual vs predicted departure times. After a month of data, generate a reliability grade for each line, each station, and each time-of-day window. Show commuters exactly which trains are consistently late and by how much, with a 'leave by' recommendation that accounts for real observed delays, not just the schedule.",
        "data_gaps": [
            "Single point-in-time snapshot only -- no accumulated reliability history",
            "Can't track actual train positions between stations (only departure estimates)",
            "No comparison between predicted and actual departure times",
            "No service alert or disruption history",
            "No ridership or crowding data",
            "Limited to BART -- no integration with Muni, Caltrain, or AC Transit",
        ],
        "related_apis": [
            {"name": "BART GTFS-Realtime", "url": "https://www.bart.gov/schedules/developers/gtfs-realtime", "description": "GTFS-RT feed that may include VehiclePosition messages (actual train locations), not just departure predictions.", "free": True},
            {"name": "511.org Transit API", "url": "https://511.org/open-data/transit", "description": "Regional transit data for the entire Bay Area including Muni, Caltrain, AC Transit, and BART.", "free": True},
            {"name": "MTC Open Data", "url": "https://opendata.mtc.ca.gov/", "description": "Metropolitan Transportation Commission data including regional ridership statistics and performance metrics.", "free": True},
            {"name": "BART Ridership Data", "url": "https://www.bart.gov/about/reports/ridership", "description": "Historical ridership data by station and time period. Could overlay crowding patterns on reliability scores.", "free": True},
        ],
        "data_sources": [
            {
                "name": "BART API",
                "url": "https://api.bart.gov/api/",
                "provider": "Bay Area Rapid Transit",
                "coverage": "BART system (San Francisco Bay Area)",
                "granularity": "Per station, per departure estimate",
                "update_frequency": "Real-time (live departure estimates)",
                "authentication": "Free public API key (MW9S-E7SL-26DU-VV8V)",
                "rate_limits": "No published limits",
                "history": "Real-time only (no historical departures)",
                "key_fields": ["station_abbr", "station_name", "destination", "minutes", "platform", "direction", "delay"],
                "caveats": "Departure estimates are predictions, not guaranteed times. During service disruptions, data may be incomplete or delayed. The public API key is shared across all users. No accumulated historical data.",
            },
        ],
        "data_freshness": "Departure estimates are fetched in real-time from the BART API on each request. Reliability scores are computed from a single point-in-time snapshot of current departures across all stations. No historical tracking or trend analysis is performed.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8017)
