# Getting Started

Everything needed to set up and run Feed apps locally.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.14+ | Required. Earlier versions may work but 3.14 is the target. |
| pip | Latest | Comes with Python |
| Mapbox token | -- | Free tier (50K map loads/month). Required for map-based apps. |

Optional but recommended:

- Git for version control
- A terminal with good ANSI color support (the dark theme logs look better)

## Clone and Setup

```bash
git clone <repo-url>
cd feed
```

## API Keys

Copy the example environment file and fill in your keys:

```bash
cp env.example .env
```

The `.env` file lives at the repo root and is shared across all apps:

```bash
# Mapbox (free tier: 50K map loads/month)
# Get token at https://account.mapbox.com/access-tokens/
MAPBOX_TOKEN=

# EIA API v2 (free, register at https://www.eia.gov/opendata/register.php)
EIA_API_KEY=

# EPA AQS API (free, just needs an email)
EPA_EMAIL=

# OpenWeatherMap (free tier: 1000 calls/day)
# Get key at https://home.openweathermap.org/api_keys
OWM_API_KEY=

# Congress.gov API (free, register at https://api.congress.gov/sign-up/)
CONGRESS_API_KEY=

# FEC API (free, register at https://api.open.fec.gov/developers/)
FEC_API_KEY=
```

Not all keys are needed for all apps. See [API Keys](../04-data-sources/02-api-keys.md) for which apps need which keys.

## Running an App

Each app is self-contained. Set up its virtual environment and run:

```bash
cd energy-grid

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip3 install -r requirements.txt
pip3 install -e ../_shared

# Run the app
python3 app.py
```

The app prints its URL on startup:

```text
  Energy Grid
  http://127.0.0.1:8001
```

If the default port is busy, it automatically picks the next available port in the 8000-8099 range.

## Running Backfill Scripts

Some apps (aqi-map, bridge-watch) require data to be ingested before they have anything to display. Run the backfill scripts from the app directory:

```bash
cd aqi-map
source .venv/bin/activate
python3 scripts/backfill_aqi.py
```

Backfill scripts respect API rate limits and can be interrupted and resumed. They report progress to the console.

## Default Ports

| App | Default Port |
|-----|-------------|
| aqi-map | 8000 |
| energy-grid | 8001 |
| flight-explorer | 8002 |
| bridge-watch | 8010 |
| creek-level | 8011 |
| dark-sky-finder | 8012 |
| permit-pulse | 8013 |
| legis-track | 8014 |
| court-flow | 8015 |
| risk-map | 8016 |
| transit-pulse | 8017 |

## Next Steps

- [Creating New Apps](02-creating-new-apps.md) -- add a new app to the monorepo
- [Troubleshooting](03-troubleshooting.md) -- common issues and fixes
