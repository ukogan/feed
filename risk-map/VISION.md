# Risk Map -- Vision Document

## Origin

California faces two major natural hazards -- earthquakes and wildfires -- that are top of mind for homebuyers, renters, and insurance companies. The USGS publishes earthquake data. Cal Fire and NIFC publish fire perimeters. The National Weather Service publishes fire weather alerts. Nobody combines all three into a single risk view. The concept is a unified natural hazard map for California.

## Market Opportunity

- **Who needs this**: California homebuyers (a very large market), insurance companies assessing risk, emergency preparedness planners, renters evaluating neighborhoods, real estate agents providing risk context to clients.
- **Evidence of demand**: California has 40 million residents and natural hazard risk is a constant concern. Insurance companies are withdrawing from the California market due to wildfire risk, making risk awareness a consumer necessity. Every significant earthquake or fire season drives massive search traffic for risk information.
- **Competitive landscape**: USGS provides earthquake maps. Cal Fire provides fire hazard severity zone maps. NWS provides fire weather alerts. No tool overlays all three on a single map with a consumer-friendly interface. First Street Foundation provides flood and fire risk scores but charges for data.

## Data Sources

- **USGS Earthquake Hazards API** (https://earthquake.usgs.gov/fdsnws/event/1/): Free, no key required. Real-time earthquake data with configurable date range and magnitude filter. Updated within minutes of detection.
- **NIFC Wildland Fire Perimeters** (via ArcGIS at https://services3.arcgis.com/): Free, no key required. Active fire perimeter polygons updated every approximately 5 minutes during fire season.
- **NWS Weather Alerts API** (https://api.weather.gov/alerts/): Free, no key required (User-Agent header required). Real-time fire weather watches and red flag warnings.

**Coverage and limitations**: Earthquake data is excellent -- the USGS API is one of the best government APIs. Fire perimeter data from NIFC is active-fires-only; it shows current burn areas but not historical fire scars or prospective fire risk zones. Fire weather alerts are transient and only exist when issued. Outside of fire season, the fire data layers may show nothing.

**Data freshness**: All three sources are queried in real-time on each request. The risk summary endpoint aggregates 30-day earthquake activity, current active fires, and active fire weather alerts.

## MVP Assessment

**What works well**: The earthquake visualization is compelling by itself. Querying 365 days of California earthquakes returns 2,000+ events that beautifully trace the major fault lines. The combined risk summary (earthquake count, max magnitude, active fires, fire acres, fire weather alerts) gives a quick snapshot. Three independent data sources combine gracefully with independent error handling.

**What doesn't work or is limited**: Fire perimeter data is seasonal -- during non-fire months, the fire layer may be empty, which makes the "combined risk" framing feel incomplete. The app is California-specific, which limits the addressable market. There is no persistent risk scoring by location -- it shows current conditions, not long-term risk assessment.

**Key surprises**: The earthquake visualization alone is worth the price of admission. Seeing a year of earthquakes plotted on a map immediately reveals fault structures that are invisible on a static map. The number of M1+ earthquakes in California (often 2,000+ per year) surprises most people.

**Data quality vs. expectations**: Earthquake data exceeded expectations in both quality and visual impact. Fire perimeter data is good when fires are active but empty otherwise, which was expected but still limits the product. Fire weather alerts work as designed.

## Viability Verdict

**STRONG** for California -- the earthquake visualization alone is compelling, and the combined hazard view is genuinely novel. The seasonal nature of fire data is a limitation but not fatal, since earthquake data provides year-round value. Expanding to include historical fire perimeters and prospective fire risk zones (using Cal Fire's Fire Hazard Severity Zone data) would make the fire layer useful year-round.

## Next Steps

If pursuing further:
- Add Cal Fire's Fire Hazard Severity Zone data to show prospective fire risk year-round, not just active fires.
- Integrate historical fire perimeters to show "this area burned in 2020."
- Add a location-specific risk report: enter an address and get earthquake proximity, fire risk zone, and historical fire/quake activity.
- Expand beyond California to other high-risk states (Oklahoma for earthquakes, Pacific Northwest for both).
- Add insurance context: link risk data to insurance availability and pricing trends.
- Build a notification system: "Red flag warning issued for your area" or "M4+ earthquake within 50 miles."
