"""Congress data client with sample data fallback.

Uses Congress.gov API and FEC API when keys are available.
Falls back to clearly labeled SAMPLE_DATA when keys are not set.
Stock trade data always uses sample data (no free public API exists).
"""

import os
from datetime import datetime, timedelta

import httpx


CONGRESS_API_KEY = os.getenv("CONGRESS_API_KEY", "")
FEC_API_KEY = os.getenv("FEC_API_KEY", "")


# ── Sample Data (used when API keys are not configured) ──

SAMPLE_MEMBERS = [
    {
        "id": "SAMPLE_S001",
        "name": "SAMPLE_DATA: Jane Smith",
        "party": "D",
        "state": "CA",
        "chamber": "Senate",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_S002",
        "name": "SAMPLE_DATA: John Doe",
        "party": "R",
        "state": "TX",
        "chamber": "Senate",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_H001",
        "name": "SAMPLE_DATA: Maria Garcia",
        "party": "D",
        "state": "NY",
        "chamber": "House",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_H002",
        "name": "SAMPLE_DATA: Robert Chen",
        "party": "R",
        "state": "FL",
        "chamber": "House",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_S003",
        "name": "SAMPLE_DATA: Emily Johnson",
        "party": "D",
        "state": "WA",
        "chamber": "Senate",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_H003",
        "name": "SAMPLE_DATA: David Park",
        "party": "R",
        "state": "OH",
        "chamber": "House",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_S004",
        "name": "SAMPLE_DATA: Sarah Williams",
        "party": "D",
        "state": "IL",
        "chamber": "Senate",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_H004",
        "name": "SAMPLE_DATA: Michael Torres",
        "party": "R",
        "state": "AZ",
        "chamber": "House",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_S005",
        "name": "SAMPLE_DATA: Lisa Chang",
        "party": "D",
        "state": "CO",
        "chamber": "Senate",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_H005",
        "name": "SAMPLE_DATA: James Wilson",
        "party": "R",
        "state": "GA",
        "chamber": "House",
        "is_sample": True,
    },
]

SAMPLE_BILLS = [
    {
        "id": "SAMPLE_HR1234",
        "title": "SAMPLE_DATA: Clean Energy Investment Act",
        "introduced": "2025-09-15",
        "sponsor": "SAMPLE_S001",
        "sponsor_name": "SAMPLE_DATA: Jane Smith",
        "status": "Passed House",
        "subjects": ["Energy", "Environment"],
        "is_sample": True,
    },
    {
        "id": "SAMPLE_HR5678",
        "title": "SAMPLE_DATA: Technology Antitrust Reform Act",
        "introduced": "2025-10-01",
        "sponsor": "SAMPLE_H002",
        "sponsor_name": "SAMPLE_DATA: Robert Chen",
        "status": "In Committee",
        "subjects": ["Technology", "Antitrust"],
        "is_sample": True,
    },
    {
        "id": "SAMPLE_S4321",
        "title": "SAMPLE_DATA: Pharmaceutical Pricing Transparency Act",
        "introduced": "2025-11-10",
        "sponsor": "SAMPLE_S003",
        "sponsor_name": "SAMPLE_DATA: Emily Johnson",
        "status": "Introduced",
        "subjects": ["Healthcare", "Pharmaceuticals"],
        "is_sample": True,
    },
    {
        "id": "SAMPLE_HR9012",
        "title": "SAMPLE_DATA: Defense Modernization Authorization",
        "introduced": "2025-08-20",
        "sponsor": "SAMPLE_S002",
        "sponsor_name": "SAMPLE_DATA: John Doe",
        "status": "Passed Senate",
        "subjects": ["Defense", "Military"],
        "is_sample": True,
    },
    {
        "id": "SAMPLE_S5555",
        "title": "SAMPLE_DATA: Financial Markets Oversight Act",
        "introduced": "2025-12-01",
        "sponsor": "SAMPLE_S004",
        "sponsor_name": "SAMPLE_DATA: Sarah Williams",
        "status": "In Committee",
        "subjects": ["Finance", "Banking"],
        "is_sample": True,
    },
]

