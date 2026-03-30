# Synthesizer: Comprehensive School District Report

## What this does

Produces a full financial and outcomes analysis for any California K-12 school district. Answers: how much is spent, where does it go, what are the results, how does it compare to similar districts, and what is the pension/salary burden. This is the education-focused deep dive for Public Return.

## Data sources used

| Source | Skill | Purpose |
|--------|-------|---------|
| CDE School Finances (SACS) | `data-sources/cde-school-finances` | Revenue and expenditure detail by function and object code |
| CDE Test Scores (CAASPP) | `data-sources/cde-test-scores` | Student outcome data (ELA and math proficiency) |
| CalPERS/CalSTRS pension data | `data-sources/calpers-pension` | Pension obligation burden |
| Transparent California | `data-sources/transparent-california` | Individual salary and total compensation data |
| SCO ByTheNumbers | `data-sources/sco-bythenumbers` | Supplemental spending context for the city/county |

## Input

- **District name** or **CDS code** (County-District-School code, e.g., `41-69005` for Redwood City Elementary)
- Optional: comparison district(s) or "auto-compare"

## Step-by-step workflow

### Step 1: Identify the district and its metadata

**From CDS code or name, establish:**
- Full district name
- County code and district code
- Grade span (K-6, K-8, 9-12, K-12)
- Enrollment (total ADA — Average Daily Attendance)
- District type (elementary, high school, unified)

CDS codes for 94062 area:
| District | CDS Code | Type | Grades |
|----------|----------|------|--------|
| Redwood City Elementary | 41-69005 | Elementary | K-8 |
| Sequoia Union High | 41-69062 | High School | 9-12 |

### Step 2: Pull financial data (CDE SACS)

Query the CDE SACS (Standardized Account Code Structure) data for the district.

**Revenue side** — categorize by source:
- **LCFF sources** (Object 8010-8099): State apportionment + local property tax. This is the base funding.
- **Federal revenue** (Object 8100-8299): Title I, IDEA, etc.
- **Other state revenue** (Object 8300-8599): Lottery, categorical programs.
- **Local revenue** (Object 8600-8799): Parcel taxes, fees, donations, interest.

**Expenditure side** — categorize two ways:

