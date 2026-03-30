# CAL-ACCESS: California Campaign Finance Data

## What this is

CAL-ACCESS is the California Secretary of State's database tracking money in state politics -- campaign contributions, expenditures, and lobbying activity. It contains every dollar donated to or spent by California state candidates, ballot measure committees, and political parties. The raw database has 76 tables and is notoriously messy. Two access paths exist: cleaned/processed CSVs from the California Civic Data Coalition (recommended) and raw bulk downloads from the Secretary of State.

## Data sources

### 1. Processed CSVs via Big Local News (recommended)

The California Civic Data Coalition's open-source tools clean and normalize CAL-ACCESS data into well-structured CSV files. These are hosted by Stanford's Big Local News project.

```
https://biglocalnews.org
```

Register for a free account, then search for the **"California campaign finance data"** project. Files update daily.

Documentation of processed file schemas:
```
https://calaccess.californiacivicdata.org/documentation/processed-files/
```

### 2. Raw bulk download from Secretary of State

```
https://campaignfinance.cdn.sos.ca.gov/dbwebexport.zip
```

Updated daily. Contains tab-delimited text files from all 76 CAL-ACCESS database tables. ~1 GB compressed.

Documentation/data dictionary:
```
https://campaignfinance.cdn.sos.ca.gov/calaccess-documentation.zip
```

### 3. Interactive search (not bulk)

```
https://powersearch.sos.ca.gov/
```

Web UI for looking up individual filers, filings, and contributions. Not suitable for bulk analysis.

## Authentication

None for any access path. All data is public.

## Recommended approach: Processed CSVs

The processed files from the California Civic Data Coalition organize raw CAL-ACCESS data into normalized tables organized around California's campaign finance forms. For most use cases, you need only a few tables.

### Key processed files

| File | Description |
|------|-------------|
| **Form460Filing** | Campaign Disclosure Statement (semi-annual/pre-election filings) |
| **Form460ScheduleAItem** | Monetary contributions received |
| **Form460ScheduleB1Item** | Loans received |
| **Form460ScheduleCItem** | Nonmonetary contributions received |
| **Form460ScheduleDItem** | Payments supporting/opposing candidates |
| **Form460ScheduleEItem** | Payments made (expenditures) |
| **Form460ScheduleFItem** | Accrued expenses (unpaid bills) |
| **Form496Filing** | Late independent expenditure reports |
| **Form497Filing** | Late contribution reports |
| **CandidateFlat** | Simple candidate list with party, office, district |
| **BallotMeasureFlat** | Ballot measures with names, descriptions |

### Form460ScheduleAItem fields (monetary contributions)

This is the core table -- who gave money to whom.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Unique record ID |
| `filing` | FK | Reference to the Form 460 filing |
| `line_item` | int | Form line number |
| `date_received` | date | When the contribution was received |
| `date_received_thru` | date | End date if contribution spans multiple days |
| `amount` | decimal | Amount received in this period |
| `cumulative_election_amount` | decimal | Total from this contributor during election cycle |
| `cumulative_ytd_amount` | decimal | Year-to-date total from this contributor |
| `contributor_code` | string | `IND` (individual), `COM` (committee), `OTH` (other), `PTY` (party), `SCC` (small contributor committee), `OFF` (officeholder), `RCP` (recipient committee) |
| `contributor_lastname` | string | Last name or business name |
| `contributor_firstname` | string | First name (individuals) |
| `contributor_city` | string | City |
| `contributor_state` | string | State |
| `contributor_zip` | string | ZIP code |
| `contributor_employer` | string | Employer (individuals) |
| `contributor_occupation` | string | Occupation (individuals) |
| `contributor_is_self_employed` | bool | Self-employment flag |
| `contributor_committee_id` | string | Filer ID if contributor is a committee |
| `intermediary_lastname` | string | Intermediary/bundler last name |
| `intermediary_firstname` | string | Intermediary first name |
| `intermediary_city` | string | Intermediary city |
| `intermediary_state` | string | Intermediary state |
| `intermediary_zip` | string | Intermediary ZIP |
| `intermediary_employer` | string | Intermediary employer |
| `intermediary_occupation` | string | Intermediary occupation |
| `intermediary_is_self_employed` | bool | Intermediary self-employment flag |
| `intermediary_committee_id` | string | Intermediary committee ID |
| `transaction_id` | string | Unique transaction ID across filing versions |
| `transaction_type` | string | `F` (forgiven loan), `I` (intermediary), `R` (returned), `T` (third-party), `X` (transfer) |
| `memo_reference_number` | string | Reference to attached memo |

### Form460ScheduleEItem fields (expenditures)

Who the campaign paid money to and for what.

| Field | Type | Description |
|-------|------|-------------|
| `amount` | decimal | Amount paid |
| `payee_lastname` | string | Vendor/payee name |
| `payee_city` | string | Payee city |
| `payee_state` | string | Payee state |
| `expense_description` | string | What the expenditure was for |
| `payment_code` | string | Payment type code |

## How to use

### Download processed data from Big Local News

```python
# Register at biglocalnews.org, get your credentials
# Then use their Python client or download CSVs directly

import pandas as pd

# After downloading from Big Local News:
contributions = pd.read_csv("Form460ScheduleAItem.csv")
filings = pd.read_csv("Form460Filing.csv")

# Join contributions to filings to get the filer (candidate/committee)
merged = contributions.merge(
    filings[["id", "filer_id", "filer_lastname", "filer_firstname", "election_date"]],
    left_on="filing",
    right_on="id",
    suffixes=("", "_filing"),
)
```

