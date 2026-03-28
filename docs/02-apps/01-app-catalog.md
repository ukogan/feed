# App Catalog

All 11 Feed apps with their ports, data sources, current status, and viability verdicts from VISION.md assessments.

## Summary Table

| App | Port | Data Source(s) | Viability |
|-----|------|---------------|-----------|
| [aqi-map](#aqi-map) | 8000 | EPA AQS | STRONG |
| [energy-grid](#energy-grid) | 8001 | EIA API v2 | PROMISING |
| [flight-explorer](#flight-explorer) | 8002 | ADSB.lol, FAA Registry, BTS | PROMISING |
| [bridge-watch](#bridge-watch) | 8010 | NBI (FHWA) | PROMISING |
| [creek-level](#creek-level) | 8011 | USGS Water Services | PROMISING |
| [dark-sky-finder](#dark-sky-finder) | 8012 | Open-Meteo, IDA Dark Sky | PROMISING |
| [permit-pulse](#permit-pulse) | 8013 | Socrata (multi-city) | NEEDS WORK |
| [legis-track](#legis-track) | 8014 | Congress.gov, FEC | PROMISING |
| [court-flow](#court-flow) | 8015 | CourtListener | PROMISING |
| [risk-map](#risk-map) | 8016 | USGS, NIFC, NWS | STRONG |
| [transit-pulse](#transit-pulse) | 8017 | BART API | NEEDS WORK |

## App Details

### aqi-map

**Historical air quality heatmap with animated time slider.**

Visualizes PM2.5 and Ozone readings from EPA monitoring stations across the US using a Deck.gl HeatmapLayer. Users scrub through months and years with a time slider to compare seasonal air quality patterns.

- **Key features**: ~1,790 stations loaded, monthly aggregations, parameter filtering (PM2.5/Ozone)
- **Data pattern**: Batch backfill to SQLite (requires running ingestion script)
- **Status**: 3 of 50 states ingested (NY, FL, WA). Large states (CA, TX) timeout via API -- needs bulk CSV download.
- **Viability**: STRONG -- the market gap is real (BreezoMeter acquired for ~$200M) and the concept is validated.

### energy-grid

**US energy generation mix with carbon intensity and smart timing advice.**

Shows real-time fuel mix for all major US ISOs (CAISO, ERCOT, PJM, MISO, NYISO, ISONE, SPP) as stacked area charts. Computes carbon intensity and recommends optimal times to use electricity. Includes the [Personal Carbon Accountant](02-carbon-accountant.md) as a flagship sub-feature.

- **Key features**: Multi-ISO fuel mix charts, carbon intensity calculation, smart timing advisor, Personal Carbon Accountant, Green Button XML upload
- **Data pattern**: On-demand API fetch (EIA API v2)
- **Status**: Fully functional. 4-6 hour data lag is inherent to the EIA source.
- **Viability**: PROMISING -- "when to charge your EV" advice is genuinely useful. Engagement frequency is the concern.

### flight-explorer

**"What flew over me?" real-time aircraft tracker.**

Enter a location and see every aircraft currently overhead with registration, type, altitude, speed, and heading. Look up any aircraft by tail number, hex code, or callsign.

- **Key features**: Overhead detection by radius, aircraft lookup (registration/hex/callsign), seat count estimation, area map view
- **Data pattern**: On-demand API fetch (ADSB.lol is real-time, no key required)
- **Status**: Real-time tracking works. Historical features written but archives not downloaded (3.4 GB/day).
- **Viability**: PROMISING -- overhead detection is engaging. Retention depends on historical analysis features.

### bridge-watch

**US bridge condition map from the National Bridge Inventory.**

Color-codes bridges by condition rating (good/fair/poor) on an interactive map. Shows year built, daily traffic counts, and structural details.

- **Key features**: State-level filtering, condition classification (worst of deck/superstructure/substructure), summary statistics
- **Data pattern**: Batch backfill to SQLite from NBI CSV downloads
- **Status**: Functional but API reliability was intermittent during development. 2,000-record limit per query for large states.
- **Viability**: PROMISING -- strong viral potential ("look at the bridges in your state"). Contingent on data reliability.

### creek-level

**USGS stream gauge viewer for creek and river water levels.**

Browse monitoring stations by state, view current gauge height and discharge readings, and chart historical levels over configurable time periods.

- **Key features**: State-based station listing, per-site history charts (1-day to 7-day), 15-minute update intervals
- **Data pattern**: On-demand API fetch (USGS Water Services, no key required)
- **Status**: Fully functional. No sparkline previews in station list yet.
- **Viability**: PROMISING -- excellent data source, clear use cases (kayakers, flood monitoring). Needs alerts to drive retention.

### dark-sky-finder

**Stargazing location finder combining dark skies, cloud cover, and moon phase.**

Finds the nearest dark sky location, checks tonight's cloud cover forecast, and factors in moon illumination to recommend the best stargazing conditions.

- **Key features**: ~50 IDA-certified dark sky locations, Open-Meteo cloud cover forecasts (total/low/mid/high), client-side moon phase calculation
- **Data pattern**: On-demand API fetch (Open-Meteo, no key required) + static dark sky dataset
- **Status**: Functional. Dark sky dataset is static and limited to ~50 IDA-certified sites.
- **Viability**: PROMISING -- simple, differentiated concept. Needs expanded location database.

### permit-pulse

**Multi-city building permit tracker for real estate intelligence.**

Aggregates permit data from NYC, San Francisco, Chicago, Los Angeles, and Seattle via Socrata open data portals. Shows monthly trends, type breakdowns, and hot zones by neighborhood.

- **Key features**: 5-city coverage, permit type normalization, monthly trend analytics, neighborhood hot zones
- **Data pattern**: On-demand API fetch (Socrata, no key required)
- **Status**: Functional but normalization quality varies by city. Many permits fall into "Other" category.
- **Viability**: NEEDS WORK -- validated by Shovels.ai's funding, but data normalization across cities is the unsolved core challenge.

### legis-track

**Congressional bills and campaign finance combined view.**

Browse recent bills, search members of Congress, and see per-member detail combining sponsored legislation with campaign finance data from the FEC.

- **Key features**: Bill browsing, member search, per-member detail (bills + campaign finance), legislative timeline
- **Data pattern**: On-demand API fetch (Congress.gov + FEC APIs)
- **Status**: Functional. Name matching between Congress.gov and FEC is fragile. Stock trade data (original vision) has no free API.
- **Viability**: PROMISING -- free combined view of bills + money is differentiated. Scoped down from original "follow the money" vision.

### court-flow

**Federal court trending topics from CourtListener.**

Surfaces what is trending in federal litigation by searching for legal topics and comparing activity levels. Provides search, aggregation by court and date, and recent opinion feeds.

- **Key features**: Opinion search, court aggregation, date breakdown, trending topic detection (10 hardcoded topics)
- **Data pattern**: On-demand API fetch (CourtListener, no key required)
- **Status**: Functional. Trending detection is crude (hardcoded search terms, not NLP).
- **Viability**: PROMISING -- the data is genuinely valuable and free. Needs better topic detection.

### risk-map

**California earthquake and wildfire risk map.**

Overlays USGS earthquake data, NIFC active fire perimeters, and NWS fire weather alerts on a single map. Provides a risk summary endpoint aggregating 30-day activity.

- **Key features**: 365-day earthquake history (traces fault lines visually), active fire perimeters, red flag warnings, combined risk summary
- **Data pattern**: On-demand API fetch (three independent sources, all free, no keys)
- **Status**: Fully functional. Fire layer is seasonal (empty during non-fire months).
- **Viability**: STRONG -- earthquake visualization alone is compelling. California-specific focus limits market but depth compensates.

### transit-pulse

**BART reliability scoring from real-time departure data.**

Computes per-line and per-station reliability scores from current BART departure estimates. Dashboard combines stations, departures, and reliability metrics.

- **Key features**: Station listing with coordinates, per-station departures, reliability scoring (percent on-time, average delay), line-level color coding
- **Data pattern**: On-demand API fetch (BART API with shared demo key)
- **Status**: Functional but fundamentally limited. "Reliability" is computed from a single snapshot, not historical accumulation.
- **Viability**: NEEDS WORK -- the vision requires historical data accumulation that the BART API does not provide. Currently shows "current delay status" rather than true reliability ratings.

## Next Steps

- [Carbon Accountant](02-carbon-accountant.md) -- deep dive into the flagship feature
- [Data Sources](../04-data-sources/01-free-public-apis.md) -- API reference
