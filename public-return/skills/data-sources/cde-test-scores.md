# CA Department of Education: Test Scores (CAASPP)

## What this is

The California Assessment of Student Performance and Progress (CAASPP) publishes annual test results for every school and district in California. This is the primary outcome metric for K-12 education spending. Data is available as bulk CSV downloads — no API, but the files are well-structured and freely downloadable.

## Data URL

Research files (bulk download):
```
https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB?ps=true&lstTestYear=2024&lstTestType=B
```

Change `lstTestYear` for different years. Available from 2014-15 (2015) through 2024-25 (2025).

## Authentication

None. Public download. No key required.

## File format

- Caret-delimited CSV (separator: `^`)
- Also available as fixed-width TXT
- Files range from 8 MB to 200+ MB depending on granularity
- One row per school/district/subgroup/grade/test combination

## Key columns

| Column | Description |
|--------|-------------|
| `County_Code` | 2-digit county FIPS (San Mateo = 41) |
| `District_Code` | 5-digit district code |
| `School_Code` | 7-digit school code (0000000 = district aggregate) |
| `Test_Year` | e.g., 2024 |
| `Subgroup_ID` | 1 = All Students, 74 = Socioeconomically Disadvantaged, etc. |
| `Grade` | 13 = All Grades combined |
| `Test_Id` | 1 = ELA, 2 = Math |
| `Students_Tested` | Count |
| `Percentage_Standard_Met_and_Above` | The key outcome metric |
| `Percentage_Standard_Exceeded` | Top performers |
| `Percentage_Standard_Not_Met` | Lowest performers |

## How to use

### Download and filter

```python
import csv
import io
import httpx

async def get_district_scores(county_code: str, district_code: str, year: int = 2024):
    """Download CAASPP data and filter to a specific district."""
    # The entity-level file is smaller than the full file
    url = f"https://caaspp-elpac.ets.org/caaspp/ResearchFileListSB?ps=true&lstTestYear={year}&lstTestType=B"
    # Direct file URL pattern (entity-level, all students):
    file_url = f"https://caaspp-elpac.ets.org/caaspp/DashViewReportSB?ps=true&lstTestYear={year}&lstTestType=B&lstCounty={county_code}&lstDistrict={district_code}&lstSchool=0000000"

    # For bulk analysis, download the research file:
    # sb_ca{year}_all_csv_v3.zip from the research files page
    # Then filter by County_Code and District_Code
    pass
```

### Key district codes for 94062

| District | County Code | District Code | CDS Code |
|----------|-------------|---------------|----------|
| Redwood City Elementary | 41 | 69005 | 41-69005 |
| Sequoia Union High | 41 | 69062 | 41-69062 |

### What questions this answers

- What percentage of students in my district meet grade-level standards in ELA and math?
- How does my district compare to similar districts?
- Has performance improved or declined over the last 5-10 years?
- Is there an achievement gap between subgroups (income, race, English learner status)?
- How do per-pupil spending levels correlate with test performance across districts?

### Combining with spending data

The power is in the join: pull spending from CDE SACS or SCO ByTheNumbers, pull outcomes from CAASPP, and compare across districts. This answers: "Are districts that spend more per pupil actually getting better results?"

Spoiler: the correlation is weak, because spending differences are driven largely by pension obligations and personnel costs, not by classroom resources.

## Gotchas

- File is caret-delimited (`^`), not comma-delimited
- `Percentage_Standard_Met_and_Above` may be `*` (suppressed for small student counts <11)
- `Subgroup_ID` 1 = "All Students" is what you usually want for district comparison
- `Grade` 13 = "All Grades" aggregate
- `School_Code` 0000000 = district-level aggregate (not a specific school)
- Files are large — download once and cache locally
- 2020 and 2021 data is missing or incomplete due to COVID testing cancellations
