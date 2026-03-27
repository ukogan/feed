"""Flight Explorer: What flew over me? Tail number tracking and overhead analysis."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from _shared.geo import geocode_address
from services.adsb_client import (
    fetch_aircraft_in_area,
    fetch_aircraft_by_hex,
    fetch_aircraft_by_registration,
    fetch_aircraft_by_callsign,
    parse_adsb_aircraft,
    get_seat_count,
)
from services.overhead_calc import find_overhead_aircraft, summarize_overhead

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

app, templates = create_app(
    title="Flight Explorer",
    app_dir=APP_DIR,
    description="Discover what's flying over you right now",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "mapbox_token": MAPBOX_TOKEN,
    })


@app.get("/api/overhead")
async def get_overhead(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius: float = Query(10, ge=1, le=100, description="Radius in NM"),
):
    """Get aircraft currently overhead a location."""
    try:
        aircraft = await fetch_aircraft_in_area(lat, lng, radius_nm=radius)
        overhead = find_overhead_aircraft(aircraft, lat, lng, radius_nm=radius)
        summary = summarize_overhead(overhead)

        return {
            "location": {"lat": lat, "lng": lng},
            "radius_nm": radius,
            "aircraft": overhead,
            "summary": summary,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/geocode")
async def geocode(address: str = Query(...)):
    """Geocode an address to lat/lng."""
    if not MAPBOX_TOKEN:
        return JSONResponse(
            {"error": "MAPBOX_TOKEN not set in .env"},
            status_code=500,
        )
    try:
        lat, lng = await geocode_address(address, MAPBOX_TOKEN)
        return {"lat": lat, "lng": lng, "address": address}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=404)


@app.get("/api/aircraft/{identifier}")
async def get_aircraft(identifier: str):
    """Look up an aircraft by hex, registration, or callsign.

    Tries registration first, then hex, then callsign.
    """
    results = []

    # Try as registration (starts with N for US)
    if identifier.upper().startswith("N") or len(identifier) <= 7:
        try:
            results = await fetch_aircraft_by_registration(identifier.upper())
        except Exception:
            pass

    # Try as hex
    if not results and len(identifier) == 6:
        try:
            results = await fetch_aircraft_by_hex(identifier.lower())
        except Exception:
            pass

    # Try as callsign
    if not results:
        try:
            results = await fetch_aircraft_by_callsign(identifier.upper())
        except Exception:
            pass

    if not results:
        return JSONResponse(
            {"error": f"Aircraft '{identifier}' not found or not currently transmitting"},
            status_code=404,
        )

    parsed = [parse_adsb_aircraft(ac) for ac in results]
    for p in parsed:
        p["seat_count"] = get_seat_count(p.get("type_code", ""))

    return {"aircraft": parsed}


@app.get("/api/area")
async def get_area(
    lat: float = Query(...),
    lng: float = Query(...),
    radius: float = Query(50),
):
    """Get all aircraft in an area (for map display)."""
    try:
        aircraft = await fetch_aircraft_in_area(lat, lng, radius_nm=radius)
        parsed = [parse_adsb_aircraft(ac) for ac in aircraft]
        for p in parsed:
            p["seat_count"] = get_seat_count(p.get("type_code", ""))
        return {"aircraft": parsed, "count": len(parsed)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    run_app(app, default_port=8002)
