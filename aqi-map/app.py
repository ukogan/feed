"""AQI Time-Slider Map: Historical air quality heatmap with animated time slider."""

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

# Add parent to path for _shared
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.server import create_app, run_app

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "data" / "aqi.db"

app, templates = create_app(
    title="AQI Time-Slider Map",
    app_dir=APP_DIR,
    description="Historical air quality heatmap with animated time controls",
)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/")
async def index(request: Request):
    mapbox_token = os.getenv("MAPBOX_TOKEN", "")
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": mapbox_token,
    })


@app.get("/api/stations")
async def get_stations():
    """Get all monitoring stations with lat/lng."""
    conn = get_db()
    rows = conn.execute(
        "SELECT site_id, name, lat, lng, state_name, county_name FROM stations"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/aqi")
async def get_aqi(
    year: int = Query(..., ge=2000, le=2026),
    month: int = Query(0, ge=0, le=12),
    parameter: str = Query("PM2.5"),
):
    """Get AQI data for a time period.

    If month=0, returns all months for that year.
    Returns [{site_id, lat, lng, aqi, year, month}]
    """
    conn = get_db()

    if month > 0:
        rows = conn.execute("""
            SELECT m.site_id, s.lat, s.lng, m.avg_aqi as aqi, m.year, m.month
            FROM monthly_aqi m
            JOIN stations s ON m.site_id = s.site_id
            WHERE m.year = ? AND m.month = ? AND m.parameter = ?
        """, (year, month, parameter)).fetchall()
    else:
        rows = conn.execute("""
            SELECT m.site_id, s.lat, s.lng, m.avg_aqi as aqi, m.year, m.month
            FROM monthly_aqi m
            JOIN stations s ON m.site_id = s.site_id
            WHERE m.year = ? AND m.parameter = ?
        """, (year, parameter)).fetchall()

    conn.close()
    return [dict(r) for r in rows]


@app.get("/api/years")
async def get_available_years():
    """Get list of years with data."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT DISTINCT year FROM monthly_aqi ORDER BY year"
        ).fetchall()
        conn.close()
        return [r["year"] for r in rows]
    except Exception:
        conn.close()
        return []


if __name__ == "__main__":
    run_app(app, default_port=8000)
