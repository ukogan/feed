# Synthesizer: Where Do My CA Property Taxes Go?

## What this does

Takes a California address (or zip code) and produces a plain-language breakdown of where the property taxes go: which government entities receive the money, what they spend it on, and how their spending compares to similar jurisdictions. This is the flagship "follow the money" query for Public Return.

## Data sources used

| Source | Skill | Purpose |
|--------|-------|---------|
| BOE Tax Rate Area lookup | `data-sources/boe-tra-lookup` | Resolve address to Tax Rate Area; get list of taxing entities and their share of the 1% base levy |
| SCO ByTheNumbers | `data-sources/sco-bythenumbers` | Get spending breakdowns for the city, county, and special districts that receive tax revenue |
| CalPERS pension data | `data-sources/calpers-pension` | Show pension obligations as a share of each entity's budget |
| CDE School Finances (SACS) | `data-sources/cde-school-finances` | Get school district revenue and expenditure detail |
| CDE Test Scores (CAASPP) | `data-sources/cde-test-scores` | Attach outcome data to the school spending numbers |

## Step-by-step workflow

### Step 1: Resolve address to taxing jurisdictions

**Input**: Street address, city, or zip code (e.g., "123 Main St, Redwood City, CA 94062" or just "94062")

**Action**: Use the BOE Tax Rate Area (TRA) lookup to identify:
- The Tax Rate Area code for this location
- All taxing entities that receive a share of the 1% base property tax levy
- The allocation percentage for each entity

**API call**:
```
# BOE TRA lookup — see boe-tra-lookup skill for exact endpoint
# Returns: list of entities with their TRA allocation percentages
# Example entities for 94062:
#   San Mateo County, Redwood City, Redwood City Elementary SD,
#   Sequoia Union High SD, San Mateo County Community College District,
#   Midpeninsula Regional Open Space District, etc.
```

**Output of this step**: A table like:

| Entity | Type | Share of 1% Levy |
|--------|------|-----------------|
| San Mateo County | County | ~17% |
| Redwood City | City | ~11% |
| Redwood City Elementary SD | School District | ~27% |
| Sequoia Union High SD | School District | ~14% |
| San Mateo County Community College | Community College | ~6% |
| Midpeninsula Regional Open Space | Special District | ~2% |
| Bay Area Air Quality Mgmt | Special District | ~0.3% |
| Other entities | Various | Remainder |

Note: Percentages are illustrative. Actual allocations vary by TRA and change annually. The 1% base levy is set by Prop 13; voter-approved bonds, parcel taxes, and Mello-Roos assessments are additional and are NOT part of this allocation.

### Step 2: Get spending data for each entity

For each taxing entity identified in Step 1, pull the most recent spending data.

**For the city** (e.g., Redwood City):
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json
  ?entity_name=Redwood City
  &fiscal_year=2022-2023
  &$order=value DESC
  &$limit=200
```

**For the county** (e.g., San Mateo County):
```
GET https://counties.bythenumbers.sco.ca.gov/resource/{county_expenditure_id}.json
  ?entity_name=San Mateo
  &fiscal_year=2022-2023
```

**For special districts**:
```
GET https://districts.bythenumbers.sco.ca.gov/resource/m9u3-wdam.json
  ?entity_name={district_name}
  &fiscal_year=2022-2023
```

**For school districts** (use CDE SACS, not SCO):
```
# See cde-school-finances skill for SACS endpoint
# Query by County-District-School (CDS) code
# Redwood City Elementary: CDS 41-69005
# Sequoia Union High: CDS 41-69062
```

### Step 3: Get pension burden for each entity

For each non-school entity, query CalPERS pension data:
```
# See calpers-pension skill for endpoint
# Query employer contribution as % of total expenditures
# For Redwood City: employer pension contribution / total city expenditures
```

For school districts, pension data comes from CalSTRS (California State Teachers' Retirement System), which may be embedded in the SACS data under Object Code 3000-series (employee benefits).

### Step 4: Get school outcome data

For each school district identified in Step 1, pull CAASPP test scores:

```python
# Filter CAASPP research file for:
#   County_Code = 41 (San Mateo)
#   District_Code = 69005 (Redwood City Elementary)
#   School_Code = 0000000 (district aggregate)
#   Subgroup_ID = 1 (All Students)
#   Grade = 13 (All Grades)
#   Test_Id = 1 (ELA) and 2 (Math)
#   Test_Year = 2024 (most recent)
```

Key metric: `Percentage_Standard_Met_and_Above` for ELA and Math.

### Step 5: Compose the narrative

Assemble all data into a structured narrative. See template below.

## Narrative template

```
WHERE YOUR PROPERTY TAXES GO: {address or zip}
=========================================================

