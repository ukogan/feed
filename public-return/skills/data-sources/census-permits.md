# Census Bureau Building Permits Survey

## What this is

The U.S. Census Bureau's Building Permits Survey (BPS) tracks new privately-owned residential construction permits issued by ~20,100 permit-issuing jurisdictions nationwide. Data is available at the place (city), county, CBSA (metro area), state, and national levels, going back to 1980+. This is the best leading indicator of development activity -- permits precede construction by 6-18 months.

## Base URL

```
https://www.census.gov/construction/bps/
```

Main landing page:
```
https://www.census.gov/permits
```

## Data download (Place-level ASCII files)

The place-level data lives here:
```
https://www2.census.gov/econ/bps/Place/
```

Files are organized by Census region:
- `Place/West Region/` -- California is here (region code 4, division code 9 "Pacific")
- `Place/South Region/`
- `Place/Midwest Region/`
- `Place/Northeast Region/`

### File naming convention

| Type | Pattern | Example | Description |
|------|---------|---------|-------------|
| Annual summary | `<Region><YYYY>A.TXT` | `WE2024A.TXT` | Full-year totals for all places |
| Annual revised | `<Region><YYYY>R.TXT` | `WE2024R.TXT` | Monthly breakdowns for the year |
| Current month | `<Region><YYMM>C.TXT` | `WE2601C.TXT` | Single month data |
| Year-to-date | `<Region><YYMM>Y.TXT` | `WE2601Y.TXT` | Cumulative Jan through month |
| Monthly cumulative | `<Region><YYMM>R.TXT` | `WE2601R.TXT` | Monthly records with corrections |

Region codes: `NE` (Northeast), `MW` (Midwest), `SO` (South), `WE` (West)

### Other geographic levels

```
https://www2.census.gov/econ/bps/County/    -- county-level
https://www2.census.gov/econ/bps/CBSA/      -- metro area (2024+)
https://www2.census.gov/econ/bps/State/     -- state-level
```

Documentation:
```
https://www2.census.gov/econ/bps/Documentation/placeasc.pdf
```

## Authentication

None. Fully public. No API key required.

## File format

ASCII comma-delimited text files. No header row -- use the record layout below.

### Annual file record layout (Attachment B from placeasc.pdf)

| Field | Description |
|-------|-------------|
| 1 | Survey Date (YYYYMM, annual = YYYY99) |
| 2 | FIPS state code (2-digit; California = 06) |
| 3 | Building Permit Survey ID (6-digit, alphabetical sort key) |
| 4 | FIPS county code (3-digit; San Mateo = 081) |
| 5 | Census Place code (4-digit) |
| 6 | FIPS Place code (5-digit; Redwood City = 60102) |
| 7 | FIPS MCD code (5-digit) |
| 8 | 2000 Population |
| 9 | CSA code (3-digit, or 999) |
| 10 | CBSA code (5-digit, or 99999) |
| 11 | Footnote code (blank or 2) |
| 12 | Central City flag (blank or 1) |
| 13 | Zip Code of permit office |
| 14 | Census Region code (4 = West) |
| 15 | Census Division code (9 = Pacific) |
| 16 | Number of Months Reported |
| 17 | Place Name |

**Permit data fields (repeated for 4 structure types):**

| Structure Type Code | Meaning |
|---------------------|---------|
| 101 | 1-unit (single family) |
| 103 | 2-units (duplex) |
| 104 | 3-4 units |
| 105 | 5+ units (apartments/condos) |

For each structure type, three values:
- **Buildings**: Number of buildings permitted
- **Units**: Number of housing units permitted
- **Valuation**: Construction valuation in dollars ($1,000s)

Annual files have TWO sets of these 12 fields:
- Fields 18-29: Estimates with imputation (includes imputed data for non-reporters)
- Fields 30-41: Reported only (only actual reported data)

## How to query

### Download and parse annual California place data

