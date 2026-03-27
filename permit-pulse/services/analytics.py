"""Analytics functions for permit data aggregation."""

from collections import defaultdict
from datetime import datetime


def permits_by_month(records: list[dict]) -> list[dict]:
    """Group permits by month, returning counts and total value."""
    monthly = defaultdict(lambda: {"count": 0, "value": 0})
    for r in records:
        date_str = r.get("date")
        if not date_str:
            continue
        month_key = date_str[:7]  # YYYY-MM
        monthly[month_key]["count"] += 1
        monthly[month_key]["value"] += r.get("value", 0)

    return [
        {"month": k, "count": v["count"], "value": round(v["value"], 2)}
        for k, v in sorted(monthly.items())
    ]


def permits_by_type(records: list[dict]) -> dict:
    """Count permits by normalized type."""
    counts = defaultdict(int)
    for r in records:
        counts[r.get("type", "Other")] += 1
    return dict(sorted(counts.items(), key=lambda x: -x[1]))


def hot_zones(records: list[dict], top_n: int = 10) -> list[dict]:
    """Find neighborhoods with highest permit activity."""
    zones = defaultdict(lambda: {"count": 0, "value": 0})
    for r in records:
        hood = r.get("neighborhood", "Unknown")
        zones[hood]["count"] += 1
        zones[hood]["value"] += r.get("value", 0)

    sorted_zones = sorted(zones.items(), key=lambda x: -x[1]["count"])[:top_n]
    return [
        {"neighborhood": k, "count": v["count"], "value": round(v["value"], 2)}
        for k, v in sorted_zones
    ]


def compute_stats(records: list[dict]) -> dict:
    """Compute summary stats for a set of permits."""
    if not records:
        return {
            "total_permits": 0,
            "total_value": 0,
            "avg_value": 0,
            "yoy_change": None,
        }

    total = len(records)
    total_value = sum(r.get("value", 0) for r in records)
    avg_value = total_value / total if total else 0

    # YoY change: compare last 6 months vs prior 6 months
    now = datetime.utcnow()
    six_months_ago = now.replace(month=now.month - 6) if now.month > 6 else now.replace(
        year=now.year - 1, month=now.month + 6
    )
    twelve_months_ago = now.replace(year=now.year - 1)

    recent_count = 0
    prior_count = 0
    for r in records:
        date_str = r.get("date")
        if not date_str:
            continue
        try:
            d = datetime.strptime(date_str[:10], "%Y-%m-%d")
        except ValueError:
            continue
        if d >= six_months_ago:
            recent_count += 1
        elif d >= twelve_months_ago:
            prior_count += 1

    yoy_change = None
    if prior_count > 0:
        yoy_change = round(((recent_count - prior_count) / prior_count) * 100, 1)

    return {
        "total_permits": total,
        "total_value": round(total_value, 2),
        "avg_value": round(avg_value, 2),
        "yoy_change": yoy_change,
    }