YOUR TAX RATE AREA: {TRA code}

For every $1 of your base property tax (the 1% Prop 13 levy), here is
where it goes:

  {entity_name_1} ({type})              ${amount_1}  ({pct_1}%)
  {entity_name_2} ({type})              ${amount_2}  ({pct_2}%)
  ...

On a home assessed at ${assessed_value}, your base property tax is
${base_tax}. Additional amounts for voter-approved bonds, parcel taxes,
and special assessments are NOT included here.

---

{ENTITY_NAME}: HOW THEY SPEND IT
---------------------------------
Your share to {entity}: ${your_share}/year

Top spending categories (FY {year}):
  1. {category_1}: ${amount} ({pct}% of budget)
  2. {category_2}: ${amount} ({pct}% of budget)
  ...

Pension obligations: ${pension_amount} ({pension_pct}% of budget)
  - This means ${pension_per_dollar} of every dollar {entity} receives
    goes to retirement costs for current and former employees.

[Repeat for each major entity]

---

YOUR SCHOOL DISTRICTS
---------------------
{district_name} (grades {range})
  Per-pupil spending: ${per_pupil}
  Spending breakdown:
    Instruction:         ${instruction} ({pct}%)
    Administration:      ${admin} ({pct}%)
    Employee benefits:   ${benefits} ({pct}%)
    Other:               ${other} ({pct}%)

  Student outcomes (CAASPP {year}):
    ELA proficiency:     {ela_pct}% meeting standard
    Math proficiency:    {math_pct}% meeting standard

[Repeat for each school district]

---

CONTEXT
-------
- {city} spends ${per_capita} per resident, compared to ${comparison}
  in similar-sized Bay Area cities.
- {school_district} spends ${per_pupil} per student. The state average
  is ${state_avg}. {pct}% of that goes to employee benefits and pension.
- Your total effective property tax rate (including bonds and parcel
  taxes) is approximately {effective_rate}%.
```

## Example: 94062 (Redwood City)

### Step 1 result: Taxing entities for a typical 94062 TRA

| Entity | Type | Approx. Share |
|--------|------|--------------|
| San Mateo County General | County | 17.2% |
| San Mateo County Library JPA | Special District | 2.8% |
| Redwood City | City | 10.8% |
| Redwood City Elementary SD | K-8 School District | 26.5% |
| Sequoia Union High SD | 9-12 School District | 14.1% |
| San Mateo Co. Community College | Community College | 5.9% |
| Bay Area Air Quality Mgmt | Special District | 0.3% |
| Midpeninsula Regional Open Space | Special District | 1.5% |
| Sequoia Healthcare District | Special District | 3.2% |
| Other (mosquito abatement, etc.) | Various | ~17.7% |

### Step 2 result: City spending (Redwood City, FY 2022-23)

From SCO ByTheNumbers (`ju3w-4gxp`):

| Category | Amount | % of Total |
|----------|--------|-----------|
| Public Safety | ~$75M | ~38% |
| Transportation | ~$25M | ~13% |
| Community Development | ~$20M | ~10% |
| Culture & Leisure | ~$18M | ~9% |
| General Government | ~$30M | ~15% |
| Utilities | ~$15M | ~8% |
| Other | ~$15M | ~7% |

### Step 3 result: Pension burden

Redwood City employer pension contributions (CalPERS): approximately $25-30M/year, or roughly 12-15% of total city expenditures. This has grown ~60% over the past decade.

### Step 4 result: School outcomes

**Redwood City Elementary (41-69005), 2024 CAASPP:**
- ELA: ~55% meeting or exceeding standard
- Math: ~42% meeting or exceeding standard

**Sequoia Union High (41-69062), 2024 CAASPP:**
- ELA: ~70% meeting or exceeding standard
- Math: ~42% meeting or exceeding standard

Note: Scores vary significantly by school within these districts, and by student subgroup (socioeconomic status is the strongest predictor).

### Assembled narrative (abbreviated)

```
WHERE YOUR PROPERTY TAXES GO: 94062 (Redwood City)
=========================================================

