# Transit Pulse -- Vision Document

## Origin

Transit apps show schedules, but nobody rates transit lines by historical reliability. The concept is "Yelp for transit lines" -- giving each line and station a reliability score based on actual performance data. BART (Bay Area Rapid Transit) was chosen as the initial system because it has a free, well-documented API with real-time departure data.

## Market Opportunity

- **Who needs this**: Transit riders (millions in the Bay Area alone), commuters choosing between routes, real estate buyers evaluating transit accessibility, transit agencies needing public accountability metrics, transportation journalists and advocates.
- **Evidence of demand**: Transit reliability is a constant source of frustration and public discussion. Social media complaints about late trains are ubiquitous. Transit agencies publish annual performance reports, but nobody provides real-time or near-real-time reliability scoring that riders can check before commuting.
- **Competitive landscape**: Transit apps (Google Maps, Apple Maps, Transit app, Citymapper) show schedules and real-time arrivals but do not score or compare reliability across lines. Transit agencies publish performance reports quarterly or annually. No consumer tool answers "which BART line is most reliable right now?"

## Data Sources

- **BART API** (https://api.bart.gov/api/): Free public API with a shared demo key (MW9S-E7SL-26DU-VV8V). Provides station information (coordinates, addresses) and real-time estimated departures per station. No published rate limits.

**Coverage and limitations**: The BART API provides real-time departure estimates only -- there are no historical departures or historical performance data available through the API. The "delay" field in departure estimates represents how many seconds a train is delayed, but this is a point-in-time snapshot, not a cumulative reliability metric. The public API key is shared across all users.

**Data freshness**: All data is fetched in real-time from the BART API on each request. Reliability scores are computed from a single snapshot of current departures across all stations.

## MVP Assessment

**What works well**: Station listing with coordinates works. Per-station departure estimates load correctly. The reliability computation (percent on-time, average delay by line and by station) produces meaningful output from real data. The dashboard endpoint combines stations, departures, and reliability into a single view. Line-level color coding makes the data visually intuitive.

**What doesn't work or is limited**: The fundamental limitation is that "reliability" is computed from a single point-in-time snapshot, not from accumulated historical data. A snapshot taken at 2pm on a Tuesday tells you about current conditions, not about whether the Yellow line is systematically less reliable than the Blue line. Without historical data accumulation, the reliability scores are essentially "current delay status" rebranded. The system is BART-only, limiting geographic appeal.

**Key surprises**: The BART API is straightforward and works as documented. The delay field is genuinely useful -- trains do report non-zero delays, making the reliability calculation non-trivial. But the lack of historical data means the core product promise ("rate lines by reliability") cannot be fully delivered without building a data collection pipeline.

**Data quality vs. expectations**: The real-time data is accurate and well-structured. However, the vision requires historical data that the API does not provide, which means the app would need to poll the API regularly and accumulate its own historical dataset.

## Viability Verdict

**NEEDS WORK** -- the concept is strong but the MVP reveals a fundamental gap: the BART API provides real-time snapshots only, and the "reliability score" vision requires historical accumulation. The app currently shows "current delay status," which is useful but not the promised "reliability rating." Building a data collection pipeline that polls the BART API every few minutes and accumulates weeks of data would unlock the actual product vision, but this requires persistent infrastructure (a database, a cron job, hosting).

## Next Steps

If pursuing further:
- Build a data collection pipeline: poll the BART API every 5 minutes, store results in a database, and compute rolling reliability scores from accumulated data (7-day, 30-day, 90-day windows).
- Add historical trend charts: "Yellow line reliability over the past month."
- Implement time-of-day analysis: "this line is most reliable at 10am, least reliable at 5pm."
- Expand beyond BART to other transit systems with real-time APIs (Muni, Caltrain, NYC MTA, CTA).
- Add user-facing alerts: "your morning commute line is currently experiencing delays."
- Compare actual arrival times against published schedules (requires both schedule and real-time data).
