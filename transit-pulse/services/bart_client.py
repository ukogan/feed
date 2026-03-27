"""BART API client for station and real-time departure data."""

from datetime import datetime

import httpx

BART_API_KEY = "MW9S-E7SL-26DU-VV8V"  # Public demo key
BART_API_BASE = "https://api.bart.gov/api"

# BART line colors and names
BART_LINES = {
    "ROUTE 1": {"name": "Yellow", "color": "#ffff33", "abbr": "YL"},
    "ROUTE 2": {"name": "Yellow", "color": "#ffff33", "abbr": "YL"},
    "ROUTE 3": {"name": "Orange", "color": "#ff9933", "abbr": "OR"},
    "ROUTE 4": {"name": "Orange", "color": "#ff9933", "abbr": "OR"},
    "ROUTE 5": {"name": "Green", "color": "#339933", "abbr": "GR"},
    "ROUTE 6": {"name": "Green", "color": "#339933", "abbr": "GR"},
    "ROUTE 7": {"name": "Red", "color": "#ff0000", "abbr": "RD"},
    "ROUTE 8": {"name": "Red", "color": "#ff0000", "abbr": "RD"},
    "ROUTE 11": {"name": "Blue", "color": "#0099cc", "abbr": "BL"},
    "ROUTE 12": {"name": "Blue", "color": "#0099cc", "abbr": "BL"},
    "ROUTE 19": {"name": "Beige", "color": "#d5cfa3", "abbr": "BG"},
    "ROUTE 20": {"name": "Beige", "color": "#d5cfa3", "abbr": "BG"},
}

# Line destination-based mapping (more reliable)
LINE_BY_DEST = {
    "Antioch": {"name": "Yellow", "color": "#ffff33"},
    "SFO/Millbrae": {"name": "Yellow", "color": "#ffff33"},
    "SF Airport": {"name": "Yellow", "color": "#ffff33"},
    "Millbrae": {"name": "Yellow", "color": "#ffff33"},
    "Richmond": {"name": "Orange", "color": "#ff9933"},
    "Berryessa": {"name": "Orange", "color": "#ff9933"},
    "Berryessa/North San Jose": {"name": "Orange", "color": "#ff9933"},
    "Daly City": {"name": "Green", "color": "#339933"},
    "Dublin/Pleasanton": {"name": "Blue", "color": "#0099cc"},
}


async def fetch_stations() -> list[dict]:
    """Fetch all BART stations with coordinates.

    Returns list of dicts with: abbr, name, lat, lng, address, city, county, zipcode.
    """
    params = {
        "cmd": "stns",
        "key": BART_API_KEY,
        "json": "y",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BART_API_BASE}/stn.aspx", params=params)
        resp.raise_for_status()
        data = resp.json()

    stations_data = data.get("root", {}).get("stations", {}).get("station", [])
    results = []
    for stn in stations_data:
        results.append({
            "abbr": stn.get("abbr", ""),
            "name": stn.get("name", ""),
            "lat": float(stn.get("gtfs_latitude", 0)),
            "lng": float(stn.get("gtfs_longitude", 0)),
            "address": stn.get("address", ""),
            "city": stn.get("city", ""),
            "county": stn.get("county", ""),
            "zipcode": stn.get("zipcode", ""),
        })

    return results


