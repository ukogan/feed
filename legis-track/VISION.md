# Legis Track -- Vision Document

## Origin

The original concept was "follow the money" -- connecting congressional bills to campaign finance and stock trades to reveal potential conflicts of interest. Capitol Trades proved consumer interest in the Congress-money connection by building a business around congressional stock trades. The MVP aimed to combine bills, campaign finance, and stock trades into one view per member.

## Market Opportunity

- **Who needs this**: Politically engaged citizens, journalists covering Congress, advocacy organizations tracking legislation, political science researchers, lobbyists tracking legislative activity.
- **Evidence of demand**: Capitol Trades (congressional stock trades) has a paying user base. Quiver Quantitative has active users tracking political data. OpenSecrets attracts millions of visitors for campaign finance data. GovTrack has loyal users for bill tracking. The appetite for "what is my representative doing and who is paying them" is well-established.
- **Competitive landscape**: GovTrack tracks bills but not money. OpenSecrets tracks money but not bills. Capitol Trades tracks stock trades (paid). No free tool combines bills and campaign finance in a single per-member view. The original vision included stock trades, but no free API exists for congressional stock trade data.

## Data Sources

- **Congress.gov API v3** (https://api.congress.gov/v3/): Free API key required. Covers all sessions of Congress, both chambers. Provides member profiles, bill details, sponsorship, and cosponsorship. Near-daily updates during sessions.
- **FEC API v1** (https://api.open.fec.gov/v1/): Free API key required. Covers federal elections (President, Senate, House). Provides candidate finance summaries, committee data, and contribution breakdowns. 1,000 requests per hour rate limit.

**Coverage and limitations**: Congress.gov API works well for bills and members but member search is limited to the first page of results. FEC API works for campaign finance but name matching between Congress.gov and FEC is imprecise -- the same person may appear under slightly different name formats. Stock trade data has no free API, so that feature was removed from the MVP entirely.

**Data freshness**: Both APIs are queried directly on each request with no caching. Campaign finance data lags real-time by days to weeks depending on filing schedules.

## MVP Assessment

**What works well**: Member search and bill browsing work. The per-member detail view (sponsored bills + campaign finance) provides genuine insight. The timeline of recent legislative events is a useful feed. The architecture cleanly separates Congress.gov and FEC data.

**What doesn't work or is limited**: The original vision of "follow the money" including stock trades had to be scoped down because there is no free API for congressional stock trade data. Member name matching between Congress.gov and FEC is fragile -- different name orderings, middle names, and suffixes cause mismatches. The app requires two API keys (Congress.gov and FEC) to function.

**Key surprises**: The Congress.gov API is better than expected -- well-documented, reliable, and comprehensive for bill data. The FEC API is adequate but the name-matching problem between the two systems is harder than anticipated. The absence of a free stock trade API was a significant scope reduction.

**Data quality vs. expectations**: Bill data quality is excellent. Campaign finance data is good but the cross-system name matching introduces noise. The stock trade vision was unachievable with free data.

## Viability Verdict

**PROMISING** -- the bills + campaign finance combination works and provides real value, but the original "follow the money" vision (including stock trades) had to be significantly scoped down. The competitive position is clear: free, combined view of legislation and campaign finance. The main risk is that without the stock trade angle, the product is incremental over existing free tools rather than transformative.

## Next Steps

If pursuing further:
- Implement fuzzy name matching or build a crosswalk table between Congress.gov bioguideIds and FEC candidate IDs to solve the name-matching problem.
- Add voting records to the per-member view (Congress.gov supports this).
- Scrape or license congressional stock trade data from financial disclosure filings (PDFs on efdsearch.senate.gov) to restore the original "follow the money" vision.
- Add bill tracking and alerts: "notify me when this bill has a new action."
- Build a "money flow" visualization showing campaign contributions alongside legislative activity on a timeline.
- Cache member and bill data to reduce API calls and improve response times.