For a home assessed at $1,500,000, your base property tax (1% levy)
is $15,000/year. Here is where that $15,000 goes:

  Redwood City Elementary SD         $3,975  (26.5%)
  San Mateo County                   $2,580  (17.2%)
  Sequoia Union High SD              $2,115  (14.1%)
  Redwood City                       $1,620  (10.8%)
  San Mateo Co. Community College    $885    (5.9%)
  Sequoia Healthcare District        $480    (3.2%)
  San Mateo County Library JPA       $420    (2.8%)
  Midpeninsula Regional Open Space   $225    (1.5%)
  Other entities                     $2,700  (18.0%)

This is ONLY the 1% base levy. Your actual tax bill also includes
voter-approved bonds (~0.15-0.25%), parcel taxes ($200-800/parcel
depending on district), and any Mello-Roos assessments.

---

REDWOOD CITY: HOW THEY SPEND YOUR $1,620
-----------------------------------------
Top spending categories (FY 2022-23):
  1. Public Safety (police, fire):  $616  (38% of budget)
  2. General Government:            $243  (15%)
  3. Transportation:                $211  (13%)
  4. Community Development:         $162  (10%)
  5. Culture & Leisure:             $146  (9%)

Pension reality: ~$0.13 of every dollar the city spends goes to
CalPERS pension obligations. This is up from ~$0.08 a decade ago.

---

YOUR SCHOOL DISTRICTS
---------------------
Redwood City Elementary (K-8), CDS 41-69005:
  Your property tax share: $3,975/year
  Per-pupil spending: ~$16,000 (varies by year)
  Student outcomes (2024 CAASPP):
    ELA proficiency:  55% meeting standard
    Math proficiency: 42% meeting standard

Sequoia Union High (9-12), CDS 41-69062:
  Your property tax share: $2,115/year
  Per-pupil spending: ~$20,000 (varies by year)
  Student outcomes (2024 CAASPP):
    ELA proficiency:  70% meeting standard
    Math proficiency: 42% meeting standard
```

## Important caveats to always include

1. **Prop 13 base levy only**: The 1% allocation shown here is only part of the property tax bill. Voter-approved GO bonds, parcel taxes, Mello-Roos CFDs, and special assessments are additional and go directly to the issuing entity (usually schools or infrastructure).

2. **Property taxes are not the only revenue source**: Cities and counties also receive sales tax, transient occupancy tax, fees, state/federal transfers, etc. The property tax share shown here does not represent the entity's entire budget.

3. **School funding is equalized**: California's Local Control Funding Formula (LCFF) adjusts state aid to compensate for differences in local property tax revenue. High-property-tax districts get less state aid. So the property tax allocation to schools does not directly determine per-pupil spending — it determines how much comes from local vs. state sources.

4. **TRA allocations shift**: The AB 8 formula (1979) froze relative shares and adjusts them incrementally. New development, annexations, and RDA dissolution can shift allocations over time.

5. **Data currency**: SCO ByTheNumbers typically lags 1-2 years. CAASPP scores lag ~6 months. BOE TRA data may lag up to a year. Always note the fiscal year of each data point.

## Error handling

- **Address not found in TRA lookup**: Fall back to zip code. If zip code spans multiple TRAs, show the most common TRA for that zip or list the range.
- **Entity not found in SCO data**: Some small special districts do not report to SCO. Note this and skip the spending breakdown for that entity.
- **Suppressed test scores**: CAASPP suppresses results for groups with fewer than 11 students. Note when data is suppressed.
- **Missing fiscal year**: If the most recent year is not available, use the most recent available and note the gap.
