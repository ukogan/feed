# CA Department of Education: School Finances (SACS)

## What this is

The Standardized Account Code Structure (SACS) is California's uniform financial reporting system for all K-12 local educational agencies (LEAs) -- school districts, county offices of education, and charter schools. Every LEA submits annual "unaudited actual" financial data to CDE using SACS codes. This is the definitive source for understanding how California school districts spend money. Data is available from FY 1995-96 through 2024-25.

For FY 2024-25, 1,743 LEAs (983 districts, 702 charter schools, 58 county offices) submitted data.

## Data URL

Download page:
```
https://www.cde.ca.gov/ds/fd/fd/
```

Direct download (most recent year):
```
https://www3.cde.ca.gov/fiscal-downloads/sacs_data/2024-25/sacs2425.exe
https://www3.cde.ca.gov/fiscal-downloads/sacs_data/2023-24/sacs2324.exe
```

URL pattern for any year:
```
https://www3.cde.ca.gov/fiscal-downloads/sacs_data/{YYYY-YY}/sacs{YYYYYY}.exe
```
Example: `2022-23` -> `sacs2223.exe`

SACS Data Viewer (web UI, 2022-23 onward):
```
https://www.cde.ca.gov/ds/fd/dv/
```

Ed-Data (friendly interface for browsing, not bulk download):
```
https://www.ed-data.org/
```

## Authentication

None. Public download. No key required.

## File format

- Self-extracting EXE containing a Microsoft Access database (`.mdb`)
- Each file is 40-45 MB compressed
- On Mac/Linux, use `7z` or `unzip` to extract (the EXE is a standard ZIP archive)
- The `.mdb` file can be read with `mdbtools` (command line) or Python's `pandas` via `pyodbc`/`mdb-export`

## SACS account code structure

Each financial line item is coded with a 19-digit account string:

```
Fund(2) - Resource(4) - Year(1) - Goal(4) - Function(4) - Object(4) - Site(2)
```

Example: `62-6300-0-1110-1000-4300-01`
- Fund 62 = Charter School Enterprise Fund
- Resource 6300 = Restricted Lottery
- Year 0 = Same as fiscal year
- Goal 1110 = Regular Education, K-12
- Function 1000 = Instruction
- Object 4300 = Books and Supplies (Materials & Supplies)
- Site 01 = Specific school site

### Object codes (what was spent)

| Object Code | Definition |
|-------------|------------|
| 1000-1999 | Certificated Personnel Salaries (teachers, administrators) |
| 2000-2999 | Classified Personnel Salaries (non-credentialed staff) |
| 3000-3999 | Employee Benefits (STRS, PERS, health insurance) |
| 4000-4999 | Books and Supplies |
| 5000-5999 | Services and Other Operating Expenditures |
| 6000-6999 | Capital Outlay |
| 7000-7499 | Other Outgo |
| 7600-7699 | Other Financing Uses |
| 8000-8999 | Revenues and Other Financing Sources |
| 9000-9999 | Balance Sheet |

### Function codes (what service was performed)

| Function | Description |
|----------|-------------|
| 1000-1999 | **Instruction** (classroom teaching) |
| 1000 | Instruction (general) |
| 1110-1190 | Special Education instruction |
| 2000-2999 | **Instruction-Related Services** |
| 2100-2150 | Instructional supervision and administration |
| 2420 | Library, media, and technology |
| 2700 | School administration |
| 3000-3999 | **Pupil Services** |
| 3110 | Guidance and counseling |
| 3140 | Health services |
| 3600 | Pupil transportation |
| 3700 | Food services |
| 4000-4999 | **Ancillary Services** (athletics, etc.) |
| 5000-5999 | **Community Services** |
| 7000-7999 | **General Administration** |
| 7100 | Board and superintendent |
| 7200 | Other general administration |
| 7300-7700 | Fiscal, HR, central services |
| 8000-8999 | **Plant Services** (maintenance, operations, security) |
| 9000-9999 | **Other Outgo** (debt, transfers) |

### Fund codes (which pot of money)

| Fund | Description |
|------|-------------|
| 01 | General Fund (main operating fund for districts) |
| 09 | Charter School Special Revenue Fund |
| 11 | Adult Education |
| 12 | Child Development |
| 13 | Cafeteria |
| 14 | Deferred Maintenance |
| 21 | Capital Building Bond |
| 25 | Capital Facilities |
| 51 | Bond Interest and Redemption |
| 62 | Charter School Enterprise Fund |

### Goal codes (what population is served)

| Goal | Description |
|------|-------------|
| 0000 | Undistributed |
| 0001 | General Education, Pre-K |
| 1110 | Regular Education, K-12 |
| 3100-3800 | Alternative/continuation/vocational schools |
| 5000-5999 | Special Education |
| 7110 | Nonagency - Educational |

## Key database fields

| Field | Type | Description |
|-------|------|-------------|
| `Ccode` | Text(2) | County code (first 2 digits of CDS code) |
| `Dcode` | Text(5) | District code (digits 3-7 of CDS code) |
| `SchoolCode` | Text(7) | School code (last 7 digits of CDS, 0000000 = district-level) |
| `Fiscalyear` | Text(4) | Fiscal year |
| `Period` | Text(4) | Report period (`A` = Unaudited Actual) |
| `Fund` | Text(2) | Fund code |
| `Resource` | Text(4) | Resource code |
| `Goal` | Text(4) | Goal code |
| `Function` | Text(4) | Function code |
| `Object` | Text(4) | Object code |
| `Value` | Decimal | Dollar amount |
| `Dname` | Text(75) | District name |

## How to use

