"""Legis Track: Congress member lookup with bills and campaign finance."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env BEFORE importing services (they read os.getenv at module level)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.congress_client import (
    fetch_members,
    fetch_bills,
    fetch_member_bills,
    fetch_contributions,
    is_live,
)
from services.analysis import build_timeline

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="Legis Track",
    app_dir=APP_DIR,
    description="Congress member lookup with bills and campaign finance",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "has_keys": is_live(),
    })


@app.get("/api/members")
async def get_members(q: str = Query("", description="Search query")):
    """Search congress members."""
    members = await fetch_members(query=q)
    return {"members": members, "count": len(members)}


@app.get("/api/bills")
async def get_bills(limit: int = Query(20, ge=1, le=100)):
    """Get recent bills."""
    bills = await fetch_bills(limit=limit)
    return {"bills": bills, "count": len(bills)}


@app.get("/api/member/{member_id}")
async def get_member_detail(member_id: str):
    """Get detailed view for a specific member."""
    # Fetch member directly by bioguideId rather than searching the first 50
    from services.congress_client import CONGRESS_API_KEY
    member = None
    if CONGRESS_API_KEY:
        try:
            import httpx
            url = f"https://api.congress.gov/v3/member/{member_id}"
            params = {"api_key": CONGRESS_API_KEY, "format": "json"}
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
            m = data.get("member", {})
            if m:
                member = {
                    "id": m.get("bioguideId", member_id),
                    "name": f"{m.get('lastName', '')}, {m.get('firstName', '')}",
                    "party": (m.get("partyHistory", [{}])[0].get("partyName", "") or "")[:1],
                    "state": m.get("state", ""),
                    "chamber": "",
                }
        except Exception:
            pass

    if not member:
        member = {"id": member_id, "name": member_id, "party": "", "state": "", "chamber": ""}

    sponsored = await fetch_member_bills(member_id)
    contributions = await fetch_contributions(member.get("name", ""))

    return {
        "member": member,
        "sponsored_bills": sponsored,
        "campaign_finance": contributions,
    }


@app.get("/api/timeline")
async def get_timeline():
    """Get timeline of recent legislative events."""
    bills = await fetch_bills(limit=50)
    events = build_timeline(bills)
    return {"events": events[:50], "count": len(events)}


@app.get("/api/contributions")
async def get_contributions(name: str = Query("", description="Candidate name")):
    """Look up campaign finance for a candidate."""
    if not name:
        return {"contributions": [], "count": 0}
    data = await fetch_contributions(candidate_name=name)
    return {"contributions": data, "count": len(data)}


if __name__ == "__main__":
    run_app(app, default_port=8014)
