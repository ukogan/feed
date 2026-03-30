# Synthesizer: Citizen Query Translation

## What this does

Translates natural language questions from citizens into structured data queries across Public Return's data sources. This is the "front door" skill -- it takes a messy human question and routes it to the right combination of data source skills, normalizers, and synthesizers to produce an honest answer.

## Design principle: Abundance framing, not rage bait

Every answer should be framed to inform, not inflame. The goal is to help citizens understand where their money goes and what it buys, not to manufacture outrage. This means:

- Lead with **what services are provided**, then show costs
- Always include **context** (peer comparison, trend, structural explanation)
- Distinguish between **discretionary choices** (policy) and **non-discretionary obligations** (pensions, mandates, debt)
- Name the **tradeoffs** rather than implying waste
- When spending looks high, explain what would happen if it were cut

## Query taxonomy

### Category 1: "Where does my money go?"

**Example questions:**
- "Where do my property taxes go?"
- "What does my city spend money on?"
- "How much of my taxes go to pensions?"
- "What am I paying for?"

**Intent**: Understand spending allocation

**Routing:**

```
1. Identify jurisdiction
   -> boe-tra-lookup (if address/zip given)
   -> User clarification (if ambiguous: "Do you mean your city, county, or school district?")

2. Get spending data
   -> sco-bythenumbers (for city/county/special district)
   -> cde-school-finances (for school district)

3. Normalize categories
   -> normalizers/spending-categories

4. Add pension context
   -> calpers-pension (for city/county)
   -> SACS Object 3101-3202 (for school district CalSTRS/CalPERS)

5. Add comparison context
   -> normalizers/comparable-jurisdictions
   -> sco-bythenumbers (for peer cities)

6. If address given, use full property tax synthesizer
   -> synthesizers/ca-property-tax
```

**Answer frame:**
```
Your {entity} spent ${total} last year (${per_capita} per resident).
Here is where it went:
  [spending breakdown by universal category]

For context, similar {type}s in the {region} spend ${peer_avg} per
{unit}. {Entity}'s spending is {comparison_description}.

{pension_pct}% of the budget goes to pension obligations -- retirement
benefits earned by current and former employees. This is {trend} over
the past decade and is largely non-discretionary (set by actuarial
requirements, not annual policy choices).
```

### Category 2: "Is my city/district spending too much on X?"

**Example questions:**
- "Is my city spending too much on police?"
- "Why does my city spend so much on administration?"
- "Are we paying too much for schools?"
- "Why is our fire department so expensive?"

**Intent**: Evaluate spending relative to expectations

**Routing:**

```
1. Identify entity and spending category
   -> Parse the category from the question
   -> Map to universal taxonomy (normalizers/spending-categories)

2. Get spending data for target entity
   -> sco-bythenumbers or cde-school-finances

3. Find comparable entities
   -> normalizers/comparable-jurisdictions

4. Get same category spending for comparables
   -> sco-bythenumbers or cde-school-finances (for each peer)

5. Normalize all entities
   -> normalizers/spending-categories (same adjustments for all)

6. For public safety questions, add outcome data
   -> ca-doj-crime (crime rates for context)

7. For school questions, add outcome data
   -> cde-test-scores (CAASPP proficiency)
```

**Answer frame:**
```
{Entity} spends ${amount} per {unit} on {category}, which is
{comparison} compared to similar {type}s:

  [peer comparison table]

What this buys:
  [specific services, staffing levels, or outcomes]

Why it might be {higher/lower}:
  - {structural_reason_1} (e.g., "contracts fire service from county")
  - {policy_reason_1} (e.g., "maintains a higher officer-per-capita ratio")
  - {cost_reason_1} (e.g., "Bay Area compensation is higher than state average")

The question is not just "how much?" but "what are you getting for it?"
{outcome_data_if_available}
```

### Category 3: "How does my school compare?"

**Example questions:**
- "How good is my school district?"
- "How do test scores in my district compare?"
- "Are we getting good results for what we spend?"
- "Is my school district better than the neighboring one?"

**Intent**: Evaluate education quality and spending efficiency

**Routing:**

```
1. Identify school district
   -> CDS code lookup or name match

2. Use full school district report synthesizer
   -> synthesizers/school-district-report

3. Find comparable districts
   -> normalizers/comparable-jurisdictions (school methodology)

4. Get test scores for all
   -> cde-test-scores (CAASPP for target + peers)

5. Get financial data for all
   -> cde-school-finances (SACS for target + peers)
```

**Answer frame:**
```
{District} serves {enrollment} students across grades {span}.

OUTCOMES:
  {ela_pct}% of students meet ELA standards; {math_pct}% meet math.
  Among similar districts (same size, similar demographics), this is
  {comparison}.

  The achievement gap between socioeconomically disadvantaged and
  non-disadvantaged students is {gap} percentage points -- {gap_context}.

SPENDING:
  Per-pupil spending: ${per_pupil} ({comparison} vs. peers)
  {instruction_pct}% goes to classroom instruction
  {admin_pct}% goes to administration
  {benefits_pct}% goes to employee benefits and pension

SPENDING vs. OUTCOMES:
  Among peers, the correlation between per-pupil spending and test
  scores is {weak/moderate}. The strongest predictor of test scores
  is student demographics ({sed_pct}% socioeconomically disadvantaged),
  not spending levels.
```

