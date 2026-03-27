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


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "AQI Map",
        "app_description": "Historical air quality heatmap with animated time controls. Visualizes PM2.5 and Ozone readings from EPA monitoring stations across the US.",
        "data_sources": [
            {
                "name": "EPA AQS API",
                "url": "https://aqs.epa.gov/data/api/",
                "provider": "US Environmental Protection Agency",
                "coverage": "US nationwide, ~1,300 monitoring stations",
                "granularity": "Hourly readings per station",
                "update_frequency": "Hourly",
                "authentication": "Free (email address used as API key)",
                "rate_limits": "~10 requests/minute",
                "history": "Back to 1990",
                "key_fields": ["site_id", "aqi", "parameter (88101=PM2.5, 44201=Ozone)", "lat", "lng", "state", "county"],
                "caveats": "Not all stations report all parameters. Some stations have gaps in historical data.",
            },
            {
                "name": "OpenWeatherMap Air Pollution API",
                "url": "https://api.openweathermap.org/",
                "provider": "OpenWeatherMap",
                "coverage": "Global coverage",
                "granularity": "Hourly per coordinate",
                "update_frequency": "Hourly",
                "authentication": "API key required (free tier available)",
                "rate_limits": "1,000 calls/day on free tier",
                "history": "Since November 2020",
                "key_fields": ["aqi", "pm2_5", "pm10", "o3", "no2", "so2", "co"],
                "caveats": "Free tier has limited daily calls. Global coverage but resolution varies by region.",
            },
        ],
        "data_freshness": "AQI data is stored in a local SQLite database with monthly aggregations. The app displays historical monthly averages per station, not real-time readings. Data must be ingested via a separate import process.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8000)
