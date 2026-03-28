# Data Layer

This page covers how Feed apps store, fetch, and cache data.

## SQLite Per App

Each app that needs persistent storage uses its own SQLite database in `<app>/data/`. The `data/` directory is gitignored -- databases are created locally by backfill scripts or on first run.

```python
import sqlite3

DB_PATH = APP_DIR / "data" / "aqi.db"

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Dict-like row access
    return conn
```

Apps using SQLite:

| App | Database | Contents |
|-----|----------|----------|
| aqi-map | `data/aqi.db` | EPA monitoring stations, monthly AQI aggregations |
| bridge-watch | `data/bridges.db` | NBI bridge records with condition ratings |
| flight-explorer | `data/history.db` | Historical ADS-B archives (when ingested) |

Apps without a database (on-demand API fetch only): energy-grid, creek-level, dark-sky-finder, permit-pulse, legis-track, court-flow, risk-map, transit-pulse.

## Async HTTP Client

The `Fetcher` class in `_shared/fetch.py` wraps `httpx.AsyncClient` with two features:

### Rate Limiting

A token-bucket rate limiter ensures the app does not exceed a target requests-per-second:

```python
class RateLimiter:
    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self._last_request = 0.0

    async def wait(self) -> None:
        elapsed = time.monotonic() - self._last_request
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()
```

This is particularly important for the EPA AQS API (~10 requests/minute) and the FEC API (1,000 requests/hour).

### Cache Integration

The `Fetcher` checks the SQLite cache before making HTTP requests, and stores responses after fetching:

```python
fetcher = Fetcher(
    cache=Cache("data/cache.db"),
    requests_per_second=2.0,
    default_ttl=3600,
)

# This checks cache first, rate-limits if needed, then fetches
data = await fetcher.get_json(url, params=params)
```

The cache key is a SHA-256 hash of the URL plus serialized parameters.

## Data Ingestion Approaches

### Real-Time (On-Demand)

Most apps fetch data from upstream APIs when a user makes a request. The flow is:

1. User hits an API endpoint (e.g., `/api/fuel-mix?iso=CISO`)
2. App calls the upstream API (e.g., EIA API v2)
3. App processes and returns the response

No local storage is involved. This is the simplest approach but makes every request dependent on upstream availability and speed.

### Batch Backfill

Apps with large historical datasets use backfill scripts in `<app>/scripts/`. These run manually from the command line:

```bash
cd aqi-map
python3 scripts/backfill_aqi.py --state NY --years 2020,2021,2022
```

Backfill scripts typically:

1. Query the upstream API with pagination and rate limiting
2. Insert results into the local SQLite database
3. Report progress and handle errors gracefully
4. Can be run incrementally (re-running skips already-ingested data)

### Hybrid

Some apps could benefit from both approaches: backfill historical data for fast queries, then supplement with real-time API calls for the latest data. No app currently implements this pattern, but it is a natural evolution.

## Geocoding

The `_shared/geo.py` module provides:

- `geocode_address(address, mapbox_token)` -- converts addresses to lat/lng via the Mapbox Geocoding API
- `haversine_distance_nm(lat1, lng1, lat2, lng2)` -- great-circle distance in nautical miles
- `bounding_box(lat, lng, radius_nm)` -- bounding box for area queries

Geocoding requires a `MAPBOX_TOKEN` in the `.env` file.

## Next Steps

- [API Keys](../04-data-sources/02-api-keys.md) -- which keys are needed and where to get them
- [Data Gaps](../04-data-sources/03-data-gaps.md) -- known data limitations