### Category 4: "Why are my taxes so high?"

**Example questions:**
- "Why is my property tax bill so high?"
- "Why does this cost so much?"
- "Why do my taxes keep going up?"

**Intent**: Understand tax burden and drivers of cost growth

**Routing:**

```
1. Identify jurisdiction and tax type
   -> boe-tra-lookup (property tax)

2. Property tax: use full synthesizer
   -> synthesizers/ca-property-tax

3. Get multi-year trend data
   -> sco-bythenumbers (multiple fiscal years for target entity)

4. Identify cost growth drivers
   -> calpers-pension (pension contribution rate trend)
   -> transparent-ca (compensation growth)
   -> census-permits (if growth/development is a factor)

5. Compare to peers
   -> normalizers/comparable-jurisdictions
```

**Answer frame:**
```
Your property tax bill has {n} components:
  [base 1% levy breakdown]
  [voter-approved bonds]
  [parcel taxes]
  [special assessments]

Over the past {n} years, your total tax burden has grown by {pct}%.
The main drivers:

1. Rising assessed values: Prop 13 limits increases to 2%/year on the
   base, but reassessment on sale can reset to market value.

2. Voter-approved bonds: {list of recent bond measures}

3. Rising service costs: Pension contributions have grown from {old}%
   to {new}% of budgets. Employee compensation has grown {rate}%
   annually, driven by {factors}.

4. {Additional context: new services, infrastructure needs, etc.}

Compared to similar communities, your effective tax rate is
{comparison}. The main structural difference is {factor}.
```

### Category 5: "How much do government employees make?"

**Example questions:**
- "What does the city manager make?"
- "How much do teachers in my district earn?"
- "What are police overtime costs?"
- "How much does the superintendent make?"

**Intent**: Understand public employee compensation

**Routing:**

```
1. Identify entity and role
   -> transparent-ca (individual compensation data)
   -> If school district: also cde-school-finances (aggregate salary data)

2. Get compensation data
   -> transparent-ca (search by agency slug and job title keywords)

3. Add context
   -> normalizers/comparable-jurisdictions (find peer entities)
   -> transparent-ca (same roles at peer entities)
   -> calpers-pension (pension contribution context)
```

**Answer frame:**
```
{Role} at {entity}: ${total_comp} total compensation
  Base pay:    ${base}
  Other pay:   ${other} (includes {components})
  Benefits:    ${benefits} (includes ${pension} pension contribution)

Context:
  Median {role} at similar {type}s: ${peer_median}
  Range: ${peer_min} to ${peer_max}
  {Entity}'s {role} is at the {percentile} percentile.

Total compensation includes employer-paid benefits (health insurance,
pension contributions) that the employee does not receive as cash.
The pension contribution reflects the employer's cost to fund both
current-year benefits and past unfunded liabilities.
```

### Category 6: "What's happening with pensions?"

**Example questions:**
- "How much pension debt does my city have?"
- "What's the funded ratio?"
- "How much of my taxes go to pensions?"
- "Is the pension situation getting better or worse?"

**Intent**: Understand pension obligations and their budget impact

**Routing:**

```
1. Identify entity
   -> Determine if CalPERS, CalSTRS, 1937 Act (SamCERA, LACERA, etc.)

2. Get pension data
   -> calpers-pension (for cities/counties/special districts)
   -> cde-school-finances SACS Object 3101-3202 (for school CalSTRS)

3. Get total budget for ratio
   -> sco-bythenumbers (total expenditures)
   -> cde-school-finances (total expenditures for schools)

4. Compare to peers
   -> normalizers/comparable-jurisdictions
   -> calpers-pension (for peer entities)

5. Get trend data
   -> Multi-year pension contribution rates
```

**Answer frame:**
```
{Entity} participates in {pension_system}.

Current status:
  Funded ratio: {ratio}% (meaning {100-ratio}% of promised benefits
  are not yet funded)
  Unfunded liability: ${ufl}
  Annual employer contribution: ${contribution} ({pct}% of payroll)

Budget impact:
  Pension costs consume {budget_pct}% of {entity}'s total budget.
  This has grown from {old_pct}% in {old_year}.

  For every $1 in salary paid to a {typical_role}, {entity} pays
  an additional ${pension_per_dollar} to CalPERS for that employee's
  retirement.

Compared to peers:
  [peer funded ratios and contribution rates]

Trend: {improving/declining}. The funded ratio has moved from {old}%
to {new}% over {n} years. {explanation of drivers: investment returns,
benefit changes, demographic shifts}.

Important: Pension obligations are legally protected under CA law.
Reducing pension costs for current employees requires negotiation;
for retirees, it is essentially impossible. The main lever is
reducing headcount or negotiating lower benefits for new hires
(PEPRA, enacted 2013, did this).
```

## Query parsing rules

### Extracting the jurisdiction

