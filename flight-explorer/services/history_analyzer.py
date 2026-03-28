"""Analyze overhead aircraft flight histories.

Takes current overhead aircraft (from ADSB.lol) and their OpenSky flight
histories, then aggregates by destination airport, country, and US state.
"""

from services.adsb_client import AIRCRAFT_SEATS
from services.airport_data import lookup_airport, get_country_name


def _estimate_seats(type_code: str) -> int:
    """Estimate seats from type code. Falls back to 0 for unknown types."""
    return AIRCRAFT_SEATS.get(type_code, 0)


def analyze_overhead_history(
    overhead_aircraft: list[dict],
    flight_histories: dict[str, list[dict]],
) -> dict:
    """Analyze where overhead aircraft have been.

    Args:
        overhead_aircraft: list of currently overhead aircraft dicts
            (from ADSB.lol, with hex, type_code, callsign, etc.)
        flight_histories: dict mapping icao24 hex -> list of OpenSky flight records
            Each flight has: estDepartureAirport, estArrivalAirport, firstSeen,
            lastSeen, callsign, icao24

    Returns dict with:
        - destinations: {airport_code: {count, total_seats, name, city, country, state, lat, lng}}
        - by_country: [{country, country_name, count, total_seats}]
        - by_state: [{state, count, total_seats}] (US states only)
        - unique_aircraft: int
        - total_flights: int
        - total_seats: int
        - aircraft_details: list of per-aircraft summaries
    """
    destinations = {}  # airport_code -> aggregated stats
    total_flights = 0
    total_seats = 0
    aircraft_details = []

    # Build a lookup from hex -> overhead aircraft info
    ac_by_hex = {}
    for ac in overhead_aircraft:
        h = ac.get("hex", "").lower().strip()
        if h:
            ac_by_hex[h] = ac

    unique_hexes = set()

    for hex_code, flights in flight_histories.items():
        if not flights:
            continue

        hex_lower = hex_code.lower().strip()
        ac_info = ac_by_hex.get(hex_lower, {})
        type_code = ac_info.get("type_code", "")
        seats = _estimate_seats(type_code)

        ac_flights = []

        for flight in flights:
            dep = flight.get("estDepartureAirport") or ""
            arr = flight.get("estArrivalAirport") or ""
            callsign = (flight.get("callsign") or "").strip()

            # Count both departure and arrival airports
            for airport_code in [dep, arr]:
                if not airport_code:
                    continue

                if airport_code not in destinations:
                    airport_info = lookup_airport(airport_code)
                    if airport_info:
                        destinations[airport_code] = {
                            "code": airport_code,
                            "name": airport_info["name"],
                            "city": airport_info["city"],
                            "country": airport_info["country"],
                            "state": airport_info.get("state"),
                            "lat": airport_info["lat"],
                            "lng": airport_info["lng"],
                            "count": 0,
                            "total_seats": 0,
                        }
                    else:
                        destinations[airport_code] = {
                            "code": airport_code,
                            "name": airport_code,
                            "city": None,
                            "country": None,
                            "state": None,
                            "lat": None,
                            "lng": None,
                            "count": 0,
                            "total_seats": 0,
                        }

                destinations[airport_code]["count"] += 1
                destinations[airport_code]["total_seats"] += seats

            total_flights += 1
            total_seats += seats
            unique_hexes.add(hex_lower)

            ac_flights.append({
                "callsign": callsign,
                "departure": dep,
                "arrival": arr,
                "first_seen": flight.get("firstSeen"),
                "last_seen": flight.get("lastSeen"),
            })

        if ac_flights:
            aircraft_details.append({
                "hex": hex_lower,
                "type_code": type_code,
                "callsign": ac_info.get("callsign", ""),
                "tail_number": ac_info.get("tail_number", ""),
                "description": ac_info.get("description", ""),
                "owner": ac_info.get("owner", ""),
                "seats": seats,
                "flights": ac_flights,
                "flight_count": len(ac_flights),
            })

    # Sort destinations by seat count descending
    dest_list = sorted(
        destinations.values(),
        key=lambda d: d["total_seats"],
        reverse=True,
    )

    # Aggregate by country
    country_agg = {}
    for d in dest_list:
        c = d.get("country")
        if not c:
            continue
        if c not in country_agg:
            country_agg[c] = {
                "country": c,
                "country_name": get_country_name(c),
                "count": 0,
                "total_seats": 0,
            }
        country_agg[c]["count"] += d["count"]
        country_agg[c]["total_seats"] += d["total_seats"]

    by_country = sorted(
        country_agg.values(),
        key=lambda x: x["total_seats"],
        reverse=True,
    )

    # Aggregate by US state
    state_agg = {}
    for d in dest_list:
        if d.get("country") != "US" or not d.get("state"):
            continue
        s = d["state"]
        if s not in state_agg:
            state_agg[s] = {"state": s, "count": 0, "total_seats": 0}
        state_agg[s]["count"] += d["count"]
        state_agg[s]["total_seats"] += d["total_seats"]

    by_state = sorted(
        state_agg.values(),
        key=lambda x: x["total_seats"],
        reverse=True,
    )

    return {
        "destinations": dest_list,
        "by_country": by_country,
        "by_state": by_state,
        "unique_aircraft": len(unique_hexes),
        "total_flights": total_flights,
        "total_seats": total_seats,
        "aircraft_details": aircraft_details,
    }
