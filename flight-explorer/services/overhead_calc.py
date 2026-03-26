"""Calculate which flights pass overhead a given location.

Core algorithm: given a point (lat, lng) and a set of aircraft positions,
find all aircraft within a specified radius and altitude range.
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from _shared.geo import haversine_distance_nm

from services.adsb_client import parse_adsb_aircraft, get_seat_count


def find_overhead_aircraft(
    aircraft_list: list[dict],
    center_lat: float,
    center_lng: float,
    radius_nm: float = 5.0,
    min_alt_ft: float = 0,
    max_alt_ft: float = 45000,
) -> list[dict]:
    """Filter aircraft to those passing overhead a point.

    Args:
        aircraft_list: Raw ADSB.lol aircraft records
        center_lat: Observer latitude
        center_lng: Observer longitude
        radius_nm: Radius in nautical miles (default 5 NM ~ 9.3 km)
        min_alt_ft: Minimum altitude filter
        max_alt_ft: Maximum altitude filter

    Returns:
        List of overhead passes with distance, altitude, and aircraft info.
    """
    overhead = []

    for ac_raw in aircraft_list:
        ac = parse_adsb_aircraft(ac_raw)

        lat = ac.get("lat")
        lng = ac.get("lng")
        if lat is None or lng is None:
            continue

        # Get altitude
        alt = ac.get("alt_baro")
        if alt == "ground" or alt is None:
            alt = ac.get("alt_geom", 0)
        try:
            alt = float(alt)
        except (TypeError, ValueError):
            continue

        if alt < min_alt_ft or alt > max_alt_ft:
            continue

        # Calculate distance
        distance = haversine_distance_nm(center_lat, center_lng, lat, lng)
        if distance > radius_nm:
            continue

        seat_count = get_seat_count(ac.get("type_code", ""))

        overhead.append({
            "hex": ac["hex"],
            "tail_number": ac["tail_number"],
            "type_code": ac["type_code"],
            "callsign": ac["callsign"],
            "description": ac["description"],
            "owner": ac["owner"],
            "lat": lat,
            "lng": lng,
            "altitude_ft": alt,
            "distance_nm": round(distance, 2),
            "heading": ac.get("heading", 0),
            "speed_kts": ac.get("ground_speed", 0),
            "vertical_rate": ac.get("vertical_rate", 0),
            "seat_count": seat_count,
            "on_ground": ac["on_ground"],
        })

    # Sort by distance (closest first)
    overhead.sort(key=lambda x: x["distance_nm"])
    return overhead


def summarize_overhead(passes: list[dict]) -> dict:
    """Generate summary statistics for overhead passes."""
    if not passes:
        return {
            "total_flights": 0,
            "total_seats": 0,
            "unique_aircraft": 0,
            "unique_types": [],
            "altitude_range": {"min": 0, "max": 0},
        }

    altitudes = [p["altitude_ft"] for p in passes if p["altitude_ft"] > 0]
    types = {}
    hexes = set()
    total_seats = 0

    for p in passes:
        hexes.add(p["hex"])
        tc = p["type_code"]
        if tc:
            types[tc] = types.get(tc, 0) + 1
        total_seats += p["seat_count"]

    type_list = sorted(types.items(), key=lambda x: -x[1])

    return {
        "total_flights": len(passes),
        "total_seats": total_seats,
        "unique_aircraft": len(hexes),
        "unique_types": [{"type": t, "count": c} for t, c in type_list[:10]],
        "altitude_range": {
            "min": min(altitudes) if altitudes else 0,
            "max": max(altitudes) if altitudes else 0,
        },
    }
