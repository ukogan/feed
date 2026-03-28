# Free Public APIs

Comprehensive reference of all free public APIs used across the Feed portfolio.

## Government APIs

### EPA AQS (Air Quality System)

- **URL**: <https://aqs.epa.gov/data/api/>
- **Used by**: aqi-map
- **Auth**: Free -- email address used as API key (`EPA_EMAIL` in `.env`)
- **Rate limits**: ~10 requests/minute; large state queries timeout at 60 seconds
- **Coverage**: ~1,790 monitoring stations nationwide
- **Granularity**: Hourly readings per station, aggregated to monthly
- **History**: Back to 1990
- **Key parameters**: PM2.5 (code 88101), Ozone (code 44201)
- **Notes**: Not all stations report all parameters. Bulk CSV downloads recommended for large states (CA, TX).

### EIA API v2 (Energy Information Administration)

- **URL**: <https://api.eia.gov/v2/>
- **Used by**: energy-grid
- **Auth**: Free API key required (`EIA_API_KEY` in `.env`)
- **Rate limits**: 9,000 requests/hour
- **Coverage**: All major US ISOs (CAISO, ERCOT, PJM, MISO, NYISO, ISONE, SPP)
- **Granularity**: Hourly generation by fuel type per ISO
- **History**: Since July 2018
- **Key fields**: `respondent` (ISO), `fueltype`, `value` (MWh), `period`
- **Notes**: 4-6 hour data lag from real-time. Well-designed and reliable API.

### USGS Water Services

- **URL**: <https://waterservices.usgs.gov/>
- **Used by**: creek-level
- **Auth**: Free, no key required
- **Rate limits**: No published limit (fair use expected)
- **Coverage**: Thousands of stream gauges nationwide
- **Granularity**: 15-minute update intervals per gauge
- **History**: Decades per site
- **Key parameters**: Gauge height (00065), Discharge (00060)
- **Notes**: Some gauges may go offline during extreme weather. Provisional data subject to revision. Supports ISO 8601 duration queries (P1D, P7D).

### USGS Earthquake Hazards

- **URL**: <https://earthquake.usgs.gov/fdsnws/event/1/>
- **Used by**: risk-map
- **Auth**: Free, no key required
- **Rate limits**: No published limit
- **Coverage**: Global earthquake detection
- **Granularity**: Per-event with magnitude, location, depth, time
- **History**: Extensive historical catalog
- **Notes**: Updated within minutes of detection. Configurable date range and magnitude filter.

### FHWA National Bridge Inventory (NBI)

- **URL**: <https://geo.dot.gov/>
- **Used by**: bridge-watch
- **Auth**: Free, no key required
- **Rate limits**: No published limit
- **Coverage**: 600,000+ US bridges
- **Granularity**: Per-bridge condition ratings, year built, daily traffic
- **Key fields**: Condition ratings (0-9 scale for deck, superstructure, substructure), FIPS state code
- **Notes**: Returns up to 2,000 bridges per query. API reliability was intermittent during development. Annual update cycle by state DOTs. CSV bulk download is a more reliable alternative.

### NIFC Wildland Fire Perimeters

- **URL**: <https://services3.arcgis.com/> (ArcGIS hosted)
- **Used by**: risk-map
- **Auth**: Free, no key required
- **Rate limits**: No published limit
- **Coverage**: Active US wildfires
- **Granularity**: Fire perimeter polygons, updated ~every 5 minutes during fire season
- **Notes**: Active fires only -- no historical fire scars or prospective risk zones. Empty during non-fire season.

### NWS Weather Alerts

- **URL**: <https://api.weather.gov/alerts/>
- **Used by**: risk-map
- **Auth**: Free, no key required (User-Agent header required)
- **Rate limits**: No published limit
- **Coverage**: US nationwide weather alerts
- **Granularity**: Per-alert with geographic zones
- **Notes**: Used specifically for fire weather watches and red flag warnings. Alerts are transient and only exist when issued.

### Congress.gov API v3

