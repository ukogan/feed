# Creek Level -- Vision Document

## Origin

The USGS operates thousands of stream gauges across the US, reporting water levels every 15 minutes. This data is free and authoritative, but the USGS Water Watch portal is designed for hydrologists, not for kayakers checking whether their local creek is runnable or homeowners wondering if the creek behind their house is rising. The opportunity is to make this data consumer-friendly.

## Market Opportunity

- **Who needs this**: Kayakers and rafters checking river conditions, anglers timing their trips, homeowners in flood-prone areas monitoring nearby waterways, hikers planning creek crossings, local emergency managers tracking flood risk.
- **Evidence of demand**: Recreational river users are an engaged community that actively seeks flow data. Fishing forums frequently link to USGS gauge pages. Flood-prone homeowners check water levels during storms. The data is already heavily used -- just through a terrible interface.
- **Competitive landscape**: USGS Water Watch is the primary source but has a government-grade UI. Various fishing apps incorporate gauge data but only for specific rivers. American Whitewater maintains a gauge list for kayakers. No one app provides a clean, map-based, mobile-friendly view of all USGS gauges.

## Data Sources

- **USGS Water Services** (https://waterservices.usgs.gov/): Free, no API key required. Covers thousands of stream gauges nationwide with 15-minute update intervals. Supports queries by state, site number, and parameter code. Key parameters are gauge height (00065) and discharge (00060). Historical data available per site going back decades.

**Coverage and limitations**: Not all gauges report all parameters (some report only gauge height, not discharge). Some gauges may go offline during extreme weather -- precisely when the data is most wanted. Provisional data is subject to revision. The API has no published rate limits but expects fair use.

**Data freshness**: Gauge readings are fetched directly from USGS on each request. Data is near-real-time with 15-minute intervals. Historical queries support ISO 8601 duration periods (P1D for 1 day, P7D for 7 days).

## MVP Assessment

**What works well**: The USGS API is reliable, well-documented, and returns data in a clean format. The state-based site listing works. Individual site history with configurable time periods (1 day, 7 days) provides useful detail. The API requires no authentication, which simplifies deployment.

**What doesn't work or is limited**: The app currently fetches all active sites for a state on each request, which can be slow for states with hundreds of gauges. There is no sparkline or inline visualization in the station list -- users must click into individual sites. The map view requires a Mapbox token.

**Key surprises**: The USGS data is remarkably consistent and well-structured compared to other government APIs. The 15-minute update frequency is genuinely useful for real-time monitoring.

**Data quality vs. expectations**: Exceeded expectations. The data is clean, well-documented, and the API is stable.

## Viability Verdict

**PROMISING** -- the data source is excellent and the use cases are real. The main challenge is differentiation: the core value is making existing public data prettier, which is necessary but may not sustain engagement beyond initial curiosity. Adding alerts (notify me when gauge X exceeds Y feet) and activity-specific context (is this river runnable for kayaking?) would transform it from a data viewer into a tool people return to.

## Next Steps

If pursuing further:
- Add sparkline previews in the station list so users can see trends without clicking in.
- Implement threshold alerts: "notify me when this gauge exceeds X feet."
- Add recreational context: kayak runability ratings by flow level, fishing condition indicators.
- Cache state-level site lists (they change rarely) to speed up initial load.
- Build a "nearby gauges" feature using geolocation.
- Add flood stage indicators from NWS to show when a gauge is approaching or exceeding flood levels.
