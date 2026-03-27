# Permit Pulse -- Vision Document

## Origin

Building permits are a leading indicator for real estate activity: new construction signals neighborhood growth, demolitions signal redevelopment, and renovation volume signals gentrification. Shovels.ai raised venture capital specifically for paid permit data, validating the market. The concept is to aggregate free permit data from multiple cities' open data portals and present it as a real estate intelligence tool.

## Market Opportunity

- **Who needs this**: Real estate investors looking for early signals of neighborhood change, developers scouting for activity clusters, homebuyers researching neighborhoods, urban planners tracking development patterns, journalists covering housing.
- **Evidence of demand**: Shovels.ai raised VC for paid permit data aggregation. Real estate investors actively monitor permit activity as a leading indicator. Individual city permit portals get significant traffic from developers and contractors.
- **Competitive landscape**: Shovels.ai offers paid permit data. Individual city open data portals provide raw permit feeds but only for their own jurisdiction. No free tool aggregates and normalizes permit data across multiple cities into a single dashboard.

## Data Sources

- **Socrata Open Data APIs** (https://dev.socrata.com/): Individual city governments publish permit data via the Socrata platform. Currently configured for NYC, San Francisco, Chicago, Los Angeles, and Seattle. Free access, no API key required (though an app token increases rate limits). Varies by city from daily to weekly updates.

**Coverage and limitations**: This is the hardest data challenge in the portfolio. Each city uses completely different field names, date formats, permit type classifications, and geographic descriptors. NYC uses `pre__filing_date` and `job_type` with codes like "NB" and "A1". San Francisco uses `filed_date` and `permit_type_definition` with descriptive strings. Chicago uses `issue_date` and `permit_type` with verbose labels. The normalization code maps each city's schema to a common format, but edge cases are inevitable. Some cities' estimated cost fields are unreliable or often empty.

**Data freshness**: Permits are fetched directly from each city's Socrata API on each request. Analytics (monthly trends, hot zones, type breakdowns) are computed on the fly.

## MVP Assessment

**What works well**: The multi-city architecture is well-structured. The normalization layer handles the major schema differences. Per-city analytics (monthly trends, type breakdowns, hot zones by neighborhood) provide useful breakdowns. The all-cities comparison view gives a macro perspective.

**What doesn't work or is limited**: Data normalization across cities is the fundamental challenge and it is not fully solved. Permit type mapping is lossy -- many permits fall into "Other" because city-specific types do not map cleanly to the standard categories. Some cities may fail to return data due to API changes or schema updates. The value fields (estimated cost) are inconsistent between cities and often missing. Geographic resolution varies: NYC uses "borough," SF uses "neighborhoods_analysis_boundaries," Chicago uses "community_area."

**Key surprises**: The degree of schema variation between cities was expected but still proved harder than anticipated in practice. Each city is essentially its own integration project. Adding a new city requires researching its specific Socrata endpoint, field names, and type classifications.

**Data quality vs. expectations**: Below expectations. The data exists and is queryable, but normalization quality varies significantly by city. The "leading indicator" value of the data is real, but extracting it requires more city-specific tuning than a generic approach allows.

## Viability Verdict

**NEEDS WORK** -- the concept is validated by Shovels.ai's funding, but the data normalization problem is the core challenge and it has not been sufficiently solved. Each city is its own integration project with unique field names, type codes, and data quality issues. Scaling beyond 5 cities would require either a much more robust normalization pipeline or a shift to city-by-city deep integration rather than a generic approach.

## Next Steps

If pursuing further:
- Invest heavily in per-city normalization: treat each city as a separate integration with validation tests.
- Add data quality indicators per city so users know which cities have reliable data.
- Build a permit type taxonomy that is more nuanced than the current 4-category system (New Construction, Renovation, Demolition, Other).
- Add geocoding to place permits on a map (currently only neighborhood-level geography).
- Consider focusing on fewer cities with deeper, higher-quality integration rather than broad but shallow coverage.
- Add historical trend analysis: "permit volume in this neighborhood is up 30% year-over-year."
