# Energy Grid -- Vision Document

## Origin

No consumer-friendly US app shows "when to charge your EV" based on real grid data. Electricity Maps exists but is global, subscription-based, and not actionable for American consumers. The EIA publishes hourly fuel mix data for every major US ISO, but the data sits behind an API that only developers and energy analysts use. The concept is to turn this data into actionable timing advice: charge your EV or run your dishwasher when the grid is cleanest.

## Market Opportunity

- **Who needs this**: EV owners (20M+ in the US and growing), energy-conscious homeowners, demand response program participants, sustainability-minded consumers, utility companies looking for customer engagement tools.
- **Evidence of demand**: ev.energy raised $63M for EV charging optimization. GridStatus raised $8M for grid data tools. Energize Capital is actively investing in the space. Time-of-use electricity pricing is expanding, creating financial incentive to shift load to clean/cheap hours.
- **Competitive landscape**: Electricity Maps has a limited free tier and is developer-focused. GridStatus targets developers and utilities. Individual ISO dashboards (CAISO, ERCOT) exist but are ugly and hard to interpret. No consumer tool says "charge now, the grid is 60% renewable."

## Data Sources

- **EIA API v2** (https://api.eia.gov/v2/): Free API key required. Covers all major US ISOs (CAISO, ERCOT, PJM, MISO, NYISO, ISONE, SPP). Provides hourly generation by fuel type. Rate limit of 9,000 requests per hour. Data available since July 2018.

**Coverage and limitations**: The EIA data has a 4-6 hour lag from real-time. This means "current" conditions actually reflect the grid several hours ago. Some ISOs report fuel categories differently, requiring normalization. Generation values are in MWh.

**Data freshness**: Data is fetched directly from the EIA API on each request. The 4-6 hour lag is inherent to the data source, not the app.

## MVP Assessment

**What works well**: The stacked area chart renders beautifully with real CAISO data, showing the daily solar ramp and evening gas ramp visually. Carbon intensity calculation based on fuel mix is functional and meaningful. The smart timing advisor (analyzing 7-day patterns to find the cleanest windows) provides genuinely useful advice. The multi-ISO summary view gives a quick national overview. The fuel type display with colors and names is polished.

**What doesn't work or is limited**: The 4-6 hour data lag means the "right now" framing is slightly misleading. Safari date parsing required fixing (a recurring browser compatibility issue). The summary endpoint makes sequential API calls for each ISO, which can be slow. There is no caching, so every page load hits the EIA API.

**Key surprises**: The EIA API is well-designed and reliable. CAISO data in particular is striking because California's solar ramp is so dramatic -- the visualization immediately tells a story about renewable energy's daily cycle. The "best time to charge" advice, while simple, feels genuinely novel for a free tool.

**Data quality vs. expectations**: The data is high quality and authoritative. The lag is the only significant limitation, and it is inherent to how ISOs report to the EIA.

## Viability Verdict

**PROMISING** -- the "when to charge" advice is genuinely useful, and the visualization is compelling. The main concern is engagement frequency: this may be a "check once a day" tool rather than something with high daily active usage. Integration with smart home devices or EV charging APIs could transform it from informational to automated, but that is a significant engineering lift.

## Next Steps

If pursuing further:
- Add server-side caching (15-30 minute TTL) to reduce EIA API calls and improve response times.
- Build push notifications: "Your grid is under 200 gCO2/kWh right now -- good time to charge."
- Integrate with smart home APIs (Home Assistant, SmartThings) or EV charging APIs (Tesla, ChargePoint) for automated scheduling.
- Add electricity price data (where available from ISOs) alongside carbon intensity, since cost is a stronger motivator for most people than carbon.
- Implement historical trend views to show how the grid has gotten cleaner over time.
- Add a "carbon savings calculator" that estimates the CO2 difference between charging at the best vs. worst time.
