# Feed: Public Data Feed POC Portfolio

A monorepo of small web apps that combine free public data feeds in novel ways.

## Structure

```
feed/
  _shared/          # Shared Python package (FastAPI factory, caching, fetching)
  aqi-map/          # AQI time-slider heatmap (EPA + OpenWeatherMap)
  energy-grid/      # US energy grid visualization (EIA API)
  flight-explorer/  # "What flew over me" flight tracker (ADSB.lol + FAA)
  ...               # More POC apps to come
```

## Tech Stack

- **Backend:** Python3 + FastAPI, Jinja2 templates, SQLite per app
- **Frontend:** Vanilla JS (no build step), Deck.gl + Mapbox GL JS for maps, D3.js for charts
- **Icons:** Lucide SVGs via CDN (no emojis)
- **Deployment:** Local-first, Railway-ready

## Commands

```bash
# Run any app
cd <app-dir> && python3 app.py

# Backfill data for an app
cd <app-dir> && python3 scripts/<script>.py

# Install deps for an app
cd <app-dir> && python3 -m venv .venv && source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install -e ../_shared
```

## Conventions

- Each app is a self-contained directory with its own `app.py`, `data/`, `static/`, `templates/`
- Shared code lives in `_shared/` and is pip-installed in editable mode
- SQLite databases go in `<app>/data/` (gitignored)
- API keys live in `.env` at the repo root (gitignored)
- No emojis in code or UI — use Lucide SVG icons
- Dark theme: slate background (#0f172a), per-app accent colors