### Extract and load the data (Mac/Linux)

```bash
# The .exe is just a ZIP file
pip install mdbtools  # or: brew install mdbtools

# Download and extract
curl -o sacs2324.exe https://www3.cde.ca.gov/fiscal-downloads/sacs_data/2023-24/sacs2324.exe
7z x sacs2324.exe -o./sacs2324/

# List tables in the Access database
mdb-tables sacs2324/sacs2324.mdb

# Export a table to CSV
mdb-export sacs2324/sacs2324.mdb SACS > sacs2324.csv
```

### Load into Python

```python
import subprocess
import pandas as pd
import io

def load_sacs(mdb_path: str, table: str = "SACS") -> pd.DataFrame:
    """Export an MDB table to CSV via mdbtools, then load into pandas."""
    result = subprocess.run(
        ["mdb-export", mdb_path, table],
        capture_output=True, text=True
    )
    return pd.read_csv(io.StringIO(result.stdout))

df = load_sacs("sacs2324/sacs2324.mdb")
```

### Filter to a specific district

```python
# Redwood City Elementary: County=41, District=69005
rce = df[(df["Ccode"] == "41") & (df["Dcode"] == "69005")]

# General Fund expenditures only (Fund 01, Object 1000-7999)
expenditures = rce[
    (rce["Fund"] == "01") &
    (rce["Object"].str[:1].isin(["1","2","3","4","5","6","7"]))
]
```

### Calculate spending breakdown by function

```python
# Group by function to see instruction vs. admin vs. pupil services
by_function = expenditures.groupby("Function")["Value"].sum().sort_values(ascending=False)

# Simplify into categories
def categorize_function(func_code: str) -> str:
    code = int(func_code)
    if 1000 <= code <= 1999: return "Instruction"
    elif 2000 <= code <= 2999: return "Instruction-Related"
    elif 3000 <= code <= 3999: return "Pupil Services"
    elif 4000 <= code <= 4999: return "Ancillary Services"
    elif 5000 <= code <= 5999: return "Community Services"
    elif 7000 <= code <= 7999: return "General Administration"
    elif 8000 <= code <= 8999: return "Plant Services"
    elif 9000 <= code <= 9999: return "Other Outgo"
    else: return "Other"

expenditures["Category"] = expenditures["Function"].apply(categorize_function)
summary = expenditures.groupby("Category")["Value"].sum().sort_values(ascending=False)
```

### Calculate pension burden

```python
# Object 3101-3102 = STRS contributions
# Object 3201-3202 = PERS contributions
pension = expenditures[
    expenditures["Object"].str[:3].isin(["310", "320"])
]["Value"].sum()

total_expenditures = expenditures["Value"].sum()
pension_pct = round(pension / total_expenditures * 100, 1)
print(f"Pension as % of spending: {pension_pct}%")
```

### Compare districts

```python
# Key district codes for San Mateo County (Ccode=41)
districts = {
    "69005": "Redwood City Elementary",
    "69062": "Sequoia Union High",
    "68999": "San Mateo Union High",
    "68965": "San Carlos Elementary",
}

for dcode, name in districts.items():
    dist = df[(df["Ccode"] == "41") & (df["Dcode"] == dcode)]
    gen_fund = dist[dist["Fund"] == "01"]
    total = gen_fund[
        gen_fund["Object"].str[:1].isin(["1","2","3","4","5","6","7"])
    ]["Value"].sum()
    print(f"{name}: ${total:,.0f}")
```

## What questions this answers

- How much does my school district spend on instruction vs. administration?
- What percentage of the budget goes to employee salaries and benefits?
- How large is the pension burden (CalSTRS/CalPERS contributions)?
- How does my district compare to similar districts in per-pupil spending?
- What share of spending comes from restricted vs. unrestricted funds?
- How has spending changed over time?
- What are the largest non-salary expenditure categories?

### Combining with other data

Join with CAASPP test scores (by CDS code) to compare spending vs. outcomes. Join with Census population/income data to analyze spending relative to community wealth. Join with SCO ByTheNumbers for city-level spending comparison to see how school spending relates to municipal spending in the same community.

## Gotchas

- **File format is .exe wrapping an Access .mdb**: On Mac/Linux, treat the .exe as a ZIP and use `mdbtools` to extract CSV data. Do not try to run the .exe.
- **CDS codes must be zero-padded**: County is 2 digits, district is 5 digits, school is 7 digits. Always use string comparison, not numeric.
- **Fund 01 is the main operating fund**: For most district comparisons, filter to Fund 01 (General Fund). Charter schools may use Fund 09 or 62.
- **Object codes 1000-7999 = expenditures, 8000-8999 = revenues**: Do not mix them when calculating totals.
- **Negative values exist**: Adjustments, reversals, and transfers can produce negative line items.
- **Period "A" = Unaudited Actual**: This is the year-end actual data. Other periods (B, I1, I2) are budget and interim reports.
- **Not all charter schools file via SACS**: Some use the "Alternative Form" (separate download). About 700 charters are in SACS; others are in the alt form file.
- **Per-pupil calculations need ADA, not enrollment**: Use K12ADA (Average Daily Attendance) from the same dataset for per-pupil calculations. ADA is lower than enrollment.
- **Pension object codes**: CalSTRS is roughly object 3101-3102, CalPERS is 3201-3202. Employee health/welfare benefits are 3401-3602. Check the CSAM for exact mappings.
- **The data reflects what LEAs reported**: It may differ from board-adopted budgets or audited financials.
- **Pre-2004 data uses J-200 format**: A different structure. An archive file converts it to comparable format but requires separate handling.
