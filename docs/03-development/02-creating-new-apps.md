# Creating New Apps

Step-by-step guide to adding a new app to the Feed monorepo.

## Step 1: Create the Directory Structure

```bash
mkdir -p my-app/{services,templates,static/{css,js},scripts,data}
```

This creates:

```text
my-app/
  services/           # API clients and business logic
  templates/          # Jinja2 templates
  static/
    css/              # App-specific styles
    js/               # App-specific JavaScript
  scripts/            # Backfill and data ingestion scripts
  data/               # SQLite databases (gitignored)
```

## Step 2: Create `requirements.txt`

At minimum:

```text
fastapi
uvicorn[standard]
jinja2
python-dotenv
httpx
```

Add any app-specific dependencies (e.g., `lxml` for XML parsing).

## Step 3: Create `app.py`

Use the standard factory pattern:

```python
"""My App: one-line description."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Query, Request
from fastapi.responses import JSONResponse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _shared.server import create_app, run_app

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

APP_DIR = Path(__file__).parent

app, templates = create_app(
    title="My App",
    app_dir=APP_DIR,
    description="What this app does",
)


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})


# Add API endpoints here...


if __name__ == "__main__":
    run_app(app, default_port=8020)  # Pick an unused port
```

Key points:

- The `sys.path.insert` line makes `_shared` importable
- `load_dotenv` reads from the repo root `.env`
- Pass `request` as the first argument to `TemplateResponse` (Starlette 1.0 requirement)

## Step 4: Create the Index Template

Create `templates/index.html`:

```html
{% extends "base.html" %}

{% block title %}My App{% endblock %}
{% block accent_color %}#f59e0b{% endblock %}
{% block accent_dim %}#78350f{% endblock %}

{% block head %}
<link rel="stylesheet" href="/static/css/app.css">
{% endblock %}

{% block content %}
<div class="container">
    <h1>My App</h1>
    <!-- App content here -->
</div>
{% endblock %}

{% block scripts %}
<script src="/static/js/app.js"></script>
{% endblock %}
```

The `accent_color` and `accent_dim` blocks set the app's theme color (used for links, highlights, and accents throughout the shared base template).

## Step 5: Set Up the Virtual Environment

```bash
cd my-app
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install -e ../_shared
```

The `-e` (editable) install of `_shared` means changes to shared code are picked up immediately without reinstalling.

## Step 6: Add API Clients

Create service modules in `services/` for each external API:

```python
# services/my_client.py
import httpx

async def fetch_data(param: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(
            "https://api.example.com/data",
            params={"q": param},
        )
        response.raise_for_status()
        return response.json()
```

For APIs with rate limits, use the shared `Fetcher`:

```python
from _shared.cache import Cache
from _shared.fetch import Fetcher

fetcher = Fetcher(
    cache=Cache(APP_DIR / "data" / "cache.db"),
    requests_per_second=0.5,  # Respect the API's rate limit
    default_ttl=900,          # Cache for 15 minutes
)
```

## Step 7: Add the Data Sources Page

Every app should expose a `/data` route:

```python
@app.get("/data")
async def data_sources(request: Request):
    return templates.TemplateResponse(request, "data-sources.html", {
        "app_name": "My App",
        "app_description": "What this app does.",
        "data_sources": [
            {
                "name": "Example API",
                "url": "https://api.example.com/",
                "provider": "Example Organization",
                "coverage": "US nationwide",
                "authentication": "Free, no key required",
                "rate_limits": "100 requests/minute",
            },
        ],
    })
```

The `data-sources.html` template is shared and renders a standardized data sources page.

## Step 8: Add to Navigation

The shared base template includes a navigation bar. To add the new app, update the nav links in the shared template or configure the app's title (which appears automatically).

## Step 9: Create VISION.md

Document the product vision, market opportunity, data sources, MVP assessment, and viability verdict. See any existing app's `VISION.md` for the format.

## Checklist

- [ ] Directory structure created
- [ ] `requirements.txt` with dependencies
- [ ] `app.py` using `create_app` / `run_app` factory
- [ ] Index template extending `base.html`
- [ ] Virtual environment set up with `_shared` installed
- [ ] API client(s) in `services/`
- [ ] `/data` route with data sources page
- [ ] `VISION.md` with product assessment
- [ ] Default port assigned (check existing ports to avoid conflicts)

## Next Steps

- [Troubleshooting](03-troubleshooting.md) -- common issues when developing
- [Architecture Patterns](../01-architecture/02-patterns.md) -- deeper look at the patterns
