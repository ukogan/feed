# Bridge Watch -- Vision Document

## Origin

The American Society of Civil Engineers gives US bridges a "C" grade. There are over 600,000 bridges in the National Bridge Inventory, many with condition ratings that would alarm the people who drive over them daily. The "I drive over THAT?" shock factor, combined with the political spotlight on infrastructure spending, creates an opportunity for a consumer-facing visualization that makes this public data accessible.

## Market Opportunity

- **Who needs this**: Commuters curious about the bridges they cross daily, journalists covering infrastructure, local advocates pushing for repairs, real estate buyers evaluating neighborhoods, insurance adjusters.
- **Evidence of demand**: Infrastructure is a perennial political topic. Bridge failures (e.g., Fern Hollow Bridge in Pittsburgh, 2022) generate national coverage. The data is public but buried in government CSV dumps and ArcGIS portals that no ordinary person would navigate.
- **Competitive landscape**: No consumer-facing visualization exists. The NBI data lives on geo.dot.gov behind a REST API designed for GIS professionals. State DOT websites occasionally publish bridge reports, but nothing interactive or map-based for the general public.

## Data Sources

- **National Bridge Inventory REST API** (https://geo.dot.gov/): Hosted by the US DOT Federal Highway Administration. Free, no authentication required. Provides per-bridge data including condition ratings (0-9 scale for deck, superstructure, substructure), year built, and average daily traffic counts. Queried by FIPS state code.

**Coverage and limitations**: The API returns up to 2,000 bridges per query (configurable via `resultRecordCount`). For states with more bridges than the limit, results are truncated. Condition ratings use a 0-9 scale where 9 is excellent and 4 or below is "poor." The data is updated annually by state DOTs, so recently repaired bridges may still show old ratings.

**Data freshness**: Bridge data is fetched directly from the NBI REST API on each request -- no local caching. The underlying data reflects the most recent annual inspection cycle.

## MVP Assessment

**What works well**: The concept is strong. Color-coding bridges by condition (good/fair/poor) on a map creates an immediate visual impact. The condition classification logic (worst of deck/superstructure/substructure) is sound. State-level filtering with summary statistics (percent good/fair/poor) provides useful context. The API is free and requires no key.

**What doesn't work or is limited**: During initial testing, the API was reportedly returning 0 bridges for some queries, suggesting the API endpoint or query format may be unreliable. The 2,000-record limit means large states like Texas or California may have their bridge inventory truncated. There is no pagination implemented. Lat/lng coordinates in the NBI use a non-standard format that requires parsing (the code handles this but it was a source of bugs).

**Key surprises**: The NBI contains a surprising amount of detail per bridge -- not just condition but year built, traffic counts, and structural type. The shock-value factor is real: seeing clusters of "poor" bridges on roads you drive daily is genuinely compelling.

**Data quality vs. expectations**: When the API returns data, the quality is good. The concern is API reliability and completeness for high-bridge-count states.

## Viability Verdict

**PROMISING** -- contingent on the NBI API working reliably. The concept is differentiated and the data is uniquely available. The main risks are API reliability (intermittent zero-result responses) and the record limit for large states. If the API proves stable, this has strong viral potential: "Look at the bridges in your state" is inherently shareable content.

## Next Steps

If pursuing further:
- Investigate and resolve the zero-bridge-count API issue (may need pagination or alternate query parameters).
- Implement pagination to handle states with more than 2,000 bridges.
- Add a "search by address" or "bridges near me" feature for personal relevance.
- Build a comparison view showing how a state's bridge condition has changed over time (NBI publishes annual snapshots).
- Consider downloading the full NBI CSV and hosting it locally to avoid API reliability issues.
