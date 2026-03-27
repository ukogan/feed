"""Socrata Open Data API client for building permit data across cities.

Each city publishes permit data on their Socrata portal.
We use the SODA API (no auth needed for low-volume requests).
"""

import httpx
from datetime import datetime, timedelta


# City configurations: endpoint, date field, type field, address/neighborhood field
CITIES = {
    "nyc": {
        "name": "New York City",
        "url": "https://data.cityofnewyork.us/resource/ipu4-2vj7.json",
        "date_field": "pre__filing_date",
        "type_field": "job_type",
        "address_field": "borough",
        "value_field": "initial_cost",
        "type_map": {
            "NB": "New Construction",
            "A1": "Renovation",
            "A2": "Renovation",
            "A3": "Renovation",
            "DM": "Demolition",
            "SG": "Sign",
        },
    },
    "sf": {
        "name": "San Francisco",
        "url": "https://data.sfgov.org/resource/i98e-djp9.json",
        "date_field": "filed_date",
        "type_field": "permit_type_definition",
        "address_field": "neighborhoods_analysis_boundaries",
        "value_field": "estimated_cost",
        "type_map": {
            "additions alterations or repairs": "Renovation",
            "erect a new building": "New Construction",
            "demolitions": "Demolition",
            "sign - erect": "Sign",
            "wall or painted sign": "Sign",
            "otc alterations permit": "Renovation",
        },
    },
    "chicago": {
        "name": "Chicago",
        "url": "https://data.cityofchicago.org/resource/ydr8-5enu.json",
        "date_field": "issue_date",
        "type_field": "permit_type",
        "address_field": "community_area",
        "value_field": "reported_cost",
        "type_map": {
            "PERMIT - NEW CONSTRUCTION": "New Construction",
            "PERMIT - RENOVATION/ALTERATION": "Renovation",
            "PERMIT - WRECKING/DEMOLITION": "Demolition",
            "PERMIT - EASY PERMIT PROCESS": "Renovation",
            "PERMIT - ELECTRICAL": "Renovation",
        },
    },
    "la": {
        "name": "Los Angeles",
        "url": "https://data.lacity.org/resource/yv23-pmwf.json",
        "date_field": "issue_date",
        "type_field": "permit_type",
        "address_field": "community_plan_area",
        "value_field": "valuation",
        "type_map": {
            "Bldg-New": "New Construction",
            "Bldg-Alter/Repair": "Renovation",
            "Bldg-Demolition": "Demolition",
            "Bldg-Addition": "Renovation",
            "Grading": "Other",
        },
    },
    "seattle": {
        "name": "Seattle",
        "url": "https://data.seattle.gov/resource/76t5-zqzr.json",
        "date_field": "issue_date",
        "type_field": "permitclass",
        "address_field": "neighborhood",
        "value_field": "estprojectcost",
        "type_map": {
            "Residential": "Renovation",
            "Commercial": "New Construction",
            "Institutional": "New Construction",
            "Multifamily": "New Construction",
            "Industrial": "New Construction",
        },
    },
}


def _normalize_type(raw_type: str | None, type_map: dict) -> str:
    """Normalize permit type string to a standard category."""
    if not raw_type:
        return "Other"
    raw_lower = raw_type.strip().lower()
    for key, value in type_map.items():
        if key.lower() in raw_lower or raw_lower in key.lower():
            return value
    return "Other"


async def fetch_permits(
    city_key: str,
    limit: int = 1000,
    months_back: int = 12,
) -> list[dict]:
    """Fetch recent permits from a city's Socrata endpoint.

    Returns normalized records with: date, type, neighborhood, value, raw_type.
    """
    if city_key not in CITIES:
        raise ValueError(f"Unknown city: {city_key}. Valid: {list(CITIES.keys())}")

    config = CITIES[city_key]
    date_field = config["date_field"]
    cutoff = (datetime.utcnow() - timedelta(days=months_back * 30)).strftime("%Y-%m-%dT00:00:00")

    params = {
        "$limit": limit,
        "$order": f"{date_field} DESC",
        "$where": f"{date_field} > '{cutoff}'",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(config["url"], params=params)
        response.raise_for_status()
        raw_records = response.json()

    records = []
    for r in raw_records:
        date_val = r.get(date_field)
        if not date_val:
            continue

        raw_type = r.get(config["type_field"], "")
        permit_type = _normalize_type(raw_type, config["type_map"])
        neighborhood = r.get(config["address_field"], "Unknown") or "Unknown"

        value_raw = r.get(config["value_field"])
        try:
            value = float(value_raw) if value_raw else 0
        except (ValueError, TypeError):
            value = 0

        records.append({
            "date": date_val[:10] if date_val else None,
            "type": permit_type,
            "raw_type": raw_type,
            "neighborhood": str(neighborhood),
            "value": value,
            "city": city_key,
        })

    return records


async def fetch_all_cities(limit_per_city: int = 1000, months_back: int = 12) -> dict:
    """Fetch permits from all cities. Returns {city_key: [records]}."""
    results = {}
    for city_key in CITIES:
        try:
            records = await fetch_permits(city_key, limit=limit_per_city, months_back=months_back)
            results[city_key] = records
        except Exception as e:
            results[city_key] = {"error": str(e)}
    return results
