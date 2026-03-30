# Normalizer: Spending Category Taxonomy

## What this does

Maps spending categories from different California government data sources into a single universal taxonomy so you can honestly compare spending across cities, counties, school districts, and special districts. Without normalization, "Public Safety" in one dataset and "Public Protection" in another look like different things when they mean the same thing, and "General Government" hides very different cost structures depending on entity type.

## The problem

Each SCO reporting system uses different category names:

- **Cities** (dataset `ju3w-4gxp`): "Public Safety", "Transportation", "Community Development", "Health", "Culture and Leisure", "General Government"
- **Counties** (dataset `uctr-c2j8`): "Public Protection", "Public Ways and Facilities", "Education", "Public Assistance", "Health", "Sanitation", "Recreation and Cultural Services", "General Government"
- **Special Districts** (dataset `m9u3-wdam`): "Salaries and Wages", "Services and Supplies", "Fixed Assets", "Employee Benefits" (by object, not by function)
- **School Districts** (CDE SACS): Function codes 1000-9000 with a completely different taxonomy: "Instruction", "School Administration", "Pupil Services", "Plant Services"

You cannot just compare raw categories across entity types.

## Universal taxonomy

These 8 categories capture the functional purpose of spending across all CA government entity types:

| Universal Category | Code | Description |
|-------------------|------|-------------|
| **Public Safety** | `PS` | Police, fire, corrections, prosecution, courts, animal control, emergency services |
| **Infrastructure** | `INF` | Roads, bridges, transit, water, sewer, solid waste, airports, harbors, public works |
| **Health & Human Services** | `HHS` | Public health, hospitals, mental health, social services, public assistance, housing |
| **Education** | `EDU` | K-12 instruction, libraries, community colleges, after-school programs |
| **Community & Culture** | `CC` | Parks, recreation, arts, community events, open space, leisure facilities |
| **General Administration** | `ADM` | Elected officials, finance, HR, legal, city/county manager, IT, general overhead |
| **Debt & Capital** | `DC` | Debt service, bond payments, capital outlay, major construction projects |
| **Personnel Costs (Cross-cutting)** | `PER` | Pension contributions, employee benefits -- reported separately because these inflate every other category |

**Note on Personnel Costs**: This is not a functional category like the others. Pension and benefit costs are embedded within every other category (police officers' pensions are in Public Safety, teachers' pensions are in Education). The `PER` code is used when a data source reports by object (what type of expense) rather than by function (what service). Some analyses will want to pull pension costs out of their functional category and show them separately.

## Mapping tables

### SCO Cities -> Universal

| SCO City Category | Universal | Notes |
|------------------|-----------|-------|
| Public Safety | **PS** | Direct match |
| Transportation | **INF** | Roads, streets, transit |
| Community Development | **INF** | Planning, building inspection, code enforcement, redevelopment. Could also be ADM -- judgment call. Mapped to INF because it directly enables physical development. |
| Health | **HHS** | Direct match |
| Culture and Leisure | **CC** | Parks, recreation, libraries, arts |
| General Government | **ADM** | Includes elected officials, city manager, finance, legal, HR. **Tricky**: also includes city clerk, elections, and sometimes IT. This is pure overhead. |
| Public Utilities | **INF** | Water, sewer, electric, gas (enterprise fund operations) |
| Other Expenditures | varies | Must inspect subcategory_1/subcategory_2 to classify |
| Capital Outlay | **DC** | Major construction, equipment purchases |
| Debt Service | **DC** | Bond payments, interest |
| General Government and Public Safety | split | Combined category in some cities. Must inspect subcategories to split, or allocate proportionally based on similar cities. |
| Health and Culture and Leisure | split | Combined category. Inspect subcategories. |
| Transportation and Community Development | **INF** | Both map to INF, so no conflict. |
| Airport/Harbor/Transit/Sewer/Solid Waste/Water/Electric/Gas Enterprise Fund | **INF** | Enterprise fund operations -- infrastructure services |
| Hospital Enterprise Fund | **HHS** | Healthcare delivery |
| Internal Service Fund | **ADM** | Fleet management, central purchasing, self-insurance |
| Conduit Financing | **DC** | Passthrough financing for development |

