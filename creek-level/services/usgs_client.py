"""USGS Water Services API client for gauge height and discharge data."""

import httpx

BASE_URL = "https://waterservices.usgs.gov/nwis"

# US states for the dropdown
US_STATES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


async def fetch_sites(state_cd: str = "CA") -> list[dict]:
    """Fetch active stream gauge sites for a state via the IV endpoint.

    Uses instantaneous values endpoint which returns both site locations
    and current readings in one call.
    """
    return await _fetch_sites_via_iv(state_cd)


async def _fetch_sites_via_iv(state_cd: str) -> list[dict]:
    """Fetch sites by getting instantaneous values for gauge height across a state.

    This gives us both the site locations and current readings in one call.
    """
    params = {
        "format": "json",
        "stateCd": state_cd,
        "parameterCd": "00065",  # gauge height
        "siteType": "ST",
        "siteStatus": "active",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.get(f"{BASE_URL}/iv/", params=params, follow_redirects=True)
        resp.raise_for_status()
        data = resp.json()

    ts_list = data.get("value", {}).get("timeSeries", [])
    seen = set()
    sites = []

    for ts in ts_list:
        info = ts.get("sourceInfo", {})
        site_no = info.get("siteCode", [{}])[0].get("value", "")
        if site_no in seen:
            continue
        seen.add(site_no)

        geo = info.get("geoLocation", {}).get("geogLocation", {})
        lat = geo.get("latitude")
        lng = geo.get("longitude")

        # Get latest value and compute trend
        values = ts.get("values", [{}])[0].get("value", [])
        latest_val = None
        trend = "stable"

        if values:
            latest_val = _safe_float(values[-1].get("value"))
            if len(values) >= 4:
                trend = _compute_trend(values)

        sites.append({
            "site_no": site_no,
            "name": info.get("siteName", "Unknown"),
            "lat": lat,
            "lng": lng,
            "latest_value": latest_val,
            "trend": trend,
            "unit": "ft",
        })

    return sites


async def fetch_site_history(site_no: str, period: str = "P1D") -> dict:
    """Fetch gauge height history for a specific site.

    Returns dict with site info and time-series values.
    """
    params = {
        "format": "json",
        "sites": site_no,
        "parameterCd": "00065,00060",  # gauge height + discharge
        "period": period,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{BASE_URL}/iv/", params=params)
        resp.raise_for_status()
        data = resp.json()

    ts_list = data.get("value", {}).get("timeSeries", [])
    result = {"site_no": site_no, "series": {}}

    for ts in ts_list:
        info = ts.get("sourceInfo", {})
        var_info = ts.get("variable", {})
        param_cd = var_info.get("variableCode", [{}])[0].get("value", "")
        param_name = var_info.get("variableName", "")
        unit = var_info.get("unit", {}).get("unitAbbreviation", "")

        values = ts.get("values", [{}])[0].get("value", [])
        points = []
        for v in values:
            fval = _safe_float(v.get("value"))
            if fval is not None:
                points.append({
                    "time": v.get("dateTime"),
                    "value": fval,
                })

        result["name"] = info.get("siteName", "Unknown")
        geo = info.get("geoLocation", {}).get("geogLocation", {})
        result["lat"] = geo.get("latitude")
        result["lng"] = geo.get("longitude")
        result["series"][param_cd] = {
            "name": param_name,
            "unit": unit,
            "values": points,
        }

    return result


def _safe_float(val) -> float | None:
    """Convert a value to float, returning None on failure."""
    if val is None:
        return None
    try:
        f = float(val)
        # USGS uses -999999 as a sentinel for missing data
        if f <= -999999:
            return None
        return f
    except (ValueError, TypeError):
        return None


def _compute_trend(values: list[dict]) -> str:
    """Compute trend from a list of USGS value dicts.

    Compares the average of the last quarter to the first quarter.
    Returns 'rising', 'falling', or 'stable'.
    """
    nums = [_safe_float(v.get("value")) for v in values]
    nums = [n for n in nums if n is not None]
    if len(nums) < 4:
        return "stable"

    quarter = max(1, len(nums) // 4)
    early_avg = sum(nums[:quarter]) / quarter
    late_avg = sum(nums[-quarter:]) / quarter

    if early_avg == 0:
        return "stable"

    change_pct = (late_avg - early_avg) / early_avg * 100

    if change_pct > 30:
        return "high"
    elif change_pct > 10:
        return "rising"
    elif change_pct < -10:
        return "falling"
    return "stable"