By **function** (what it's for):
| Function Code | Category |
|--------------|----------|
| 1000 | Instruction |
| 2100 | Instructional supervision/admin |
| 2200 | Instructional library/media/tech |
| 2700 | School administration |
| 3100 | Food services |
| 5000 | Facilities/maintenance |
| 7100 | Debt service |
| Other 2xxx | District administration |

By **object** (what type of expense):
| Object Code | Category |
|-------------|----------|
| 1000-1999 | Certificated salaries (teachers, principals) |
| 2000-2999 | Classified salaries (aides, custodians, office) |
| 3000-3999 | Employee benefits (health, pension — CalSTRS/CalPERS/PERS) |
| 4000-4999 | Books and supplies |
| 5000-5999 | Services and operating |
| 6000-6999 | Capital outlay |
| 7000-7999 | Other (transfers, debt) |

**Key derived metrics:**
- Per-pupil spending = Total expenditures / ADA
- Instruction share = Function 1000 expenditures / Total expenditures
- Personnel share = (Objects 1000-3999) / Total expenditures
- Pension/benefits share = Object 3000-3999 / Total expenditures
- Admin share = (Functions 2100-2700 minus instructional supervision) / Total expenditures

### Step 3: Pull test score data (CAASPP)

From the CAASPP research file, filter:
```
County_Code = {county_code}
District_Code = {district_code}
School_Code = 0000000          # district aggregate
Test_Year = 2024               # most recent
```

**Pull for these subgroups** (Subgroup_ID):
| ID | Subgroup |
|----|----------|
| 1 | All Students |
| 74 | Socioeconomically Disadvantaged |
| 75 | Not Socioeconomically Disadvantaged |
| 160 | English Learners |
| 120 | Hispanic or Latino |
| 128 | White |
| 131 | Asian |

**Pull for both tests:**
- Test_Id 1 = ELA
- Test_Id 2 = Math

**Pull grade-level and all-grades data:**
- Grade 13 = All Grades (for summary)
- Individual grades for trend detail

**Key metrics:**
- `Percentage_Standard_Met_and_Above` (primary)
- `Percentage_Standard_Exceeded` (top performers)
- `Percentage_Standard_Not_Met` (struggling students)
- `Students_Tested` (for context on suppressed data)

**Multi-year trend**: Pull Test_Year 2019, 2022, 2023, 2024 (skip 2020-2021 — COVID cancellations).

### Step 4: Pull salary and compensation data (Transparent California)

From Transparent California:
```
# See transparent-california skill for endpoint
# Query by entity name matching the school district
# Returns: individual employee records with
#   base_pay, overtime_pay, other_pay, benefits, total_compensation
```

**Derive:**
- Median teacher total compensation (filter by job title containing "teacher")
- Median administrator total compensation (filter by "principal", "superintendent", "director")
- Superintendent total compensation (specific lookup)
- Ratio of highest-paid employee to median teacher
- Distribution of total compensation (quartiles)
- Number of employees earning > $150K, > $200K total comp

### Step 5: Pull pension data

**CalSTRS** (teachers): From SACS Object 3000-series or CalSTRS employer contribution reports:
- Employer contribution rate (currently ~19.1% of certificated salary)
- Total employer CalSTRS contribution
- Unfunded liability allocated to district (if available)

**CalPERS** (classified staff): From CalPERS data:
- Employer contribution rate (currently ~25-27% of classified salary)
- Total employer CalPERS contribution

**Combined pension burden:**
- Total pension contributions / Total expenditures
- Total pension contributions / Total salary costs
- Year-over-year trend (pension rates have risen sharply since 2014)

### Step 6: Find comparable districts

**Comparison methodology:**

Select 5-8 comparable districts based on these criteria, in priority order:

1. **Same district type** (elementary, high school, unified) — mandatory filter
2. **Similar enrollment** (within 50-200% of target district's ADA)
3. **Similar demographics** — % socioeconomically disadvantaged students (within +/- 15 percentage points)
4. **Same region** — prefer same county, then adjacent counties, then same metro area
5. **Similar property wealth** — assessed valuation per ADA (from BOE or SACS data) within 50-200%

**For Redwood City Elementary (41-69005):**
- Type: Elementary (K-8)
- ADA: ~7,500
- % Socioeconomically Disadvantaged: ~45%
- County: San Mateo (41)
- Region: Peninsula/South Bay

Comparable districts might include:

| District | CDS | ADA | % SED | County |
|----------|-----|-----|-------|--------|
| San Mateo-Foster City | 41-68999 | ~8,500 | ~30% | San Mateo |
| Burlingame Elementary | 41-68486 | ~3,200 | ~12% | San Mateo |
| San Carlos Elementary | 41-69021 | ~3,000 | ~10% | San Mateo |
| Mountain View Whisman | 43-69450 | ~5,200 | ~35% | Santa Clara |
| Sunnyvale Elementary | 43-69807 | ~6,000 | ~40% | Santa Clara |
| Jefferson Elementary (Daly City) | 41-68619 | ~7,000 | ~55% | San Mateo |

Note: Perfect comparables don't exist. Always disclose the comparison criteria and acknowledge where districts differ meaningfully (e.g., Burlingame has much lower % SED, so direct outcome comparison is misleading without adjusting for demographics).

**For each comparable, pull the same SACS and CAASPP data and compute the same metrics.**

### Step 7: Compose the report

Assemble into the narrative template below.

## Report template

```
SCHOOL DISTRICT REPORT: {district_name}
CDS Code: {cds_code} | Grades: {grade_span} | Enrollment: {ada} ADA
================================================================

FINANCIAL OVERVIEW (FY {year})
------------------------------
Total Revenue:      ${total_revenue}
Total Expenditures: ${total_expenditures}
Per-Pupil Spending: ${per_pupil}

Revenue Sources:
  LCFF (state + local property tax):  ${lcff}  ({lcff_pct}%)
  Federal:                            ${fed}   ({fed_pct}%)
  Other state:                        ${state} ({state_pct}%)
  Local (parcel tax, fees, etc.):     ${local} ({local_pct}%)

WHERE THE MONEY GOES
--------------------
By function:
  Instruction:                ${instruction}  ({instr_pct}%)
  School administration:      ${school_admin} ({sa_pct}%)
  District administration:    ${dist_admin}   ({da_pct}%)
  Pupil services:             ${pupil_svc}    ({ps_pct}%)
  Maintenance/facilities:     ${maint}        ({m_pct}%)
  Food services:              ${food}         ({f_pct}%)
  Other:                      ${other}        ({o_pct}%)

By type of expense:
  Certificated salaries:      ${cert_sal}     ({cs_pct}%)
  Classified salaries:        ${class_sal}    ({cls_pct}%)
  Employee benefits:          ${benefits}     ({b_pct}%)
    of which pension:         ${pension}      ({p_pct}%)
  Books & supplies:           ${books}        ({bk_pct}%)
  Services & operating:       ${services}     ({sv_pct}%)
  Capital outlay:             ${capital}      ({cap_pct}%)

THE PENSION PICTURE
-------------------
CalSTRS employer contribution:  ${calstrs}  (rate: {calstrs_rate}%)
CalPERS employer contribution:  ${calpers}  (rate: {calpers_rate}%)
Total pension cost:             ${total_pension}
Pension as % of total budget:   {pension_budget_pct}%

Trend: Pension costs have grown from {old_pct}% of the budget in
{old_year} to {new_pct}% in {new_year}. Every dollar that goes to
pension is a dollar not available for classroom instruction.

COMPENSATION
------------
(Source: Transparent California, {tc_year})

Median teacher total compensation:        ${median_teacher}
Median administrator total compensation:  ${median_admin}
Superintendent total compensation:        ${supt_comp}
Employees earning > $200K total comp:     {count_200k}

STUDENT OUTCOMES (CAASPP {test_year})
-------------------------------------
                        ELA          Math
All Students:           {ela_all}%   {math_all}%
Socioeconomically Disadv: {ela_sed}% {math_sed}%
Not Socioeconomically D:  {ela_nsed}%{math_nsed}%
English Learners:       {ela_el}%    {math_el}%

Achievement gap (Not SED minus SED):
  ELA: {ela_gap} percentage points
  Math: {math_gap} percentage points

Trend (2019 to {test_year}):
  ELA All Students: {ela_2019}% -> {ela_now}% ({ela_delta})
  Math All Students: {math_2019}% -> {math_now}% ({math_delta})

HOW {DISTRICT} COMPARES
------------------------
                        {district}  Peer Avg  Rank
Per-pupil spending:     ${pp}       ${pp_avg} {rank}/N
% to instruction:       {i_pct}%    {i_avg}%  {rank}/N
% to admin:             {a_pct}%    {a_avg}%  {rank}/N
% to pension/benefits:  {pb_pct}%   {pb_avg}% {rank}/N
ELA proficiency:        {ela}%      {ela_avg}% {rank}/N
Math proficiency:       {math}%     {math_avg}%{rank}/N

Comparable districts: {list of comparables with CDS codes}
Comparison criteria: same type ({type}), similar enrollment,
similar demographics ({pct_sed}% +/- 15pp SED), same region.

SPENDING vs. OUTCOMES
---------------------
{district} spends ${per_pupil} per student and achieves {ela_all}%
ELA / {math_all}% math proficiency.

Among peers:
- {higher_spender} spends ${hs_pp} more per pupil but achieves
  similar/lower/higher outcomes ({hs_ela}% ELA, {hs_math}% math).
- {lower_spender} spends ${ls_pp} less per pupil but achieves
  similar/higher outcomes ({ls_ela}% ELA, {ls_math}% math).

The correlation between per-pupil spending and test scores across
these peers is {correlation_description}. The largest driver of
outcome differences is student demographics (% socioeconomically
disadvantaged), not spending levels.
```

## Example: Redwood City Elementary (CDS 41-69005)

### Financial summary (illustrative, FY 2022-23)

| Metric | Value |
|--------|-------|
| Total Expenditures | ~$145M |
| ADA | ~7,500 |
| Per-pupil spending | ~$19,300 |
| % to instruction | ~58% |
| % to admin (all) | ~8% |
| % to employee benefits | ~24% |
| % to pension specifically | ~12% |

### Revenue sources

| Source | Amount | % |
|--------|--------|---|
| LCFF (property tax + state) | ~$100M | ~69% |
| Federal | ~$12M | ~8% |
| Other state | ~$15M | ~10% |
| Local (parcel tax, fees, grants) | ~$18M | ~13% |

Note: Redwood City Elementary benefits from a voter-approved parcel tax (Measure H) that provides supplemental local funding.

### Test scores (2024 CAASPP)

| Subgroup | ELA % Met/Exceeded | Math % Met/Exceeded |
|----------|-------------------|-------------------|
| All Students | ~55% | ~42% |
| Socioeconomically Disadv. | ~35% | ~23% |
| Not Socioeconomically Disadv. | ~78% | ~64% |
| English Learners | ~15% | ~12% |
| Hispanic/Latino | ~38% | ~25% |
| White | ~82% | ~70% |
| Asian | ~85% | ~78% |

Achievement gap (Not SED minus SED): ELA ~43pp, Math ~41pp.

### Peer comparison (illustrative)

| District | Per-Pupil | % Instruction | ELA % | Math % | % SED |
|----------|-----------|--------------|-------|--------|-------|
| **Redwood City Elem** | **$19,300** | **58%** | **55%** | **42%** | **45%** |
| San Mateo-Foster City | $18,500 | 60% | 62% | 52% | 30% |
| Mountain View Whisman | $20,100 | 57% | 60% | 50% | 35% |
| Jefferson Elem (Daly City) | $17,800 | 59% | 45% | 33% | 55% |
| Sunnyvale Elem | $19,000 | 58% | 58% | 48% | 40% |

Observation: Redwood City Elementary's lower aggregate scores are largely explained by its higher percentage of socioeconomically disadvantaged students compared to San Mateo-Foster City or Mountain View Whisman. When comparing the "Not SED" subgroup across districts, performance differences narrow substantially.

### Key findings for narrative

1. **Spending is above average** for the region but driven by high cost of living and pension obligations, not unusually high instructional spending.
2. **The achievement gap is the story**: 43 percentage points separate SED and non-SED students in ELA. This is the district's central challenge.
3. **Pension costs are crowding out other spending**: Employee benefits consume ~24% of the budget, up from ~18% a decade ago. This is a statewide trend, not specific to this district.
4. **Parcel tax matters**: Without Measure H revenue, per-pupil spending would drop by ~$800-1,000, putting the district below peer average.

## Comparison methodology notes

### Why demographics matter more than spending

Across California districts, the correlation between per-pupil spending and test scores is weak (r ~ 0.1-0.2). The correlation between % socioeconomically disadvantaged and test scores is strong (r ~ -0.7 to -0.8). Any honest district comparison must account for this.

**How to adjust for demographics:**
- Always show % SED alongside test scores
- Compare "like to like" — SED students in District A vs. SED students in District B
- Use the CAASPP subgroup breakdown (Subgroup_ID 74 and 75) rather than just "All Students"
- Note that LCFF provides supplemental/concentration grants for high-SED districts, so spending may be higher precisely because demographics are more challenging

### What "comparable" means and its limits

No two districts are truly comparable. The comparison is a starting point for questions, not a verdict. Always disclose:
- Which criteria were used and which districts were selected
- Where the comparables diverge (enrollment size, demographics, geography)
- That the comparison does not control for all variables (teacher quality, community factors, housing stability, etc.)

## Error handling

- **District not found**: Validate CDS code format (2-digit county, 5-digit district). If name search, fuzzy match against CDE district directory and confirm with user.
- **No SACS data for year**: Use most recent available year. Note the gap.
- **Suppressed CAASPP data** (`*` in percentage fields): Report as "fewer than 11 students tested — data suppressed for privacy." Do not estimate or impute.
- **No Transparent California match**: District name may differ between CDE and TC databases. Try variations (e.g., "Redwood City School District" vs. "Redwood City Elementary School District"). If no match, skip salary section and note.
- **Fewer than 3 comparable districts found**: Relax criteria in order — first expand enrollment range, then expand geographic scope, then relax demographic similarity. Always note relaxed criteria.
