"""Analysis functions for legislative data."""

from datetime import datetime


def build_timeline(
    bills: list[dict],
) -> list[dict]:
    """Build a timeline of legislative events."""
    events = []

    for bill in bills:
        events.append({
            "date": bill.get("introduced", ""),
            "type": "introduced",
            "label": f"{bill['id']} introduced",
            "detail": bill["title"],
        })
        if bill.get("status_date") and bill.get("status"):
            events.append({
                "date": bill["status_date"],
                "type": "action",
                "label": bill["status"],
                "detail": f"{bill['id']}: {bill['title']}",
            })

    return sorted(events, key=lambda x: x.get("date", ""), reverse=True)


def format_currency(amount: float) -> str:
    """Format a number as currency."""
    if not amount:
        return "$0"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:.0f}"
