"""EIA API v2 client for real-time grid data.

API docs: https://www.eia.gov/opendata/documentation.php
Base URL: https://api.eia.gov/v2/
"""

import os
from datetime import datetime, timedelta

import httpx


EIA_BASE = "https://api.eia.gov/v2"

# Major ISO/RTO respondent codes in EIA data
MAJOR_ISOS = {
    "CISO": "California ISO",
    "ERCO": "ERCOT (Texas)",
    "PJM": "PJM (Mid-Atlantic)",
    "MISO": "MISO (Midwest)",
    "NYIS": "NYISO (New York)",
    "ISNE": "ISO New England",
    "SWPP": "SPP (Southwest)",
}


async def fetch_fuel_mix(
    api_key: str,
    respondent: str = None,
    hours_back: int = 24,
) -> list[dict]:
    """Fetch hourly generation by fuel type from EIA.

    Uses electricity/rto/fuel-type-data endpoint.
    """
    end = datetime.utcnow()
    start = end - timedelta(hours=hours_back)

    params = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "start": start.strftime("%Y-%m-%dT%H"),
        "end": end.strftime("%Y-%m-%dT%H"),
        "length": 5000,
    }

    if respondent:
        params["facets[respondent][]"] = respondent

    url = f"{EIA_BASE}/electricity/rto/fuel-type-data/data/"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    records = data.get("response", {}).get("data", [])
    return records


async def fetch_demand(
    api_key: str,
    respondent: str = None,
    hours_back: int = 24,
) -> list[dict]:
    """Fetch hourly demand data."""
    end = datetime.utcnow()
    start = end - timedelta(hours=hours_back)

    params = {
        "api_key": api_key,
        "frequency": "hourly",
        "data[0]": "value",
        "sort[0][column]": "period",
        "sort[0][direction]": "asc",
        "start": start.strftime("%Y-%m-%dT%H"),
        "end": end.strftime("%Y-%m-%dT%H"),
        "length": 5000,
    }

    if respondent:
        params["facets[respondent][]"] = respondent

    url = f"{EIA_BASE}/electricity/rto/demand-data/data/"

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()

    return data.get("response", {}).get("data", [])
