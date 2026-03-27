"""Legis Track: Follow the money -- connecting bills, stock trades, and campaign contributions."""

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
    fetch_trades,
    fetch_votes,
    SAMPLE_MEMBERS,
    SAMPLE_BILLS,
)
from services.analysis import find_suspicious_trades, build_timeline

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="Legis Track",
    app_dir=APP_DIR,
    description="Follow the money: connecting bills, stock trades, and campaign contributions",
)


@app.get("/")
async def index(request: Request):
    has_keys = bool(os.getenv("CONGRESS_API_KEY"))
    return templates.TemplateResponse(request, "index.html", {
        "has_keys": has_keys,
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


@app.get("/api/trades")
async def get_trades(member_id: str = Query("", description="Filter by member")):
    """Get stock trade disclosures."""
    trades = await fetch_trades(member_id=member_id)
    return {"trades": trades, "count": len(trades)}


@app.get("/api/votes")
async def get_votes(bill_id: str = Query("", description="Filter by bill")):
    """Get voting records."""
    votes = await fetch_votes(bill_id=bill_id)
    return {"votes": votes, "count": len(votes)}


@app.get("/api/suspicious")
async def get_suspicious(window_days: int = Query(14, ge=1, le=90)):
    """Find trades that are suspiciously timed relative to bill votes."""
    trades = await fetch_trades()
    votes = await fetch_votes()
    bills = await fetch_bills()

    flagged = find_suspicious_trades(trades, votes, bills, window_days=window_days)
    return {"flagged": flagged, "count": len(flagged)}


@app.get("/api/timeline")
async def get_timeline(member_id: str = Query("")):
    """Get combined timeline of trades and legislative events."""
    trades = await fetch_trades(member_id=member_id)
    votes = await fetch_votes()
    bills = await fetch_bills()

    events = build_timeline(trades, votes, bills)
    return {"events": events, "count": len(events)}


@app.get("/api/member/{member_id}")
async def get_member_detail(member_id: str):
    """Get detailed view for a specific member."""
    members = await fetch_members()
    member = next((m for m in members if m["id"] == member_id), None)
    if not member:
        return JSONResponse({"error": f"Member not found: {member_id}"}, status_code=404)

    trades = await fetch_trades(member_id=member_id)
    votes = await fetch_votes()
    bills = await fetch_bills()

    # Get votes this member participated in
    member_votes = [v for v in votes if v["member_id"] == member_id]
    member_bill_ids = {v["bill_id"] for v in member_votes}
    member_bills = [b for b in bills if b["id"] in member_bill_ids]

    flagged = find_suspicious_trades(trades, member_votes, bills)

    return {
        "member": member,
        "trades": trades,
        "votes": member_votes,
        "bills": member_bills,
        "flagged_trades": flagged,
    }


if __name__ == "__main__":
    run_app(app, default_port=8014)