async def fetch_departures(station_abbr: str) -> list[dict]:
    """Fetch estimated departures for a station.

    Returns list of dicts with: destination, abbreviation, minutes, platform,
    direction, length, color, delay, hexcolor, line_name.
    """
    params = {
        "cmd": "etd",
        "orig": station_abbr,
        "key": BART_API_KEY,
        "json": "y",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{BART_API_BASE}/etd.aspx", params=params)
        resp.raise_for_status()
        data = resp.json()

    station_data = data.get("root", {}).get("station", [])
    if not station_data:
        return []

    etd_list = station_data[0].get("etd", [])
    results = []

    for etd in etd_list:
        destination = etd.get("destination", "")
        dest_abbr = etd.get("abbreviation", "")

        for est in etd.get("estimate", []):
            minutes_str = est.get("minutes", "0")
            minutes = 0 if minutes_str == "Leaving" else int(minutes_str) if minutes_str.isdigit() else 0

            delay_str = est.get("delay", "0")
            delay = int(delay_str) if delay_str and delay_str.isdigit() else 0

            hexcolor = est.get("hexcolor", "#ffffff")
            line_info = LINE_BY_DEST.get(destination, {"name": "Unknown", "color": hexcolor})

            results.append({
                "destination": destination,
                "abbreviation": dest_abbr,
                "minutes": minutes,
                "platform": est.get("platform", ""),
                "direction": est.get("direction", ""),
                "length": int(est.get("length", 0)),
                "color": est.get("color", ""),
                "delay": delay,
                "hexcolor": hexcolor,
                "line_name": line_info["name"],
                "line_color": line_info["color"],
            })

    return results


async def fetch_all_departures() -> dict[str, list[dict]]:
    """Fetch departures for all stations. Returns {station_abbr: [departures]}."""
    stations = await fetch_stations()

    results = {}
    async with httpx.AsyncClient(timeout=20) as client:
        for station in stations:
            abbr = station["abbr"]
            try:
                params = {
                    "cmd": "etd",
                    "orig": abbr,
                    "key": BART_API_KEY,
                    "json": "y",
                }
                resp = await client.get(f"{BART_API_BASE}/etd.aspx", params=params)
                resp.raise_for_status()
                data = resp.json()

                station_data = data.get("root", {}).get("station", [])
                if station_data:
                    departures = []
                    for etd in station_data[0].get("etd", []):
                        destination = etd.get("destination", "")
                        for est in etd.get("estimate", []):
                            minutes_str = est.get("minutes", "0")
                            minutes = 0 if minutes_str == "Leaving" else int(minutes_str) if minutes_str.isdigit() else 0
                            delay_str = est.get("delay", "0")
                            delay = int(delay_str) if delay_str and delay_str.isdigit() else 0
                            hexcolor = est.get("hexcolor", "#ffffff")
                            line_info = LINE_BY_DEST.get(destination, {"name": "Unknown", "color": hexcolor})

                            departures.append({
                                "destination": destination,
                                "minutes": minutes,
                                "delay": delay,
                                "hexcolor": hexcolor,
                                "line_name": line_info["name"],
                                "line_color": line_info["color"],
                                "length": int(est.get("length", 0)),
                            })
                    results[abbr] = departures
            except Exception:
                results[abbr] = []

    return results


def compute_reliability(departures_by_station: dict[str, list[dict]]) -> dict:
    """Compute reliability scores from departure data.

    Returns per-line and per-station reliability metrics.
    """
    # Per-line aggregation
    line_delays = {}
    station_scores = {}

    for station_abbr, departures in departures_by_station.items():
        total = len(departures)
        delayed = sum(1 for d in departures if d.get("delay", 0) > 0)
        total_delay_seconds = sum(d.get("delay", 0) for d in departures)

        on_time_pct = ((total - delayed) / total * 100) if total > 0 else 100

        station_scores[station_abbr] = {
            "total_departures": total,
            "delayed": delayed,
            "on_time_pct": round(on_time_pct, 1),
            "avg_delay_seconds": round(total_delay_seconds / total, 1) if total > 0 else 0,
        }

        for dep in departures:
            line = dep.get("line_name", "Unknown")
            if line not in line_delays:
                line_delays[line] = {
                    "total": 0,
                    "delayed": 0,
                    "total_delay": 0,
                    "color": dep.get("line_color", "#ffffff"),
                }
            line_delays[line]["total"] += 1
            if dep.get("delay", 0) > 0:
                line_delays[line]["delayed"] += 1
            line_delays[line]["total_delay"] += dep.get("delay", 0)

    # Compute line scores
    line_scores = {}
    for line, stats in line_delays.items():
        total = stats["total"]
        on_time_pct = ((total - stats["delayed"]) / total * 100) if total > 0 else 100
        line_scores[line] = {
            "on_time_pct": round(on_time_pct, 1),
            "avg_delay_seconds": round(stats["total_delay"] / total, 1) if total > 0 else 0,
            "total_departures": total,
            "delayed": stats["delayed"],
            "color": stats["color"],
        }

    return {
        "lines": line_scores,
        "stations": station_scores,
        "timestamp": datetime.utcnow().isoformat(),
    }
