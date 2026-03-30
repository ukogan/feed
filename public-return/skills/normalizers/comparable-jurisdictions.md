# Normalizer: Comparable Jurisdiction Methodology

## What this does

Defines how to find a defensible set of "peer" jurisdictions for any California city, county, or school district. Comparisons are the backbone of Public Return -- they turn raw numbers into meaning ("Redwood City spends $900/capita on public safety" means nothing until you know the range is $500-$1,200 for similar cities). This skill ensures peer groups are honest, not cherry-picked.

## Why this is hard

No two jurisdictions are truly comparable. The goal is to control for the variables that most explain spending differences, so the remaining variation reflects actual policy choices. The top confounders are:

1. **Population/enrollment size** -- Economies of scale matter. A city of 5,000 and a city of 500,000 cannot be compared.
2. **Income/wealth** -- Wealthier communities generate more revenue and have different service expectations.
3. **Demographics** -- Age, race/ethnicity, poverty rate, and English learner percentage drive both service demand and outcomes.
4. **Geography/region** -- Cost of living, labor markets, and climate affect what things cost.
5. **Governance structure** -- What services an entity provides (own police vs. contract, own utilities vs. not) determines what shows up in the budget.

## Data sources for comparison metrics

| Metric | Source | How to Get It |
|--------|--------|---------------|
| Population | Census ACS 5-year | `api.census.gov` -- Table B01003 |
| Median household income | Census ACS 5-year | Table B19013 |
| % below poverty | Census ACS 5-year | Table B17001 |
| Racial/ethnic composition | Census ACS 5-year | Table B03002 |
| Median home value | Census ACS 5-year | Table B25077 |
| City revenue per capita | SCO ByTheNumbers | Revenue dataset |
| City expenditure per capita | SCO ByTheNumbers | `ju3w-4gxp` with `estimated_population` |
| School enrollment (ADA) | CDE SACS | ADA field in SACS data |
| % socioeconomically disadvantaged | CDE DataQuest | FRPM (Free/Reduced Price Meals) data |
| % English learners | CDE DataQuest | EL enrollment data |
| Assessed valuation | County assessor or BOE | AV per capita or per ADA |
| Services provided | SCO ByTheNumbers | Presence/absence of utility, hospital, transit categories |

### Census ACS API

```python
import httpx

async def get_city_demographics(state_fips: str = "06", place_fips: str = None):
    """Pull key demographic indicators from Census ACS 5-year."""
    base = "https://api.census.gov/data/2024/acs/acs5"
    variables = [
        "B01003_001E",  # Total population
        "B19013_001E",  # Median household income
        "B25077_001E",  # Median home value
        "B17001_002E",  # Population below poverty
        "B17001_001E",  # Population for whom poverty status is determined
    ]
    params = {
        "get": ",".join(variables),
        "for": f"place:{place_fips}" if place_fips else "place:*",
        "in": f"state:{state_fips}",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(base, params=params)
        return resp.json()
```

Note: Census API requires no key for small queries. For bulk use, register at `api.census.gov/data/key_signup.html`. The 2020-2024 ACS 5-year estimates are the most recent available.

### CA Department of Finance Population Estimates

DOF provides the most current city/county population estimates in California, more current than ACS (updated annually, January 1 estimates released each May).

Download page:
```
https://dof.ca.gov/forecasting/demographics/estimates/
```

E-4 (cities, counties, state, 2021-2025):
```
https://dof.ca.gov/forecasting/demographics/estimates/e-4-population-estimates-for-cities-counties-and-the-state-2021-2025-with-2020-census-benchmark/
```

Ranked cities 2025 (Excel):
```
https://dof.ca.gov/media/docs/forecasting/Demographics/estimates-e1/RankCities_2025.xlsx
```

Use DOF for the population denominator in per-capita calculations, not ACS or Census decennial counts.

## Methodology: Cities

### Step 1: Mandatory filters

These are hard constraints -- a city must pass all to be considered comparable:

