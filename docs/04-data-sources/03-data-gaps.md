# Data Gaps

Known limitations, missing data, and workarounds discovered during MVP development across the Feed portfolio.

## Cross-Cutting Issues

### No Caching on Most Apps

Most apps fetch data from upstream APIs on every request. This means:

- Every page load hits the external API
- Apps are subject to upstream rate limits and latency
- Repeated requests for the same data waste API quota

The `_shared/cache.py` and `_shared/fetch.py` modules provide caching infrastructure, but most apps have not integrated it yet. Adding caching with appropriate TTLs (15-30 minutes for most sources) is a common next step across the portfolio.

### Mapbox Dependency for Maps

Six of 11 apps need a Mapbox token for their map UI. Without it, the map layer does not render. The API endpoints still work, but the primary user experience is broken. The Mapbox free tier (50K loads/month) is sufficient for development and light use.

## Per-App Data Gaps

### aqi-map

- **Large state API timeouts**: CA and TX queries timeout at 60 seconds via the EPA AQS API. Workaround: use EPA bulk CSV downloads instead of per-state API calls.
- **Incomplete coverage**: Only 3 of 50 states have PM2.5 data ingested (NY, FL, WA). Full national coverage requires systematic backfill.
- **OpenWeatherMap not integrated**: Listed as a data source but not used in the pipeline.
- **No wildfire smoke overlay**: Wildfire smoke is the dominant AQI driver in western states but NOAA HMS data is not integrated.

### energy-grid

- **4-6 hour data lag**: The EIA API reports data with a multi-hour delay. The "real-time" framing is misleading during rapid grid changes.
- **No electricity price data**: The timing advisor recommends the greenest hours but cannot factor in cost, which is a stronger motivator for most consumers.
- **No demand-side data**: Only generation/supply data is available, not consumption/demand.
- **No generation forecast**: Cannot predict upcoming fuel mix for planning ahead.

### energy-grid (Carbon Accountant)

- **Green Button `powerOfTenMultiplier` inconsistency**: Utilities populate this field differently (omitted, set to 0, or set to values producing implausible readings). The parser applies heuristics but may misinterpret unusual files.
- **Carbon intensity is estimated**: Computed from fuel mix emission factors, not measured directly at the point of consumption.

### flight-explorer

- **No origin/destination**: ADS-B data provides current position only. You can see what is flying but not where it came from or where it is going.
- **Historical archives not downloaded**: The pipeline code exists but the ADSB.lol daily archives (3.4 GB/day) have not been ingested.
- **Approximate seat counts**: Hardcoded lookup table covers only 39 aircraft type codes.
- **No airline/flight number**: ADS-B provides callsign, which often but not always matches the flight number.

### bridge-watch

- **NBI API reliability**: The API intermittently returned 0 bridges for some queries during development. The cause was not definitively identified.
- **2,000-record limit**: Large states (TX, CA) have more bridges than the per-query limit. No pagination implemented. Workaround: use the NBI CSV download for complete state data.
- **Annual update cycle**: Recently repaired bridges may still show old condition ratings until the next annual inspection.

### creek-level

- **No sparkline previews**: Users must click into individual sites to see gauge history. The station list shows only current readings.
- **Offline gauges during extreme weather**: Some gauges go offline during floods and storms -- precisely when the data is most needed.

### dark-sky-finder

- **Small, static location dataset**: Only ~50 IDA-certified dark sky locations are included. Many excellent stargazing spots are not IDA-certified.
- **Coarse cloud cover grid**: The default 3-degree grid step misses microclimates and local conditions.
- **No light pollution modeling**: Beyond the fixed location list, there is no assessment of light pollution for arbitrary locations.

### permit-pulse

- **Data normalization across cities**: The core unsolved challenge. Each city uses different field names, date formats, and permit type classifications. Many permits fall into "Other" because city-specific types do not map cleanly.
- **Inconsistent cost data**: Estimated cost fields are unreliable or often empty across cities.
- **Variable geographic resolution**: NYC uses borough, SF uses analysis boundaries, Chicago uses community area. No unified geocoding.

### legis-track

- **No stock trade data**: The original "follow the money" vision included congressional stock trades, but no free API exists for this data. The feature was removed from scope.
- **Fragile name matching**: Linking Congress.gov members to FEC candidates requires name matching, which fails on different name orderings, middle names, and suffixes.
- **Two API keys required**: The app needs both `CONGRESS_API_KEY` and `FEC_API_KEY` to be fully functional.

### court-flow

- **Crude trending detection**: The "trending topics" feature searches for 10 hardcoded legal terms and counts results. It cannot discover emerging topics or detect actual trends.
- **Sequential API calls**: Trending topic computation makes multiple sequential CourtListener requests, which is slow and hits rate limits.

### risk-map

- **Seasonal fire data**: During non-fire months, the NIFC fire perimeter layer may be empty, making the "combined risk" framing feel incomplete.
- **No prospective fire risk**: Shows current active fires only, not fire hazard severity zones or historical fire scars.
- **California-specific**: The app only covers California, limiting the addressable audience.

### transit-pulse

- **Snapshot-only reliability**: "Reliability scores" are computed from a single point-in-time snapshot of current departures, not from accumulated historical data. A snapshot at 2pm on Tuesday does not indicate whether the Yellow line is systematically less reliable than the Blue line.
- **No BART VehiclePosition feed**: The BART API does not provide vehicle position data, only departure estimates. Real-time vehicle tracking is not possible.
- **No historical data API**: BART does not expose historical performance data. Building true reliability scores would require polling the API regularly and accumulating data locally.

## Next Steps

- [Free Public APIs](01-free-public-apis.md) -- full API reference
- [App Catalog](../02-apps/01-app-catalog.md) -- app descriptions and status
