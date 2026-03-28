"""OpenSky Network API client with SQLite caching.

Endpoints used:
- /flights/aircraft: historical flights for an aircraft (last 30 days)
- /tracks/all: waypoint track for a specific flight
- /states/all: real-time aircraft in a bounding box

Rate limits (anonymous): ~400 credits/day. Cache aggressively.
"""

import json
import sqlite3
import time
from pathlib import Path

import httpx

OPENSKY_BASE = "https://opensky-network.org/api"
CACHE_DB = Path(__file__).resolve().parents[1] / "data" / "opensky_cache.db"
CACHE_TTL_SECONDS = 24 * 60 * 60  # 24 hours


def _get_db() -> sqlite3.Connection:
    """Get or create the cache database."""
    CACHE_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_DB))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    """)
    conn.commit()
    return conn


def _cache_get(key: str) -> dict | list | None:
    """Retrieve a cached value if it exists and hasn't expired."""
    conn = _get_db()
    row = conn.execute(
        "SELECT value, created_at FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()

    if row is None:
        return None

    value_str, created_at = row
    if time.time() - created_at > CACHE_TTL_SECONDS:
        return None

    return json.loads(value_str)


def _cache_set(key: str, value: dict | list) -> None:
    """Store a value in the cache."""
    conn = _get_db()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), time.time()),
    )
    conn.commit()
    conn.close()


async def fetch_aircraft_flights(icao24: str, days_back: int = 7) -> list[dict]:
    """Get flights for an aircraft in the last N days.

    Returns list of dicts with keys:
        icao24, firstSeen, lastSeen, estDepartureAirport,
        estArrivalAirport, callsign, estDepartureAirportHorizDistance, etc.
    """
    icao24 = icao24.lower().strip()
    cache_key = f"flights:{icao24}:{days_back}"

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    end_ts = int(time.time())
    begin_ts = end_ts - (days_back * 86400)

    url = f"{OPENSKY_BASE}/flights/aircraft"
    params = {"icao24": icao24, "begin": begin_ts, "end": end_ts}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 404:
                # No flights found
                _cache_set(cache_key, [])
                return []
            if resp.status_code == 429:
                # Rate limited
                return []
            resp.raise_for_status()
            flights = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            return []

    if not isinstance(flights, list):
        flights = []

    _cache_set(cache_key, flights)
    return flights


async def fetch_flight_track(icao24: str, flight_time: int) -> list[dict]:
    """Get waypoint track for a specific flight.

    Args:
        icao24: ICAO 24-bit hex address
        flight_time: Unix timestamp of when the flight was active

    Returns list of waypoint dicts with keys:
        time, latitude, longitude, baro_altitude, true_track, on_ground
    """
    icao24 = icao24.lower().strip()
    cache_key = f"track:{icao24}:{flight_time}"

    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    url = f"{OPENSKY_BASE}/tracks/all"
    params = {"icao24": icao24, "time": flight_time}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code in (404, 429):
                _cache_set(cache_key, [])
                return []
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            return []

    path = data.get("path", [])
    waypoints = []
    for wp in path:
        if len(wp) >= 6:
            waypoints.append({
                "time": wp[0],
                "latitude": wp[1],
                "longitude": wp[2],
                "baro_altitude": wp[3],
                "true_track": wp[4],
                "on_ground": wp[5],
            })

    _cache_set(cache_key, waypoints)
    return waypoints


async def fetch_overhead_now(lat: float, lng: float, radius_deg: float = 0.15) -> list[dict]:
    """Get aircraft currently in a bounding box around a point.

    Uses the OpenSky /states/all endpoint with bounding box.
    Returns list of state vectors as dicts.
    """
    lamin = lat - radius_deg
    lamax = lat + radius_deg
    lomin = lng - radius_deg
    lomax = lng + radius_deg

    url = f"{OPENSKY_BASE}/states/all"
    params = {"lamin": lamin, "lamax": lamax, "lomin": lomin, "lomax": lomax}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(url, params=params)
            if resp.status_code == 429:
                return []
            resp.raise_for_status()
            data = resp.json()
        except (httpx.HTTPError, json.JSONDecodeError):
            return []

    states = data.get("states", []) or []
    aircraft = []
    for s in states:
        if len(s) < 17:
            continue
        aircraft.append({
            "icao24": s[0],
            "callsign": (s[1] or "").strip(),
            "origin_country": s[2],
            "time_position": s[3],
            "last_contact": s[4],
            "longitude": s[5],
            "latitude": s[6],
            "baro_altitude": s[7],
            "on_ground": s[8],
            "velocity": s[9],
            "true_track": s[10],
            "vertical_rate": s[11],
            "geo_altitude": s[13],
            "squawk": s[14],
        })

    return aircraft
