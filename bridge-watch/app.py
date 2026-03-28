"""Bridge Watch: US bridge condition map powered by the National Bridge Inventory."""

import os
import sqlite3
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.nbi_client import STATE_CODES

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "data" / "bridges.db"
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app, templates = create_app(
    title="Bridge Watch",
    app_dir=APP_DIR,
    description="US bridge condition map from the National Bridge Inventory",
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


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
    """Fetch bridges for a state from local SQLite database."""
    if state not in STATE_CODES:
        return JSONResponse(
            {"error": f"Invalid state code: {state}"},
            status_code=400,
        )

    if not DB_PATH.exists():
        return {
            "bridges": [],
            "stats": {"total": 0, "good": 0, "fair": 0, "poor": 0,
                       "pct_good": 0, "pct_fair": 0, "pct_poor": 0},
            "state_code": state,
            "state_name": STATE_CODES[state],
            "error": "No bridge data loaded. Run: python3 scripts/download_nbi.py",
        }

    conn = get_db()
    state_padded = state
    rows = conn.execute(
        "SELECT * FROM bridges WHERE state_code = ? LIMIT 5000",
        (state_padded,)
    ).fetchall()
    conn.close()

    bridges = []
    for r in rows:
        bridges.append({
            "name": r["name"],
            "lat": r["lat"],
            "lng": r["lng"],
            "year_built": r["year_built"],
            "adt": r["adt"] or 0,
            "deck": r["deck_cond"],
            "superstructure": r["super_cond"],
            "substructure": r["sub_cond"],
            "condition": r["condition"],
        })

    # Compute stats
    total = len(bridges)
    good = sum(1 for b in bridges if b["condition"] == "good")
    fair = sum(1 for b in bridges if b["condition"] == "fair")
    poor = sum(1 for b in bridges if b["condition"] == "poor")

    return {
        "bridges": bridges,
        "stats": {
            "total": total,
            "good": good, "fair": fair, "poor": poor,
            "pct_good": round(good / total * 100) if total else 0,
            "pct_fair": round(fair / total * 100) if total else 0,
            "pct_poor": round(poor / total * 100) if total else 0,
        },
        "state_code": state,
        "state_name": STATE_CODES[state],
    }


@app.get("/api/states")
async def get_states():
    """Return available states (those with data in the database)."""
    if not DB_PATH.exists():
        return {"states": [{"code": k, "name": v} for k, v in STATE_CODES.items()]}

    conn = get_db()
    loaded = conn.execute(
        "SELECT DISTINCT state_code FROM bridges"
    ).fetchall()
    conn.close()
    loaded_codes = {r["state_code"].lstrip("0") .zfill(2) for r in loaded}

    return {
        "states": [
            {"code": k, "name": v, "loaded": k in loaded_codes}
            for k, v in STATE_CODES.items()
        ]
    }


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Bridge Watch",
        "app_description": "US bridge condition map from the National Bridge Inventory. Visualizes structural condition ratings, age, and traffic for 600K+ bridges.",
        "vision_assessment": "Pivoted from the NBI REST API (now requires auth) to FHWA bulk CSV downloads. Bridge data loads from local SQLite populated by download script. The visualization concept works well -- condition-coded markers with traffic and age data.",
        "killer_feature": "Bridge life clock -- show a bridge's full biography: when built, condition trend over decades, statistical estimate of when it will need rehabilitation based on deterioration curves for its structural type, overlaid with daily traffic count to show risk exposure.",
        "data_gaps": [
            "Only 10 states pre-configured (easily expandable)",
            "No historical inspection trend data (only latest annual snapshot)",
            "No bridge closure or weight restriction alerts",
            "No correlation with seismic risk zones",
        ],
        "related_apis": [
            {"name": "FHWA NBI CSV Downloads", "url": "https://www.fhwa.dot.gov/bridge/nbi/ascii.cfm", "description": "Annual bulk downloads of the complete NBI. Primary data source.", "free": True},
            {"name": "USGS Earthquake Hazards", "url": "https://earthquake.usgs.gov/", "description": "Overlay seismic activity near bridges for vulnerability assessment.", "free": True},
        ],
        "data_sources": [
            {
                "name": "National Bridge Inventory (NBI) via FHWA CSV",
                "url": "https://www.fhwa.dot.gov/bridge/nbi/ascii.cfm",
                "provider": "Federal Highway Administration",
                "coverage": "US nationwide, 600,000+ bridges",
                "granularity": "Per bridge with condition ratings, coordinates, traffic",
                "update_frequency": "Annually (published ~June each year)",
                "authentication": "Free download, no key required",
                "rate_limits": "None (bulk download)",
                "history": "Annual snapshots available for multiple years",
                "key_fields": ["structure_number", "deck/super/sub condition (0-9)", "year_built", "ADT (traffic)", "lat/lng"],
                "caveats": "Fixed-width text format requires parsing. Condition ratings 0-9 (9=excellent, 0=failed). Data is annual so recently repaired bridges may show old ratings.",
            },
        ],
        "data_freshness": "Bridge data is downloaded from FHWA and stored in local SQLite. Run scripts/download_nbi.py to populate. Data reflects the 2024 annual NBI snapshot.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8010)
