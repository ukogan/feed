"""ADSB.lol API client for real-time and historical flight data.

API docs: https://api.adsb.lol/docs
Data license: ODbL (Open Database License)
"""

import httpx


ADSB_API_BASE = "https://api.adsb.lol/v2"


async def fetch_aircraft_in_area(
    lat: float, lng: float, radius_nm: float = 25
) -> list[dict]:
    """Fetch currently visible aircraft near a point.

    Returns list of aircraft state vectors.
    """
    url = f"{ADSB_API_BASE}/lat/{lat}/lon/{lng}/dist/{radius_nm}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    return data.get("ac", [])


async def fetch_aircraft_by_hex(hex_code: str) -> list[dict]:
    """Fetch current position of a specific aircraft by ICAO hex."""
    url = f"{ADSB_API_BASE}/hex/{hex_code}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    return data.get("ac", [])


async def fetch_aircraft_by_callsign(callsign: str) -> list[dict]:
    """Fetch aircraft by callsign (e.g., UAL123)."""
    url = f"{ADSB_API_BASE}/callsign/{callsign}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    return data.get("ac", [])


async def fetch_aircraft_by_registration(reg: str) -> list[dict]:
    """Fetch aircraft by registration/tail number (e.g., N12345)."""
    url = f"{ADSB_API_BASE}/reg/{reg}"

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(url)
        response.raise_for_status()
        data = response.json()

    return data.get("ac", [])


def parse_adsb_aircraft(ac: dict) -> dict:
    """Normalize an ADSB.lol aircraft record to a consistent format."""
    return {
        "hex": ac.get("hex", "").strip(),
        "tail_number": ac.get("r", "").strip(),  # registration
        "type_code": ac.get("t", ""),  # aircraft type ICAO code
        "callsign": ac.get("flight", "").strip(),
        "lat": ac.get("lat"),
        "lng": ac.get("lon"),
        "alt_baro": ac.get("alt_baro"),  # barometric altitude (ft or "ground")
        "alt_geom": ac.get("alt_geom"),  # geometric altitude (ft)
        "ground_speed": ac.get("gs"),  # knots
        "heading": ac.get("track"),  # true track over ground
        "vertical_rate": ac.get("baro_rate"),  # ft/min
        "squawk": ac.get("squawk"),
        "category": ac.get("category"),  # A1-A7 aircraft category
        "on_ground": ac.get("alt_baro") == "ground",
        "seen": ac.get("seen"),  # seconds since last message
        "seen_pos": ac.get("seen_pos"),  # seconds since last position
        "description": ac.get("desc", ""),  # aircraft description
        "owner": ac.get("ownOp", ""),  # owner/operator
    }


# Common aircraft type codes -> seat counts (approximate)
AIRCRAFT_SEATS = {
    "B738": 189, "B739": 220, "B737": 149, "B38M": 178, "B39M": 220,
    "B752": 200, "B753": 243, "B763": 269, "B764": 304,
    "B772": 314, "B773": 396, "B77W": 396, "B788": 242, "B789": 290, "B78X": 318,
    "A319": 156, "A320": 186, "A20N": 186, "A321": 220, "A21N": 220,
    "A332": 293, "A333": 293, "A339": 300, "A343": 295, "A346": 380,
    "A359": 325, "A35K": 366, "A380": 555,
    "E170": 76, "E175": 88, "E190": 114, "E195": 132,
    "CRJ2": 50, "CRJ7": 78, "CRJ9": 90, "CRJX": 104,
    "DH8D": 78, "AT76": 78, "AT75": 70,
}


def get_seat_count(type_code: str) -> int:
    """Estimate seat count from aircraft type code."""
    return AIRCRAFT_SEATS.get(type_code, 0)
