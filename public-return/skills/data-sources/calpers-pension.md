# CalPERS Pension Data

## What this is

The California Public Employees' Retirement System (CalPERS) is the largest public pension fund in the US, managing retirement benefits for ~2 million members across ~3,000 public employers. CalPERS publishes actuarial valuation reports for every contracting public agency, disclosing funded status, unfunded liabilities, and required employer contribution rates. This data is critical for understanding how much of a city's budget is consumed by pension obligations.

**Important**: San Mateo County employees (including the county itself) are NOT in CalPERS. They use SamCERA (San Mateo County Employees' Retirement Association). Cities within San Mateo County (Redwood City, San Mateo, etc.) ARE in CalPERS. See the SamCERA section at the bottom.

## Data sources

### 1. Summary Valuation Results (Interactive Tool)

The primary way to access and compare pension data across agencies.

```
https://www.calpers.ca.gov/employers/actuarial-resources/summary-valuation-results-overview
```

Full-window tool:
```
https://www.calpers.ca.gov/employers/actuarial-resources/summary-valuation-results-overview/summary-valuation-full-window
```

**What it provides**: Funded ratios, contribution rates, accrued liabilities, market value of assets, unfunded accrued liability (UAL), and employer contribution requirements for every CalPERS-contracting public agency.

**Filters**: By agency name, CalPERS ID, entity type (city, county, special district, school), and county.

**Download**: The tool supports data export. A User Manual (PDF, 5 MB) is available at calpers.ca.gov.

### 2. Individual Agency Valuation Reports (PDF)

Full actuarial valuation reports for each agency, organized by CalPERS ID, name, type, and county.

```
https://www.calpers.ca.gov/employers/actuarial-resources/public-agency-actuarial-valuation-reports
```

The latest three years of reports are available. The June 30, 2023 valuations set contribution rates for FY 2025-26.

### 3. SCO ByTheNumbers - City Pension Dataset

The State Controller also publishes pension data reported by cities.

- **Socrata ID**: `83vk-3ee7`
- **Endpoint**: `https://bythenumbers.sco.ca.gov/resource/83vk-3ee7.json`
- **Years**: 2021-2024

## Authentication

None. All data is public. No API key required.

## Key data fields (from valuation reports)

| Field | Description |
|-------|-------------|
| Accrued Liability | Total present value of benefits earned to date |
| Market Value of Assets (MVA) | Current market value of the pension fund's assets |
| Unfunded Accrued Liability (UAL) | Accrued Liability minus MVA -- the pension "debt" |
| Funded Ratio | MVA / Accrued Liability (e.g., 75% = 25% underfunded) |
| Employer Normal Cost Rate | % of payroll for benefits accruing in the current year |
| UAL Amortization Payment | Annual dollar payment to pay down the unfunded liability |
| Total Employer Contribution Rate | Normal Cost Rate + UAL payment as % of payroll |
| Member Count | Active, transferred, separated, and retired members |
| Payroll | Covered payroll used for rate calculations |

## How to query

### SCO pension data via SODA API

```python
import httpx

async def get_city_pension_data(city: str, year: str = "2023-2024"):
    """Get pension contribution data from SCO ByTheNumbers."""
    url = "https://bythenumbers.sco.ca.gov/resource/83vk-3ee7.json"
    params = {
        "$where": f"entity_name='{city}' AND fiscal_year='{year}'",
        "$limit": 100,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        return resp.json()
```

### Downloading a specific agency valuation report

The valuation reports page supports filtering by county. For San Mateo County cities:
1. Go to the Public Agency Actuarial Valuation Reports page
2. Filter by County = "San Mateo"
3. Download individual PDF reports for each plan (Miscellaneous and Safety are separate plans)

### Using the Summary Valuation Results tool

The interactive tool (Tableau-based) does not have a direct API. To get data programmatically:
1. Use the tool to filter and export CSV/Excel
2. Or query the SCO ByTheNumbers pension dataset via SODA API (above)

## What questions this answers

- What is the funded ratio of my city's pension plan? (How deep is the hole?)
- How much of each payroll dollar goes to pension costs?
- What is the city's total unfunded pension liability?
- How do pension costs compare across similar cities?
- Is the pension situation improving or getting worse over time?
- How much of the city budget goes to paying down past pension debt vs. current benefits?

## Combining with spending data

The real power is in the ratio: pull total city expenditures from SCO ByTheNumbers (`ju3w-4gxp`), pull pension contributions from the pension dataset (`83vk-3ee7`), and compute pension costs as a percentage of total spending. This answers: "What share of every tax dollar goes to pensions?"

For deeper analysis, combine with Transparent California compensation data to see per-employee pension costs and how they vary by department.

## CalPERS plan types

Most cities have two CalPERS plans:
- **Miscellaneous**: Non-safety employees (admin, planning, public works, etc.)
- **Safety**: Police and fire employees (higher benefits, higher costs)

PEPRA (2013 reform) created lower-cost tiers for employees hired after January 1, 2013, but Classic members (pre-PEPRA) still dominate costs at most agencies.

## SamCERA (San Mateo County)

San Mateo County and its direct employees use SamCERA, not CalPERS.

```
https://www.samcera.org/actuarial-valuations
```

- As of June 30, 2024: funded ratio of 87.6%, total fund value of $6.73 billion
- SamCERA publishes Annual Comprehensive Financial Reports (ACFR) and triennial actuarial experience studies
- Financial reports: `https://www.samcera.org/financial-reports`

SamCERA's funded ratio (87.6%) is significantly higher than the average CalPERS agency statewide (~68%), which is important context when comparing San Mateo County to other counties.

## Gotchas

- CalPERS valuation reports are PDFs, not structured data -- you need the Summary Valuation Results tool or SCO dataset for machine-readable data
- Valuations have a 2-year lag: June 30, 2023 valuation sets FY 2025-26 rates
- "Funded ratio" can be calculated on a market value basis or actuarial value basis -- these differ, sometimes substantially
- Each city may have multiple plans (Miscellaneous, Safety, sometimes separate tiers)
- Small cities may be in CalPERS risk pools rather than having standalone plans -- their funded ratio reflects the pool, not their individual experience
- Employer contribution rates are expressed as a percentage of payroll PLUS a fixed dollar UAL payment -- both components matter
- San Mateo County (SamCERA) and UC system (UCRS) are separate from CalPERS
- The SCO pension dataset (`83vk-3ee7`) only covers 2021-2024; for older data, use the valuation reports
