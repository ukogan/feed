"""Bridge Watch: US bridge condition map powered by the National Bridge Inventory."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.nbi_client import fetch_bridges, compute_stats, STATE_CODES

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app, templates = create_app(
    title="Bridge Watch",
    app_dir=APP_DIR,
    description="US bridge condition map from the National Bridge Inventory",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": MAPBOX_TOKEN,
        "state_codes": STATE_CODES,
    })


@app.get("/api/bridges")
async def get_bridges(
    state: str = Query("06", description="FIPS state code"),
):
    """Fetch bridges for a state and return GeoJSON-like data with stats."""
    if state not in STATE_CODES:
        return JSONResponse(
            {"error": f"Invalid state code: {state}"},
            status_code=400,
        )
    try:
        bridges = await fetch_bridges(state_code=state)
        stats = compute_stats(bridges)
        return {
            "bridges": bridges,
            "stats": stats,
            "state_code": state,
            "state_name": STATE_CODES[state],
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/states")
async def get_states():
    """Return the list of available state codes and names."""
    return {"states": [{"code": k, "name": v} for k, v in STATE_CODES.items()]}


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Bridge Watch",
        "app_description": "US bridge condition map powered by the National Bridge Inventory. Visualizes structural condition ratings, age, and traffic data for 600K+ bridges.",
        "vision_assessment": "The NBI REST API now requires an authentication token, which blocks the core data source. The app currently shows 0 bridges. The vision needs to pivot to FHWA bulk CSV downloads or find an alternative endpoint. The visualization concept (condition-coded bridge markers with age and traffic data) is sound, but the data pipeline is broken.",
        "killer_feature": "Bridge life clock -- for any bridge you cross regularly, show its full biography: when it was built, every inspection it's ever had, how its condition scores have trended over decades, and a statistical estimate of when it will likely need major rehabilitation or replacement based on deterioration curves for its structural type. Overlay with the daily traffic count to show the risk exposure.",
        "data_gaps": [
            "NBI REST API now requires auth token -- app shows 0 bridges (BLOCKED)",
            "Need to pivot to FHWA bulk CSV downloads (annual snapshots available)",
            "No historical inspection trend data in current implementation (only latest snapshot)",
            "No bridge closure or weight restriction alerts",
            "No correlation with seismic risk zones for earthquake-prone regions",
            "No funding or rehabilitation project status data",
        ],
        "related_apis": [
            {"name": "FHWA NBI CSV Downloads", "url": "https://www.fhwa.dot.gov/bridge/nbi/ascii.cfm", "description": "Annual bulk CSV downloads of the complete National Bridge Inventory. The fallback data source since the REST API now requires auth.", "free": True},
            {"name": "FHWA HPMS", "url": "https://www.fhwa.dot.gov/policyinformation/hpms.cfm", "description": "Highway Performance Monitoring System. Road condition and traffic volume data that could enrich bridge context.", "free": True},
            {"name": "USGS Earthquake Hazards", "url": "https://earthquake.usgs.gov/fdsnws/event/1/", "description": "Overlay seismic activity near bridges to assess earthquake vulnerability.", "free": True},
        ],
        "data_sources": [
            {
                "name": "National Bridge Inventory (NBI)",
                "url": "https://geo.dot.gov/",
                "provider": "US Department of Transportation / Federal Highway Administration",
                "coverage": "US nationwide, 600,000+ bridges",
                "granularity": "Per bridge, with spatial query support",
                "update_frequency": "Annually",
                "authentication": "Now requires auth token (previously free)",
                "rate_limits": "REST API with standard rate limiting",
                "history": "Current inventory snapshot with year-built data",
                "key_fields": ["structure_number", "condition_deck (0-9)", "condition_superstructure (0-9)", "condition_substructure (0-9)", "year_built", "adt (traffic count)", "lat", "lng"],
                "caveats": "API now requires authentication -- currently blocked. Condition ratings use a 0-9 scale (9=excellent, 0=failed). Annual updates mean recently repaired bridges may still show old ratings.",
            },
        ],
        "data_freshness": "Bridge data pipeline is currently blocked due to NBI REST API authentication requirement. The underlying data is updated annually by state DOTs. Pivot to FHWA bulk CSV downloads is needed to restore functionality.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8010)
