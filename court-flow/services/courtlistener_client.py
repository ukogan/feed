"""CourtListener REST API client for federal litigation data.

API docs: https://www.courtlistener.com/api/rest/v4/
Free, no key needed for basic access (rate limited).
"""

import httpx
from datetime import datetime, timedelta
from urllib.parse import urlencode


CL_BASE = "https://www.courtlistener.com/api/rest/v4"
CL_SEARCH = "https://www.courtlistener.com/api/rest/v4/search"

# Major federal courts
FEDERAL_COURTS = {
    "scotus": "Supreme Court of the United States",
    "ca1": "First Circuit",
    "ca2": "Second Circuit",
    "ca3": "Third Circuit",
    "ca4": "Fourth Circuit",
    "ca5": "Fifth Circuit",
    "ca6": "Sixth Circuit",
    "ca7": "Seventh Circuit",
    "ca8": "Eighth Circuit",
    "ca9": "Ninth Circuit",
    "ca10": "Tenth Circuit",
    "ca11": "Eleventh Circuit",
    "cadc": "D.C. Circuit",
    "cafc": "Federal Circuit",
}


async def search_opinions(
    query: str,
    limit: int = 20,
    court: str = "",
) -> list[dict]:
    """Search opinions on CourtListener.

    Uses the search endpoint with type=o for opinions.
    """
    params = {
        "q": query,
        "type": "o",
        "order_by": "score desc",
        "format": "json",
    }
    if court:
        params["court"] = court

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(CL_SEARCH, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", [])[:limit]:
        results.append({
            "id": item.get("id"),
            "case_name": item.get("caseName", ""),
            "court": item.get("court", ""),
            "court_citation": item.get("court_citation_string", ""),
            "date_filed": item.get("dateFiled", ""),
            "snippet": item.get("snippet", ""),
            "absolute_url": item.get("absolute_url", ""),
            "citation": item.get("citation", []),
            "judge": item.get("judge", ""),
            "status": item.get("status", ""),
        })

    return results


async def fetch_opinions(
    limit: int = 20,
    days_back: int = 30,
) -> list[dict]:
    """Fetch recent opinions from CourtListener."""
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = f"{CL_BASE}/opinions/"
    params = {
        "date_created__gte": cutoff,
        "order_by": "-date_created",
        "format": "json",
        "page_size": min(limit, 20),
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "id": item.get("id"),
            "date_created": item.get("date_created", ""),
            "date_modified": item.get("date_modified", ""),
            "type": item.get("type", ""),
            "sha1": item.get("sha1", ""),
            "download_url": item.get("download_url", ""),
            "cluster": item.get("cluster", ""),
        })

    return results


async def fetch_dockets(
    limit: int = 20,
    days_back: int = 30,
    court: str = "",
) -> list[dict]:
    """Fetch recent docket entries from CourtListener."""
    cutoff = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")

    url = f"{CL_BASE}/dockets/"
    params = {
        "date_modified__gte": cutoff,
        "order_by": "-date_modified",
        "format": "json",
        "page_size": min(limit, 20),
    }
    if court:
        params["court__id"] = court

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "id": item.get("id"),
            "case_name": item.get("case_name", ""),
            "court": item.get("court", ""),
            "date_filed": item.get("date_filed", ""),
            "date_modified": item.get("date_modified", ""),
            "docket_number": item.get("docket_number", ""),
            "source": item.get("source", ""),
            "absolute_url": item.get("absolute_url", ""),
        })

    return results


async def fetch_courts() -> list[dict]:
    """Fetch list of courts from CourtListener."""
    url = f"{CL_BASE}/courts/"
    params = {
        "format": "json",
        "page_size": 100,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "id": item.get("id", ""),
            "full_name": item.get("full_name", ""),
            "short_name": item.get("short_name", ""),
            "jurisdiction": item.get("jurisdiction", ""),
            "url": item.get("url", ""),
        })

    return results