| Filter | Rule | Rationale |
|--------|------|-----------|
| State | California only | Different states have different governance, so cross-state comparisons are unreliable |
| Population band | 0.33x to 3x target city | Economies of scale make cities of very different sizes incomparable |
| Governance match | Same set of major services provided | Cities that run utilities or hospitals cannot be compared to those that don't without adjustment (see spending-categories normalizer) |

### Step 2: Similarity scoring

For each city passing the mandatory filters, compute a similarity score based on weighted distance:

| Dimension | Weight | Metric | Distance Function |
|-----------|--------|--------|------------------|
| Population | 25% | Total population | `abs(log(pop_a / pop_b))` |
| Income | 25% | Median household income | `abs(income_a - income_b) / avg(income_a, income_b)` |
| Demographics | 20% | % below poverty line | `abs(pov_a - pov_b)` percentage points |
| Geography | 20% | Same metro area / region | 0 = same metro, 0.3 = adjacent, 0.7 = same state region, 1.0 = opposite end of state |
| Home value | 10% | Median home value | `abs(log(value_a / value_b))` |

```python
import math

def city_similarity(target: dict, candidate: dict) -> float:
    """Score 0 (identical) to 1 (maximally different). Lower is more similar."""
    pop_dist = abs(math.log(candidate["population"] / target["population"]))
    inc_dist = abs(candidate["median_income"] - target["median_income"]) / (
        (candidate["median_income"] + target["median_income"]) / 2
    )
    pov_dist = abs(candidate["pct_poverty"] - target["pct_poverty"]) / 100
    geo_dist = geographic_distance(target["region"], candidate["region"])
    val_dist = abs(math.log(candidate["median_home_value"] / target["median_home_value"]))

    return (
        0.25 * min(pop_dist, 1.0) +
        0.25 * min(inc_dist, 1.0) +
        0.20 * min(pov_dist * 5, 1.0) +  # scale: 20pp difference = max
        0.20 * geo_dist +
        0.10 * min(val_dist, 1.0)
    )
```

### Step 3: Select peer group

1. Rank all California cities by similarity score
2. Take the top 8-10
3. Verify that the group is not all from one county (geographic diversity check)
4. Verify that the group includes cities both above and below the target on key metrics (not all richer or all poorer)
5. If fewer than 5 pass the mandatory filters, relax the population band to 0.25x-4x

### Step 4: Structural adjustment

Before comparing spending, adjust for structural differences using the spending-categories normalizer:

- Remove utility enterprise spending for cities that run utilities
- Remove hospital spending for cities that run hospitals
- Note contracted services (police/fire) that shift spending to another entity
- Separate capital projects from operating spending

#### Enterprise fund adjustment

```python
def adjusted_per_capita(city_data: dict, exclude_enterprise: bool = True) -> float:
    """
    Per-capita spending with or without enterprise funds.
    city_data: {total_expenditures, enterprise_fund_expenditures, population}
    """
    if exclude_enterprise:
        operating = city_data["total_expenditures"] - city_data["enterprise_fund_expenditures"]
    else:
        operating = city_data["total_expenditures"]
    return operating / city_data["population"]
```

#### Contract services adjustment

Cities that contract for fire (CalFire, fire district) or police (county sheriff) show lower "Public Safety" spending but pay contract costs that may appear in different budget categories. When comparing:
- Check if city has fire/police departments or contracts
- If contracted, look for contract costs in "Public Safety" or "General Government" subcategories
- Note the contract arrangement in the comparison output

#### School district LCFF adjustment

California's LCFF provides supplemental/concentration grants based on Unduplicated Pupil Percentage (UPP = % EL + % Foster Youth + % SED, unduplicated). High-UPP districts receive more state funding but serve higher-need populations. Do not penalize districts for receiving more funding -- the additional funding is targeted at the additional need.

### Example: Peer group for Redwood City

**Target profile:**
- Population: ~84,000
- Median household income: ~$120,000
- % below poverty: ~7%
- Region: San Francisco-San Jose metro (Peninsula)
- Median home value: ~$1.6M
- Services: Own police, own fire, no utilities

**Population band (0.33x-3x):** 28,000 - 252,000

**Top peers by similarity score:**

