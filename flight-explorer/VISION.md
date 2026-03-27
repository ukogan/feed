# Flight Explorer -- Vision Document

## Origin

The "what flew over me?" question is universal. Flightradar24 is a $400M+ business proving that aviation tracking has massive consumer appeal. But existing flight trackers focus on tracking specific flights or watching global air traffic. Nobody focuses on the "overhead" angle: stand in your backyard, point at a plane, and find out what it is, where it is going, and how many people are on board.

## Market Opportunity

- **Who needs this**: Aviation enthusiasts (a large and engaged community), curious people who hear planes overhead, plane spotters, people living near airports who want to know what is flying over them, educators teaching about aviation.
- **Evidence of demand**: Flightradar24 has millions of users and 65% margins. FlightAware has a large user base. The ADS-B receiver community is active and growing. Aviation enthusiast forums and social media accounts have massive followings.
- **Competitive landscape**: FR24 and FlightAware dominate real-time flight tracking but are map-centric ("find a flight on the map"). ADS-B Exchange provides raw data. None focus on the "overhead" experience: "I am standing here, what is above me?"

## Data Sources

- **ADSB.lol API** (https://api.adsb.lol/v2/): Community-operated ADS-B receiver network. Free, no API key required. Global real-time aircraft positions with approximately 10-second updates. ODbL licensed.
- **BTS T-100 Domestic Segment Data** (https://transtats.bts.gov/): Quarterly route-level passenger data from US carriers. Free, no key required.
- **FAA Aircraft Registry** (https://registry.faa.gov/): US-registered aircraft lookup by N-number. Free, no key required.

**Coverage and limitations**: ADSB.lol coverage depends on community receiver density -- excellent over populated areas, sparse over oceans and remote regions. Aircraft without ADS-B transponders (older aircraft, military) are invisible. Real-time data only; no historical positions. Seat count lookup uses a hardcoded table by aircraft type code, so estimates are approximate.

**Data freshness**: Aircraft positions are fetched in real-time on each request. The data is as current as the ADS-B network allows (typically within seconds).

## MVP Assessment

**What works well**: The real-time overhead detection works. ADSB.lol returns rich data -- hex code, registration, type, callsign, position, altitude, speed, heading -- and it is completely free with no API key. The area search and aircraft lookup endpoints function correctly. The concept of "here is what is flying over you right now" is immediately engaging.

**What doesn't work or is limited**: Historical data ("what flew over me yesterday at 3pm") requires building a pipeline from ADSB.lol daily archives, which has not been implemented. Seat count estimates are rough approximations from a hardcoded lookup table. The geocode feature requires a Mapbox token. Aircraft identification by registration/hex/callsign tries multiple lookup strategies sequentially, which can be slow if early attempts fail.

**Key surprises**: ADSB.lol is remarkably generous -- free, no key, no published rate limits, real-time data. This is a strong foundation. The overhead calculation (filtering aircraft by position relative to the user's location) works well and feels magical in practice.

**Data quality vs. expectations**: Better than expected for real-time data. The ADS-B network provides surprisingly complete coverage over populated areas. The main gap is historical data, which would unlock the most interesting use cases (patterns over time, daily flight counts, noise analysis).

## Viability Verdict

**PROMISING** -- real-time overhead detection works and is genuinely engaging. The business model challenge is that the "what's flying over me" experience is impressive but potentially shallow -- users check once, say "cool," and may not return. Building historical analysis ("your neighborhood averages 47 overhead flights per hour between 6am-10am") would create recurring value. The free data source is a major advantage.

## Next Steps

If pursuing further:
- Build a historical data pipeline from ADSB.lol daily archives to enable "what flew over me yesterday/last week" queries.
- Add flight path prediction and approach pattern visualization for airports.
- Implement noise estimation based on aircraft type and altitude.
- Build a "flight diary" feature where users can save interesting aircraft they have spotted.
- Add airline and route information by correlating callsigns with published schedules.
- Create a "busiest overhead hours" analysis from accumulated historical data.
