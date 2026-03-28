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
from services.history_client import (
    find_historical_overhead,
    find_aircraft_history,
    get_historical_stats,
    get_indexed_dates,
)
from services.opensky_client import fetch_aircraft_flights, fetch_flight_track
from services.history_analyzer import analyze_overhead_history

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


@app.get("/api/aircraft/{identifier}/history")
async def get_aircraft_history_endpoint(
    identifier: str,
    start: str = Query(None, description="Start date YYYY-MM-DD"),
    end: str = Query(None, description="End date YYYY-MM-DD"),
):
    """Get historical tracks for a specific aircraft."""
    try:
        tracks = find_aircraft_history(
            identifier, start_date=start, end_date=end
        )
        if not tracks:
            return JSONResponse(
                {"error": f"No historical data found for '{identifier}'"},
                status_code=404,
            )
        return {"identifier": identifier, "tracks": tracks, "count": len(tracks)}
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


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


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Flight Explorer",
        "app_description": "Discover what aircraft are flying overhead right now. Look up tail numbers, track flights, and explore real-time air traffic.",
        "vision_assessment": "Real-time tracking via ADSB.lol works perfectly -- the overhead detection is satisfying and immediate. The historical pipeline code is written but the archives are 3.4GB daily tarballs that haven't been downloaded yet, so historical features are non-functional. Seat count estimation is approximate (hardcoded lookup table covering 39 aircraft types). The fundamental limitation of ADS-B data is that you can't determine origin or destination -- you only see current position, heading, and altitude.",
        "killer_feature": "Flight deja vu -- show that the exact same physical airplane (not just the same flight number) that flew over your house today also flew over it 3 weeks ago, and trace its entire journey in between. Every city it visited, every airport it touched down at, rendered as an animated globe trail. Requires historical archive ingestion but the hex code (ICAO address) makes individual aircraft tracking possible.",
        "data_gaps": [
            "Cannot determine origin or destination from ADS-B position data alone",
            "Historical archive pipeline exists in code but 3.4GB/day tarballs haven't been downloaded",
            "Seat capacity is approximate -- hardcoded lookup table covers only 39 aircraft types",
            "No airline or flight number data (ADS-B gives callsign, which is often but not always the flight number)",
            "Coverage depends on community receiver density -- gaps over oceans and remote areas",
            "No noise level data for overhead flights",
        ],
        "related_apis": [
            {"name": "OpenSky Network", "url": "https://opensky-network.org/apidoc/", "description": "30-day historical track data for any aircraft. Academic project with free tier. Could fill the historical gap without downloading terabytes of archives.", "free": True},
            {"name": "FAA ATCSCC", "url": "https://www.fly.faa.gov/adv/adv_list.jsp", "description": "Air traffic control system command center advisories. Ground stops, delays, and reroutes in real-time.", "free": True},
            {"name": "DOT Aircraft Noise Maps", "url": "https://www.bts.gov/topics/airlines-and-airports/", "description": "Noise contour maps around airports. Could overlay noise exposure data on overhead flights.", "free": True},
            {"name": "ADS-B Exchange", "url": "https://www.adsbexchange.com/data/", "description": "Another community ADS-B network with historical data access. Paid API but unfiltered (includes military).", "free": False},
        ],
        "data_sources": [
            {
                "name": "ADSB.lol API",
                "url": "https://api.adsb.lol/v2/",
                "provider": "ADSB.lol (community ADS-B receiver network)",
                "coverage": "Global real-time aircraft positions",
                "granularity": "Per-aircraft, ~10 second position updates",
                "update_frequency": "Real-time (approximately every 10 seconds)",
                "authentication": "Free, no key required",
                "rate_limits": "No published limit, community-operated",
                "history": "Real-time only (no historical positions)",
                "key_fields": ["hex", "registration", "type", "callsign", "lat", "lng", "altitude", "speed", "heading"],
                "caveats": "Coverage depends on community receiver density. Aircraft without ADS-B transponders are not visible. ODbL license.",
            },
            {
                "name": "BTS T-100 Domestic Segment Data",
                "url": "https://transtats.bts.gov/",
                "provider": "Bureau of Transportation Statistics",
                "coverage": "US domestic air carriers",
                "granularity": "Quarterly aggregates by route",
                "update_frequency": "Quarterly",
                "authentication": "Free, no key required",
                "rate_limits": "None published",
                "history": "Historical data available (years of archives)",
                "key_fields": ["carrier", "origin", "destination", "passengers", "seats", "departures"],
                "caveats": "Data is quarterly, so it lags real-time by several months. Only covers US domestic carriers.",
            },
            {
                "name": "FAA Aircraft Registry",
                "url": "https://registry.faa.gov/",
                "provider": "Federal Aviation Administration",
                "coverage": "US-registered aircraft (N-numbers)",
                "granularity": "Per aircraft registration",
                "update_frequency": "Monthly",
                "authentication": "Free, no key required",
                "rate_limits": "None published",
                "history": "Current registry snapshot",
                "key_fields": ["n_number", "aircraft_type", "manufacturer", "model", "owner_name", "city", "state"],
                "caveats": "Only covers US-registered aircraft. Owner information may be a trust or LLC rather than the actual operator.",
            },
        ],
        "data_freshness": "Aircraft positions are fetched in real-time from ADSB.lol on each request. The app queries by geographic area and matches aircraft overhead based on position and heading. Seat capacity estimates use a hardcoded lookup table covering 39 aircraft type codes.",
    })


