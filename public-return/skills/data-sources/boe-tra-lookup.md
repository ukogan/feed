# BOE/CDTFA: Tax Rate Area (TRA) Lookup

## What this is

A Tax Rate Area (TRA) is a geographic zone within a California county that defines the unique combination of taxing jurisdictions (city, school districts, special districts, redevelopment areas) that levy property taxes on parcels in that area. Every property in California belongs to exactly one TRA, identified by a 6-digit code. The TRA is the key that connects an address to all the government entities funded by its property taxes.

TRA boundaries and assignments are maintained by the Board of Equalization (BOE) Tax Area Services Section (TASS), now administratively housed under the California Department of Tax and Fee Administration (CDTFA). Data is published annually for each assessment roll year.

## Data sources

### 1. Interactive TRA Maps (per county)

```
https://boe.ca.gov/maps/{CountyName}Co.htm
```

Examples:
- `https://boe.ca.gov/maps/SanMateoCo.htm`
- `https://boe.ca.gov/maps/SantaClaraCo.htm`
- `https://boe.ca.gov/maps/LosAngelesCo.htm`

Each county map page includes:
- Interactive map with TRA polygon boundaries
- Address search (zoom to address, see TRA number)
- TRA number search (enter 6-digit code to zoom)
- Download link for TRA shapefile and TRA-to-District table

### 2. GIS Data (ArcGIS Hub)

Shapefiles and feature services per county via CDTFA's ArcGIS Hub:
```
https://cdtfa.hub.arcgis.com/
```

Example dataset for San Mateo 2025:
```
https://cdtfa.hub.arcgis.com/maps/CDTFA::san-mateo-2025-roll-year/about
```

Available in: Shapefile (ZIP), GeoJSON, KML, File Geodatabase, CSV, Excel, GeoPackage.

URL pattern for ArcGIS datasets:
```
https://gis-california.opendata.arcgis.com/datasets/CDTFA::boe-tra-{year}-co{county_fips}
```

Example: San Mateo (FIPS 41), 2022 roll year:
```
https://gis-california.opendata.arcgis.com/datasets/CDTFA::boe-tra-2022-co41/explore
```

### 3. CDTFA Tax Rate API (sales tax, not property tax)

For looking up the sales tax rate and Tax Area Code (TAC) for a given address:

By address:
```
GET https://services.maps.cdtfa.ca.gov/api/taxrate/GetRateByAddress?address={street}&city={city}&zip={zip}
```

By coordinates:
```
GET https://services.maps.cdtfa.ca.gov/api/taxrate/GetRateByLngLat?latitude={lat}&longitude={lng}
```

**Note**: This API returns *sales tax* rates and TAC codes, not property tax TRAs. However, the TAC is related to the TRA and can be useful for identifying jurisdiction boundaries.

### 4. Annual TRA datasets (via email)

Full annual TRA datasets (change notices, data tables, CAD/GIS files) are available from TASS by request:
- Email: TASS@boe.ca.gov
- Phone: 916-274-3250
- Data is published May 1 each year (preliminary March 15)
- Distributed via shared BOX folder with access credentials

## Authentication

- BOE map pages: None, fully public
- ArcGIS Hub downloads: None
- CDTFA Tax Rate API: None, no key required
- Annual TASS datasets: Email request required for BOX access

## How TRAs work

1. Every parcel in California belongs to one TRA
2. The TRA code (6 digits, zero-padded) identifies the unique combination of taxing entities
3. A TRA-to-District table maps each TRA to its constituent taxing jurisdictions
4. When jurisdictions change boundaries (annexation, formation, dissolution), TRAs are updated

The TRA-to-District table typically contains:

| Field | Description |
|-------|-------------|
| `TRA` | 6-digit TRA number |
| `DistrictCode` | Code for each taxing entity in that TRA |
| `DistrictName` | Name of the taxing entity |
| `DistrictType` | Type (city, school, special district, etc.) |
| `TaxRate` | Property tax rate allocated to that entity |

## How to use

### Look up a TRA for an address (manual)

1. Go to `https://boe.ca.gov/maps/SanMateoCo.htm`
2. Enter the address in the search bar
3. The map zooms to the location and displays the TRA number
4. Click the TRA polygon for details

### Look up a TRA programmatically

