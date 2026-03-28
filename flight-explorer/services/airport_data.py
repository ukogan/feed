"""Airport metadata lookup.

Top ~100 US airports and major international airports used by OpenSky.
OpenSky returns ICAO 4-letter codes (e.g., KSFO, KLAX).
"""

AIRPORTS = {
    # California
    "KSFO": {"name": "San Francisco Intl", "city": "San Francisco", "state": "CA", "country": "US", "lat": 37.62, "lng": -122.38},
    "KLAX": {"name": "Los Angeles Intl", "city": "Los Angeles", "state": "CA", "country": "US", "lat": 33.94, "lng": -118.41},
    "KSAN": {"name": "San Diego Intl", "city": "San Diego", "state": "CA", "country": "US", "lat": 32.73, "lng": -117.19},
    "KSJC": {"name": "San Jose Intl", "city": "San Jose", "state": "CA", "country": "US", "lat": 37.36, "lng": -121.93},
    "KOAK": {"name": "Oakland Intl", "city": "Oakland", "state": "CA", "country": "US", "lat": 37.72, "lng": -122.22},
    "KSMF": {"name": "Sacramento Intl", "city": "Sacramento", "state": "CA", "country": "US", "lat": 38.70, "lng": -121.59},
    "KSNA": {"name": "John Wayne / Orange County", "city": "Santa Ana", "state": "CA", "country": "US", "lat": 33.68, "lng": -117.87},
    "KBUR": {"name": "Hollywood Burbank", "city": "Burbank", "state": "CA", "country": "US", "lat": 34.20, "lng": -118.36},
    "KONT": {"name": "Ontario Intl", "city": "Ontario", "state": "CA", "country": "US", "lat": 34.06, "lng": -117.60},
    "KPSP": {"name": "Palm Springs Intl", "city": "Palm Springs", "state": "CA", "country": "US", "lat": 33.83, "lng": -116.51},
    # East Coast
    "KJFK": {"name": "John F Kennedy Intl", "city": "New York", "state": "NY", "country": "US", "lat": 40.64, "lng": -73.78},
    "KLGA": {"name": "LaGuardia", "city": "New York", "state": "NY", "country": "US", "lat": 40.77, "lng": -73.87},
    "KEWR": {"name": "Newark Liberty Intl", "city": "Newark", "state": "NJ", "country": "US", "lat": 40.69, "lng": -74.17},
    "KBOS": {"name": "Boston Logan Intl", "city": "Boston", "state": "MA", "country": "US", "lat": 42.36, "lng": -71.01},
    "KPHL": {"name": "Philadelphia Intl", "city": "Philadelphia", "state": "PA", "country": "US", "lat": 39.87, "lng": -75.24},
    "KDCA": {"name": "Ronald Reagan Washington", "city": "Washington", "state": "DC", "country": "US", "lat": 38.85, "lng": -77.04},
    "KIAD": {"name": "Washington Dulles Intl", "city": "Dulles", "state": "VA", "country": "US", "lat": 38.94, "lng": -77.46},
    "KBWI": {"name": "Baltimore/Washington Intl", "city": "Baltimore", "state": "MD", "country": "US", "lat": 39.18, "lng": -76.67},
    "KMIA": {"name": "Miami Intl", "city": "Miami", "state": "FL", "country": "US", "lat": 25.79, "lng": -80.29},
    "KFLL": {"name": "Fort Lauderdale-Hollywood", "city": "Fort Lauderdale", "state": "FL", "country": "US", "lat": 26.07, "lng": -80.15},
    "KMCO": {"name": "Orlando Intl", "city": "Orlando", "state": "FL", "country": "US", "lat": 28.43, "lng": -81.31},
    "KTPA": {"name": "Tampa Intl", "city": "Tampa", "state": "FL", "country": "US", "lat": 27.98, "lng": -82.53},
    "KATL": {"name": "Hartsfield-Jackson Atlanta", "city": "Atlanta", "state": "GA", "country": "US", "lat": 33.64, "lng": -84.43},
    "KCLT": {"name": "Charlotte Douglas Intl", "city": "Charlotte", "state": "NC", "country": "US", "lat": 35.21, "lng": -80.94},
    "KRDU": {"name": "Raleigh-Durham Intl", "city": "Raleigh", "state": "NC", "country": "US", "lat": 35.88, "lng": -78.79},
    # Midwest
    "KORD": {"name": "O'Hare Intl", "city": "Chicago", "state": "IL", "country": "US", "lat": 41.97, "lng": -87.91},
    "KMDW": {"name": "Midway Intl", "city": "Chicago", "state": "IL", "country": "US", "lat": 41.79, "lng": -87.75},
    "KDTW": {"name": "Detroit Metro Wayne County", "city": "Detroit", "state": "MI", "country": "US", "lat": 42.21, "lng": -83.35},
    "KMSP": {"name": "Minneapolis-St Paul Intl", "city": "Minneapolis", "state": "MN", "country": "US", "lat": 44.88, "lng": -93.22},
    "KSTL": {"name": "St Louis Lambert Intl", "city": "St Louis", "state": "MO", "country": "US", "lat": 38.75, "lng": -90.37},
    "KMCI": {"name": "Kansas City Intl", "city": "Kansas City", "state": "MO", "country": "US", "lat": 39.30, "lng": -94.71},
    "KCVG": {"name": "Cincinnati/Northern Kentucky", "city": "Cincinnati", "state": "OH", "country": "US", "lat": 39.05, "lng": -84.66},
    "KCLE": {"name": "Cleveland Hopkins Intl", "city": "Cleveland", "state": "OH", "country": "US", "lat": 41.41, "lng": -81.85},
    "KCMH": {"name": "John Glenn Columbus Intl", "city": "Columbus", "state": "OH", "country": "US", "lat": 39.99, "lng": -82.89},
    "KIND": {"name": "Indianapolis Intl", "city": "Indianapolis", "state": "IN", "country": "US", "lat": 39.72, "lng": -86.29},
    "KMKE": {"name": "Milwaukee Mitchell Intl", "city": "Milwaukee", "state": "WI", "country": "US", "lat": 42.95, "lng": -87.90},
    # South/Southwest
    "KDFW": {"name": "Dallas/Fort Worth Intl", "city": "Dallas", "state": "TX", "country": "US", "lat": 32.90, "lng": -97.04},
    "KDAL": {"name": "Dallas Love Field", "city": "Dallas", "state": "TX", "country": "US", "lat": 32.85, "lng": -96.85},
    "KIAH": {"name": "George Bush Intercontinental", "city": "Houston", "state": "TX", "country": "US", "lat": 29.98, "lng": -95.34},
    "KHOU": {"name": "William P Hobby", "city": "Houston", "state": "TX", "country": "US", "lat": 29.65, "lng": -95.28},
    "KAUS": {"name": "Austin-Bergstrom Intl", "city": "Austin", "state": "TX", "country": "US", "lat": 30.19, "lng": -97.67},
    "KSAT": {"name": "San Antonio Intl", "city": "San Antonio", "state": "TX", "country": "US", "lat": 29.53, "lng": -98.47},
    "KPHX": {"name": "Phoenix Sky Harbor Intl", "city": "Phoenix", "state": "AZ", "country": "US", "lat": 33.44, "lng": -112.01},
    "KLAS": {"name": "Harry Reid Intl", "city": "Las Vegas", "state": "NV", "country": "US", "lat": 36.08, "lng": -115.15},
    "KDEN": {"name": "Denver Intl", "city": "Denver", "state": "CO", "country": "US", "lat": 39.86, "lng": -104.67},
    "KSLC": {"name": "Salt Lake City Intl", "city": "Salt Lake City", "state": "UT", "country": "US", "lat": 40.79, "lng": -111.98},
    "KABQ": {"name": "Albuquerque Intl Sunport", "city": "Albuquerque", "state": "NM", "country": "US", "lat": 35.04, "lng": -106.61},
    "KBNA": {"name": "Nashville Intl", "city": "Nashville", "state": "TN", "country": "US", "lat": 36.12, "lng": -86.68},
    "KMEM": {"name": "Memphis Intl", "city": "Memphis", "state": "TN", "country": "US", "lat": 35.04, "lng": -89.98},
    "KMSY": {"name": "Louis Armstrong New Orleans", "city": "New Orleans", "state": "LA", "country": "US", "lat": 29.99, "lng": -90.26},
    # Pacific Northwest
    "KSEA": {"name": "Seattle-Tacoma Intl", "city": "Seattle", "state": "WA", "country": "US", "lat": 47.45, "lng": -122.31},
    "KPDX": {"name": "Portland Intl", "city": "Portland", "state": "OR", "country": "US", "lat": 45.59, "lng": -122.60},
    # Mountain/Other US
    "KBOI": {"name": "Boise Airport", "city": "Boise", "state": "ID", "country": "US", "lat": 43.56, "lng": -116.22},
    "KPIT": {"name": "Pittsburgh Intl", "city": "Pittsburgh", "state": "PA", "country": "US", "lat": 40.49, "lng": -80.23},
    "KBDL": {"name": "Bradley Intl", "city": "Hartford", "state": "CT", "country": "US", "lat": 41.94, "lng": -72.68},
    "KPBI": {"name": "Palm Beach Intl", "city": "West Palm Beach", "state": "FL", "country": "US", "lat": 26.68, "lng": -80.10},
    "KRNO": {"name": "Reno-Tahoe Intl", "city": "Reno", "state": "NV", "country": "US", "lat": 39.50, "lng": -119.77},
    "PANC": {"name": "Ted Stevens Anchorage", "city": "Anchorage", "state": "AK", "country": "US", "lat": 61.17, "lng": -150.00},
    "PHNL": {"name": "Daniel K Inouye Intl", "city": "Honolulu", "state": "HI", "country": "US", "lat": 21.32, "lng": -157.92},
    "PHOG": {"name": "Kahului Airport", "city": "Kahului", "state": "HI", "country": "US", "lat": 20.90, "lng": -156.43},
    "KRSW": {"name": "Southwest Florida Intl", "city": "Fort Myers", "state": "FL", "country": "US", "lat": 26.54, "lng": -81.76},
    "KJAN": {"name": "Jackson-Medgar Wiley Evers", "city": "Jackson", "state": "MS", "country": "US", "lat": 32.31, "lng": -90.08},
    "KOMA": {"name": "Eppley Airfield", "city": "Omaha", "state": "NE", "country": "US", "lat": 41.30, "lng": -95.89},
    "KRIC": {"name": "Richmond Intl", "city": "Richmond", "state": "VA", "country": "US", "lat": 37.51, "lng": -77.32},
    "KBUF": {"name": "Buffalo Niagara Intl", "city": "Buffalo", "state": "NY", "country": "US", "lat": 42.94, "lng": -78.73},
    "KSYR": {"name": "Syracuse Hancock Intl", "city": "Syracuse", "state": "NY", "country": "US", "lat": 43.11, "lng": -76.11},
    # Canada
    "CYYZ": {"name": "Toronto Pearson Intl", "city": "Toronto", "state": "ON", "country": "CA", "lat": 43.68, "lng": -79.63},
    "CYVR": {"name": "Vancouver Intl", "city": "Vancouver", "state": "BC", "country": "CA", "lat": 49.19, "lng": -123.18},
    "CYUL": {"name": "Montreal-Trudeau Intl", "city": "Montreal", "state": "QC", "country": "CA", "lat": 45.47, "lng": -73.74},
    "CYYC": {"name": "Calgary Intl", "city": "Calgary", "state": "AB", "country": "CA", "lat": 51.13, "lng": -114.01},
    # Mexico
    "MMMX": {"name": "Mexico City Intl", "city": "Mexico City", "state": None, "country": "MX", "lat": 19.44, "lng": -99.07},
    "MMUN": {"name": "Cancun Intl", "city": "Cancun", "state": None, "country": "MX", "lat": 21.04, "lng": -86.87},
    "MMTJ": {"name": "Tijuana Intl", "city": "Tijuana", "state": None, "country": "MX", "lat": 32.54, "lng": -116.97},
    "MMPR": {"name": "Puerto Vallarta Intl", "city": "Puerto Vallarta", "state": None, "country": "MX", "lat": 20.68, "lng": -105.25},
    "MMGL": {"name": "Guadalajara Intl", "city": "Guadalajara", "state": None, "country": "MX", "lat": 20.52, "lng": -103.31},
    # Europe
    "EGLL": {"name": "London Heathrow", "city": "London", "state": None, "country": "GB", "lat": 51.47, "lng": -0.46},
    "LFPG": {"name": "Paris Charles de Gaulle", "city": "Paris", "state": None, "country": "FR", "lat": 49.01, "lng": 2.55},
    "EDDF": {"name": "Frankfurt am Main", "city": "Frankfurt", "state": None, "country": "DE", "lat": 50.03, "lng": 8.57},
    "EHAM": {"name": "Amsterdam Schiphol", "city": "Amsterdam", "state": None, "country": "NL", "lat": 52.31, "lng": 4.76},
    "LEMD": {"name": "Madrid Barajas", "city": "Madrid", "state": None, "country": "ES", "lat": 40.47, "lng": -3.56},
    "LIRF": {"name": "Rome Fiumicino", "city": "Rome", "state": None, "country": "IT", "lat": 41.80, "lng": 12.25},
    "LSZH": {"name": "Zurich Airport", "city": "Zurich", "state": None, "country": "CH", "lat": 47.46, "lng": 8.55},
    # Asia-Pacific
    "RJTT": {"name": "Tokyo Haneda", "city": "Tokyo", "state": None, "country": "JP", "lat": 35.55, "lng": 139.78},
    "RJAA": {"name": "Tokyo Narita", "city": "Tokyo", "state": None, "country": "JP", "lat": 35.76, "lng": 140.39},
    "RKSI": {"name": "Incheon Intl", "city": "Seoul", "state": None, "country": "KR", "lat": 37.46, "lng": 126.44},
    "VHHH": {"name": "Hong Kong Intl", "city": "Hong Kong", "state": None, "country": "HK", "lat": 22.31, "lng": 113.91},
    "WSSS": {"name": "Singapore Changi", "city": "Singapore", "state": None, "country": "SG", "lat": 1.35, "lng": 103.99},
    "YSSY": {"name": "Sydney Kingsford Smith", "city": "Sydney", "state": None, "country": "AU", "lat": -33.95, "lng": 151.18},
    "NZAA": {"name": "Auckland Airport", "city": "Auckland", "state": None, "country": "NZ", "lat": -37.01, "lng": 174.79},
    "ZBAA": {"name": "Beijing Capital Intl", "city": "Beijing", "state": None, "country": "CN", "lat": 40.08, "lng": 116.58},
    "ZSPD": {"name": "Shanghai Pudong Intl", "city": "Shanghai", "state": None, "country": "CN", "lat": 31.14, "lng": 121.81},
    "RPLL": {"name": "Ninoy Aquino Intl", "city": "Manila", "state": None, "country": "PH", "lat": 14.51, "lng": 121.02},
    "VTBS": {"name": "Suvarnabhumi Airport", "city": "Bangkok", "state": None, "country": "TH", "lat": 13.69, "lng": 100.75},
    "VIDP": {"name": "Indira Gandhi Intl", "city": "New Delhi", "state": None, "country": "IN", "lat": 28.57, "lng": 77.10},
    "VABB": {"name": "Chhatrapati Shivaji Intl", "city": "Mumbai", "state": None, "country": "IN", "lat": 19.09, "lng": 72.87},
    # Middle East
    "OMDB": {"name": "Dubai Intl", "city": "Dubai", "state": None, "country": "AE", "lat": 25.25, "lng": 55.36},
    "OEJN": {"name": "King Abdulaziz Intl", "city": "Jeddah", "state": None, "country": "SA", "lat": 21.67, "lng": 39.16},
    "OTHH": {"name": "Hamad Intl", "city": "Doha", "state": None, "country": "QA", "lat": 25.26, "lng": 51.61},
    "LLBG": {"name": "Ben Gurion Intl", "city": "Tel Aviv", "state": None, "country": "IL", "lat": 32.01, "lng": 34.89},
    # South America
    "SBGR": {"name": "Guarulhos Intl", "city": "Sao Paulo", "state": None, "country": "BR", "lat": -23.43, "lng": -46.47},
    "SCEL": {"name": "Arturo Merino Benitez", "city": "Santiago", "state": None, "country": "CL", "lat": -33.39, "lng": -70.79},
    "SKBO": {"name": "El Dorado Intl", "city": "Bogota", "state": None, "country": "CO", "lat": 4.70, "lng": -74.15},
    "SPJC": {"name": "Jorge Chavez Intl", "city": "Lima", "state": None, "country": "PE", "lat": -12.02, "lng": -77.11},
}

# Country code to display name
COUNTRY_NAMES = {
    "US": "United States", "CA": "Canada", "MX": "Mexico",
    "GB": "United Kingdom", "FR": "France", "DE": "Germany",
    "NL": "Netherlands", "ES": "Spain", "IT": "Italy", "CH": "Switzerland",
    "JP": "Japan", "KR": "South Korea", "HK": "Hong Kong", "SG": "Singapore",
    "AU": "Australia", "NZ": "New Zealand", "CN": "China", "PH": "Philippines",
    "TH": "Thailand", "IN": "India", "AE": "United Arab Emirates",
    "SA": "Saudi Arabia", "QA": "Qatar", "IL": "Israel",
    "BR": "Brazil", "CL": "Chile", "CO": "Colombia", "PE": "Peru",
}


def lookup_airport(icao_code: str) -> dict | None:
    """Look up airport metadata by ICAO code."""
    if not icao_code:
        return None
    return AIRPORTS.get(icao_code.upper())


def get_country_name(code: str) -> str:
    """Get display name for a country code."""
    return COUNTRY_NAMES.get(code, code)
