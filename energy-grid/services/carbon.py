"""Carbon intensity calculation from fuel mix.

Emission factors from EPA eGRID (gCO2/kWh by fuel type).
"""

# EIA fuel type codes -> display names and emission factors
FUEL_INFO = {
    "COL": {"name": "Coal", "co2_g_kwh": 980, "color": "#4a4a4a", "renewable": False},
    "NG": {"name": "Natural Gas", "co2_g_kwh": 410, "color": "#f59e0b", "renewable": False},
    "NUC": {"name": "Nuclear", "co2_g_kwh": 12, "color": "#8b5cf6", "renewable": False},
    "SUN": {"name": "Solar", "co2_g_kwh": 45, "color": "#fbbf24", "renewable": True},
    "WND": {"name": "Wind", "co2_g_kwh": 11, "color": "#38bdf8", "renewable": True},
    "WAT": {"name": "Hydro", "co2_g_kwh": 24, "color": "#06b6d4", "renewable": True},
    "OIL": {"name": "Oil", "co2_g_kwh": 890, "color": "#78716c", "renewable": False},
    "OTH": {"name": "Other", "co2_g_kwh": 500, "color": "#94a3b8", "renewable": False},
    "GEO": {"name": "Geothermal", "co2_g_kwh": 38, "color": "#ef4444", "renewable": True},
    "BIO": {"name": "Biomass", "co2_g_kwh": 230, "color": "#22c55e", "renewable": True},
    "WAS": {"name": "Waste", "co2_g_kwh": 500, "color": "#a3a3a3", "renewable": False},
    "STG": {"name": "Storage", "co2_g_kwh": 0, "color": "#a78bfa", "renewable": False},
    "PS": {"name": "Pumped Storage", "co2_g_kwh": 0, "color": "#818cf8", "renewable": False},
}

# Fuel types that are "clean" (low carbon)
CLEAN_FUELS = {"SUN", "WND", "WAT", "NUC", "GEO"}


def calculate_carbon_intensity(fuel_breakdown: dict[str, float]) -> float:
    """Calculate weighted average carbon intensity (gCO2/kWh) from fuel mix.

    Args:
        fuel_breakdown: {fuel_code: MWh} mapping
    """
    total_mwh = sum(fuel_breakdown.values())
    if total_mwh == 0:
        return 0

    weighted_sum = sum(
        mwh * FUEL_INFO.get(fuel, {"co2_g_kwh": 500})["co2_g_kwh"]
        for fuel, mwh in fuel_breakdown.items()
    )
    return weighted_sum / total_mwh


def calculate_renewable_pct(fuel_breakdown: dict[str, float]) -> float:
    """Calculate percentage of generation from renewable sources."""
    total = sum(fuel_breakdown.values())
    if total == 0:
        return 0

    renewable = sum(
        mwh for fuel, mwh in fuel_breakdown.items()
        if FUEL_INFO.get(fuel, {}).get("renewable", False)
    )
    return (renewable / total) * 100


def get_fuel_display(fuel_code: str) -> dict:
    """Get display info for a fuel type."""
    return FUEL_INFO.get(fuel_code, {"name": fuel_code, "co2_g_kwh": 500, "color": "#94a3b8", "renewable": False})
