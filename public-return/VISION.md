# Public Return

## What is this?

Enter your address. See every government entity that taxes you. See where every dollar goes. See what you get for it. Understand why.

Not a dashboard. Not a gotcha tool. A diagnostic tool for public investment that treats government spending the way an investor treats a portfolio: what are we putting in, what are we getting out, and what's in the way of getting more?

## The problem

Nobody understands where their tax dollars go.

A homeowner in Redwood City, CA pays ~$14,000/year in property tax to 15-20 separate government entities — county, city, school districts, community college district, open space district, mosquito abatement district, and more. They have no idea what each one does with the money, whether they're getting a good deal compared to similar places, or why their kids' school has 32 students per class despite high spending per pupil.

Democrats say "most of your county budget goes to education." Republicans say "most of it goes to pensions." Both can be right simultaneously, and neither framing helps a citizen understand what's actually happening.

## What exists today and why it fails

**USAFacts** (Steve Ballmer, ~$40M/year): Built a government 10-K report. Gets 865K monthly visits — poor ROI. Shows aggregate national data, not YOUR money. No emotional hook. No one comes back.

**OpenGov**: Started as citizen transparency, pivoted entirely to selling enterprise software to governments. Acquired for $1.8B. The pivot tells you something: they concluded there's no consumer market for budget transparency.

**Transparent California**: Actually works — because it's personal (look up YOUR fire chief's salary) and emotional (outrage is shareable). But it's a gotcha tool with no context. Salary without context is misleading.

**Ed-Data**: Shows per-pupil spending but deliberately excludes parcel taxes and foundation donations — the exact mechanism by which wealthy districts outspend poor ones.

**National Priorities Project**: Federal tax receipt calculator. Good concept but federal only. Property tax is where the confusion and the money is.

### What they all miss

1. No address-based personalization — none lets you start from YOUR tax bill
2. No explanation of WHY — they show numbers without structural context
3. No connection between spending and outcomes
4. No comparison to similar places
5. No connection to decisions (ballot measures, budget hearings)

## The framing: Abundance, not austerity

This product is NOT "government wastes your money." That framing is lazy, misleading, and politically toxic.

The framing is **abundance** (per Ezra Klein and Derek Thompson): America is rich enough to have good schools, fast transit, affordable housing, and functioning infrastructure. The question is what's preventing us from getting more for what we spend, and what would have to change.

### What this means in practice

| Rage bait | Abundance framing |
|-----------|-------------------|
| "Your fire chief makes $400K!" | "Your city spends 3x what comparable cities do per resident on fire. Here's why, and what others do differently." |
| "Pensions are eating your taxes!" | "22% of your school budget is catching up on decades of pension underfunding. Here's what that means for class sizes today, and when the catch-up ends." |
| "Government waste!" | "This interchange cost $500M. A comparable one in Oregon cost $180M. The difference is mostly soft costs: consulting, environmental review, litigation." |
| Conclusion: government is bad | Conclusion: government could deliver more with what it has |

## The honesty problem: Outcomes are hard

Public spending outcomes are diffuse, lagged, and interconnected. This product must handle that honestly rather than pretending clean ROI exists.

**Temporal diffusion**: The pensions we pay now funded teachers 20 years ago. Debt service pays for past infrastructure decisions — sometimes good ones. Infrastructure investments pay off over 50-100 years.

**Population diffusion**: Caltrain electrification ($2.4B) benefits riders, drivers (less congestion), employers (labor pool), property owners (land value), and the tax base (economic growth). A school dollar produces outcomes in the student, the community, and the economy — over a lifetime.

**Counterfactual difficulty**: Fire department spending produces the absence of fires. How do you measure what didn't happen?

## The product: Five layers

### Layer 1: What you pay
Enter your address. See your total tax burden across all jurisdictions. Pure facts, no interpretation.

"You pay $14,200/year in property tax. It goes to 17 entities."

### Layer 2: Where it goes
For each entity, see spending by category: programs vs personnel vs pensions/benefits vs debt service vs capital. Simple pie/bar visualization.

"Redwood City School District: 62% personnel, 19% pension catch-up, 8% facilities, 6% admin, 5% other."

### Layer 3: What you get (outcomes)
Measurable outcomes mapped to spending: test scores, graduation rates, crime rates, response times, road quality, park acres, transit ridership.

"Your district: $23K/pupil, 65% proficiency. Comparable district: $19K/pupil, 71% proficiency."

### Layer 4: The structural diagnosis
WHY the numbers are what they are. Not editorializing — explaining the mechanisms.

"The $4K/pupil gap is mostly pension catch-up (AB 1469, 2014) and higher personnel costs. The comparable district has a newer pension plan with lower legacy obligations."

### Layer 5: The investment view
Capital spending framed as investment with expected returns, using evidence from comparable projects elsewhere.

"This $2.4B Caltrain project costs $X per household. Comparable transit electrification in Denver produced 40% ridership growth and 15% property value increase within 5 years of completion."

## Bonus: The decision layer
When ballot measures appear, connect them to the framework:

"Measure X would add $200/year to your property tax to fund road repairs. Your city's current road condition score is 58/100, ranking 340th of 482 CA cities. The measure targets bringing it to 72/100 within 5 years. Cities that passed similar measures improved by an average of 12 points."

## Who is this for?

**Primary**: Homeowners who pay property tax and want to understand it. Not policy wonks — regular people who vote and care about their community.

**Secondary**: Local journalists covering city/county/school budgets. They need the comparison and structural context.

**Tertiary**: Civic leaders and candidates who want to ground budget debates in data rather than ideology.

## How does it sustain itself?

- **Traffic**: Property tax bills arrive annually. Ballot measures drive seasonal spikes. "Where does my money go?" is a perennial search query.
- **Shareability**: "I pay $3,200/year to pension catch-up" is personal and shareable without being rage bait if framed with context.
- **B2B**: Local news organizations embedding budget context in coverage. Real estate platforms showing tax burden + service quality by neighborhood.
- **Portfolio signal**: Demonstrates genuinely original product thinking — the address-based personalization layer that nobody has built.

## Technical feasibility (to be validated)

The data largely exists across ~10 public sources:
- County assessor: address to Tax Rate Area to taxing jurisdictions
- State Controller (bythenumbers.sco.ca.gov): city/county/special district budgets
- CDE/SACS/Ed-Data: school district finances
- CalPERS/CalSTRS: pension obligations by employer
- CDE DataQuest: school outcome metrics
- CA DOJ OpenJustice: crime data
- MTC: road condition scores
- Census: demographics for comparable jurisdiction matching

The open question is whether the address-to-jurisdiction-to-budget linking layer can be built from public data, or whether it requires manual integration from county assessor records.

## MVP scope

**One zip code: 94062 (Redwood City, CA).**

Build the five layers for a single address. Hand-curate the jurisdiction mapping and budget data if APIs don't exist. Prove the concept works as a user experience before solving the data integration problem at scale.

If a hand-built version for one zip code is compelling, the scaling problem becomes a fundraising pitch, not a prerequisite.
