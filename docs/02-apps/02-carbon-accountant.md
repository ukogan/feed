# Personal Carbon Accountant

The Personal Carbon Accountant is the flagship feature within the energy-grid app. It connects personal electricity usage patterns to actual grid fuel mix data, showing users exactly how dirty or clean their specific electricity was, hour by hour.

## How It Works

The core idea: electricity from the grid is not uniformly "clean" or "dirty." At 2pm in California, the grid may be 60% solar. At 8pm, it may be 70% natural gas. The Carbon Accountant maps a user's hourly consumption against the actual generation mix to compute their personal carbon footprint -- and then recommends how to shift usage to cleaner hours.

### Input: Usage Profile

The user provides a 24-element array representing their hourly electricity consumption in kWh (one value per hour of the day, from midnight to 11pm).

Three ways to provide a profile:

1. **Preset profiles** -- choose from built-in archetypes
2. **Manual entry** -- adjust sliders for each hour
3. **Green Button XML upload** -- import real smart meter data

### Processing Pipeline

1. Fetch 7 days of fuel mix data from the EIA API for the selected ISO
2. Build an hourly carbon intensity map (gCO2/kWh) from the fuel mix
3. Multiply each hour's usage by that hour's carbon intensity
4. Compute an optimized schedule that shifts flexible load to the lowest-carbon hours
5. Return the carbon breakdown, optimization potential, and savings estimate

### Output

- Hourly carbon emissions breakdown (green vs. brown kWh)
- Total CO2 produced over the analysis period
- Optimized schedule showing where to shift usage
- Savings potential in CO2 and estimated cost

## Preset Usage Profiles

Four built-in profiles approximate common household patterns:

| Profile | Daily kWh | Pattern |
|---------|-----------|---------|
| Average Household | ~30 | Low overnight baseline, morning ramp, evening peak |
| EV Owner | ~45 | Heavy overnight charging (3.5 kWh/hr midnight-5am) |
| Work From Home | ~35 | Elevated daytime usage from computing and HVAC |
| 9-5 Worker | ~28 | Morning and evening peaks, low midday (away at work) |

Each profile is defined as 24 hourly kWh values in `services/carbon_accountant.py`.

## Green Button XML Support

Green Button is a US Department of Energy standard that allows utility customers to download their smart meter data in XML format. Many US utilities support Green Button data export.

The parser (`services/green_button.py`) handles:

- ESPI (Energy Services Provider Interface) namespace variations
- Both prefixed and bare XML namespaces
- `IntervalReading` extraction with start time and duration
- Unit of measure conversion (Wh to kWh via `powerOfTenMultiplier`)
- Aggregation of interval readings into a 24-hour hourly profile

### Upload Flow

1. User uploads an XML file via the `/api/carbon-account/upload` endpoint
2. Parser validates the file (must be XML, max 10 MB)
3. Readings are extracted, converted to kWh, and aggregated by hour of day
4. The resulting 24-hour profile is returned for use with the carbon analysis

### Known Limitation

The `powerOfTenMultiplier` field in Green Button XML is inconsistently populated across utilities. Some utilities omit it, some set it to 0, and some set it to values that produce implausible readings. The parser applies heuristics to handle common cases but may misinterpret unusual files.

## API Endpoints

### `POST /api/carbon-account`

Analyze personal carbon footprint from a usage profile.

```json
{
  "iso": "CISO",
  "usage_profile": [0.6, 0.5, 0.4, ...],
  "period_days": 7
}
```

The `usage_profile` must have exactly 24 values. The `iso` defaults to `"CISO"` (California ISO).

### `GET /api/carbon-account/presets`

Returns the preset usage profiles.

### `GET /api/carbon-account/demo?iso=CISO`

Runs a demo analysis using the Average Household profile. Useful for testing without providing a custom profile.

### `POST /api/carbon-account/upload`

Accepts a Green Button XML file upload and returns the parsed hourly usage profile.

## Technical Implementation

The carbon intensity calculation uses emission factors per fuel type (defined in `services/carbon.py`). Each fuel type (natural gas, coal, nuclear, solar, wind, etc.) has a known gCO2/kWh factor. The fuel mix at each hour determines the grid's blended carbon intensity.

The optimization algorithm identifies the lowest-carbon hours in the day (based on 7-day average patterns) and suggests shifting flexible load (EV charging, laundry, dishwasher) to those windows.

## Next Steps

- [App Catalog](01-app-catalog.md) -- overview of all apps
- [Data Sources](../04-data-sources/01-free-public-apis.md) -- EIA API reference