### SCO Counties -> Universal

| SCO County Category | Universal | Notes |
|--------------------|-----------|-------|
| Public Protection | **PS** | Sheriff, DA, probation, courts, fire (if county-operated), OES |
| Public Ways and Facilities | **INF** | Roads, bridges, county infrastructure |
| Education | **EDU** | County Office of Education, libraries |
| Public Assistance | **HHS** | CalWORKs, CalFresh, General Relief, In-Home Supportive Services |
| Health | **HHS** | Public health department, behavioral health, hospitals |
| Sanitation | **INF** | Waste management, water quality |
| Recreation and Cultural Services | **CC** | Parks, community centers |
| General Government | **ADM** | Board of Supervisors, County Executive, assessor, auditor-controller, treasurer, recorder, elections. **Tricky**: County "General Government" is much larger than city equivalent because counties run more administrative functions (assessor, recorder, public guardian, etc.) |
| Hospital Activity/Enterprise | **HHS** | County-operated hospitals (e.g., SF General, LAC+USC) |
| Refuse Activity/Enterprise | **INF** | Solid waste enterprise |
| Airport Activity/Enterprise | **INF** | County-operated airports |
| All Enterprise Funds | **INF** | Same as cities |
| Debt Service / Capital Outlay | **DC** | Same as cities |
| Public Ways and Facilities, Health, and Sanitation | split | Combined category. If cannot split, allocate: 40% INF, 40% HHS, 20% INF |

### CDE SACS (School Districts) -> Universal

School districts are almost entirely **EDU**, but breaking down within education is important:

| SACS Function Code | Universal | Sub-category |
|-------------------|-----------|-------------|
| 1000 (Instruction) | **EDU** | Classroom instruction |
| 2100 (Instructional supervision) | **EDU** | Curriculum, coaching |
| 2200 (Library/media/tech) | **EDU** | Learning resources |
| 2700 (School administration) | **ADM** | Principals, school office staff |
| 3100 (Guidance/counseling) | **HHS** | Student support services |
| 3140 (Health services) | **HHS** | School nurses |
| 3600 (Pupil transportation) | **INF** | School buses |
| 3700 (Food services) | **HHS** | Cafeteria, free/reduced lunch |
| 4000 (Ancillary/athletics) | **CC** | Sports, extracurriculars |
| 5000 (Community services) | **CC** | Adult ed, community programs |
| 7100 (Board/superintendent) | **ADM** | Governance overhead |
| 7200-7700 (Central admin) | **ADM** | District office, HR, finance |
| 8000-8999 (Plant services) | **INF** | Maintenance, custodial, utilities, security |
| 9000-9999 (Other outgo) | **DC** | Debt service, transfers |

SACS Object Codes for cross-cutting pension analysis:

| SACS Object Code | Universal | Description |
|-----------------|-----------|-------------|
| 3101-3102 | **PER** | CalSTRS employer contributions |
| 3201-3202 | **PER** | CalPERS employer contributions |
| 3401-3602 | **PER** | Health/welfare benefits |

### SCO Special Districts -> Universal

Special districts are tricky because the SCO reports them primarily by **object** (type of expense) rather than by **function** (purpose). You must use the district type to infer the function.

| SCO Special District Category | Universal | Notes |
|------------------------------|-----------|-------|
| Salaries and Wages | **PER** | Cannot assign to a function without knowing district type |
| Services and Supplies | varies | Same -- depends on district type |
| Employee Benefits | **PER** | Cross-cutting |
| Fixed Assets | **DC** | Capital equipment/property |
| Contributions to Outside Agencies | varies | Grants, JPA payments |
| Governmental Funds | varies | Operating expenditures |
| All Enterprise Funds (Water, Sewer, etc.) | **INF** | Infrastructure services |
| Transportation | **INF** | Transit districts |

