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
        "data_sources": [
            {
                "name": "National Bridge Inventory (NBI)",
                "url": "https://geo.dot.gov/",
                "provider": "US Department of Transportation / Federal Highway Administration",
                "coverage": "US nationwide, 600,000+ bridges",
                "granularity": "Per bridge, with spatial query support",
                "update_frequency": "Annually",
                "authentication": "Free, no key required",
                "rate_limits": "REST API with standard rate limiting",
                "history": "Current inventory snapshot with year-built data",
                "key_fields": ["structure_number", "condition_deck (0-9)", "condition_superstructure (0-9)", "condition_substructure (0-9)", "year_built", "adt (traffic count)", "lat", "lng"],
                "caveats": "Condition ratings use a 0-9 scale (9=excellent, 0=failed). Some bridges may have incomplete data. Annual updates mean recently repaired bridges may still show old ratings.",
            },
        ],
        "data_freshness": "Bridge data is fetched directly from the NBI REST API per state on each request. The underlying data is updated annually by state DOTs. Condition ratings reflect the most recent inspection cycle.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8010)
