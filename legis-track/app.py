"""Legis Track: Congress member lookup with bills and campaign finance."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
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

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

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
    members = await fetch_members()
    member = next((m for m in members if m["id"] == member_id), None)
    if not member:
        return JSONResponse({"error": f"Member not found: {member_id}"}, status_code=404)

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