SAMPLE_TRADES = [
    {
        "id": "SAMPLE_T001",
        "member_id": "SAMPLE_S001",
        "member_name": "SAMPLE_DATA: Jane Smith",
        "date": "2025-09-10",
        "ticker": "ENPH",
        "company": "Enphase Energy",
        "type": "Purchase",
        "amount_range": "$15,001 - $50,000",
        "sector": "Energy",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T002",
        "member_id": "SAMPLE_S001",
        "member_name": "SAMPLE_DATA: Jane Smith",
        "date": "2025-09-12",
        "ticker": "FSLR",
        "company": "First Solar",
        "type": "Purchase",
        "amount_range": "$50,001 - $100,000",
        "sector": "Energy",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T003",
        "member_id": "SAMPLE_H002",
        "member_name": "SAMPLE_DATA: Robert Chen",
        "date": "2025-09-28",
        "ticker": "MSFT",
        "company": "Microsoft",
        "type": "Sale",
        "amount_range": "$100,001 - $250,000",
        "sector": "Technology",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T004",
        "member_id": "SAMPLE_H002",
        "member_name": "SAMPLE_DATA: Robert Chen",
        "date": "2025-10-02",
        "ticker": "GOOGL",
        "company": "Alphabet",
        "type": "Purchase",
        "amount_range": "$50,001 - $100,000",
        "sector": "Technology",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T005",
        "member_id": "SAMPLE_S003",
        "member_name": "SAMPLE_DATA: Emily Johnson",
        "date": "2025-11-05",
        "ticker": "PFE",
        "company": "Pfizer",
        "type": "Sale",
        "amount_range": "$15,001 - $50,000",
        "sector": "Healthcare",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T006",
        "member_id": "SAMPLE_S002",
        "member_name": "SAMPLE_DATA: John Doe",
        "date": "2025-08-18",
        "ticker": "LMT",
        "company": "Lockheed Martin",
        "type": "Purchase",
        "amount_range": "$100,001 - $250,000",
        "sector": "Defense",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T007",
        "member_id": "SAMPLE_S002",
        "member_name": "SAMPLE_DATA: John Doe",
        "date": "2025-08-22",
        "ticker": "RTX",
        "company": "RTX Corporation",
        "type": "Purchase",
        "amount_range": "$50,001 - $100,000",
        "sector": "Defense",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T008",
        "member_id": "SAMPLE_H003",
        "member_name": "SAMPLE_DATA: David Park",
        "date": "2025-10-20",
        "ticker": "AAPL",
        "company": "Apple Inc.",
        "type": "Purchase",
        "amount_range": "$15,001 - $50,000",
        "sector": "Technology",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T009",
        "member_id": "SAMPLE_S004",
        "member_name": "SAMPLE_DATA: Sarah Williams",
        "date": "2025-11-28",
        "ticker": "JPM",
        "company": "JPMorgan Chase",
        "type": "Purchase",
        "amount_range": "$100,001 - $250,000",
        "sector": "Finance",
        "is_sample": True,
    },
    {
        "id": "SAMPLE_T010",
        "member_id": "SAMPLE_S005",
        "member_name": "SAMPLE_DATA: Lisa Chang",
        "date": "2025-09-05",
        "ticker": "NEE",
        "company": "NextEra Energy",
        "type": "Purchase",
        "amount_range": "$50,001 - $100,000",
        "sector": "Energy",
        "is_sample": True,
    },
]

SAMPLE_VOTES = [
    {
        "bill_id": "SAMPLE_HR1234",
        "member_id": "SAMPLE_S001",
        "vote": "Yea",
        "date": "2025-10-15",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR1234",
        "member_id": "SAMPLE_S002",
        "vote": "Nay",
        "date": "2025-10-15",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR1234",
        "member_id": "SAMPLE_S003",
        "vote": "Yea",
        "date": "2025-10-15",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR5678",
        "member_id": "SAMPLE_H001",
        "vote": "Yea",
        "date": "2025-11-01",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR5678",
        "member_id": "SAMPLE_H002",
        "vote": "Yea",
        "date": "2025-11-01",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR9012",
        "member_id": "SAMPLE_S002",
        "vote": "Yea",
        "date": "2025-09-20",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR9012",
        "member_id": "SAMPLE_S001",
        "vote": "Nay",
        "date": "2025-09-20",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR5678",
        "member_id": "SAMPLE_H003",
        "vote": "Nay",
        "date": "2025-11-01",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_S5555",
        "member_id": "SAMPLE_S004",
        "vote": "Yea",
        "date": "2025-12-10",
        "is_sample": True,
    },
    {
        "bill_id": "SAMPLE_HR1234",
        "member_id": "SAMPLE_S005",
        "vote": "Yea",
        "date": "2025-10-15",
        "is_sample": True,
    },
]


def _is_api_available() -> dict:
    """Check which APIs have keys configured."""
    return {
        "congress": bool(CONGRESS_API_KEY),
        "fec": bool(FEC_API_KEY),
    }


async def fetch_members(query: str = "") -> list[dict]:
    """Fetch congress members. Uses sample data if no API key."""
    if not CONGRESS_API_KEY:
        if query:
            return [m for m in SAMPLE_MEMBERS if query.lower() in m["name"].lower()]
        return SAMPLE_MEMBERS

    # Live API call
    url = "https://api.congress.gov/v3/member"
    params = {"api_key": CONGRESS_API_KEY, "limit": 50, "format": "json"}
    if query:
        params["query"] = query

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    members = []
    for m in data.get("members", []):
        members.append({
            "id": m.get("bioguideId", ""),
            "name": m.get("name", ""),
            "party": m.get("partyName", "")[:1],
            "state": m.get("state", ""),
            "chamber": m.get("terms", {}).get("item", [{}])[-1].get("chamber", ""),
            "is_sample": False,
        })
    return members


async def fetch_bills(limit: int = 20) -> list[dict]:
    """Fetch recent bills. Uses sample data if no API key."""
    if not CONGRESS_API_KEY:
        return SAMPLE_BILLS

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
            "sponsor": "",
            "sponsor_name": "",
            "status": b.get("latestAction", {}).get("text", ""),
            "subjects": [],
            "is_sample": False,
        })
    return bills


async def fetch_trades(member_id: str = "") -> list[dict]:
    """Fetch stock trades. Uses sample data (no free reliable API for this)."""
    # Stock trade data currently only available from aggregators or scraping.
    # Always returns sample data for MVP.
    if member_id:
        return [t for t in SAMPLE_TRADES if t["member_id"] == member_id]
    return SAMPLE_TRADES


async def fetch_votes(bill_id: str = "") -> list[dict]:
    """Fetch voting records. Uses sample data if no API key."""
    if not CONGRESS_API_KEY:
        if bill_id:
            return [v for v in SAMPLE_VOTES if v["bill_id"] == bill_id]
        return SAMPLE_VOTES
    # With key, would use Congress.gov roll call votes
    if bill_id:
        return [v for v in SAMPLE_VOTES if v["bill_id"] == bill_id]
    return SAMPLE_VOTES
