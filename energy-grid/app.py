"""Energy Grid Viz: Real-time US energy generation with carbon intensity and smart timing."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.eia_client import fetch_fuel_mix, fetch_demand, MAJOR_ISOS
from services.carbon import (
    calculate_carbon_intensity,
    calculate_renewable_pct,
    get_fuel_display,
    FUEL_INFO,
)
from services.advisor import analyze_hourly_patterns, get_best_windows

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
EIA_API_KEY = os.getenv("EIA_API_KEY", "")

app, templates = create_app(
    title="Energy Grid",
    app_dir=APP_DIR,
    description="Real-time US energy generation mix with carbon intensity and smart timing advice",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "isos": MAJOR_ISOS,
    })


@app.get("/api/fuel-mix")
async def get_fuel_mix(
    iso: str = Query("CISO", description="ISO respondent code"),
    hours: int = Query(24, ge=1, le=168),
):
    """Get hourly fuel mix for an ISO."""
    if not EIA_API_KEY:
        return JSONResponse(
            {"error": "EIA_API_KEY not set in .env"},
            status_code=500,
        )

    records = await fetch_fuel_mix(EIA_API_KEY, respondent=iso, hours_back=hours)

    # Enrich with display info
    for r in records:
        fuel_code = r.get("fueltype", r.get("type-name", "OTH"))
        display = get_fuel_display(fuel_code)
        r["fuel_name"] = display["name"]
        r["fuel_color"] = display["color"]

    return records


@app.get("/api/summary")
async def get_summary():
    """Get current summary for all major ISOs."""
    if not EIA_API_KEY:
        return JSONResponse(
            {"error": "EIA_API_KEY not set in .env"},
            status_code=500,
        )

    summaries = []
    for code, name in MAJOR_ISOS.items():
        try:
            records = await fetch_fuel_mix(EIA_API_KEY, respondent=code, hours_back=1)
            # Aggregate latest hour by fuel type
            fuel_totals = {}
            for r in records:
                fuel = r.get("fueltype", r.get("type-name", "OTH"))
                value = r.get("value", 0)
                if value and float(value) > 0:
                    fuel_totals[fuel] = fuel_totals.get(fuel, 0) + float(value)

            total = sum(fuel_totals.values())
            carbon = calculate_carbon_intensity(fuel_totals)
            renewable = calculate_renewable_pct(fuel_totals)

            summaries.append({
                "respondent": code,
                "name": name,
                "total_mwh": round(total, 0),
                "carbon_intensity": round(carbon, 1),
                "renewable_pct": round(renewable, 1),
                "fuel_breakdown": {
                    k: {"mwh": round(v, 0), **get_fuel_display(k)}
                    for k, v in fuel_totals.items()
                },
            })
        except Exception as e:
            summaries.append({
                "respondent": code,
                "name": name,
                "error": str(e),
            })

    return summaries


@app.get("/api/advice")
async def get_advice(
    iso: str = Query("CISO"),
):
    """Get smart timing advice based on 7-day patterns."""
    if not EIA_API_KEY:
        return JSONResponse({"error": "EIA_API_KEY not set"}, status_code=500)

    records = await fetch_fuel_mix(EIA_API_KEY, respondent=iso, hours_back=168)
    patterns = analyze_hourly_patterns(records)
    windows = get_best_windows(patterns)

    return {
        "iso": iso,
        "hourly_patterns": patterns,
        "best_windows": windows,
    }


@app.get("/api/isos")
async def get_isos():
    """List available ISOs."""
    return MAJOR_ISOS


@app.get("/api/fuel-info")
async def get_fuel_info():
    """Get fuel type display information."""
    return FUEL_INFO


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Energy Grid",
        "app_description": "Real-time US energy generation mix with carbon intensity and smart timing advice. Covers all major ISOs including CAISO, ERCOT, PJM, MISO, NYISO, ISONE, and SPP.",
        "vision_assessment": "The EIA API works well and the stacked area chart renders beautifully with real CAISO data. The smart timing advice feature is functional and genuinely useful. The 4-6 hour data lag limits the 'real-time' claim but the historical pattern analysis compensates. The biggest gap is the absence of electricity price data, which would transform the timing advisor from 'when is greenest' to 'when is greenest AND cheapest.'",
        "killer_feature": "Personal carbon accountant -- connect your smart meter data (Green Button standard) and see exactly how dirty or clean YOUR specific electricity was, hour by hour, based on the actual generation mix at the time you consumed it. Show the dollar cost of switching your EV charging or laundry to the greenest window, with a year-over-year carbon savings tracker.",
        "data_gaps": [
            "No electricity price data -- the timing advisor can't factor in cost",
            "No plant-level generation data (only ISO-level aggregates)",
            "4-6 hour data lag means 'real-time' is misleading during rapid grid changes",
            "Carbon intensity is estimated from fuel mix, not measured directly",
            "No demand-side data (only generation/supply side)",
            "No forecast of upcoming generation mix for planning ahead",
        ],
        "related_apis": [
            {"name": "CAISO OASIS", "url": "http://oasis.caiso.com/", "description": "Real-time and day-ahead electricity prices for California ISO. Locational marginal pricing at node level.", "free": True},
            {"name": "WattTime", "url": "https://www.watttime.org/api-documentation/", "description": "Real-time and forecast marginal carbon intensity by grid region. Purpose-built for 'when to use electricity' decisions.", "free": False},
            {"name": "Green Button (OpenEI)", "url": "https://www.energy.gov/data/green-button", "description": "Standard format for utility smart meter data. Enables personal consumption analysis against grid mix.", "free": True},
            {"name": "Open-Meteo Weather", "url": "https://open-meteo.com/", "description": "Solar irradiance and wind speed forecasts to predict renewable generation capacity.", "free": True},
        ],
        "data_sources": [
            {
                "name": "EIA API v2",
                "url": "https://api.eia.gov/v2/",
                "provider": "US Energy Information Administration",
                "coverage": "US electricity grid, all major ISOs (CAISO, ERCOT, PJM, MISO, NYISO, ISONE, SPP)",
                "granularity": "Hourly generation by fuel type per ISO",
                "update_frequency": "Hourly (with 4-6 hour data lag)",
                "authentication": "Free API key required",
                "rate_limits": "9,000 requests/hour",
                "history": "Since July 2018",
                "key_fields": ["respondent (ISO)", "fueltype", "value (MWh)", "period", "type-name"],
                "caveats": "Data has a 4-6 hour lag from real-time. Some ISOs may report fuel categories differently. Generation values are in MWh.",
            },
        ],
        "data_freshness": "Data is fetched directly from the EIA API on each request. The 4-6 hour lag means 'current' data reflects conditions several hours ago. The smart timing advisor analyzes 7-day patterns to recommend optimal usage windows.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8001)