- **URL**: <https://api.congress.gov/v3/>
- **Used by**: legis-track
- **Auth**: Free API key required (`CONGRESS_API_KEY` in `.env`)
- **Rate limits**: Not publicly documented
- **Coverage**: All sessions of Congress, both chambers
- **Granularity**: Per-bill, per-member
- **Key fields**: Member profiles, bill details, sponsorship, cosponsorship
- **Notes**: Near-daily updates during sessions. Well-documented and reliable. Member search limited to first page of results.

### FEC API v1 (Federal Election Commission)

- **URL**: <https://api.open.fec.gov/v1/>
- **Used by**: legis-track
- **Auth**: Free API key required (`FEC_API_KEY` in `.env`)
- **Rate limits**: 1,000 requests/hour
- **Coverage**: Federal elections (President, Senate, House)
- **Granularity**: Per-candidate finance summaries, committee data, contribution breakdowns
- **Notes**: Name matching between FEC and Congress.gov records is imprecise. Campaign finance data lags by days to weeks.

## Community and Open Data APIs

### ADSB.lol

- **URL**: <https://api.adsb.lol/v2/>
- **Used by**: flight-explorer
- **Auth**: Free, no key required
- **Rate limits**: No published limit (community-operated)
- **Coverage**: Global real-time aircraft positions
- **Granularity**: Per-aircraft, ~10-second position updates
- **Key fields**: `hex`, `registration`, `type`, `callsign`, `lat`, `lng`, `altitude`, `speed`, `heading`
- **Notes**: Coverage depends on community receiver density -- excellent over populated areas, sparse over oceans. ODbL license. Cannot determine origin or destination from position data alone.

### Open-Meteo Weather

- **URL**: <https://api.open-meteo.com/>
- **Used by**: dark-sky-finder
- **Auth**: Free, no key required
- **Rate limits**: 10,000 calls/day on free tier
- **Coverage**: Global weather forecasts
- **Granularity**: Hourly cloud cover forecasts (total, low, mid, high layers)
- **Notes**: Cloud cover accuracy decreases beyond 48 hours. Grid-based queries with configurable resolution.

### Socrata Open Data

- **URL**: <https://dev.socrata.com/>
- **Used by**: permit-pulse
- **Auth**: Free, no key required (app token increases rate limits)
- **Rate limits**: Varies by city portal
- **Coverage**: NYC, San Francisco, Chicago, Los Angeles, Seattle
- **Granularity**: Per-permit records
- **Notes**: Each city uses completely different field names, date formats, and permit type classifications. Normalization is the core challenge.

### CourtListener API v4

- **URL**: <https://www.courtlistener.com/api/rest/v4/>
- **Used by**: court-flow
- **Auth**: Free, no key required for basic usage
- **Rate limits**: Not publicly documented (limits exist)
- **Coverage**: Federal courts (SCOTUS, Circuit, District)
- **Granularity**: Per-opinion, per-docket
- **Notes**: Trailing-slash required on endpoints. State court coverage varies. Not all opinions include full text.

### BART API

- **URL**: <https://api.bart.gov/api/>
- **Used by**: transit-pulse
- **Auth**: Free shared demo key (`MW9S-E7SL-26DU-VV8V`)
- **Rate limits**: No published limit
- **Coverage**: BART system (Bay Area, CA)
- **Granularity**: Per-station real-time departure estimates
- **Notes**: Real-time snapshots only -- no historical departures or performance data. The delay field represents current seconds delayed, not cumulative reliability.

## Additional APIs Referenced but Not Integrated

These APIs appear in VISION.md files as potential enhancements:

| API | Use Case | Free? |
|-----|----------|-------|
| OpenSky Network | 30-day historical aircraft tracks | Yes (academic) |
| PurpleAir | Dense PM2.5 sensor network (~30K sensors) | No (paid API) |
| NOAA HMS Smoke Plumes | Satellite-detected wildfire smoke | Yes |
| WattTime | Real-time marginal carbon intensity | No (paid) |
| CAISO OASIS | California electricity prices | Yes |
| FAA ATCSCC | Air traffic control advisories | Yes |

## Next Steps

- [API Keys](02-api-keys.md) -- how to get and configure keys
- [Data Gaps](03-data-gaps.md) -- known limitations