```python
import csv
import io
import httpx

async def get_ca_permits(year: int = 2024):
    """Download annual place-level permits for the West region, filter to California."""
    url = f"https://www2.census.gov/econ/bps/Place/West%20Region/we{year}a.txt"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()

    reader = csv.reader(io.StringIO(resp.text))
    results = []
    for row in reader:
        if len(row) < 29:
            continue
        fips_state = row[1].strip()
        if fips_state != "06":  # California
            continue
        results.append({
            "survey_date": row[0].strip(),
            "fips_state": fips_state,
            "fips_county": row[3].strip(),
            "fips_place": row[5].strip(),
            "place_name": row[16].strip(),
            "single_family_bldgs": int(row[17]) if row[17].strip() else 0,
            "single_family_units": int(row[18]) if row[18].strip() else 0,
            "single_family_val": int(row[19]) if row[19].strip() else 0,
            "duplex_units": int(row[21]) if row[21].strip() else 0,
            "three_four_units": int(row[24]) if row[24].strip() else 0,
            "five_plus_units": int(row[27]) if row[27].strip() else 0,
            "five_plus_val": int(row[28]) if row[28].strip() else 0,
        })
    return results


def filter_by_county(permits: list, county_fips: str = "081") -> list:
    """Filter to a specific county (081 = San Mateo County)."""
    return [p for p in permits if p["fips_county"] == county_fips]


def filter_by_place(permits: list, place_name: str = "Redwood City") -> list:
    """Filter to a specific city by name (case-sensitive partial match)."""
    return [p for p in permits if place_name.lower() in p["place_name"].lower()]
```

### Multi-year trend

```python
async def permits_trend(place_name: str, start_year: int = 2015, end_year: int = 2024):
    """Get permits for a city across multiple years."""
    trend = []
    for year in range(start_year, end_year + 1):
        permits = await get_ca_permits(year)
        city = filter_by_place(permits, place_name)
        if city:
            c = city[0]
            total_units = (c["single_family_units"] + c["duplex_units"]
                          + c["three_four_units"] + c["five_plus_units"])
            trend.append({"year": year, "total_units": total_units, **c})
    return trend
```

## Key FIPS codes for San Mateo County

| City | FIPS Place Code |
|------|----------------|
| Redwood City | 60102 |
| San Mateo | 68252 |
| Daly City | 17918 |
| South San Francisco | 73262 |
| San Carlos | 65028 |
| Menlo Park | 46870 |
| Foster City | 25338 |
| Belmont | 05108 |
| San Bruno | 65070 |
| Half Moon Bay | 31708 |

San Mateo County FIPS: `06081`
CBSA (San Francisco-Oakland-Berkeley): `41860`

## What questions this answers

- How many housing units were permitted in my city last year?
- What is the mix of single-family vs. multi-family construction?
- Is development activity accelerating or declining?
- How does my city's permitting compare to neighboring cities?
- What is the dollar value of new construction?
- Are there any years with unusual spikes (large apartment projects)?
- Is the city meeting its RHNA housing production targets?

## Combining with other data

- **SCO ByTheNumbers**: Compare cities that permit a lot of housing vs. their spending patterns. New development generates revenue (property tax, fees) but also requires services.
- **Property Tax data**: New construction adds to the property tax roll. Compare permits to assessed value growth.
- **Population data**: Compare housing production to population growth. Are cities keeping up?
- **RHNA targets**: Compare actual permits to ABAG/HCD Regional Housing Needs Allocation targets.

## Gotchas

- Files have NO header row -- use the field layout above
- Valuation is in thousands of dollars (multiply by 1,000 for actual dollar value, though some years may be actual dollars -- verify against known totals)
- Place names may have footnote suffixes like `#`, `(N)`, `@1` -- strip these before matching
- `(N)` means the place was added after the 2004 universe was established; its data is NOT included in summary statistics
- Source code 5 = imputed data (no report received) -- be cautious with these
- Not all jurisdictions issue permits (some unincorporated areas permit through the county)
- The 2000 Population field is frozen at Census 2000 values -- do not use for current per-capita calculations
- Annual data is typically released the first workday of May for the prior year
- Files for different years may have slightly different formatting -- always validate row length
- The "Reported and Imputed" data (fields 18-29) is what you usually want for analysis; "Reported Only" (fields 30-41) excludes imputed values for non-reporters