| City | Pop | Med Income | % Poverty | Region | Score |
|------|-----|-----------|-----------|--------|-------|
| San Mateo | 105K | $125K | 6% | Peninsula | 0.08 |
| Mountain View | 82K | $135K | 5% | South Bay | 0.10 |
| Santa Clara | 127K | $140K | 6% | South Bay | 0.14 |
| Daly City | 104K | $100K | 8% | Peninsula | 0.15 |
| Milpitas | 80K | $130K | 5% | South Bay | 0.16 |
| Hayward | 162K | $95K | 10% | East Bay | 0.22 |
| Richmond | 116K | $75K | 14% | East Bay | 0.28 |
| Vallejo | 121K | $72K | 16% | North Bay | 0.32 |

Notes:
- Mountain View and Santa Clara run their own utilities -- must adjust their spending totals
- Richmond and Vallejo are more distant peers (lower income, higher poverty) but provide useful "floor" comparison
- All are in the Bay Area, which ensures similar labor cost environment

## Methodology: School Districts

School district comparisons use different dimensions because the "customers" are students, not residents.

### Step 1: Mandatory filters

| Filter | Rule | Rationale |
|--------|------|-----------|
| State | California only | LCFF funding formula is CA-specific |
| District type | Must match (elementary, high, unified) | Grade spans determine cost structures |
| Enrollment band | 0.33x to 3x target ADA | Scale effects are real in education too |

### Step 2: Similarity scoring

| Dimension | Weight | Metric | Source |
|-----------|--------|--------|--------|
| Enrollment | 20% | ADA | CDE SACS |
| % Socioeconomically Disadvantaged | 30% | FRPM % | CDE DataQuest |
| % English Learners | 15% | EL % | CDE DataQuest |
| Geography | 20% | Same county/metro | Manual or geocoding |
| Property wealth | 15% | Assessed value per ADA | County assessor or SACS |

**Demographics get the highest weight** because % SED is the single strongest predictor of test scores (r ~ -0.7 to -0.8). Comparing a 10% SED district to a 60% SED district on test outcomes is meaningless without adjustment.

```python
def district_similarity(target: dict, candidate: dict) -> float:
    """Score 0 (identical) to 1 (maximally different)."""
    enr_dist = abs(math.log(candidate["ada"] / target["ada"]))
    sed_dist = abs(candidate["pct_sed"] - target["pct_sed"]) / 100
    el_dist = abs(candidate["pct_el"] - target["pct_el"]) / 100
    geo_dist = geographic_distance(target["region"], candidate["region"])
    av_dist = abs(math.log(candidate["av_per_ada"] / target["av_per_ada"]))

    return (
        0.20 * min(enr_dist, 1.0) +
        0.30 * min(sed_dist * 3.3, 1.0) +  # scale: 30pp difference = max
        0.15 * min(el_dist * 5, 1.0) +      # scale: 20pp difference = max
        0.20 * geo_dist +
        0.15 * min(av_dist, 1.0)
    )
```

### Step 3: Select peer group

Same process as cities: rank by score, take top 5-8, verify diversity.

### Step 4: Demographic adjustment for outcome comparisons

When comparing test scores, always:
1. Show scores for "All Students" AND for matched subgroups (SED vs. SED, non-SED vs. non-SED)
2. Note the % SED difference between compared districts
3. If % SED differs by more than 15 percentage points, flag the comparison as unreliable for aggregate scores

### Example: Peer group for Redwood City Elementary (41-69005)

**Target profile:**
- Type: Elementary (K-8)
- ADA: ~7,500
- % SED: ~45%
- % EL: ~30%
- County: San Mateo (41)
- Region: Peninsula

**Top peers:**

