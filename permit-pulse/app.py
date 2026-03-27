"""Permit Pulse: Multi-city building permit aggregator as real estate leading indicator."""

import sys
from pathlib import Path

from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.socrata_client import CITIES, fetch_permits, fetch_all_cities
from services.analytics import permits_by_month, permits_by_type, hot_zones, compute_stats

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="Permit Pulse",
    app_dir=APP_DIR,
    description="Multi-city building permit aggregator as real estate leading indicator",
)


@app.get("/")
async def index(request: Request):
    cities = {k: v["name"] for k, v in CITIES.items()}
    return templates.TemplateResponse(request, "index.html", {
        "cities": cities,
    })


@app.get("/api/permits")
async def get_permits(
    city: str = Query("nyc", description="City key"),
    limit: int = Query(1000, ge=100, le=5000),
    months: int = Query(12, ge=1, le=24),
):
    """Fetch permits for a single city."""
    if city not in CITIES:
        return JSONResponse(
            {"error": f"Unknown city: {city}. Valid: {list(CITIES.keys())}"},
            status_code=400,
        )
    try:
        records = await fetch_permits(city, limit=limit, months_back=months)
        return {
            "city": city,
            "city_name": CITIES[city]["name"],
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/permits/all")
async def get_all_permits(
    limit: int = Query(500, ge=100, le=2000),
    months: int = Query(12, ge=1, le=24),
):
    """Fetch permits from all cities."""
    results = await fetch_all_cities(limit_per_city=limit, months_back=months)
    summary = {}
    for city_key, data in results.items():
        if isinstance(data, dict) and "error" in data:
            summary[city_key] = {
                "name": CITIES[city_key]["name"],
                "error": data["error"],
            }
        else:
            summary[city_key] = {
                "name": CITIES[city_key]["name"],
                "count": len(data),
                "stats": compute_stats(data),
                "by_type": permits_by_type(data),
                "monthly": permits_by_month(data),
                "hot_zones": hot_zones(data, top_n=5),
            }
    return summary


@app.get("/api/analytics")
async def get_analytics(
    city: str = Query("nyc"),
    months: int = Query(12, ge=1, le=24),
):
    """Get analytics for a single city."""
    if city not in CITIES:
        return JSONResponse(
            {"error": f"Unknown city: {city}"},
            status_code=400,
        )
    try:
        records = await fetch_permits(city, limit=2000, months_back=months)
        return {
            "city": city,
            "city_name": CITIES[city]["name"],
            "stats": compute_stats(records),
            "by_type": permits_by_type(records),
            "monthly": permits_by_month(records),
            "hot_zones": hot_zones(records, top_n=10),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/cities")
async def get_cities():
    """List available cities."""
    return {k: v["name"] for k, v in CITIES.items()}


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Permit Pulse",
        "app_description": "Multi-city building permit aggregator as a real estate leading indicator. Tracks permit activity across NYC, San Francisco, Chicago, LA, and Seattle.",
        "data_sources": [
            {
                "name": "Socrata Open Data (NYC, SF, Chicago, LA, Seattle)",
                "url": "https://dev.socrata.com/",
                "provider": "Individual city governments via Socrata Open Data platform",
                "coverage": "NYC, San Francisco, Chicago, Los Angeles, Seattle",
                "granularity": "Per permit record",
                "update_frequency": "Varies by city (typically daily to weekly)",
                "authentication": "Free, no key required (app token optional for higher limits)",
                "rate_limits": "Varies by city; throttled without app token",
                "history": "Years of historical data (varies by city)",
                "key_fields": ["permit_number", "permit_type", "status", "filing_date", "address", "description", "estimated_cost"],
                "caveats": "Each city uses different field names and date formats. Data completeness varies significantly between cities. Some cities may lag in updating their open data portals.",
            },
        ],
        "data_freshness": "Permit data is fetched directly from each city's Socrata API on each request. The app normalizes different city schemas into a common format. Analytics (monthly trends, hot zones, type breakdowns) are computed on the fly from the fetched records.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8013)
