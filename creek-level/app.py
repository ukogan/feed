"""Creek Level: Real-time river and creek gauge monitor using USGS Water Services."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.usgs_client import fetch_sites, fetch_site_history, US_STATES

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app, templates = create_app(
    title="Creek Level",
    app_dir=APP_DIR,
    description="Real-time river and creek gauge monitor using USGS data",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": MAPBOX_TOKEN,
        "states": US_STATES,
    })


@app.get("/api/sites")
async def get_sites(
    state: str = Query("CA", description="Two-letter state code"),
):
    """Get active stream gauge sites for a state."""
    state = state.upper()
    if state not in US_STATES:
        return JSONResponse(
            {"error": f"Invalid state code: {state}"},
            status_code=400,
        )
    try:
        sites = await fetch_sites(state)
        return {"state": state, "count": len(sites), "sites": sites}
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to fetch sites for {state}: {str(e)}"},
            status_code=502,
        )


@app.get("/api/site/{site_no}")
async def get_site_detail(
    site_no: str,
    period: str = Query("P1D", description="ISO 8601 duration (e.g., P1D, P7D)"),
):
    """Get detailed history for a specific gauge site."""
    try:
        history = await fetch_site_history(site_no, period=period)
        return history
    except Exception as e:
        return JSONResponse(
            {"error": f"Failed to fetch data for site {site_no}: {str(e)}"},
            status_code=502,
        )


@app.get("/api/states")
async def get_states():
    """List available state codes."""
    return US_STATES


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Creek Level",
        "app_description": "Real-time river and creek gauge monitor using USGS Water Services data. Tracks gauge height and discharge at thousands of stream gauges nationwide.",
        "data_sources": [
            {
                "name": "USGS Water Services",
                "url": "https://waterservices.usgs.gov/",
                "provider": "US Geological Survey",
                "coverage": "US nationwide, thousands of stream gauges",
                "granularity": "15-minute readings per gauge",
                "update_frequency": "Every 15 minutes",
                "authentication": "Free, no key required",
                "rate_limits": "No published limits (fair use expected)",
                "history": "Decades of historical data available per site",
                "key_fields": ["site_no", "gauge_height (param 00065)", "discharge (param 00060)", "lat", "lng", "site_name", "state"],
                "caveats": "Not all gauges report all parameters. Some gauges may go offline during extreme weather events. Provisional data is subject to revision.",
            },
        ],
        "data_freshness": "Gauge readings are fetched directly from USGS on each request. Data is near-real-time with 15-minute update intervals. Historical queries use ISO 8601 duration periods (e.g., P1D for 1 day, P7D for 7 days).",
    })


if __name__ == "__main__":
    run_app(app, default_port=8011)