| User says | Interpretation |
|-----------|---------------|
| "my city" / "Redwood City" | City entity |
| "my school district" / "RCSD" | School district |
| "my county" / "San Mateo County" | County entity |
| Zip code (e.g., "94062") | Use BOE TRA to find all entities |
| Address | Use BOE TRA to find all entities |
| Ambiguous ("my taxes") | Ask: "Which entity? Your city, county, or school district?" |

### Extracting the spending category

| User says | Universal category |
|-----------|-------------------|
| "police" / "cops" / "public safety" / "law enforcement" | PS |
| "fire" / "fire department" / "firefighters" | PS (PS.fire) |
| "roads" / "streets" / "infrastructure" / "potholes" | INF |
| "water" / "sewer" / "utilities" | INF |
| "schools" / "education" / "teachers" | EDU |
| "parks" / "recreation" / "library" / "arts" | CC |
| "administration" / "overhead" / "bureaucracy" / "city hall" | ADM |
| "pensions" / "retirement" / "CalPERS" | PER |
| "debt" / "bonds" | DC |
| "health" / "mental health" / "social services" / "homeless" | HHS |

### Extracting the comparison intent

| User says | Intent |
|-----------|--------|
| "compared to" / "vs" / "versus" | Explicit comparison between named entities |
| "too much" / "too high" / "wasteful" | Peer comparison with normative framing |
| "how does X compare" / "how good" | Neutral peer comparison |
| "better" / "worse" / "rank" | Ranking among peers |
| "over time" / "trend" / "growing" / "increasing" | Multi-year trend |
| "why" | Causal explanation (structural + policy) |

## Handling adversarial or loaded questions

Citizens sometimes arrive with a conclusion and want data to support it. The system should provide honest data regardless of framing.

| Loaded question | Reframe to |
|----------------|------------|
| "Why are bureaucrats stealing my taxes?" | "Here is how {entity} spends its budget, including administrative costs compared to peers" |
| "Why can't teachers just take a pay cut?" | "Here is teacher compensation at {district} compared to peers, and the labor market context" |
| "Government workers are overpaid, right?" | "Here is total compensation by role compared to similar public and private sector positions" |
| "The schools are failing" | "Here is how {district} students perform on state assessments, by subgroup, compared to similar districts" |

The system never argues or editorializes. It provides data, context, and comparison, and lets the citizen draw conclusions.

## Multi-step synthesis example

**Question**: "Is Redwood City spending too much on police?"

**Step 1: Parse**
- Entity: Redwood City (city)
- Category: PS (Public Safety -> PS.police)
- Intent: Peer comparison with normative framing

**Step 2: Get Redwood City public safety spending**
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json
  ?entity_name=Redwood City&fiscal_year=2022-2023&category=Public Safety
```

**Step 3: Find peer cities**
-> normalizers/comparable-jurisdictions (city methodology)
-> Result: San Mateo, Mountain View, Daly City, Milpitas, Hayward, Santa Clara

**Step 4: Get public safety spending for all peers**
```
GET https://bythenumbers.sco.ca.gov/resource/ju3w-4gxp.json
  ?$where=entity_name in ('San Mateo','Mountain View','Daly City','Milpitas','Hayward','Santa Clara')
  AND fiscal_year='2022-2023' AND category='Public Safety'
```

**Step 5: Normalize**
-> spending-categories (ensure consistent categorization)
-> Per-capita calculation using DOF population estimates
-> Exclude utility enterprise funds from denominators

**Step 6: Add outcome data**
-> ca-doj-crime (crime rates for Redwood City and peers)

**Step 7: Compose answer**
```
Redwood City spends approximately $900 per resident on public safety
(police and fire), compared to a peer average of $780.

  San Mateo:     $850/capita
  Mountain View: $750/capita  (contracts fire from county)
  Daly City:     $820/capita  (contracts police from county)
  REDWOOD CITY:  $900/capita
  Milpitas:      $680/capita
  Santa Clara:   $760/capita
  Hayward:       $730/capita

Redwood City's higher spending is partly explained by:
- Operating its own police AND fire departments (some peers contract
  one or both, shifting costs off their books)
- Bay Area public safety compensation: median police officer total
  compensation is ~$220K including benefits and pension
- CalPERS pension contributions have grown from ~8% to ~15% of
  public safety department budgets over the past decade

What it buys: Redwood City's Part 1 crime rate is X per 1,000
residents, compared to the peer average of Y. Response times average
Z minutes.

The question is whether the service level justifies the cost
relative to peers, which depends on community priorities.
```

## Error handling

- **Ambiguous entity**: Ask the user to clarify before proceeding. Do not guess.
- **No data available**: State clearly what is missing and why (e.g., "SCO data for FY 2023-24 is not yet published"). Offer the most recent available year.
- **Question spans multiple entity types**: Handle each entity type separately, then summarize. "Where do my taxes go?" involves city + county + school + special districts -- use the ca-property-tax synthesizer.
- **Question is outside scope**: If the question requires data Public Return does not have (e.g., federal spending, private sector, other states), say so and suggest where to look.
- **Contradictory data**: If two sources disagree (e.g., SCO vs. city budget document), note the discrepancy and explain which source is used and why.
