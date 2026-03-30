# Transparent California: Public Employee Compensation

## What this is

Transparent California is the state's largest public-sector compensation database, containing pay and pension data for ~2.7 million employees across 2,518 agencies, plus 1.4 million pension records from 54 pension plans. Data is obtained via California Public Records Act requests and covers cities, counties, state agencies, school districts, special districts, and UC/CSU systems. Total records: ~42 million.

This is the best source for individual employee compensation data. For official aggregate compensation data, also consider the State Controller's GCC site (see below).

## URLs

### Transparent California
```
https://transparentcalifornia.com
```

Browse by year: `https://transparentcalifornia.com/salaries/2024/`
Browse by agency: `https://transparentcalifornia.com/salaries/redwood-city/`
Browse by year + agency: `https://transparentcalifornia.com/salaries/2024/redwood-city/`

### State Controller's GCC (Government Compensation in California)
```
https://publicpay.ca.gov
```

This is the official state government source with similar data, published by the State Controller's Office. CSV bulk downloads are available.

## Authentication

None for either site. Both are fully public.

## Data fields

### Transparent California

| Field | Description |
|-------|-------------|
| Employee Name | Full name |
| Job Title | Position title |
| Base Pay | Regular salary/wages |
| Overtime Pay | Overtime compensation |
| Other Pay | Bonuses, stipends, special pay, etc. |
| Total Pay | Base + Overtime + Other |
| Benefits | Employer-paid benefits (health, dental, pension contributions, etc.) |
| Total Pay & Benefits | Total compensation including employer benefit costs |
| Pension Debt | Pro-rated share of agency's unfunded pension liability per employee |
| Status | Full-time or Part-time (PT) |

### GCC (publicpay.ca.gov)

CSV downloads available at:
```
https://publicpay.ca.gov/reports/rawexport.aspx
```

Data dictionary:
```
https://publicpay.ca.gov/Reports/DataDictionary.aspx
```

GCC files are comma-delimited CSV inside ZIP archives, updated every weekday morning. They cover ~2 million positions at 5,000+ employers.

**Employer types in GCC**: State Departments, Cities, Counties, Special Districts, K-12 Education, Community Colleges, CSU, UC, Courts, First 5, Fairs & Expos.

Key GCC fields include: Entity Name, Entity Type, Department/Subdivision, Position Title, Elected Official flag, Total Wages, Regular Pay, Overtime Pay, Lump Sum Pay, Other Pay, Defined Benefit Plan Contribution, Employees Retirement Cost Covered, Deferred Compensation Plan, Health/Dental/Vision, and more.

## How to access data

### Transparent California (web scraping + CSV)

Transparent California does not have a public API. Data access methods:

1. **Website search**: Browse and search at transparentcalifornia.com
2. **CSV download**: Individual agency/year pages have a download button for CSV export
3. **Web scraping**: Parse the search results pages programmatically

```python
import httpx
from bs4 import BeautifulSoup

async def search_transparent_ca(agency_slug: str, year: int = 2024):
    """
    Download compensation data from Transparent California.
    agency_slug examples: 'redwood-city', 'state-of-california',
    'san-mateo-county', 'sequoia-union-high-school-district'
    """
    url = f"https://transparentcalifornia.com/salaries/{year}/{agency_slug}/"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        # The page lists employees in a table
        # Look for a CSV download link on the page
        # Typical pattern: /export/{agency_slug}/?year={year}
        return resp.text
```

### GCC bulk download

```python
import httpx
import zipfile
import csv
import io

async def download_gcc_data(employer_type: str = "cities", year: int = 2024):
    """
    Download GCC compensation data.
    employer_type: 'state', 'cities', 'counties', 'specialdistricts',
                   'k12education', 'communitycolleges', 'csu', 'uc', 'courts'
    """
    # The raw export page provides ZIP files containing CSV data
    # URL pattern (approximate -- verify on the raw export page):
    url = f"https://publicpay.ca.gov/reports/rawexport.aspx"
    # Download the ZIP for the desired employer type and year
    # Extract and parse the CSV
    pass
```

### Agency slugs for San Mateo County area

| Agency | Transparent CA Slug |
|--------|-------------------|
| Redwood City | `redwood-city` |
| San Mateo County | `san-mateo-county` |
| City of San Mateo | `san-mateo` |
| Menlo Park | `menlo-park` |
| San Carlos | `san-carlos` |
| Sequoia Union HSD | `sequoia-union-high-school-district` |
| Redwood City Elementary | `redwood-city-elementary-school-district` |

## What questions this answers

- What is the total compensation (pay + benefits) for employees at a specific agency?
- How much overtime does the police/fire department consume?
- What are the highest-paid positions and how do they compare across cities?
- What is the average total compensation by department?
- How much does the city spend on health/dental/vision benefits per employee?
- What is the per-employee pension contribution, and how does it compare to base pay?
- How has total compensation grown over time?
- What percentage of employees earn over $200K in total comp?

## Combining with other data

- **SCO ByTheNumbers**: Compare aggregate spending categories to individual compensation data. If Public Safety is 60% of the budget, what does the employee-level data show?
- **CalPERS pension data**: Cross-reference pension contribution rates with per-employee pension costs from Transparent California.
- **Census permits**: Compare cities with high development activity to their staffing levels. Are fast-growing cities hiring proportionally?

## Analysis patterns

### Compensation distribution by department

Download all employees for a city/year, group by department (from job title keywords: "Police", "Fire", "Public Works", etc.), and compute median/mean total compensation per department. Public safety departments typically have 2-3x the total comp of general government roles due to overtime and pension benefits.

### Pension burden per employee

Transparent California's "pension debt" column prorates the agency's unfunded pension liability across employees. This shows the true cost beyond what appears in the regular benefits column.

### Year-over-year growth

Download multiple years for the same agency and track growth in median total compensation. Compare to CPI to see real wage growth. Pension and benefit costs typically grow faster than base pay.

## Gotchas

- Transparent California has no official API -- scraping may break if they change their site structure
- The GCC site (publicpay.ca.gov) blocks automated access (403 errors) -- use their official CSV download page
- Employee names on Transparent California are public record but may raise privacy concerns in some contexts
- "Other Pay" is a catch-all that includes very different things (housing allowances, car allowances, special assignment pay, certification pay)
- Part-time employees are marked "PT" in downloads but may appear to have low pay without that context
- The "Benefits" column is employer cost, not employee take-home -- it includes the employer's pension contribution, health insurance premium, etc.
- Different agencies report to different systems: cities/counties report to GCC, but Transparent California may have more granular data obtained directly via PRA requests
- Transparent California's "pension debt" metric is their own calculation, not an official government figure
- Data availability varies by agency and year -- some agencies have data back to 2009, others only recent years
- GCC data is calendar year; some agency budget data is fiscal year -- be careful when joining
- Lump Sum Pay in GCC includes one-time payouts like excess vacation/sick leave cashouts -- these inflate single-year totals
