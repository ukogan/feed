# AQI Time-Slider Map -- Vision Document

## Origin

Research confirmed a gap in the market: nobody offers a monthly or seasonal AQI map with a time slider. The driving question is "What's air quality like here in September?" -- a question homebuyers, allergy sufferers, and outdoor enthusiasts ask regularly but cannot answer without manually digging through EPA data. Wildfire smoke events have made air quality a mainstream concern, not just a niche environmental topic.

## Market Opportunity

- **Who needs this**: Homebuyers evaluating neighborhoods, people with respiratory conditions choosing where to live, outdoor workers planning seasonal schedules, real estate agents differentiating listings.
- **Evidence of demand**: BreezoMeter was acquired by Google for approximately $200M, validating that air quality data has commercial value. Wildfire season drives 600%+ spikes in "air quality" search volume. The real estate angle -- comparing AQI across months for a given zip code -- is unexploited.
- **Competitive landscape**: PurpleAir provides a real-time sensor map but no historical slider. AirNow shows only the last 24 hours. IQAir provides city-level rankings but no historical comparisons. None of these let a user ask "how does August compare to February at this location?"

## Data Sources

- **EPA AQS API** (https://aqs.epa.gov/data/api/): The primary data source. Free access using an email address as the API key. Covers approximately 1,300 monitoring stations nationwide with data back to 1990. Supports PM2.5 (parameter 88101) and Ozone (parameter 44201).
- **OpenWeatherMap Air Pollution API**: Listed as a secondary source for global coverage but not yet integrated into the MVP pipeline.

**Coverage and limitations**: The EPA API is rate-limited to roughly 10 requests per minute, making batch backfill of historical data extremely tedious. The data is stored in a local SQLite database with monthly aggregations per station. Not all stations report all parameters, and some have gaps in their historical records. The ingestion pipeline requires an `EPA_EMAIL` environment variable.

**Data freshness**: The app displays historical monthly averages, not real-time readings. Data must be ingested via a separate import process before the app has anything to show.

## MVP Assessment

**What works well**: The Deck.gl HeatmapLayer renders an impressive visualization. The concept of scrubbing through months/years with a time slider is immediately intuitive. The SQLite-backed architecture means queries are fast once data is loaded. The API design (stations, AQI by year/month, available years) is clean and well-structured.

**What doesn't work or is limited**: The app is entirely dependent on having pre-ingested data. Out of the box with an empty database, it shows nothing. The EPA batch ingestion is slow and tedious due to rate limits. There is no automated pipeline -- someone has to run the import manually. The `/api/years` endpoint returns an empty list if no data has been loaded.

**Key surprises**: The EPA data goes back to 1990, which is deeper than expected and makes the historical comparison angle genuinely powerful. The rate limiting, however, means building a full national dataset takes days of patient API calls.

**Data quality vs. expectations**: The data itself is high quality and authoritative (it is the official EPA record). The challenge is purely logistical -- getting it into the database at scale.

## Viability Verdict

**STRONG** -- if the historical data pipeline is built out. The gap in the market is real: nobody offers month-over-month AQI comparison with a visual slider. The underlying data is authoritative and free. The primary risk is that building a complete national dataset requires significant upfront ingestion work, and keeping it current requires an ongoing pipeline. But the product concept is validated by BreezoMeter's $200M acquisition.

## Next Steps

If pursuing further:
- Build an automated ingestion pipeline that runs nightly to fetch the latest EPA data within rate limits, gradually backfilling historical years.
- Add zip-code or address search so users can type a location rather than pan a map.
- Implement server-side caching or pre-computed tiles to handle the heatmap at national scale.
- Add a "compare two locations" feature for the homebuyer use case.
- Consider supplementing EPA station data with PurpleAir sensor data for denser coverage in urban areas.