@app.get("/api/overhead/history")
async def get_overhead_history(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    start: str = Query(None, description="Start date YYYY-MM-DD"),
    end: str = Query(None, description="End date YYYY-MM-DD"),
    radius: float = Query(10, ge=1, le=100, description="Radius in NM"),
):
    """Get historical overhead passes for a location and date range."""
    try:
        passes = find_historical_overhead(
            lat, lng, radius_nm=radius, start_date=start, end_date=end
        )
        # Strip full positions from response to keep payload small
        for p in passes:
            p.pop("positions", None)

        return {
            "location": {"lat": lat, "lng": lng},
            "radius_nm": radius,
            "start": start,
            "end": end,
            "passes": passes,
            "count": len(passes),
        }
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/overhead/history/tracks")
async def get_overhead_history_tracks(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    start: str = Query(None, description="Start date YYYY-MM-DD"),
    end: str = Query(None, description="End date YYYY-MM-DD"),
    radius: float = Query(10, ge=1, le=100, description="Radius in NM"),
    limit: int = Query(50, ge=1, le=500, description="Max tracks to return"),
):
    """Get historical overhead passes with full position tracks (for map arcs)."""
    try:
        passes = find_historical_overhead(
            lat, lng, radius_nm=radius, start_date=start, end_date=end
        )
        # Limit and include positions for map rendering
        passes = passes[:limit]

        return {
            "location": {"lat": lat, "lng": lng},
            "radius_nm": radius,
            "tracks": passes,
            "count": len(passes),
        }
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/stats/history")
async def get_stats_history(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    days: int = Query(7, ge=1, le=90, description="Number of days"),
    radius: float = Query(10, ge=1, le=100, description="Radius in NM"),
):
    """Get aggregate historical statistics for overhead flights."""
    try:
        stats = get_historical_stats(lat, lng, radius_nm=radius, days=days)
        return stats
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/history/dates")
async def get_history_dates():
    """Get list of dates with indexed historical data."""
    try:
        dates = get_indexed_dates()
        return {"dates": dates}
    except FileNotFoundError as e:
        return JSONResponse({"error": str(e)}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/above-me")
async def above_me_page(request: Request):
    return templates.TemplateResponse(request, "above-me.html", {
        "mapbox_token": MAPBOX_TOKEN,
    })


@app.get("/api/above-me")
async def get_above_me(
    lat: float = Query(37.47, ge=-90, le=90),
    lng: float = Query(-122.23, ge=-180, le=180),
    days: int = Query(7, ge=1, le=30),
):
    """Get current overhead aircraft and their flight histories.

    Uses ADSB.lol for real-time overhead detection, then queries OpenSky
    for each aircraft's flight history over the last N days. Results are
    aggregated by destination airport, country, and US state.
    """
    import asyncio

    try:
        # Step 1: Get current overhead aircraft from ADSB.lol
        aircraft = await fetch_aircraft_in_area(lat, lng, radius_nm=10)
        overhead = find_overhead_aircraft(aircraft, lat, lng, radius_nm=10)

        if not overhead:
            return {
                "overhead": [],
                "analysis": {
                    "destinations": [],
                    "by_country": [],
                    "by_state": [],
                    "unique_aircraft": 0,
                    "total_flights": 0,
                    "total_seats": 0,
                    "aircraft_details": [],
                },
                "overhead_count": 0,
            }

        # Step 2: Fetch flight histories from OpenSky (concurrent, limited)
        # Cap at 20 aircraft to stay within rate limits
        aircraft_to_query = overhead[:20]

        async def fetch_history(ac):
            hex_code = ac.get("hex", "")
            if not hex_code:
                return hex_code, []
            flights = await fetch_aircraft_flights(hex_code, days_back=days)
            return hex_code, flights

        results = await asyncio.gather(
            *[fetch_history(ac) for ac in aircraft_to_query],
            return_exceptions=True,
        )

        flight_histories = {}
        for result in results:
            if isinstance(result, Exception):
                continue
            hex_code, flights = result
            if hex_code:
                flight_histories[hex_code] = flights

        # Step 3: Analyze
        analysis = analyze_overhead_history(overhead, flight_histories)

        return {
            "overhead": overhead,
            "analysis": analysis,
            "overhead_count": len(overhead),
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/above-me/tracks")
async def get_above_me_tracks(
    lat: float = Query(37.47, ge=-90, le=90),
    lng: float = Query(-122.23, ge=-180, le=180),
    days: int = Query(7, ge=1, le=30),
):
    """Get flight track waypoints for map visualization.

    Fetches tracks for up to 10 overhead aircraft to conserve API credits.
    """
    import asyncio

    try:
        # Get current overhead aircraft
        aircraft = await fetch_aircraft_in_area(lat, lng, radius_nm=10)
        overhead = find_overhead_aircraft(aircraft, lat, lng, radius_nm=10)

        if not overhead:
            return {"tracks": [], "count": 0}

        # Fetch flight histories first (to get flight times)
        aircraft_to_query = overhead[:10]
        tracks = []

        for ac in aircraft_to_query:
            hex_code = ac.get("hex", "")
            if not hex_code:
                continue

            flights = await fetch_aircraft_flights(hex_code, days_back=days)
            if not flights:
                continue

            # Fetch track for the most recent flight only (conserve API calls)
            recent = flights[0]
            flight_time = recent.get("firstSeen")
            if not flight_time:
                continue

            waypoints = await fetch_flight_track(hex_code, flight_time)
            if waypoints:
                tracks.append({
                    "hex": hex_code,
                    "callsign": (recent.get("callsign") or "").strip(),
                    "type_code": ac.get("type_code", ""),
                    "departure": recent.get("estDepartureAirport", ""),
                    "arrival": recent.get("estArrivalAirport", ""),
                    "waypoints": waypoints,
                })

        return {"tracks": tracks, "count": len(tracks)}

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    run_app(app, default_port=8002)