```python
import httpx

async def get_sales_tax_info(address: str, city: str, zip_code: str):
    """Use CDTFA API to get tax area code for an address.
    Note: Returns sales tax TAC, not property tax TRA,
    but useful for jurisdiction identification."""
    url = "https://services.maps.cdtfa.ca.gov/api/taxrate/GetRateByAddress"
    params = {
        "address": address.replace(" ", "+"),
        "city": city.replace(" ", "+"),
        "zip": zip_code,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        data = resp.json()
        for rate_info in data.get("taxRateInfo", []):
            print(f"Rate: {rate_info.get('rate')}%")
            print(f"Jurisdiction: {rate_info.get('jurisdictionName')}")
            print(f"City: {rate_info.get('city')}")
            print(f"County: {rate_info.get('county')}")
            print(f"TAC: {rate_info.get('taxAreaCode')}")
        return data
```

### Download and query TRA shapefiles

```python
import geopandas as gpd

# Download shapefile from ArcGIS Hub (example: San Mateo 2025)
# Go to the county page on cdtfa.hub.arcgis.com, click Download -> Shapefile
# Or use the GeoJSON API endpoint directly:

# Query features via ArcGIS REST API
url = (
    "https://services3.arcgis.com/uknczv4rpevve42E/arcgis/rest/services/"
    "San_Mateo_2025_Roll_Year/FeatureServer/0/query"
)
params = {
    "where": "1=1",
    "outFields": "*",
    "f": "geojson",
    "resultRecordCount": 100,
}

# Load into GeoPandas
gdf = gpd.read_file(f"{url}?where=1%3D1&outFields=*&f=geojson&resultRecordCount=100")
print(gdf.columns.tolist())
print(gdf.head())
```

### Point-in-polygon lookup (find TRA for coordinates)

```python
from shapely.geometry import Point

def find_tra(gdf, lat: float, lon: float) -> str:
    """Find the TRA number for a given lat/lon coordinate."""
    point = Point(lon, lat)
    match = gdf[gdf.geometry.contains(point)]
    if len(match) == 0:
        return None
    return match.iloc[0]["TRA"]

# Example: 123 Main St, Redwood City
tra = find_tra(gdf, 37.4852, -122.2364)
print(f"TRA: {tra}")
```

### Map TRA to taxing jurisdictions

Once you have a TRA number, look it up in the TRA-to-District table (downloaded from the county map page or TASS) to find all entities that receive property tax revenue from that area.

```python
# Load TRA-to-District table (CSV or from shapefile attributes)
tra_districts = pd.read_csv("tra_districts_sanmateo_2025.csv")

# Find all jurisdictions for a TRA
tra_number = "009001"
entities = tra_districts[tra_districts["TRA"] == tra_number]
for _, row in entities.iterrows():
    print(f"  {row['DistrictName']} ({row['DistrictType']}): {row['TaxRate']}%")
```

## What questions this answers

- What school district, city, and special districts serve my address?
- Which government entities receive property tax revenue from my parcel?
- How is the 1% base property tax rate allocated among jurisdictions?
- What is the complete list of taxing entities for any location in California?
- How do TRA boundaries differ from city boundaries or school district boundaries?

### Combining with other data

This is the "glue" skill that connects an address to all its government entities:
- Use the TRA to identify the school district, then pull finances from CDE SACS
- Use the TRA to identify the city, then pull spending from SCO ByTheNumbers
- Use the TRA to identify special districts, then pull their finances from SCO
- Use the TRA to understand the property tax allocation among all entities

## Gotchas

- **TRA != TAC**: The property tax TRA (6 digits, from BOE) is different from the sales tax TAC (Tax Area Code, from CDTFA). They cover different tax types and have different boundaries. The CDTFA API returns TACs, not TRAs.
- **TRA codes are county-specific**: TRA `009001` in San Mateo County is completely different from TRA `009001` in Santa Clara County. Always pair TRA with county.
- **TRA codes must be 6 digits, zero-padded**: Enter `009001`, not `9001`.
- **TRAs change annually**: Annexations, new districts, and boundary changes create new TRAs or modify existing ones. Always use the correct roll year.
- **The ArcGIS Hub URLs are not stable**: Dataset URLs change between roll years. Search `cdtfa.hub.arcgis.com` for the county and year you need.
- **Feature service names vary**: The ArcGIS REST service name varies by county and year. You may need to discover the correct service URL by browsing the hub.
- **Shapefiles can be large**: LA County has thousands of TRAs. Download and cache locally.
- **The CDTFA Tax Rate API is for sales tax only**: It does not return property tax rates or property tax TRA numbers. Use it for jurisdiction identification, not property tax analysis.
- **Not all counties have maps posted at the same time**: New roll year maps are posted in June, but some counties lag.
- **TRA-to-District tables may not be downloadable from the web**: For some counties, you may need to request the table from TASS@boe.ca.gov.
