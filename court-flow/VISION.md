# Court Flow -- Vision Document

## Origin

PACER generates over $150M per year in revenue, proving that demand for federal court data is substantial. CourtListener (from the Free Law Project) makes this data freely available but does not visualize trends or make the data approachable for non-lawyers. The concept is to surface "what's trending in federal litigation" -- making court activity as browsable as a news feed.

## Market Opportunity

- **Who needs this**: Legal professionals tracking case law developments, journalists covering federal litigation, researchers studying judicial trends, law students following areas of law, policy advocates monitoring regulatory enforcement.
- **Evidence of demand**: PACER's $150M+ annual revenue comes despite a terrible user experience, proving the data has intrinsic value. Legal research is dominated by Westlaw and LexisNexis, which charge thousands per year. There is room for a free, trend-focused tool that does not try to replace full legal research but instead answers "what's happening right now in federal courts?"
- **Competitive landscape**: CourtListener provides raw data and basic search but no trend visualization. Westlaw/LexisNexis are comprehensive but expensive and geared toward practicing attorneys. No tool aggregates court activity into trending topics for casual consumption.

## Data Sources

- **CourtListener API v4** (https://www.courtlistener.com/api/rest/v4/): Provided by the Free Law Project. Free access, no API key required for basic usage. Covers federal courts (SCOTUS, Circuit, District). Supports opinion search, docket browsing, and court metadata.

**Coverage and limitations**: Rate limits are not publicly documented but exist. Coverage is strongest for federal courts; state court coverage varies significantly. Not all opinions include full text. The API had a trailing-slash redirect issue that was encountered and fixed during development.

**Data freshness**: Opinions and dockets are fetched directly from CourtListener on each request with no local caching. Trending topics are computed by searching multiple legal terms (antitrust, patent, securities, etc.) and comparing result counts -- a rough heuristic, not a sophisticated NLP analysis.

## MVP Assessment

**What works well**: The search functionality works and returns real federal court opinions with case names, dates, courts, and citations. The aggregation by court and by date provides useful breakdowns. The trending topics concept -- searching for several legal terms and ranking by activity -- is a reasonable first approximation.

**What doesn't work or is limited**: The "trending" feature is crude: it searches for 10 hardcoded legal topics and counts results. This is not true trend detection (it cannot discover emerging topics). The sequential API calls for trending topics make it slow. There is no caching, so repeated requests hit CourtListener's rate limits.

**Key surprises**: The CourtListener API required fixing a trailing-slash redirect issue, which suggests the API is not heavily polished. However, the data quality is good when results are returned -- real case names, real citations, real courts.

**Data quality vs. expectations**: The data is real and authoritative (sourced from actual court filings). The limitation is in what the app does with it: the analytics are surface-level.

## Viability Verdict

**PROMISING** -- the data is genuinely valuable and free, but the "trending" concept needs a more sophisticated approach than hardcoded search terms. The competitive gap between "free CourtListener raw data" and "$10K/year Westlaw" is real. The app could become useful with better topic detection and a notification system for tracking specific legal areas.

## Next Steps

If pursuing further:
- Replace the hardcoded trending topics with actual trend detection (e.g., compare this week's filing volume to historical baselines by legal area).
- Add caching to avoid hitting CourtListener rate limits on every page load.
- Build an alert/notification feature: "notify me when a new antitrust case is filed in the 9th Circuit."
- Add case citation networks to show how opinions reference each other.
- Consider indexing opinions locally for faster full-text search and real topic extraction using NLP.
