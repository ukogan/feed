# Troubleshooting

Common issues encountered during Feed development and their solutions.

## Port Conflicts

**Symptom**: `RuntimeError: No available port in range 8000-8099` or the app starts on an unexpected port.

**Cause**: Another app or process is already using the default port.

**Fix**: The app factory automatically scans for available ports, so this usually resolves itself. If you see the error, check what is using the port:

```bash
lsof -i :8001
```

Kill the offending process or stop the other app.

## Virtual Environment Activation

**Symptom**: `ModuleNotFoundError: No module named 'fastapi'` or similar import errors.

**Cause**: The virtual environment is not activated or `_shared` is not installed.

**Fix**:

```bash
cd <app-dir>
source .venv/bin/activate
pip3 install -r requirements.txt
pip3 install -e ../_shared
```

Each app has its own `.venv`. Make sure you activate the right one.

## Starlette 1.0 TemplateResponse Signature

**Symptom**: `TypeError` or unexpected behavior when rendering templates.

**Cause**: Starlette 1.0 changed the `TemplateResponse` constructor signature. The `request` object must be the first positional argument, not passed as a keyword in the context dict.

**Fix**: Use this pattern:

```python
# Correct (Starlette 1.0+)
return templates.TemplateResponse(request, "index.html", {"key": "value"})

# Wrong (old Starlette)
return templates.TemplateResponse("index.html", {"request": request, "key": "value"})
```

All existing apps already use the correct pattern.

## Python 3.14 Jinja2 Compatibility

**Symptom**: `TypeError` or caching errors from Jinja2 template rendering.

**Cause**: Python 3.14 introduced changes that interact poorly with Jinja2's template caching.

**Fix**: The shared `create_app` factory sets `cache_size=0` on the Jinja2 environment, which disables template caching and avoids the issue:

```python
env = jinja2.Environment(loader=loader, autoescape=True, auto_reload=True, cache_size=0)
```

This is already handled in `_shared/server.py`. If you create a Jinja2 environment manually (outside the factory), remember to set `cache_size=0`.

## Safari Date Parsing

**Symptom**: Dates display as `NaN` or `Invalid Date` in Safari but work in Chrome/Firefox.

**Cause**: Safari's `Date` constructor is stricter about date string formats. It does not accept some ISO 8601 variants that Chrome tolerates.

**Fix**: When parsing date strings in JavaScript, use explicit format handling:

```javascript
// Problematic in Safari
new Date("2024-01-15 14:30:00")

// Works in all browsers
new Date("2024-01-15T14:30:00")
```

Replace spaces with `T` in datetime strings before parsing, or use a date parsing library.

## EPA AQS API Rate Limits and Timeouts

**Symptom**: Backfill script hangs, returns errors, or gets `429 Too Many Requests`.

**Cause**: The EPA AQS API is rate-limited to ~10 requests/minute. Large state queries (CA, TX) timeout at 60 seconds.

**Fix**:

- The backfill scripts include rate limiting. Do not bypass it.
- For large states, use EPA bulk CSV downloads instead of the API.
- If you hit a timeout, reduce the query scope (smaller date ranges, fewer parameters).

## Empty Database on First Run

**Symptom**: App loads but shows no data (empty charts, empty tables).

**Cause**: Apps that use SQLite (aqi-map, bridge-watch) require data to be ingested before they have anything to display.

**Fix**: Run the backfill script:

```bash
cd aqi-map
source .venv/bin/activate
python3 scripts/backfill_aqi.py
```

## Mapbox Token Missing

**Symptom**: Map does not render, or console shows Mapbox authentication errors.

**Cause**: `MAPBOX_TOKEN` is not set in `.env`.

**Fix**: Get a free token at [Mapbox Access Tokens](https://account.mapbox.com/access-tokens/) and add it to your `.env`:

```bash
MAPBOX_TOKEN=pk.your_token_here
```

Apps that need a Mapbox token: aqi-map, flight-explorer, creek-level, bridge-watch, risk-map, dark-sky-finder.

## CourtListener Trailing Slash Redirect

**Symptom**: API calls to CourtListener return 301 redirects or fail silently.

**Cause**: The CourtListener API v4 requires trailing slashes on endpoints. Without them, the server returns a redirect that some HTTP clients do not follow.

**Fix**: Ensure all CourtListener API URLs end with `/`:

```python
# Correct
url = "https://www.courtlistener.com/api/rest/v4/search/"

# Wrong (causes redirect)
url = "https://www.courtlistener.com/api/rest/v4/search"
```

## BART API Shared Key

**Symptom**: BART API returns authentication errors.

**Cause**: The BART API uses a shared public demo key. If the key is changed or revoked, all users are affected.

**Fix**: The current shared key is `MW9S-E7SL-26DU-VV8V`. This is published in BART's API documentation and intended for public use. If it stops working, check [BART API documentation](https://api.bart.gov/docs/overview/index.aspx) for the current key.

## Next Steps

- [Getting Started](01-getting-started.md) -- initial setup
- [Data Gaps](../04-data-sources/03-data-gaps.md) -- known data limitations