### Find top donors to a candidate

```python
def top_donors(df: pd.DataFrame, filer_id: str, n: int = 20):
    """Find the largest contributors to a specific filer."""
    filer_contribs = df[df["filer_id"] == filer_id]
    by_donor = (
        filer_contribs
        .groupby(["contributor_lastname", "contributor_firstname"])
        .agg(
            total=("amount", "sum"),
            count=("amount", "count"),
            first_date=("date_received", "min"),
            last_date=("date_received", "max"),
        )
        .sort_values("total", ascending=False)
    )
    return by_donor.head(n)
```

### Analyze contributions by type

```python
def contribution_breakdown(df: pd.DataFrame, filer_id: str):
    """Break down contributions by contributor type."""
    filer = df[df["filer_id"] == filer_id]
    code_labels = {
        "IND": "Individuals",
        "COM": "Committees",
        "OTH": "Other",
        "PTY": "Political Parties",
        "SCC": "Small Contributor Committees",
        "OFF": "Officeholders",
        "RCP": "Recipient Committees",
    }
    by_type = filer.groupby("contributor_code")["amount"].sum()
    by_type.index = by_type.index.map(lambda x: code_labels.get(x, x))
    return by_type.sort_values(ascending=False)
```

### Find contributions from a specific employer/industry

```python
def contributions_by_employer(df: pd.DataFrame, employer_pattern: str):
    """Find all contributions from people at a specific employer."""
    mask = df["contributor_employer"].str.contains(
        employer_pattern, case=False, na=False
    )
    matches = df[mask]
    by_recipient = (
        matches
        .groupby("filer_id")["amount"]
        .sum()
        .sort_values(ascending=False)
    )
    return by_recipient
```

### Alternative: Raw download from SOS

```bash
# Download the raw bulk data (warning: ~1 GB, 76 tables)
curl -o dbwebexport.zip https://campaignfinance.cdn.sos.ca.gov/dbwebexport.zip
unzip dbwebexport.zip -d calaccess_raw/

# Key tables in the raw download:
# RCPT_CD - Receipts (contributions received) -- this is the raw version of Schedule A
# EXPN_CD - Expenditures made
# FILER_FILINGS_CD - Links filers to their filings
# FILERS_CD - Filer information
# CVR_CAMPAIGN_DISCLOSURE_CD - Cover page of campaign disclosure statements
# SMRY_CD - Summary totals from filings
# LOAN_CD - Loans received and made
```

```python
# Load a raw table (tab-delimited, no headers in some files)
import pandas as pd

# RCPT_CD has contribution records
rcpt = pd.read_csv(
    "calaccess_raw/RCPT_CD.TSV",
    sep="\t",
    low_memory=False,
    encoding="latin-1",  # Some files have non-UTF8 characters
)
```

## What questions this answers

- Who are the biggest donors to my state legislator?
- How much money has a candidate raised and from what types of sources?
- Are there patterns in who donates to candidates who vote a certain way?
- What industries or employers contribute most to a ballot measure campaign?
- How much did a specific person or company give across all candidates?
- What is the total spending on a ballot measure (for and against)?
- How do contribution patterns differ between local vs. out-of-district donors?

### Combining with other data

Join with Open States legislator data (by filer_id or name matching) to correlate campaign donations with voting records. Join with SCO spending data to see whether donors benefit from government contracts. Join with Census demographic data to analyze donor geography vs. district demographics.

## Gotchas

- **Use the processed CSVs, not the raw download**: The raw CAL-ACCESS database has 76 tables with cryptic column names, inconsistent encoding, and duplicate records. The Civic Data Coalition's processed files fix all of this.
- **Big Local News requires free registration**: You need an account at biglocalnews.org to download the processed CSVs. Registration is free and instant.
- **`filer_id` is the key identifier**: This is how you link contributions to specific candidates or committees. It is NOT the same as a candidate's name -- the same person may have multiple filer IDs across different campaigns.
- **Contribution limits exist but are not enforced in the data**: The data contains all reported contributions. Contributions exceeding legal limits are present (they may be returned later, which shows as a separate record with `transaction_type = 'R'`).
- **Duplicate filings**: Candidates file amended returns. Use the most recent filing version or the processed `*Version` tables to avoid double-counting.
- **`amount` can be negative**: Returned contributions appear as negative amounts in some representations.
- **Name matching is messy**: Contributor names are entered by filers and not standardized. "John Smith", "SMITH, JOHN", "Smith, John Q." may all be the same person. Use employer + ZIP + name fuzzy matching for deduplication.
- **Intermediaries/bundlers**: Some contributions come through intermediaries (bundlers). The actual donor is in the `contributor_*` fields; the bundler is in `intermediary_*` fields.
- **The django-calaccess-raw-data project**: This is a Django ORM wrapper around the raw CAL-ACCESS tables (github.com/california-civic-data-coalition/django-calaccess-raw-data). It requires a full Django project setup with PostgreSQL. For our use case, the processed CSV download is simpler and sufficient.
- **Ballot measure committees**: These have filer_ids like any other committee. Use the `BallotMeasureFlat` table to map measure names/numbers to their support/oppose committees.
- **Data goes back to ~1998**: But older records are less complete and use legacy formats.
- **Late contributions (Form 497) and independent expenditures (Form 496)**: These are filed separately from the main Form 460 and are in their own tables. For complete spending pictures near elections, you need all three.
