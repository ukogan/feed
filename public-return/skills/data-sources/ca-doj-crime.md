# CA DOJ OpenJustice: Crime Data

## What this is

The California Department of Justice Criminal Justice Statistics Center (CJSC) collects crime and clearance data from every law enforcement agency in California as part of the FBI's Uniform Crime Reporting (UCR) Program. The data covers the eight Part I offenses: criminal homicide, rape, robbery, aggravated assault, burglary, larceny-theft, motor vehicle theft, and arson. Data goes back ~20 years and is published annually via the OpenJustice portal.

Starting in 2021, California began transitioning to CIBRS (California Incident-Based Reporting System), the state version of NIBRS. Data from 2021 onward is a combination of summary and incident-based reporting, converted to summary format for consistency.

## Data URL

Main portal:
```
https://openjustice.doj.ca.gov/data
```

Direct CSV downloads (requires navigating the portal; login may be required for bulk download):
```
https://data-openjustice.doj.ca.gov/
```

Third-party mirror with stable CSV URLs:
```
http://library.metatab.org/openjustice.doj.ca.gov-datasets-1.1.1/data/crimes_clearances.csv
http://library.metatab.org/openjustice.doj.ca.gov-datasets-1.1.1/data/arrests.csv
```

## Authentication

None for the exploration UI. The bulk data portal at `data-openjustice.doj.ca.gov` may require a free account for some downloads. The metatab mirror requires no auth.

## Available datasets

| Dataset | Description |
|---------|-------------|
| `crimes_clearances` | Reported crimes and clearances by year, county, and agency |
| `arrests` | Arrest counts by year, race, agency, demographics |
| `arrest_dispositions` | Arrests with disposition outcomes |
| `complaints` | Civilian complaints against peace officers by agency |
| `homicide` | Detailed homicide data |
| `ripa_stop` | RIPA stop data from law enforcement encounters |
| `lea_cjp` | Law enforcement and criminal justice personnel |
| `leoka` | Law enforcement officers killed or assaulted |

## Key columns: crimes_clearances

| Column | Description |
|--------|-------------|
| `Year` | Reporting year |
| `County` | County name |
| `NCICCode` | NCIC agency code |
| `Violent_sum` | Total violent crimes (homicide + rape + robbery + aggravated assault) |
| `Homicide_sum` | Criminal homicides |
| `ForRape_sum` | Forcible rape / rape (definition changed 2014) |
| `Robbery_sum` | Robberies |
| `AggAssault_sum` | Aggravated assaults |
| `Property_sum` | Total property crimes (burglary + vehicle theft + larceny) |
| `Burglary_sum` | Burglaries |
| `VehicleTheft_sum` | Motor vehicle thefts |
| `LarcenyTheft_sum` | Larceny-thefts |
| `TotalStructural_sum` | Arson - structural |
| `TotalMobile_sum` | Arson - mobile |
| `TotalOther_sum` | Arson - other |
| `GrandTotal_sum` | Grand total arson |

Each crime type also has corresponding `_clr` (cleared by arrest) and `_clr_exc` (cleared by exceptional means) columns.

## Key columns: arrests

| Column | Description |
|--------|-------------|
| `Year` | Reporting year |
| `County` | County name |
| `Race` | Arrestee race/ethnicity |
| `Gender` | Arrestee gender |
| `Age_Group` | Arrestee age group |
| `Status_Type` | Felony, misdemeanor, status offense |
| `Offense_Level` | Offense category |

## How to use

### Download and analyze crimes by county

```python
import pandas as pd

# Download from metatab mirror
url = "http://library.metatab.org/openjustice.doj.ca.gov-datasets-1.1.1/data/crimes_clearances.csv"
df = pd.read_csv(url)

# Filter to San Mateo County, recent years
smc = df[df["County"] == "San Mateo"]
recent = smc[smc["Year"] >= 2018]

# Violent crime trend
trend = recent.groupby("Year")["Violent_sum"].sum()
print(trend)
```

### Calculate clearance rate

```python
# Clearance rate = clearances / crimes reported * 100
def clearance_rate(df, crime_col):
    clr_col = crime_col.replace("_sum", "_clr")
    crimes = df[crime_col].sum()
    cleared = df[clr_col].sum()
    if crimes == 0:
        return 0
    return round(cleared / crimes * 100, 1)

# Homicide clearance rate for a county
county_data = df[(df["County"] == "San Mateo") & (df["Year"] == 2023)]
rate = clearance_rate(county_data, "Homicide_sum")
print(f"Homicide clearance rate: {rate}%")
```

### Compare crime rates across counties

```python
# Per-capita comparison requires population data from another source
# (Census or DOF estimates)
county_totals = (
    df[df["Year"] == 2023]
    .groupby("County")[["Violent_sum", "Property_sum"]]
    .sum()
    .sort_values("Violent_sum", ascending=False)
)
print(county_totals.head(10))
```

## What questions this answers

- What is the violent crime rate in my county/city?
- How has crime changed over the last 5-10 years?
- What is the clearance rate for different crime types?
- How does my county compare to similar counties?
- What share of crime is property vs. violent?
- Which agencies report the most/fewest crimes per capita?

### Combining with other data

Join with Census population estimates for per-capita rates. Join with SCO ByTheNumbers spending data to compare public safety spending vs. crime outcomes. Join with CDE test scores to study correlations between community safety and educational outcomes.

## Gotchas

- **Rape definition changed in 2014**: The FBI revised "forcible rape" to "rape" with a broader definition. CA DOJ implemented this January 2014. Pre-2014 and post-2014 rape numbers are not directly comparable.
- **Felony theft threshold changed in 2011**: CA raised the felony larceny threshold from $400 to $950. The property crime category was adjusted, but pre-2011 numbers may appear inconsistent.
- **CIBRS transition (2021+)**: Data from 2021 onward mixes summary and incident-based reporting. IBR data is converted to summary format, but definitional differences exist (e.g., rape reporting validations differ between systems).
- **Hierarchy rule**: When multiple Part I offenses occur in the same event, only the most serious is counted. Arson is the exception (always counted alongside).
- **Homicide/rape = victims; robbery/burglary/theft = incidents**: The unit of count differs by offense type.
- **Not all agencies report every year**: Check for gaps. Small agencies may have incomplete data.
- **County names must match exactly**: Use `"San Mateo"` not `"San Mateo County"`.
- **Clearance rates can exceed 100%**: Clearances in year N can relate to crimes reported in prior years.
- **Arson data is supplemental**: Arson columns are separate from the main violent/property crime totals.
- **The metatab mirror may lag**: It may not have the most recent year's data. Check the official portal for the latest.