**Special district type -> functional mapping:**

| District Type | Default Universal Category |
|--------------|--------------------------|
| Fire Protection | **PS** |
| Police Protection | **PS** |
| Water | **INF** |
| Sewer/Sanitation | **INF** |
| Flood Control | **INF** |
| Mosquito Abatement | **HHS** |
| Healthcare | **HHS** |
| Cemetery | **CC** |
| Parks & Recreation | **CC** |
| Library | **EDU** |
| Open Space | **CC** |
| Community Services | **CC** |
| Resource Conservation | **CC** |
| Transit | **INF** |
| Harbor/Port | **INF** |
| Airport | **INF** |
| Irrigation | **INF** |

## How to apply the normalization

```python
# City spending normalization
CITY_CATEGORY_MAP = {
    "Public Safety": "PS",
    "Transportation": "INF",
    "Community Development": "INF",
    "Health": "HHS",
    "Culture and Leisure": "CC",
    "General Government": "ADM",
    "Public Utilities": "INF",
    "Capital Outlay": "DC",
    "Debt Service": "DC",
    "Debt Service and Capital Outlay": "DC",
    "Internal Service Fund": "ADM",
    "Conduit Financing": "DC",
    "Other Expenditures": "ADM",  # default; inspect subcategories
    # Enterprise funds
    "Airport Enterprise Fund": "INF",
    "Electric Enterprise Fund": "INF",
    "Gas Enterprise Fund": "INF",
    "Harbor and Port Enterprise Fund": "INF",
    "Hospital Enterprise Fund": "HHS",
    "Other Enterprise Fund": "INF",
    "Sewer Enterprise Fund": "INF",
    "Solid Waste Enterprise Fund": "INF",
    "Transit Enterprise Fund": "INF",
    "Water Enterprise Fund": "INF",
    # Combined categories -- best effort
    "General Government and Public Safety": "PS",  # usually mostly PS
    "Health and Culture and Leisure": "HHS",
    "Transportation and Community Development": "INF",
    "Public Utilities and Other Expenditures": "INF",
}

# County spending normalization
COUNTY_CATEGORY_MAP = {
    "Public Protection": "PS",
    "Public Ways and Facilities": "INF",
    "Education": "EDU",
    "Public Assistance": "HHS",
    "Health": "HHS",
    "Sanitation": "INF",
    "Recreation and Cultural Services": "CC",
    "General Government": "ADM",
    "General": "ADM",
    "Hospital Activity/Enterprise": "HHS",
    "Hospital Enterprise Fund Fund": "HHS",
    "Refuse Activity/Enterprise": "INF",
    "Airport Activity/Enterprise": "INF",
    "Airport Enterprise Fund": "INF",
    "Debt Service": "DC",
    "Debt Service and Capital Outlay": "DC",
    "Internal Service Fund": "ADM",
    "Conduit Financing": "DC",
    "Other Enterprise": "INF",
    "Other Enterprise Fund": "INF",
    "Sewer Enterprise Fund": "INF",
    "Electric Enterprise Fund": "INF",
    "Gas Enterprise Fund": "INF",
    "Harbor and Port Enterprise Fund": "INF",
    "Transit Enterprise Fund": "INF",
    "Solid Waste Enterprise Fund": "INF",
    "Water Enterprise Fund": "INF",
    # Combined
    "Public Ways and Facilities, Health, and Sanitation": "INF",
    "Education and Recreation and Cultural Services": "EDU",
}

# SACS function code normalization
def sacs_function_to_universal(func_code: str) -> str:
    code = int(func_code)
    if 1000 <= code <= 1999: return "EDU"
    if 2000 <= code <= 2699: return "EDU"
    if code == 2700: return "ADM"  # School admin
    if 3000 <= code <= 3199: return "HHS"  # Counseling, health
    if code == 3600: return "INF"  # Transportation
    if code == 3700: return "HHS"  # Food services
    if 4000 <= code <= 4999: return "CC"  # Ancillary
    if 5000 <= code <= 5999: return "CC"  # Community services
    if 7000 <= code <= 7999: return "ADM"  # General admin
    if 8000 <= code <= 8999: return "INF"  # Plant services
    if 9000 <= code <= 9999: return "DC"   # Debt/transfers
    return "ADM"  # Default

UNIVERSAL_LABELS = {
    "PS": "Public Safety",
    "INF": "Infrastructure & Utilities",
    "HHS": "Health & Human Services",
    "EDU": "Education",
    "CC": "Community & Culture",
    "ADM": "General Administration",
    "DC": "Debt & Capital",
    "PER": "Personnel Costs (Cross-cutting)",
}
```

