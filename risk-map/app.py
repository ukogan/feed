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


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Risk Map",
        "app_description": "Combined earthquake and wildfire risk map for California. Overlays seismic activity, active fire perimeters, and fire weather alerts on a single map.",
        "vision_assessment": "The USGS earthquake API is excellent -- 2,000+ quakes beautifully visualize California's fault lines. The multi-layer risk overlay concept works well. NIFC fire perimeters may be empty depending on season (tested outside fire season). The main gap is that the app shows current hazards but not historical risk patterns or a combined risk score for a specific location. It answers 'what is happening now' but not 'how dangerous is this address over time.'",
        "killer_feature": "Address risk biography -- enter any California address and get a complete natural hazard history: every earthquake within 50 miles ranked by shaking intensity at that point (not just magnitude), every fire that burned within 10 miles, every flood zone it sits in, and a composite risk score compared to the state median. Show it as a timeline going back decades with a forward-looking probabilistic risk estimate.",
        "data_gaps": [
            "No historical fire data -- only shows current active fires",
            "No ShakeMaps (ground motion intensity at a point, not just epicenter magnitude)",
            "No combined risk score for a specific location",
            "NIFC perimeters may be empty outside fire season",
            "No flood zone data despite floods being a major California hazard",
            "No historical weather patterns to assess long-term risk trends",
        ],
        "related_apis": [
            {"name": "Cal Fire FRAP", "url": "https://frap.fire.ca.gov/", "description": "California fire perimeter history back to 1878. The historical fire data needed to assess long-term wildfire risk at any location.", "free": True},
            {"name": "USGS Quaternary Faults", "url": "https://earthquake.usgs.gov/hazards/qfaults/", "description": "Mapped fault lines with slip rates and recurrence intervals. Shows where future earthquakes are most likely.", "free": True},
            {"name": "FEMA Flood Zones (NFHL)", "url": "https://hazards.fema.gov/femaportal/wps/portal/NFHLWMS", "description": "National Flood Hazard Layer. Flood zone designations for every parcel in the US.", "free": True},
            {"name": "Open-Meteo Historical Weather", "url": "https://open-meteo.com/en/docs/historical-weather-api", "description": "Historical temperature, wind, and precipitation data. Useful for fire weather pattern analysis.", "free": True},
            {"name": "USGS ShakeMap", "url": "https://earthquake.usgs.gov/data/shakemap/", "description": "Ground motion and shaking intensity maps for significant earthquakes. Shows actual impact, not just magnitude.", "free": True},
        ],
        "data_sources": [
            {
                "name": "USGS Earthquake Hazards API",
                "url": "https://earthquake.usgs.gov/fdsnws/event/1/",
                "provider": "US Geological Survey",
                "coverage": "Global (app focuses on California)",
                "granularity": "Per earthquake event",
                "update_frequency": "Real-time (within minutes of detection)",
                "authentication": "Free, no key required",
                "rate_limits": "No published limits",
                "history": "Configurable date range and magnitude filter",
                "key_fields": ["magnitude", "depth", "lat", "lng", "place", "time", "type", "status"],
                "caveats": "Small earthquakes (< M2) may not be detected in areas with sparse seismometer coverage. Magnitude and location may be revised in the hours after an event.",
            },
            {
                "name": "NIFC Wildland Fire Perimeters",
                "url": "https://services3.arcgis.com/",
                "provider": "National Interagency Fire Center (via ArcGIS)",
                "coverage": "US nationwide active fire perimeters",
                "granularity": "Per fire perimeter (polygon geometry)",
                "update_frequency": "Every ~5 minutes during fire season",
                "authentication": "Free, no key required",
                "rate_limits": "Standard ArcGIS rate limits",
                "history": "Current active fires only",
                "key_fields": ["fire_name", "acres", "containment (%)", "discovery_date", "geometry"],
                "caveats": "Perimeter data may be empty outside fire season. Small fires may not have mapped perimeters. Acreage figures are estimates.",
            },
            {
                "name": "NWS Weather Alerts",
                "url": "https://api.weather.gov/alerts/",
                "provider": "National Weather Service",
                "coverage": "US nationwide",
                "granularity": "Per alert zone",
                "update_frequency": "Real-time (as alerts are issued/updated)",
                "authentication": "Free, no key required",
                "rate_limits": "No published limits (User-Agent header required)",
                "history": "Active alerts only",
                "key_fields": ["event", "severity", "headline", "description", "area", "onset", "expires"],
                "caveats": "App filters for fire weather watches and red flag warnings only. Alerts are transient -- they expire and are removed from the API.",
            },
        ],
        "data_freshness": "Earthquake data and fire weather alerts are fetched in real-time on each request. Fire perimeters are updated frequently during active fire season but may return empty results outside fire season. The risk summary endpoint aggregates 30-day earthquake activity, current active fires, and active fire weather alerts.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8016)
