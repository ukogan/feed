"""Client for the National Bridge Inventory REST API (geo.dot.gov)."""

import httpx

NBI_BASE_URL = (
    "https://geo.dot.gov/server/rest/services/Hosted/"
    "National_Bridge_Inventory_DS/FeatureServer/0/query"
)

OUT_FIELDS = ",".join([
    "FACILITY_CARRIED_007",
    "YEAR_BUILT_027",
    "DECK_COND_058",
    "SUPERSTRUCTURE_COND_059",
    "SUBSTRUCTURE_COND_060",
    "ADT_029",
    "LAT_016",
    "LONG_017",
])

# FIPS state codes used by the NBI STATE_CODE_001 field.
STATE_CODES: dict[str, str] = {
    "01": "Alabama",
    "02": "Alaska",
    "04": "Arizona",
    "05": "Arkansas",
    "06": "California",
    "08": "Colorado",
    "09": "Connecticut",
    "10": "Delaware",
    "11": "District of Columbia",
    "12": "Florida",
    "13": "Georgia",
    "15": "Hawaii",
    "16": "Idaho",
    "17": "Illinois",
    "18": "Indiana",
    "19": "Iowa",
    "20": "Kansas",
    "21": "Kentucky",
    "22": "Louisiana",
    "23": "Maine",
    "24": "Maryland",
    "25": "Massachusetts",
    "26": "Michigan",
    "27": "Minnesota",
    "28": "Mississippi",
    "29": "Missouri",
    "30": "Montana",
    "31": "Nebraska",
    "32": "Nevada",
    "33": "New Hampshire",
    "34": "New Jersey",
    "35": "New Mexico",
    "36": "New York",
    "37": "North Carolina",
    "38": "North Dakota",
    "39": "Ohio",
    "40": "Oklahoma",
    "41": "Oregon",
    "42": "Pennsylvania",
    "44": "Rhode Island",
    "45": "South Carolina",
    "46": "South Dakota",
    "47": "Tennessee",
    "48": "Texas",
    "49": "Utah",
    "50": "Vermont",
    "51": "Virginia",
    "53": "Washington",
    "54": "West Virginia",
    "55": "Wisconsin",
    "56": "Wyoming",
}


def _classify_condition(deck: int | None, superstructure: int | None,
                        substructure: int | None) -> str:
    """Return 'good', 'fair', or 'poor' based on the worst rating."""
    ratings = [r for r in (deck, superstructure, substructure) if r is not None]
    if not ratings:
        return "unknown"
    worst = min(ratings)
    if worst <= 4:
        return "poor"
    if worst <= 6:
        return "fair"
    return "good"


def _safe_int(value: object) -> int | None:
    """Convert a value to int, returning None if not possible."""
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _parse_bridge(attrs: dict) -> dict | None:
    """Parse a single feature's attributes into a bridge dict."""
    lat = attrs.get("LAT_016")
    lng = attrs.get("LONG_017")
    if lat is None or lng is None:
        return None
    try:
        lat = float(lat)
        lng = float(lng)
    except (ValueError, TypeError):
        return None
    if lat == 0 and lng == 0:
        return None

    deck = _safe_int(attrs.get("DECK_COND_058"))
    superstructure = _safe_int(attrs.get("SUPERSTRUCTURE_COND_059"))
    substructure = _safe_int(attrs.get("SUBSTRUCTURE_COND_060"))
    adt = _safe_int(attrs.get("ADT_029"))
    condition = _classify_condition(deck, superstructure, substructure)

    return {
        "name": attrs.get("FACILITY_CARRIED_007", "Unknown"),
        "year_built": _safe_int(attrs.get("YEAR_BUILT_027")),
        "deck": deck,
        "superstructure": superstructure,
        "substructure": substructure,
        "adt": adt or 0,
        "lat": lat,
        "lng": lng,
        "condition": condition,
    }


async def fetch_bridges(state_code: str = "06",
                        max_records: int = 2000) -> list[dict]:
    """Fetch bridge records from the NBI REST API for a given state."""
    params = {
        "where": f"STATE_CODE_001='{state_code}'",
        "outFields": OUT_FIELDS,
        "f": "json",
        "resultRecordCount": str(max_records),
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(NBI_BASE_URL, params=params)
        resp.raise_for_status()
        data = resp.json()

    features = data.get("features", [])
    bridges: list[dict] = []
    for feature in features:
        attrs = feature.get("attributes", {})
        parsed = _parse_bridge(attrs)
        if parsed is not None:
            bridges.append(parsed)
    return bridges


def compute_stats(bridges: list[dict]) -> dict:
    """Compute summary statistics for a list of bridges."""
    total = len(bridges)
    if total == 0:
        return {"total": 0, "good": 0, "fair": 0, "poor": 0,
                "pct_good": 0, "pct_fair": 0, "pct_poor": 0}
    good = sum(1 for b in bridges if b["condition"] == "good")
    fair = sum(1 for b in bridges if b["condition"] == "fair")
    poor = sum(1 for b in bridges if b["condition"] == "poor")
    return {
        "total": total,
        "good": good,
        "fair": fair,
        "poor": poor,
        "pct_good": round(100 * good / total, 1),
        "pct_fair": round(100 * fair / total, 1),
        "pct_poor": round(100 * poor / total, 1),
    }
