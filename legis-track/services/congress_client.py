"""Congress data client using Congress.gov and FEC APIs.

Congress.gov API: bills, members, votes (free key)
FEC API: campaign contributions (free key)
"""

import os
from datetime import datetime

import httpx


CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY", "")
FEC_API_KEY = os.getenv("FEC_API_KEY", "")


def is_live() -> bool:
    """Check if live API keys are configured."""
    return bool(CONGRESS_API_KEY)


async def fetch_members(query: str = "") -> list[dict]:
    """Fetch congress members from Congress.gov API."""
    if not CONGRESS_API_KEY:
        return []

    url = "https://api.congress.gov/v3/member"
    params = {"api_key": CONGRESS_API_KEY, "limit": 50, "format": "json"}
    if query:
        url = f"https://api.congress.gov/v3/member"
        params["query"] = query

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    members = []
    for m in data.get("members", []):
        terms = m.get("terms", {}).get("item", [])
        latest_term = terms[-1] if terms else {}
        members.append({
            "id": m.get("bioguideId", ""),
            "name": m.get("name", ""),
            "party": m.get("partyName", "")[:1],
            "state": m.get("state", ""),
            "chamber": latest_term.get("chamber", ""),
            "image_url": m.get("depiction", {}).get("imageUrl", ""),
        })
    return members


async def fetch_bills(limit: int = 20) -> list[dict]:
    """Fetch recent bills from Congress.gov API."""
    if not CONGRESS_API_KEY:
        return []

    url = "https://api.congress.gov/v3/bill"
    params = {
        "api_key": CONGRESS_API_KEY,
        "limit": limit,
        "format": "json",
        "sort": "updateDate+desc",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    bills = []
    for b in data.get("bills", []):
        bills.append({
            "id": f"{b.get('type', '')}{b.get('number', '')}",
            "title": b.get("title", ""),
            "introduced": b.get("introducedDate", ""),
            "congress": b.get("congress", ""),
            "type": b.get("type", ""),
            "number": b.get("number", ""),
            "status": b.get("latestAction", {}).get("text", ""),
            "status_date": b.get("latestAction", {}).get("actionDate", ""),
            "url": b.get("url", ""),
        })
    return bills


async def fetch_member_bills(member_id: str, limit: int = 20) -> list[dict]:
    """Fetch bills sponsored by a specific member."""
    if not CONGRESS_API_KEY:
        return []

    url = f"https://api.congress.gov/v3/member/{member_id}/sponsored-legislation"
    params = {
        "api_key": CONGRESS_API_KEY,
        "limit": limit,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    bills = []
    for b in data.get("sponsoredLegislation", []):
        bills.append({
            "id": f"{b.get('type', '')}{b.get('number', '')}",
            "title": b.get("title", ""),
            "introduced": b.get("introducedDate", ""),
            "congress": b.get("congress", ""),
            "status": b.get("latestAction", {}).get("text", ""),
            "status_date": b.get("latestAction", {}).get("actionDate", ""),
        })
    return bills


async def fetch_contributions(candidate_name: str = "", limit: int = 20) -> list[dict]:
    """Fetch campaign contributions from FEC API."""
    if not FEC_API_KEY:
        return []

    # First find the candidate
    url = "https://api.open.fec.gov/v1/candidates/search/"
    params = {
        "api_key": FEC_API_KEY,
        "q": candidate_name,
        "per_page": 5,
        "sort": "-election_year",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    candidates = data.get("results", [])
    if not candidates:
        return []

    candidate_id = candidates[0].get("candidate_id", "")

    # Fetch their committee's top contributors
    # First get their principal committee
    url = f"https://api.open.fec.gov/v1/candidate/{candidate_id}/totals/"
    params = {"api_key": FEC_API_KEY, "per_page": 1}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    totals = data.get("results", [{}])[0] if data.get("results") else {}

    return [{
        "candidate_id": candidate_id,
        "candidate_name": candidates[0].get("name", ""),
        "party": candidates[0].get("party", ""),
        "office": candidates[0].get("office_full", ""),
        "state": candidates[0].get("state", ""),
        "total_receipts": totals.get("receipts", 0),
        "total_disbursements": totals.get("disbursements", 0),
        "individual_contributions": totals.get("individual_contributions", 0),
        "pac_contributions": totals.get("other_political_committee_contributions", 0),
        "election_year": totals.get("cycle", ""),
    }]
