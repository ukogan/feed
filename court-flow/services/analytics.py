"""Analytics functions for court data aggregation."""

from collections import defaultdict, Counter
from datetime import datetime


def aggregate_by_court(results: list[dict]) -> list[dict]:
    """Count filings per court from search results."""
    court_counts = Counter()
    for r in results:
        court = r.get("court", "Unknown") or "Unknown"
        court_counts[court] += 1

    return [
        {"court": court, "count": count}
        for court, count in court_counts.most_common(20)
    ]


def aggregate_by_date(results: list[dict]) -> list[dict]:
    """Count filings per day from search results."""
    daily = defaultdict(int)
    for r in results:
        date_str = r.get("date_filed") or r.get("date_created", "")
        if date_str:
            day = date_str[:10]
            daily[day] += 1

    return [
        {"date": day, "count": count}
        for day, count in sorted(daily.items())
    ]


def extract_topics(results: list[dict], top_n: int = 10) -> list[dict]:
    """Extract trending topics from case names using keyword frequency.

    This is a simple approach; a real system would use NLP.
    """
    # Common legal stopwords to exclude
    stopwords = {
        "v", "vs", "the", "of", "in", "re", "et", "al", "a", "an",
        "for", "on", "to", "by", "and", "or", "not", "no", "is",
        "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should",
        "may", "might", "shall", "can", "united", "states", "inc",
        "corp", "llc", "ltd", "co", "company", "case", "court",
        "district", "circuit", "county", "city", "state", "commonwealth",
    }

    word_counts = Counter()
    for r in results:
        case_name = r.get("case_name", "")
        if not case_name:
            continue
        words = case_name.lower().split()
        for word in words:
            clean = word.strip(".,;:!?()[]{}\"'")
            if len(clean) > 2 and clean not in stopwords and clean.isalpha():
                word_counts[clean] += 1

    return [
        {"topic": word, "count": count}
        for word, count in word_counts.most_common(top_n)
    ]


def compute_stats(results: list[dict]) -> dict:
    """Compute summary statistics for a set of search results."""
    if not results:
        return {
            "total_filings": 0,
            "courts_involved": 0,
            "date_range": None,
            "filings_per_day": 0,
        }

    courts = set()
    dates = []
    for r in results:
        court = r.get("court", "")
        if court:
            courts.add(court)
        date_str = r.get("date_filed") or r.get("date_created", "")
        if date_str:
            try:
                dates.append(datetime.strptime(date_str[:10], "%Y-%m-%d"))
            except ValueError:
                pass

    date_range = None
    filings_per_day = 0
    if dates:
        min_date = min(dates)
        max_date = max(dates)
        date_range = {
            "start": min_date.strftime("%Y-%m-%d"),
            "end": max_date.strftime("%Y-%m-%d"),
        }
        days_span = max((max_date - min_date).days, 1)
        filings_per_day = round(len(results) / days_span, 1)

    return {
        "total_filings": len(results),
        "courts_involved": len(courts),
        "date_range": date_range,
        "filings_per_day": filings_per_day,
    }
