# Architectural Patterns

This page documents the recurring patterns used across all Feed apps.

## FastAPI App Factory

Every app uses the `create_app` / `run_app` factory from `_shared/server.py`. This standardizes app creation and eliminates boilerplate.

```python
from _shared.server import create_app, run_app

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="My App",
    app_dir=APP_DIR,
    description="What this app does",
)

# Define routes using app and templates...

if __name__ == "__main__":
    run_app(app, default_port=8000)
```

### What `create_app` Does

1. Creates a FastAPI instance with CORS middleware (allow all origins)
2. Mounts `<app>/static/` at `/static` if the directory exists
3. Mounts `_shared/static/` at `/shared-static`
4. Configures Jinja2 with a `ChoiceLoader` that checks app templates first, then shared templates
5. Sets `cache_size=0` on the Jinja2 environment (required for Python 3.14 compatibility)
6. Returns `(app, templates)` tuple

### What `run_app` Does

1. Calls `find_available_port()` starting from `default_port`
2. Scans ports in the 8000-8099 range until it finds an open one
3. Starts uvicorn on `127.0.0.1` with `log_level="warning"`

This means if port 8000 is busy, the app automatically picks 8001 (or the next available).

## Template System

Templates use Jinja2 inheritance with a shared base template.

### Base Template (`_shared/templates/base.html`)

Provides the common HTML shell:

- Dark theme CSS custom properties (`--bg-primary`, `--text-primary`, `--accent`, etc.)
- Inter font for UI text, JetBrains Mono for code
- Block hooks: `title`, `head`, `accent_color`, `accent_dim`, `content`

### App Template Pattern

Each app's `index.html` extends the shared base:

```html
{% extends "base.html" %}

{% block title %}My App{% endblock %}
{% block accent_color %}#22c55e{% endblock %}

{% block content %}
  <!-- App-specific HTML -->
{% endblock %}
```

The `ChoiceLoader` resolves templates by checking the app's `templates/` directory first, then falling back to `_shared/templates/`. This allows apps to override any shared template.

## Data Pipeline Patterns

Apps use one of three data access patterns:

### Pattern 1: On-Demand API Fetch

The app fetches data from the upstream API on each request. No local storage.

**Used by**: energy-grid, flight-explorer, creek-level, court-flow, risk-map, transit-pulse

```python
@app.get("/api/data")
async def get_data():
    records = await fetch_from_upstream_api(params)
    return process(records)
```

**Trade-offs**: Always fresh data. Subject to upstream rate limits and latency. Every page load hits the external API.

### Pattern 2: Backfill to SQLite

A separate script ingests historical data into a local SQLite database. The app reads from SQLite.

**Used by**: aqi-map, bridge-watch

```bash
# Run the backfill script manually
cd aqi-map && python3 scripts/backfill_aqi.py
```

```python
# App reads from local database
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
```

**Trade-offs**: Fast reads from local SQLite. Requires manual (or scheduled) backfill. Data freshness depends on when the script last ran.

### Pattern 3: Multi-Source Aggregation

The app hits multiple independent APIs and combines the results.

**Used by**: risk-map (USGS + NIFC + NWS), legis-track (Congress.gov + FEC), permit-pulse (multiple Socrata endpoints)

Each source has independent error handling so a single API failure does not break the entire page.

## Caching Strategy

The `_shared/cache.py` module provides a `Cache` class backed by SQLite with TTL support:

```python
from _shared.cache import Cache

cache = Cache(db_path="data/cache.db")

# Check cache before fetching
cached = cache.get(url, params)
if cached:
    return cached

# Fetch and cache
data = await fetch(url, params)
cache.set(url, data, ttl_seconds=900)  # 15-minute TTL
```

The `Fetcher` class in `_shared/fetch.py` integrates caching and rate limiting into a single client:

```python
from _shared.fetch import Fetcher
from _shared.cache import Cache

fetcher = Fetcher(
    cache=Cache("data/cache.db"),
    requests_per_second=2.0,
    default_ttl=3600,
)

data = await fetcher.get_json(url, params=params)
```

Most MVP apps do not use caching yet -- they hit upstream APIs directly on each request. Adding caching is a common next step noted in the VISION.md files.

## Data Sources Page Convention

Every app exposes a `/data` route that renders a standardized data sources page using the shared `data-sources.html` template. This page documents what APIs the app uses, their limitations, and vision assessments.

## Next Steps

- [Data Layer](03-data-layer.md) -- SQLite details and API client patterns
- [App Catalog](../02-apps/01-app-catalog.md) -- all 11 apps at a glance
