# Architecture Overview

Feed is a monorepo of 11 small web apps that turn free public data feeds into consumer-facing visualizations and tools. Each app is self-contained with its own routes, templates, static assets, and data layer, while sharing common infrastructure through a pip-installable `_shared` package.

## Monorepo Structure

```text
feed/
  _shared/              # Shared Python package (pip install -e)
    server.py           # FastAPI factory, port finder, template setup
    cache.py            # SQLite-backed HTTP response cache
    fetch.py            # Async HTTP client with rate limiting
    geo.py              # Geocoding and coordinate utilities
    templates/          # Shared base template (base.html)
    static/             # Shared static assets
  aqi-map/              # App: AQI time-slider heatmap
  energy-grid/          # App: US energy grid + carbon accountant
  flight-explorer/      # App: Overhead aircraft tracker
  bridge-watch/         # App: Bridge condition map
  creek-level/          # App: USGS stream gauges
  dark-sky-finder/      # App: Stargazing location finder
  permit-pulse/         # App: Multi-city building permits
  legis-track/          # App: Congress bills + campaign finance
  court-flow/           # App: Federal court trends
  risk-map/             # App: CA earthquake + wildfire risk
  transit-pulse/        # App: BART reliability scoring
  .env                  # API keys (gitignored)
  env.example           # Template for .env
  docs/                 # This documentation
```

## Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | Python 3.14 + FastAPI | Async request handling via uvicorn |
| Templates | Jinja2 | ChoiceLoader: app templates override shared templates |
| Maps | Deck.gl + Mapbox GL JS | Hardware-accelerated WebGL rendering |
| Charts | D3.js | Used for time series, stacked areas, bar charts |
| Icons | Lucide SVGs via CDN | No emojis anywhere in the UI |
| Database | SQLite per app | One `.db` file per app in `<app>/data/` |
| HTTP Client | httpx (async) | With token-bucket rate limiting |
| Styling | Vanilla CSS | Dark theme with per-app accent colors |
| Frontend | Vanilla JS | No build step, no bundler, no framework |

## App Directory Convention

Every app follows the same internal structure:

```text
<app-name>/
  app.py                # FastAPI routes and entry point
  services/             # API clients, business logic
  templates/            # Jinja2 templates (extends base.html)
  static/
    css/                # App-specific styles
    js/                 # App-specific JavaScript
  scripts/              # Backfill and data ingestion scripts
  data/                 # SQLite databases (gitignored)
  requirements.txt      # App-specific Python dependencies
  VISION.md             # Product vision and viability assessment
```

The `app.py` file is the entry point. Run it directly with `python3 app.py` and it starts a uvicorn server on the app's default port.

## Design Principles

- **Self-contained apps**: Each app can be developed, run, and deployed independently. The only shared dependency is the `_shared` package.
- **Free data only**: Every data source is free (either no key required or free API key). No paid APIs.
- **No build step**: Frontend is vanilla JS/CSS served as static files. No webpack, no npm, no transpilation.
- **Dark theme**: Slate background (`#0f172a`) with per-app accent colors defined via CSS custom properties in the base template.
- **Local-first**: Designed to run on `127.0.0.1` during development. Railway-ready for deployment.

## Next Steps

- [Patterns](02-patterns.md) -- recurring architectural patterns
- [Data Layer](03-data-layer.md) -- SQLite, caching, and API clients