| District | CDS | ADA | % SED | % EL | Region | Score |
|----------|-----|-----|-------|------|--------|-------|
| Jefferson Elem (Daly City) | 41-68619 | 7,000 | 55% | 35% | Peninsula | 0.12 |
| Sunnyvale Elem | 43-69807 | 6,000 | 40% | 25% | South Bay | 0.14 |
| Mountain View Whisman | 43-69450 | 5,200 | 35% | 28% | South Bay | 0.16 |
| San Mateo-Foster City | 41-68999 | 8,500 | 30% | 20% | Peninsula | 0.19 |
| Campbell Union Elem | 43-69393 | 7,200 | 35% | 15% | South Bay | 0.21 |
| Ravenswood City Elem | 41-69039 | 2,500 | 85% | 50% | Peninsula | 0.38 |

Notes:
- Ravenswood is geographically adjacent but demographically very different (85% SED). Include for local context but flag that aggregate score comparison is not meaningful.
- San Mateo-Foster City is the closest geographic peer but has lower SED -- subgroup-level comparison is more valid than aggregate.

## Methodology: Counties

### Mandatory filters

| Filter | Rule | Rationale |
|--------|------|-----------|
| State | California only | County responsibilities are state-defined |
| Population band | 0.33x to 3x | Scale effects |
| Urban/rural classification | Must match (urban, suburban, rural) | Service delivery models differ fundamentally |

### Similarity scoring

| Dimension | Weight | Metric |
|-----------|--------|--------|
| Population | 25% | Total county population |
| Income | 20% | Median household income |
| Poverty | 20% | % below poverty |
| Urban/rural | 15% | Census urban area percentage |
| Geography | 10% | Same state region |
| Governance complexity | 10% | Number of cities, special districts |

### Structural adjustments for counties

Counties have the most structural variation:

| Structure | Counties With | Counties Without | Impact |
|-----------|--------------|-----------------|--------|
| County hospital | SF, LA, Santa Clara, San Mateo, Alameda | Most others | Massive health spending difference |
| County fire department | LA, Orange | Most (cities run own fire) | Shifts public safety spending |
| Consolidated city-county | SF | All others | SF data conflates city and county functions |
| 1937 Act pension (vs. CalPERS) | LA, SF, San Mateo, Alameda, + others | Most smaller counties | Different pension cost structures |

San Francisco is essentially incomparable to other counties because it is a combined city-county. Always note this.

**Hospital adjustment**: Counties operating hospitals (San Mateo County Medical Center, Santa Clara Valley Medical Center, LAC+USC, etc.) have dramatically higher Health spending. When comparing:
- Note hospital operation status for every county in the comparison
- Consider excluding Hospital Enterprise Fund spending for like-for-like comparison
- Or compare only hospital-operating counties to each other

**Pension system note**: San Mateo County uses SamCERA (1937 Act county retirement), not CalPERS. LA County uses LACERA. These independent systems have different funded ratios and employer contribution rates than CalPERS, making pension burden comparisons across county pension systems require extra care. See `data-sources/calpers-pension.md` for details.

## Output format

The peer group analysis should produce:

```
PEER GROUP FOR: {entity_name}
============================

Criteria used:
  Type: {entity_type}
  Population/Enrollment band: {range}
  Weighted dimensions: {list with weights}

Target profile:
  {key metrics}

Selected peers (ranked by similarity):
  1. {peer_name} (score: {score}) -- {key differences noted}
  2. {peer_name} (score: {score}) -- {key differences noted}
  ...

Structural adjustments applied:
  - {adjustment_1}
  - {adjustment_2}

Caveats:
  - {caveat_1}
  - {caveat_2}
```

## California region definitions

For the geographic proximity dimension, use these region groupings:

| Region | Counties |
|--------|----------|
| Bay Area | Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma |
| Central Coast | Monterey, San Benito, San Luis Obispo, Santa Barbara, Santa Cruz, Ventura |
| Sacramento Metro | El Dorado, Placer, Sacramento, Sutter, Yolo, Yuba |
| San Joaquin Valley | Fresno, Kern, Kings, Madera, Merced, San Joaquin, Stanislaus, Tulare |
| Southern California - Coastal | Los Angeles, Orange, San Diego |
| Southern California - Inland | Imperial, Riverside, San Bernardino |
| North State | Butte, Colusa, Del Norte, Glenn, Humboldt, Lake, Lassen, Mendocino, Modoc, Nevada, Plumas, Shasta, Sierra, Siskiyou, Tehama, Trinity |
| Gold Country / Foothills | Alpine, Amador, Calaveras, Inyo, Mariposa, Mono, Tuolumne |

