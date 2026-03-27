"""Court Flow: Trending topics in federal litigation from CourtListener."""

import sys
from pathlib import Path

from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.courtlistener_client import (
    search_opinions,
    fetch_opinions,
    fetch_dockets,
    fetch_courts,
    FEDERAL_COURTS,
)
from services.analytics import (
    aggregate_by_court,
    aggregate_by_date,
    extract_topics,
    compute_stats,
)

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="Court Flow",
    app_dir=APP_DIR,
    description="Trending topics in federal litigation from CourtListener",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {
        "courts": FEDERAL_COURTS,
    })


@app.get("/api/search")
async def api_search(
    q: str = Query("antitrust", description="Search query"),
    limit: int = Query(20, ge=1, le=50),
    court: str = Query("", description="Court filter"),
):
    """Search opinions on CourtListener."""
    try:
        results = await search_opinions(query=q, limit=limit, court=court)
        stats = compute_stats(results)
        by_court = aggregate_by_court(results)
        by_date = aggregate_by_date(results)
        topics = extract_topics(results)

        return {
            "query": q,
            "results": results,
            "stats": stats,
            "by_court": by_court,
            "by_date": by_date,
            "topics": topics,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/recent")
async def api_recent(
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(20, ge=1, le=50),
):
    """Get recent opinions."""
    try:
        results = await fetch_opinions(limit=limit, days_back=days)
        return {"results": results, "count": len(results)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/dockets")
async def api_dockets(
    days: int = Query(30, ge=1, le=90),
    limit: int = Query(20, ge=1, le=50),
    court: str = Query("", description="Court filter"),
):
    """Get recent docket entries."""
    try:
        results = await fetch_dockets(limit=limit, days_back=days, court=court)
        return {"results": results, "count": len(results)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/courts")
async def api_courts():
    """Get list of courts."""
    try:
        courts = await fetch_courts()
        return {"courts": courts, "count": len(courts)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/trending")
async def api_trending(
    days: int = Query(30, ge=1, le=90),
):
    """Get trending topics based on recent filings.

    Searches for several common legal topics and aggregates results.
    """
    trending_queries = [
        "antitrust", "patent", "securities", "immigration",
        "environmental", "civil rights", "bankruptcy", "tax",
        "labor", "intellectual property",
    ]

    topic_counts = []
    for query in trending_queries:
        try:
            results = await search_opinions(query=query, limit=5)
            topic_counts.append({
                "topic": query,
                "count": len(results),
                "latest_date": results[0].get("date_filed", "") if results else "",
                "sample_case": results[0].get("case_name", "") if results else "",
            })
        except Exception:
            topic_counts.append({
                "topic": query,
                "count": 0,
                "latest_date": "",
                "sample_case": "",
            })

    topic_counts.sort(key=lambda x: -x["count"])
    return {"trending": topic_counts}


@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Court Flow",
        "app_description": "Trending topics in federal litigation. Search opinions, track docket activity, and see which legal topics are generating the most court activity.",
        "data_sources": [
            {
                "name": "CourtListener API v4",
                "url": "https://www.courtlistener.com/api/rest/v4/",
                "provider": "Free Law Project",
                "coverage": "Federal courts -- SCOTUS, Circuit courts, District courts",
                "granularity": "Per opinion, per docket, per court",
                "update_frequency": "Near-daily (as opinions are published)",
                "authentication": "Free, no key required for basic access",
                "rate_limits": "Rate limited (exact limits not published)",
                "history": "Historical opinions dating back decades",
                "key_fields": ["case_name", "date_filed", "court", "citation", "opinion_text", "docket_number", "judges"],
                "caveats": "Rate limits may throttle heavy usage. Not all opinions include full text. Coverage is strongest for federal courts; state court coverage varies.",
            },
        ],
        "data_freshness": "Opinions and dockets are fetched directly from CourtListener on each request. Trending topics are computed by searching multiple legal terms and comparing result counts. No local caching is applied.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8015)
