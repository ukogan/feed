"""Analysis functions for cross-referencing trades with legislation."""

from datetime import datetime, timedelta


def find_suspicious_trades(
    trades: list[dict],
    votes: list[dict],
    bills: list[dict],
    window_days: int = 14,
) -> list[dict]:
    """Find trades that occur within a time window of related bill votes.

    A trade is flagged when:
    1. The member voted on a bill
    2. The bill's subjects overlap with the trade's sector
    3. The trade happened within window_days of the vote
    """
    # Build a lookup: bill_id -> subjects
    bill_subjects = {}
    for b in bills:
        bill_subjects[b["id"]] = [s.lower() for s in b.get("subjects", [])]

    # Build: member_id -> [(vote_date, bill_id, bill_subjects)]
    member_votes = {}
    for v in votes:
        mid = v["member_id"]
        if mid not in member_votes:
            member_votes[mid] = []
        subjects = bill_subjects.get(v["bill_id"], [])
        member_votes[mid].append({
            "vote_date": v["date"],
            "bill_id": v["bill_id"],
            "vote": v["vote"],
            "subjects": subjects,
        })

    flagged = []
    for trade in trades:
        mid = trade["member_id"]
        if mid not in member_votes:
            continue

        trade_date = _parse_date(trade["date"])
        if not trade_date:
            continue

        trade_sector = trade.get("sector", "").lower()

        for mv in member_votes[mid]:
            vote_date = _parse_date(mv["vote_date"])
            if not vote_date:
                continue

            days_diff = abs((trade_date - vote_date).days)
            if days_diff > window_days:
                continue

            # Check sector overlap with bill subjects
            sector_match = any(trade_sector in s or s in trade_sector for s in mv["subjects"])

            if sector_match:
                flagged.append({
                    **trade,
                    "flag_reason": f"Trade in {trade['sector']} sector "
                                   f"{'before' if trade_date < vote_date else 'after'} "
                                   f"vote on {mv['bill_id']}",
                    "days_from_vote": days_diff,
                    "related_bill": mv["bill_id"],
                    "vote_direction": mv["vote"],
                    "trade_timing": "before" if trade_date < vote_date else "after",
                })

    return sorted(flagged, key=lambda x: x.get("days_from_vote", 999))


def build_timeline(
    trades: list[dict],
    votes: list[dict],
    bills: list[dict],
) -> list[dict]:
    """Build a combined timeline of trades and legislative events."""
    events = []

    for trade in trades:
        events.append({
            "date": trade["date"],
            "type": "trade",
            "label": f"{trade['type']} {trade['ticker']} ({trade['amount_range']})",
            "member": trade["member_name"],
            "detail": trade["company"],
            "sector": trade.get("sector", ""),
            "is_sample": trade.get("is_sample", False),
        })

    for vote in votes:
        bill = next((b for b in bills if b["id"] == vote["bill_id"]), None)
        bill_title = bill["title"] if bill else vote["bill_id"]
        events.append({
            "date": vote["date"],
            "type": "vote",
            "label": f"Voted {vote['vote']} on {vote['bill_id']}",
            "member": "",
            "detail": bill_title,
            "sector": "",
            "is_sample": vote.get("is_sample", False),
        })

    for bill in bills:
        events.append({
            "date": bill["introduced"],
            "type": "bill",
            "label": f"{bill['id']} introduced",
            "member": bill.get("sponsor_name", ""),
            "detail": bill["title"],
            "sector": ", ".join(bill.get("subjects", [])),
            "is_sample": bill.get("is_sample", False),
        })

    return sorted(events, key=lambda x: x["date"], reverse=True)


def _parse_date(date_str: str) -> datetime | None:
    """Parse a date string in YYYY-MM-DD format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str[:10], "%Y-%m-%d")
    except ValueError:
        return None