## Tricky cases and judgment calls

### 1. "General Government" includes very different things

- **Cities**: City manager, city clerk, finance, legal, HR, IT, elections, city council. Usually 10-20% of budget.
- **Counties**: Board of Supervisors, CAO, assessor, auditor-controller, treasurer-tax collector, recorder, elections, public guardian, county counsel, grand jury. Usually 8-15% but covers more functions than city equivalent.
- **School districts**: Board of education, superintendent, district office administration. Usually 5-10%.

When comparing "admin overhead" across entity types, county numbers will look higher because counties run more administrative functions by law (assessor, recorder, etc.). This is structural, not waste.

### 2. Community Development: Infrastructure or Administration?

City "Community Development" includes planning, building inspection, code enforcement, housing programs, and redevelopment. It is mapped to INF because it enables physical development. But some of it (planning staff, zoning reviews) is closer to ADM. For detailed analysis, inspect `subcategory_1`:
- Building inspection, housing programs, redevelopment -> INF
- Planning commission, zoning administration -> ADM

### 3. Enterprise funds distort comparisons

Cities that run their own water/sewer/electric utilities have much larger total budgets than cities that contract these out. When comparing cities, either:
- **Exclude enterprise funds** and compare only governmental fund spending, OR
- **Include enterprise funds** but note which cities operate utilities

Example: Palo Alto (runs electric, gas, water, sewer, fiber) has a much larger total budget than neighboring cities that buy from private utilities. Comparing raw per-capita spending without adjusting is misleading.

### 4. Special districts report by object, not function

SCO special district data primarily shows what type of expense (salaries, supplies, benefits) rather than what service it funds. For functional analysis:
- Use the district type (fire, water, healthcare, parks) as the function
- All spending by a fire district -> PS
- All spending by a water district -> INF

### 5. Pension costs are embedded everywhere

CalPERS/CalSTRS contributions appear as employee benefits within every functional category. A city's "Public Safety" spending includes police officer pension costs. To analyze pension burden:
- Pull total pension contributions from CalPERS data or from Object 3000-series in SACS
- Express as a percentage of total spending or total payroll
- Do NOT double-count by adding PER to other categories

### 6. Combined categories in SCO data

Some entities report combined categories like "General Government and Public Safety" or "Health and Culture and Leisure." Options:
- Inspect `subcategory_1` and `subcategory_2` to split
- If subcategories are not available, use the first-named category as primary
- Flag the combined category in output so the user knows it is approximate

### 7. Capital vs. operating

Capital outlay can appear within functional categories (a new fire station in Public Safety) or as a standalone "Capital Outlay" category. For trend analysis, large one-time capital projects create spikes that distort year-over-year comparisons. Consider separating capital from operating spending.

## Validation checklist

When presenting normalized cross-entity comparisons, always verify:

- [ ] Enterprise fund treatment is consistent (all included or all excluded)
- [ ] Combined categories are flagged or split
- [ ] Pension costs are not double-counted
- [ ] Capital outlays are identified (one-time vs. recurring)
- [ ] Per-capita denominators use consistent population sources (DOF estimates, not Census decennial)
- [ ] Fiscal years match across entities being compared
- [ ] Entity types being compared are acknowledged (city vs. county is structural)
