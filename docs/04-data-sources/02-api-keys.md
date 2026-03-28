# API Keys

Which apps need which keys, where to get them, and how to configure them.

## Configuration

All API keys go in a single `.env` file at the repo root. Copy the example file to get started:

```bash
cp env.example .env
```

Each app loads `.env` from the parent directory via `python-dotenv`:

```python
load_dotenv(Path(__file__).resolve().parents[1] / ".env")
```

## Key Reference

| Key | Apps That Need It | Where to Get It | Cost |
|-----|-------------------|-----------------|------|
| `MAPBOX_TOKEN` | aqi-map, flight-explorer, creek-level, bridge-watch, risk-map, dark-sky-finder | [Mapbox Access Tokens](https://account.mapbox.com/access-tokens/) | Free (50K map loads/month) |
| `EIA_API_KEY` | energy-grid | [EIA Registration](https://www.eia.gov/opendata/register.php) | Free |
| `EPA_EMAIL` | aqi-map | Any valid email address | Free |
| `OWM_API_KEY` | (aqi-map, listed but not integrated) | [OpenWeatherMap](https://home.openweathermap.org/api_keys) | Free (1K calls/day) |
| `CONGRESS_API_KEY` | legis-track | [Congress.gov Sign Up](https://api.congress.gov/sign-up/) | Free |
| `FEC_API_KEY` | legis-track | [FEC Developers](https://api.open.fec.gov/developers/) | Free |

## Apps That Need No Keys

These apps work with no API keys at all:

| App | Why No Key |
|-----|-----------|
| creek-level | USGS Water Services requires no auth (but needs Mapbox for map view) |
| dark-sky-finder | Open-Meteo requires no auth (but needs Mapbox for map view) |
| court-flow | CourtListener requires no auth |
| risk-map | USGS, NIFC, NWS all require no auth (but needs Mapbox for map view) |
| transit-pulse | BART API uses a shared public demo key (hardcoded) |
| permit-pulse | Socrata requires no auth |
| bridge-watch | NBI requires no auth (but needs Mapbox for map view) |
| flight-explorer | ADSB.lol requires no auth (but needs Mapbox for map view) |

> **Note**: Most map-based apps technically work without `MAPBOX_TOKEN` for API-only usage, but the map UI will not render without it.

## `.env` Template

```bash
# Mapbox (free tier: 50K map loads/month)
MAPBOX_TOKEN=pk.your_token_here

# EIA API v2 (free)
EIA_API_KEY=your_key_here

# EPA AQS API (just an email address)
EPA_EMAIL=your.email@example.com

# OpenWeatherMap (free tier: 1000 calls/day)
OWM_API_KEY=your_key_here

# Congress.gov API (free)
CONGRESS_API_KEY=your_key_here

# FEC API (free)
FEC_API_KEY=your_key_here
```

## Registration Notes

- **Mapbox**: Requires creating an account. The default public token works for development. Free tier covers 50,000 map loads per month.
- **EIA**: Registration is instant. Key is emailed immediately.
- **EPA AQS**: No formal registration. Any valid email address serves as the API key.
- **Congress.gov**: Registration form, key delivered by email within minutes.
- **FEC**: Registration form, key delivered instantly.
- **OpenWeatherMap**: Account required. Free tier provides 1,000 API calls per day.

## Next Steps

- [Free Public APIs](01-free-public-apis.md) -- full API reference
- [Getting Started](../03-development/01-getting-started.md) -- setup guide
