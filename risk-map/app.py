"""Risk Map: Combined earthquake + wildfire risk map for California."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.usgs_client import fetch_earthquakes
from services.fire_client import fetch_fire_perimeters, fetch_fire_weather_alerts

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app, templates = create_app(
    title="Risk Map",
    app_dir=APP_DIR,
    description="Combined earthquake and wildfire risk map for California",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": MAPBOX_TOKEN,
    })


@app.get("/api/earthquakes")
async def get_earthquakes(
    days: int = Query(365, ge=1, le=3650),
    min_mag: float = Query(1.0, ge=0, le=10),
):
    """Get recent California earthquakes."""
    try:
        quakes = await fetch_earthquakes(days_back=days, min_magnitude=min_mag)
        return {"earthquakes": quakes, "count": len(quakes)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/fires")
async def get_fires():
    """Get active wildland fire perimeters in California."""
    try:
        fires = await fetch_fire_perimeters()
        return {"fires": fires, "count": len(fires)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/fire-weather")
async def get_fire_weather():
    """Get active fire weather alerts for California."""
    try:
        alerts = await fetch_fire_weather_alerts()
        return {"alerts": alerts, "count": len(alerts)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/risk-summary")
async def get_risk_summary():
    """Get a combined risk summary for California."""
    errors = []
    quakes = []
    fires = []
    alerts = []

    try:
        quakes = await fetch_earthquakes(days_back=30, min_magnitude=1.0)
    except Exception as e:
        errors.append(f"earthquakes: {e}")

    try:
        fires = await fetch_fire_perimeters()
    except Exception as e:
        errors.append(f"fires: {e}")

    try:
        alerts = await fetch_fire_weather_alerts()
    except Exception as e:
        errors.append(f"fire_weather: {e}")

    # Compute summary stats
    total_fire_acres = sum(f.get("acres", 0) or 0 for f in fires)
    max_magnitude = max((q["magnitude"] for q in quakes), default=0)
    significant_quakes = [q for q in quakes if q["magnitude"] >= 3.0]

    return {
        "earthquake_count_30d": len(quakes),
        "significant_quakes_30d": len(significant_quakes),
        "max_magnitude_30d": max_magnitude,
        "active_fires": len(fires),
        "total_fire_acres": round(total_fire_acres, 1),
        "fire_weather_alerts": len(alerts),
        "errors": errors,
    }


if __name__ == "__main__":
    run_app(app, default_port=8016)
