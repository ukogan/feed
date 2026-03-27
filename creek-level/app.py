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
        "vision_assessment": "After fixing the wrong endpoint issue, the USGS Instantaneous Values (IV) endpoint now returns 541 CA gauges with 15-minute updates. The data quality is excellent -- USGS is one of the best-maintained federal APIs. The main gap is context: raw gauge height numbers are meaningless without flood stage thresholds, and there's no forecast integration to answer the question users actually care about: 'will this creek flood?'",
        "killer_feature": "Flood memory timeline -- for any gauge, show every flood event in its recorded history as a timeline. How high did it get? How fast did it rise? What was the weather that caused it? Then overlay the current NWS river forecast to show whether the next 7 days look like any of those historical flood patterns. Turn abstract gauge numbers into 'this creek last looked like this on [date], and here is what happened next.'",
        "data_gaps": [
            "No flood stage thresholds shown -- raw gauge height is meaningless without 'action stage' and 'flood stage' context",
            "No river forecast data to predict what happens next",
            "No precipitation data overlay to correlate rainfall with gauge response",
            "Currently limited to California (541 gauges) -- could expand nationwide",
            "No alerting or threshold notification system",
            "No watershed context (which gauges are upstream/downstream of each other)",
        ],
        "related_apis": [
            {"name": "NWS River Forecasts", "url": "https://water.weather.gov/ahps/", "description": "National Weather Service river stage forecasts with flood thresholds. The missing piece for 'will it flood?' predictions.", "free": True},
            {"name": "NOAA Precipitation Forecasts", "url": "https://www.weather.gov/documentation/services-web-api", "description": "Quantitative precipitation forecasts. Correlate expected rainfall with gauge response times.", "free": True},
            {"name": "USGS Flood Event Viewer", "url": "https://stn.wim.usgs.gov/FEV/", "description": "Historical flood event data with high-water marks and peak streamflow records.", "free": True},
            {"name": "USGS NLDI", "url": "https://waterdata.usgs.gov/blog/nldi-intro/", "description": "Network-Linked Data Index. Navigate upstream/downstream between gauges to understand watershed relationships.", "free": True},
        ],
        "data_sources": [
            {
                "name": "USGS Water Services (IV endpoint)",
                "url": "https://waterservices.usgs.gov/",
                "provider": "US Geological Survey",
                "coverage": "US nationwide -- currently showing 541 CA gauges",
                "granularity": "15-minute readings per gauge",
                "update_frequency": "Every 15 minutes",
                "authentication": "Free, no key required",
                "rate_limits": "No published limits (fair use expected)",
                "history": "Decades of historical data available per site",
                "key_fields": ["site_no", "gauge_height (param 00065)", "discharge (param 00060)", "lat", "lng", "site_name", "state"],
                "caveats": "Not all gauges report all parameters. Some gauges may go offline during extreme weather events. Provisional data is subject to revision.",
            },
        ],
        "data_freshness": "Gauge readings are fetched directly from USGS Instantaneous Values endpoint on each request. Data is near-real-time with 15-minute update intervals. Historical queries use ISO 8601 duration periods (e.g., P1D for 1 day, P7D for 7 days).",
    })


if __name__ == "__main__":
    run_app(app, default_port=8011)