```python
REGION_MAP = {
    "Alameda": "Bay Area", "Contra Costa": "Bay Area", "Marin": "Bay Area",
    "Napa": "Bay Area", "San Francisco": "Bay Area", "San Mateo": "Bay Area",
    "Santa Clara": "Bay Area", "Solano": "Bay Area", "Sonoma": "Bay Area",
    "Monterey": "Central Coast", "San Benito": "Central Coast",
    "San Luis Obispo": "Central Coast", "Santa Barbara": "Central Coast",
    "Santa Cruz": "Central Coast", "Ventura": "Central Coast",
    "El Dorado": "Sacramento Metro", "Placer": "Sacramento Metro",
    "Sacramento": "Sacramento Metro", "Sutter": "Sacramento Metro",
    "Yolo": "Sacramento Metro", "Yuba": "Sacramento Metro",
    "Fresno": "San Joaquin Valley", "Kern": "San Joaquin Valley",
    "Kings": "San Joaquin Valley", "Madera": "San Joaquin Valley",
    "Merced": "San Joaquin Valley", "San Joaquin": "San Joaquin Valley",
    "Stanislaus": "San Joaquin Valley", "Tulare": "San Joaquin Valley",
    "Los Angeles": "SoCal Coastal", "Orange": "SoCal Coastal",
    "San Diego": "SoCal Coastal",
    "Imperial": "SoCal Inland", "Riverside": "SoCal Inland",
    "San Bernardino": "SoCal Inland",
}
# Remaining counties map to "North State" or "Gold Country" as above

def geographic_distance(region_a: str, region_b: str) -> float:
    """0 = same region, 0.3 = adjacent, 1.0 = distant."""
    if region_a == region_b:
        return 0.0
    adjacent = {
        ("Bay Area", "Central Coast"), ("Bay Area", "Sacramento Metro"),
        ("Bay Area", "San Joaquin Valley"), ("Central Coast", "SoCal Coastal"),
        ("Sacramento Metro", "San Joaquin Valley"), ("Sacramento Metro", "North State"),
        ("SoCal Coastal", "SoCal Inland"), ("San Joaquin Valley", "SoCal Inland"),
    }
    pair = tuple(sorted([region_a, region_b]))
    if pair in adjacent:
        return 0.3
    return 1.0
```

## Anti-patterns: What NOT to do

### Do not cherry-pick peers to tell a story

If someone asks "is Redwood City spending too much on police?", do not select only peers with lower police spending. The peer group must be selected BEFORE looking at the metric being compared.

### Do not compare across entity types

A city's "administration" spending cannot be compared to a school district's "administration" spending. They have different responsibilities, different reporting standards, and different cost structures.

### Do not ignore structural differences

"Mountain View spends 50% more per capita than Redwood City" is technically true and completely misleading (utility enterprise). Always adjust before comparing.

### Do not compare raw test scores across different demographics

"District A has 70% proficiency and District B has 50% proficiency, so A is better" ignores that District A may be 10% SED while District B is 50% SED. Always show demographic context alongside outcomes.

### Do not present peer comparisons as rankings

The goal is context, not competition. "Redwood City ranks 6th out of 8 peers" invites a race to the bottom or demands to be #1 -- neither is useful. Instead: "Redwood City's public safety spending is within the typical range for similar Bay Area cities of its size."

## When to relax criteria

If the mandatory filters produce fewer than 3 peers, relax in this order:

1. **Expand population/enrollment band** to 0.25x-4x
2. **Expand geography** from same metro to same state region (NorCal, SoCal, Central Valley)
3. **Relax income band** from +/-30% to +/-50%
4. **If still insufficient**, note that few true peers exist and show the closest available, with prominent caveats

Some entities genuinely have no good peers (e.g., San Francisco as a consolidated city-county, or tiny rural districts). In those cases, say so honestly rather than forcing a bad comparison.
