"""Permit Pulse: Multi-city building permit aggregator as real estate leading indicator."""

import sys
from pathlib import Path

from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _shared.server import create_app, run_app
from services.socrata_client import CITIES, fetch_permits, fetch_all_cities
from services.analytics import permits_by_month, permits_by_type, hot_zones, compute_stats

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="Permit Pulse",
    app_dir=APP_DIR,
    description="Multi-city building permit aggregator as real estate leading indicator",
)


@app.get("/")
async def index(request: Request):
    cities = {k: v["name"] for k, v in CITIES.items()}
    return templates.TemplateResponse(request, "index.html", {
        "cities": cities,
    })


@app.get("/api/permits")
async def get_permits(
    city: str = Query("nyc", description="City key"),
    limit: int = Query(1000, ge=100, le=5000),
    months: int = Query(12, ge=1, le=24),
):
    """Fetch permits for a single city."""
    if city not in CITIES:
        return JSONResponse(
            {"error": f"Unknown city: {city}. Valid: {list(CITIES.keys())}"},
            status_code=400,
        )
    try:
        records = await fetch_permits(city, limit=limit, months_back=months)
        return {
            "city": city,
            "city_name": CITIES[city]["name"],
            "count": len(records),
            "records": records,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/permits/all")
async def get_all_permits(
    limit: int = Query(500, ge=100, le=2000),
    months: int = Query(12, ge=1, le=24),
):
    """Fetch permits from all cities."""
    results = await fetch_all_cities(limit_per_city=limit, months_back=months)
    summary = {}
    for city_key, data in results.items():
        if isinstance(data, dict) and "error" in data:
            summary[city_key] = {
                "name": CITIES[city_key]["name"],
                "error": data["error"],
            }
        else:
            summary[city_key] = {
                "name": CITIES[city_key]["name"],
                "count": len(data),
                "stats": compute_stats(data),
                "by_type": permits_by_type(data),
                "monthly": permits_by_month(data),
                "hot_zones": hot_zones(data, top_n=5),
            }
    return summary


@app.get("/api/analytics")
async def get_analytics(
    city: str = Query("nyc"),
    months: int = Query(12, ge=1, le=24),
):
    """Get analytics for a single city."""
    if city not in CITIES:
        return JSONResponse(
            {"error": f"Unknown city: {city}"},
            status_code=400,
        )
    try:
        records = await fetch_permits(city, limit=2000, months_back=months)
        return {
            "city": city,
            "city_name": CITIES[city]["name"],
            "stats": compute_stats(records),
            "by_type": permits_by_type(records),
            "monthly": permits_by_month(records),
            "hot_zones": hot_zones(records, top_n=10),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/cities")
async def get_cities():
    """List available cities."""
    return {k: v["name"] for k, v in CITIES.items()}


@app.get("/data")
async def data_sources(request: Request):
    normalization_html = """
<p>Each city's Socrata dataset uses different field names, date semantics, and type taxonomies. The normalization layer maps these into a common schema, but the mapping is lossy in several dimensions:</p>
<table>
    <thead>
        <tr>
            <th>Dimension</th>
            <th>NYC</th>
            <th>SF</th>
            <th>Chicago</th>
            <th>LA</th>
            <th>Seattle</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td>Date field</td>
            <td>pre__filing_date</td>
            <td>filed_date</td>
            <td>issue_date</td>
            <td>issue_date</td>
            <td>issue_date</td>
        </tr>
        <tr>
            <td>Date meaning</td>
            <td>Filing (application)</td>
            <td>Filing</td>
            <td>Issuance (approval)</td>
            <td>Issuance</td>
            <td>Issuance</td>
        </tr>
        <tr>
            <td>Type field</td>
            <td>job_type (codes)</td>
            <td>permit_type_definition (prose)</td>
            <td>permit_type (long)</td>
            <td>permit_type (short)</td>
            <td>permitclass (use category)</td>
        </tr>
        <tr>
            <td>Location</td>
            <td>borough (5)</td>
            <td>neighborhood (~40)</td>
            <td>community_area (77)</td>
            <td>community_plan_area</td>
            <td>neighborhood</td>
        </tr>
        <tr>
            <td>Value field</td>
            <td>initial_cost</td>
            <td>estimated_cost</td>
            <td>reported_cost</td>
            <td>valuation</td>
            <td>estprojectcost</td>
        </tr>
    </tbody>
</table>
<p class="norm-warn">Seattle's type mapping is particularly problematic: it maps by use class rather than action type. A residential demolition gets classified as "Renovation" because the use class is residential. The "Other" catch-all bucket contains 30-50% of records across cities. NYC and SF use filing dates (when the application was submitted) while Chicago, LA, and Seattle use issuance dates (when the permit was approved) -- these represent different moments in the permit lifecycle and are not directly comparable.</p>
"""
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "Permit Pulse",
        "app_description": "Multi-city building permit aggregator as a real estate leading indicator. Tracks permit activity across NYC, San Francisco, Chicago, LA, and Seattle.",
        "vision_assessment": "The Socrata APIs work and the multi-city normalization produces usable results, but the normalization is very lossy. Cross-city comparison is misleading: NYC filing dates vs Chicago issuance dates measure different lifecycle moments, the 'Other' category absorbs 30-50% of records, and value fields measure different things across cities. The app works as a per-city activity tracker but the cross-city comparison story is weaker than hoped.",
        "killer_feature": "Neighborhood gentrification radar -- combine permit velocity (new construction, demolitions, major renovations) with Census median income data and Zillow/Redfin price trends to identify neighborhoods in the early stages of rapid change. Show a 2-year rolling animation of permit activity overlaid on property value changes. The permits are the leading indicator; prices are the lagging confirmation.",
        "data_gaps": [
            "Cross-city comparison is misleading due to different date semantics (filing vs issuance)",
            "Seattle type mapping is wrong -- maps by use class, not action type (residential demo = 'Renovation')",
            "The 'Other' catch-all bucket contains 30-50% of records across all cities",
            "Value fields measure different things (initial_cost vs valuation vs estimated_cost)",
            "No property value or demographic data to provide economic context",
            "No geocoded locations for some cities (can't map individual permits)",
        ],
        "related_apis": [
            {"name": "Census Building Permits Survey", "url": "https://www.census.gov/construction/bps/", "description": "National building permits data aggregated by metro area. Good for macro trends but less granular than city-level Socrata data.", "free": True},
            {"name": "Zillow Research Data", "url": "https://www.zillow.com/research/data/", "description": "Home value indices by neighborhood. Could overlay property value trends on permit activity to show leading/lagging indicator relationships.", "free": True},
            {"name": "Census ACS", "url": "https://www.census.gov/programs-surveys/acs", "description": "American Community Survey demographic data by census tract. Income, housing, and population data for neighborhood context.", "free": True},
        ],
        "normalization_notes": normalization_html,
        "data_sources": [
            {
                "name": "Socrata Open Data (NYC, SF, Chicago, LA, Seattle)",
                "url": "https://dev.socrata.com/",
                "provider": "Individual city governments via Socrata Open Data platform",
                "coverage": "NYC, San Francisco, Chicago, Los Angeles, Seattle",
                "granularity": "Per permit record",
                "update_frequency": "Varies by city (typically daily to weekly)",
                "authentication": "Free, no key required (app token optional for higher limits)",
                "rate_limits": "Varies by city; throttled without app token",
                "history": "Years of historical data (varies by city)",
                "key_fields": ["permit_number", "permit_type", "status", "filing_date", "address", "description", "estimated_cost"],
                "caveats": "Each city uses different field names, date semantics, and type taxonomies. See Normalization Notes below for details.",
            },
        ],
        "data_freshness": "Permit data is fetched directly from each city's Socrata API on each request. The app normalizes different city schemas into a common format (with known lossy mappings). Analytics (monthly trends, hot zones, type breakdowns) are computed on the fly from the fetched records.",
    })


if __name__ == "__main__":
    run_app(app, default_port=8013)
