# CA State Controller: ByTheNumbers

## What this is

The California State Controller's Office publishes standardized financial data for every city, county, special district, and transit operator in the state via a Socrata-powered open data platform. Data goes back ~20 years (FY 2002-03 through 2023-24). This is the single best source for comparing government spending across California jurisdictions.

## Base URL

```
https://bythenumbers.sco.ca.gov
```

Sub-portals:
- Cities: `bythenumbers.sco.ca.gov`
- Counties: `counties.bythenumbers.sco.ca.gov`
- Special Districts: `districts.bythenumbers.sco.ca.gov`
- Transit: `transit.bythenumbers.sco.ca.gov`
- Property Tax: `propertytax.bythenumbers.sco.ca.gov`
- Roads/Streets: `roads.bythenumbers.sco.ca.gov`, `streets.bythenumbers.sco.ca.gov`
- Retirement: `retirement.bythenumbers.sco.ca.gov`

## Authentication

None. Fully public. No API key required.

## Rate limits

Standard Socrata limits. No published cap but be polite (~1 req/sec).

## Key datasets

### City Expenditures
- **Socrata ID**: `ju3w-4gxp`
- **Endpoint**: `https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json`
- **Columns**: `fiscal_year`, `county`, `entity_name`, `category`, `subcategory_1`, `subcategory_2`, `line_description`, `value`, `estimated_population`
- **Categories include**: Public Safety, Transportation, Community Development, Health, Culture & Leisure, General Government, Utilities, Debt Service

### City Expenditures Per Capita
- **Socrata ID**: `ykhf-vfsr`

### City Pension Data
- **Socrata ID**: `83vk-3ee7`
- **Years**: 2021-2024

### Special District Expenditures
- **Socrata ID**: `m9u3-wdam`

## How to query (SODA API)

Filter by city:
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json?entity_name=Redwood City
```

Filter by city and year:
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json?entity_name=Redwood City&fiscal_year=2022-2023
```

Filter by category:
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json?entity_name=Redwood City&category=Public Safety
```

SoQL query (SQL-like):
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json?$where=entity_name='Redwood City' AND fiscal_year='2022-2023'&$order=value DESC&$limit=50
```

Compare two cities:
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json?$where=entity_name in ('Redwood City','Mountain View') AND fiscal_year='2022-2023'&$order=entity_name,category
```

Bulk CSV download:
```
GET https://bythenumbers.sco.ca.gov/api/views/ju3w-4gxp/rows.csv?accessType=DOWNLOAD
```

## What to do with it

### Basic city spending profile
Query all expenditures for a city and fiscal year. Group by `category` to see the top-level breakdown (Public Safety, Transportation, etc.). Drill into `subcategory_1` and `subcategory_2` for detail.

### Multi-year trend
Query the same city across all fiscal years. Plot spending by category over time. Identify where growth is fastest (usually: public safety personnel costs and pension contributions).

### City comparison
Pull the same fiscal year for multiple similar-sized cities. Compare per-capita spending by category. Identify outliers: "Redwood City spends 40% more per capita on public safety than Mountain View. Why?"

### Pension burden
Use the pension dataset (`83vk-3ee7`) to see employer pension contributions as a share of total spending. Compare across cities.

## Gotchas

- `fiscal_year` is a string like `"2022-2023"`, not a number
- `value` is the dollar amount but may be stored as a string in some responses — cast to float
- Some line items have negative values (transfers, offsets)
- City names must match exactly (case-sensitive in some queries): use `"Redwood City"` not `"redwood city"`
- Not all cities report every year — check for gaps
- Special districts use a different dataset ID than cities
- The data reflects what cities REPORTED to the SCO, which may differ from their own budget documents due to reporting standards

## Example: Quick spending profile

```python
import httpx

async def get_city_spending(city: str, year: str = "2022-2023"):
    url = "https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json"
    params = {
        "$where": f"entity_name='{city}' AND fiscal_year='{year}'",
        "$order": "value DESC",
        "$limit": 200,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        return resp.json()
```
