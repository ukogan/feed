# Dark Sky Finder -- Vision Document

## Origin

Light pollution maps exist. Weather apps exist. Star charts exist. Nobody synthesizes all three into one answer: "Where should I go stargazing tonight?" The concept is to combine dark sky location data, real-time cloud cover forecasts, and moon phase into a single recommendation engine.

## Market Opportunity

- **Who needs this**: Amateur astronomers, astrophotographers, casual stargazers, dark sky tourism operators, national park visitors, camping trip planners.
- **Evidence of demand**: Stargazing is a popular hobby with growing interest. Dark sky tourism is a recognized economic driver for rural areas. The International Dark-Sky Association certifies dark sky places specifically to attract visitors. Apps like Star Walk and Sky Guide have millions of downloads.
- **Competitive landscape**: Light Pollution Map (lightpollutionmap.info) shows Bortle class but not weather. Clear Dark Sky provides astronomy forecasts but with a dated interface. Star Walk and similar apps focus on identifying celestial objects, not finding locations. Nobody combines "where is it dark" with "where will it be clear tonight."

## Data Sources

- **Open-Meteo Weather API** (https://api.open-meteo.com/): Free, no API key required. Global coverage with hourly cloud cover forecasts (total, low, mid, high cloud layers). 10,000 calls per day on the free tier.
- **IDA Dark Sky Places**: A hardcoded dataset of approximately 50 certified dark sky locations with coordinates and Bortle class ratings. Embedded in the source code, not fetched from an API.
- **Moon phase**: Computed client-side from a known new moon reference date. No API call required. Accurate to within a few hours for illumination percentage.

**Coverage and limitations**: Cloud cover forecasts decrease in accuracy beyond 48 hours. The dark sky location dataset is static and may not include the most recently certified sites. The grid-based cloud cover endpoint queries a coarse grid (3-degree steps by default), which provides a broad overview but misses microclimates.

**Data freshness**: Cloud cover is fetched in real-time from Open-Meteo. Dark sky locations are static. Moon phase is computed algorithmically on each page load.

## MVP Assessment

**What works well**: The concept is clean and well-scoped. Open-Meteo cloud cover data works reliably. The nearest-dark-sky-location finder with distance calculation is immediately useful. Moon phase computation is trivial and works correctly. The three-layer approach (where is it dark + will it be clear + is the moon out) is a genuinely novel synthesis.

**What doesn't work or is limited**: The hardcoded 50 IDA locations limit coverage -- there are many excellent stargazing spots that are not IDA-certified. The cloud cover grid is coarse and slow to fetch (many API calls for a national grid). There is no local light pollution modeling beyond the fixed location list.

**Key surprises**: The simplicity of the concept is its strength. Each component is straightforward, but the combination is something no existing app provides.

**Data quality vs. expectations**: Open-Meteo cloud cover forecasts are solid for the 24-48 hour window that matters for trip planning. The dark sky location data is accurate but incomplete.

## Viability Verdict

**PROMISING** -- simple concept, well-executed, and clearly differentiated. The main limitation is the small, static dark sky location dataset. Expanding it with crowdsourced locations or integrating light pollution raster data (e.g., VIIRS satellite imagery) would significantly increase utility. The app has natural expansion into astronomy event calendars (meteor showers, eclipses, planet visibility).

## Next Steps

If pursuing further:
- Expand the dark sky database beyond IDA-certified locations using light pollution map data (VIIRS/DMSP satellite imagery) to identify any low-light-pollution area, not just official sites.
- Add astronomy event integration: meteor shower peaks, planet visibility, ISS passes.
- Implement a "best night this week" recommendation that combines cloud cover forecasts with moon phase across multiple nights.
- Allow users to submit and rate stargazing locations (crowdsourced expansion).
- Add driving directions and travel time estimates to recommended locations.
- Optimize the cloud cover grid to use adaptive resolution (finer grid near dark sky sites, coarser elsewhere).
