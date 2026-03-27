"""CourtListener API client for federal litigation data.

Uses the free CourtListener REST API (no key required for basic access).
Docs: https://www.courtlistener.com/help/api/rest/
"""

from collections import defaultdict

import httpx


BASE_URL = "https://www.courtlistener.com/api/rest/v4"


async def search_opinions(
    query: str = "antitrust",
    page: int = 1,
) -> dict:
    """Search court opinions via CourtListener.

    Returns dict with 'count' and 'results' list of normalized records.
    """
    params = {
        "q": query,
        "type": "o",
        "format": "json",
        "page": page,
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/search/", params=params)
        resp.raise_for_status()
        data = resp.json()

    count = data.get("count", 0)
    raw_results = data.get("results", [])

    results = []
    for r in raw_results:
        results.append({
            "id": r.get("id", ""),
            "case_name": r.get("caseName", r.get("case_name", "")),
            "court": r.get("court", ""),
            "court_citation": r.get("court_citation_string", ""),
            "date_filed": r.get("dateFiled", r.get("date_filed", "")),
            "snippet": _clean_snippet(r.get("snippet", "")),
            "absolute_url": r.get("absolute_url", ""),
            "status": r.get("status", ""),
            "citation_count": r.get("citeCount", r.get("citation_count", 0)),
        })

    return {"count": count, "results": results}


async def fetch_courts() -> list[dict]:
    """Fetch list of federal courts from CourtListener."""
    params = {"format": "json"}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{BASE_URL}/courts/", params=params)
        resp.raise_for_status()
        data = resp.json()

    raw_courts = data.get("results", [])
    courts = []
    for c in raw_courts:
        courts.append({
            "id": c.get("id", ""),
            "short_name": c.get("short_name", ""),
            "full_name": c.get("full_name", ""),
            "jurisdiction": c.get("jurisdiction", ""),
            "url": c.get("resource_uri", ""),
        })

    return courts


def analyze_results(results: list[dict]) -> dict:
    """Compute analytics from search results.

    Returns: courts breakdown, date range, total count, top courts.
    """
    if not results:
        return {
            "by_court": [],
            "total": 0,
            "date_range": {"earliest": None, "latest": None},
            "top_courts": [],
        }

    # Count by court
    court_counts = defaultdict(int)
    dates = []

    for r in results:
        court = r.get("court") or r.get("court_citation") or "Unknown"
        court_counts[court] += 1

        date = r.get("date_filed", "")
        if date:
            dates.append(date)

    by_court = sorted(
        [{"court": k, "count": v} for k, v in court_counts.items()],
        key=lambda x: -x["count"],
    )

    dates.sort()
    date_range = {
        "earliest": dates[0] if dates else None,
        "latest": dates[-1] if dates else None,
    }

    return {
        "by_court": by_court,
        "total": len(results),
        "date_range": date_range,
        "top_courts": by_court[:5],
    }


def _clean_snippet(text: str) -> str:
    """Clean HTML tags from snippets but keep structure."""
    import re
    # Keep <mark> tags for highlighting, strip others
    text = re.sub(r'<(?!/?mark\b)[^>]+>', '', text)
    return text.strip()
