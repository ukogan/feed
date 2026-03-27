"""Query SQLite database for historical overhead passes and aircraft history.

Provides spatial queries against indexed ADSB trace data to answer
questions like "what flew over me today/this week/this month".
"""

import json
import math
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DB_PATH = APP_DIR / "data" / "flights.db"


def _get_conn(db_path: Path | None = None) -> sqlite3.Connection:
    """Open a read-only connection to the flights database."""
    path = db_path or DB_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Flights database not found at {path}. "
            "Run scripts/download_adsb_history.py and scripts/index_history.py first."
        )
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _bounding_box(lat: float, lng: float, radius_nm: float) -> dict:
    """Compute a bounding box around a point."""
    dlat = radius_nm / 60.0
    dlng = radius_nm / (60.0 * math.cos(math.radians(lat)))
    return {
        "min_lat": lat - dlat,
        "max_lat": lat + dlat,
        "min_lng": lng - dlng,
        "max_lng": lng + dlng,
    }


def _haversine_nm(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Distance between two points in nautical miles."""
    R_NM = 3440.065
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return R_NM * 2 * math.asin(math.sqrt(a))


def find_historical_overhead(
    lat: float,
    lng: float,
    radius_nm: float = 10.0,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path | None = None,
) -> list[dict]:
    """Find aircraft tracks that passed within radius of a point.

    Uses bounding-box pre-filter on the track's min/max lat/lng,
    then checks individual positions for actual proximity.

    Args:
        lat: Observer latitude
        lng: Observer longitude
        radius_nm: Search radius in nautical miles
        start_date: Start date (YYYY-MM-DD), default 7 days ago
        end_date: End date (YYYY-MM-DD), default today
        db_path: Optional override for database path

    Returns:
        List of pass records with aircraft info and closest approach.
    """
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    bbox = _bounding_box(lat, lng, radius_nm)

    conn = _get_conn(db_path)
    try:
        # Bounding box pre-filter: track bbox must overlap search bbox
        rows = conn.execute(
            """SELECT hex, date, callsign, registration, type_code, description,
                      positions, point_count
               FROM tracks
               WHERE date >= ? AND date <= ?
                 AND max_lat >= ? AND min_lat <= ?
                 AND max_lng >= ? AND min_lng <= ?""",
            (
                start_date, end_date,
                bbox["min_lat"], bbox["max_lat"],
                bbox["min_lng"], bbox["max_lng"],
            ),
        ).fetchall()
    finally:
        conn.close()

    passes = []
    for row in rows:
        positions = json.loads(row["positions"])
        closest_dist = float("inf")
        closest_pos = None

        for pos in positions:
            dist = _haversine_nm(lat, lng, pos["lat"], pos["lng"])
            if dist < closest_dist:
                closest_dist = dist
                closest_pos = pos

        if closest_dist > radius_nm:
            continue

        passes.append({
            "hex": row["hex"],
            "date": row["date"],
            "callsign": row["callsign"],
            "registration": row["registration"],
            "type_code": row["type_code"],
            "description": row["description"],
            "closest_distance_nm": round(closest_dist, 2),
            "closest_altitude_ft": closest_pos.get("alt") if closest_pos else None,
            "closest_lat": closest_pos["lat"] if closest_pos else None,
            "closest_lng": closest_pos["lng"] if closest_pos else None,
            "point_count": row["point_count"],
            "positions": positions,
        })

    passes.sort(key=lambda x: (x["date"], x["closest_distance_nm"]))
    return passes


def find_aircraft_history(
    identifier: str,
    start_date: str | None = None,
    end_date: str | None = None,
    db_path: Path | None = None,
) -> list[dict]:
    """Find all tracks for a specific aircraft by hex, registration, or callsign.

    Args:
        identifier: ICAO hex, registration (tail number), or callsign
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        List of track records with positions.
    """
    if not start_date:
        start_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    if not end_date:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    identifier_upper = identifier.upper()
    identifier_lower = identifier.lower()

    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            """SELECT hex, date, callsign, registration, type_code, description,
                      positions, min_lat, max_lat, min_lng, max_lng, point_count
               FROM tracks
               WHERE date >= ? AND date <= ?
                 AND (hex = ? OR UPPER(registration) = ? OR UPPER(callsign) = ?)
               ORDER BY date""",
            (start_date, end_date, identifier_lower, identifier_upper, identifier_upper),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "hex": row["hex"],
            "date": row["date"],
            "callsign": row["callsign"],
            "registration": row["registration"],
            "type_code": row["type_code"],
            "description": row["description"],
            "positions": json.loads(row["positions"]),
            "bounds": {
                "min_lat": row["min_lat"],
                "max_lat": row["max_lat"],
                "min_lng": row["min_lng"],
                "max_lng": row["max_lng"],
            },
            "point_count": row["point_count"],
        }
        for row in rows
    ]


def get_historical_stats(
    lat: float,
    lng: float,
    radius_nm: float = 10.0,
    days: int = 7,
    db_path: Path | None = None,
) -> dict:
    """Aggregate statistics for overhead flights over a time period.

    Returns:
        Dict with total_flights, unique_aircraft, flights_per_day,
        top_types, repeat_visitors, total_seats.
    """
    end_date = datetime.utcnow().strftime("%Y-%m-%d")
    start_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

    passes = find_historical_overhead(
        lat, lng, radius_nm, start_date, end_date, db_path
    )

    if not passes:
        return {
            "total_flights": 0,
            "unique_aircraft": 0,
            "flights_per_day": [],
            "top_types": [],
            "repeat_visitors": [],
            "total_seats": 0,
            "days_covered": days,
            "start_date": start_date,
            "end_date": end_date,
        }

    # Import here to avoid circular dependency at module level
    import sys
    sys.path.insert(0, str(APP_DIR))
    from services.adsb_client import get_seat_count

    # Unique aircraft by hex
    hex_set = set()
    hex_dates = {}  # hex -> set of dates
    type_counts = {}
    daily_counts = {}
    total_seats = 0

    for p in passes:
        h = p["hex"]
        hex_set.add(h)

        if h not in hex_dates:
            hex_dates[h] = set()
        hex_dates[h].add(p["date"])

        tc = p.get("type_code")
        if tc:
            type_counts[tc] = type_counts.get(tc, 0) + 1
            total_seats += get_seat_count(tc)

        d = p["date"]
        daily_counts[d] = daily_counts.get(d, 0) + 1

    # Repeat visitors: aircraft seen on multiple days
    repeat_visitors = []
    for h, dates in hex_dates.items():
        if len(dates) > 1:
            # Find the most recent pass for this hex
            matching = [p for p in passes if p["hex"] == h]
            if matching:
                latest = max(matching, key=lambda x: x["date"])
                repeat_visitors.append({
                    "hex": h,
                    "registration": latest.get("registration"),
                    "type_code": latest.get("type_code"),
                    "callsign": latest.get("callsign"),
                    "days_seen": len(dates),
                })

    repeat_visitors.sort(key=lambda x: -x["days_seen"])

    # Flights per day
    flights_per_day = [
        {"date": d, "count": c}
        for d, c in sorted(daily_counts.items())
    ]

    # Top aircraft types
    top_types = [
        {"type_code": t, "count": c, "seats": get_seat_count(t)}
        for t, c in sorted(type_counts.items(), key=lambda x: -x[1])[:15]
    ]

    return {
        "total_flights": len(passes),
        "unique_aircraft": len(hex_set),
        "flights_per_day": flights_per_day,
        "top_types": top_types,
        "repeat_visitors": repeat_visitors[:20],
        "total_seats": total_seats,
        "days_covered": days,
        "start_date": start_date,
        "end_date": end_date,
    }


def get_indexed_dates(db_path: Path | None = None) -> list[dict]:
    """Return list of indexed dates with track counts."""
    conn = _get_conn(db_path)
    try:
        rows = conn.execute(
            "SELECT date, indexed_at, track_count FROM index_meta ORDER BY date"
        ).fetchall()
    finally:
        conn.close()

    return [
        {"date": r["date"], "indexed_at": r["indexed_at"], "track_count": r["track_count"]}
        for r in rows
    ]
