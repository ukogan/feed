"""Personal Carbon Accountant: calculates personal carbon footprint from usage profile.

Given an hourly usage profile (24 kWh values), uses actual fuel mix data to compute:
- Hourly carbon emissions breakdown (green vs brown kWh)
- Total CO2 produced
- Optimized schedule that shifts load to lowest-carbon hours
- Savings potential in CO2 and cost
"""

from services.carbon import FUEL_INFO, calculate_carbon_intensity, calculate_renewable_pct

# Average US electricity price in $/kWh (EIA national average, 2025)
AVG_ELECTRICITY_PRICE = 0.16

# Typical household profiles (24 hourly kWh values, summing to ~30 kWh/day)
PRESET_PROFILES = {
    "average_household": {
        "name": "Average Household",
        "description": "Typical US household (~30 kWh/day)",
        "hourly_kwh": [
            0.6, 0.5, 0.4, 0.4, 0.4, 0.5,   # 12am-5am: low baseline
            0.8, 1.2, 1.5, 1.3, 1.2, 1.1,     # 6am-11am: morning ramp
            1.0, 1.0, 1.1, 1.2, 1.4, 1.8,     # 12pm-5pm: afternoon
            2.2, 2.5, 2.3, 1.8, 1.3, 0.8,     # 6pm-11pm: evening peak
        ],
    },
    "ev_owner": {
        "name": "EV Owner",
        "description": "Household with EV charging overnight (~45 kWh/day)",
        "hourly_kwh": [
            3.5, 3.5, 3.5, 3.5, 3.5, 3.0,    # 12am-5am: EV charging
            1.0, 1.2, 1.5, 1.3, 1.2, 1.1,     # 6am-11am: morning
            1.0, 1.0, 1.1, 1.2, 1.4, 1.8,     # 12pm-5pm: afternoon
            2.2, 2.5, 2.3, 1.8, 1.3, 0.8,     # 6pm-11pm: evening
        ],
    },
    "work_from_home": {
        "name": "Work From Home",
        "description": "Higher daytime usage from computing/HVAC (~35 kWh/day)",
        "hourly_kwh": [
            0.6, 0.5, 0.4, 0.4, 0.4, 0.5,    # 12am-5am: low baseline
            0.8, 1.0, 1.8, 2.0, 2.0, 2.0,     # 6am-11am: work begins
            2.0, 2.0, 2.0, 2.0, 1.8, 1.8,     # 12pm-5pm: work continues
            2.2, 2.5, 2.3, 1.8, 1.3, 0.8,     # 6pm-11pm: evening
        ],
    },
    "nine_to_five": {
        "name": "9-5 Worker",
        "description": "Away during day, peaks at morning/evening (~28 kWh/day)",
        "hourly_kwh": [
            0.5, 0.4, 0.4, 0.4, 0.4, 0.5,    # 12am-5am: low baseline
            1.2, 1.8, 2.0, 0.6, 0.5, 0.5,     # 6am-11am: morning rush then away
            0.5, 0.5, 0.5, 0.5, 0.6, 1.5,     # 12pm-5pm: away then commute
            2.5, 2.8, 2.5, 2.0, 1.5, 0.8,     # 6pm-11pm: evening peak
        ],
    },
}


def _build_hourly_carbon_map(fuel_mix_records: list[dict]) -> dict[int, dict]:
    """Build a mapping of hour -> {carbon_intensity, renewable_pct, fuel_breakdown}.

    Averages across all days in the dataset to get typical hourly patterns.
    """
    from collections import defaultdict

    hourly_fuels = defaultdict(lambda: defaultdict(list))

    for r in fuel_mix_records:
        period = r.get("period", "")
        fuel = r.get("fueltype", r.get("type-name", "OTH"))
        value = r.get("value")
        if not period or value is None:
            continue
        try:
            hour = int(period.split("T")[1][:2]) if "T" in period else 0
            hourly_fuels[hour][fuel].append(float(value))
        except (ValueError, IndexError):
            continue

    hourly_map = {}
    for hour in range(24):
        fuel_avgs = {}
        for fuel, values in hourly_fuels[hour].items():
            fuel_avgs[fuel] = sum(values) / len(values) if values else 0

        total_mwh = sum(fuel_avgs.values())
        carbon = calculate_carbon_intensity(fuel_avgs)
        renewable = calculate_renewable_pct(fuel_avgs)

        # Split into green and brown MWh
        green_mwh = sum(
            mwh for fuel, mwh in fuel_avgs.items()
            if FUEL_INFO.get(fuel, {}).get("renewable", False)
        )
        brown_mwh = total_mwh - green_mwh

        hourly_map[hour] = {
            "carbon_intensity": round(carbon, 1),
            "renewable_pct": round(renewable, 1),
            "total_mwh": round(total_mwh, 1),
            "green_mwh": round(green_mwh, 1),
            "brown_mwh": round(brown_mwh, 1),
            "fuel_breakdown": {k: round(v, 1) for k, v in fuel_avgs.items()},
        }

    return hourly_map


def calculate_personal_carbon(
    usage_profile: list[float],
    fuel_mix_records: list[dict],
    period_days: int = 7,
) -> dict:
    """Calculate personal carbon emissions from hourly usage profile.

    Args:
        usage_profile: 24 float values representing hourly kWh usage
        fuel_mix_records: Raw EIA API fuel mix records
        period_days: Number of days to project over

    Returns:
        Dict with hourly breakdown, totals, and comparison to average.
    """
    if len(usage_profile) != 24:
        raise ValueError(f"Usage profile must have 24 values, got {len(usage_profile)}")

    hourly_map = _build_hourly_carbon_map(fuel_mix_records)
    if not hourly_map:
        return {"error": "No fuel mix data available for analysis"}

    hourly_breakdown = []
    total_co2_g = 0
    total_kwh = 0
    total_green_kwh = 0
    total_brown_kwh = 0

    for hour in range(24):
        kwh = usage_profile[hour]
        grid = hourly_map.get(hour, {})
        carbon_intensity = grid.get("carbon_intensity", 400)
        renewable_pct = grid.get("renewable_pct", 0)

        co2_g = kwh * carbon_intensity
        green_kwh = kwh * (renewable_pct / 100)
        brown_kwh = kwh - green_kwh

        total_co2_g += co2_g
        total_kwh += kwh
        total_green_kwh += green_kwh
        total_brown_kwh += brown_kwh

        hourly_breakdown.append({
            "hour": hour,
            "kwh": round(kwh, 2),
            "carbon_intensity": round(carbon_intensity, 1),
            "renewable_pct": round(renewable_pct, 1),
            "co2_g": round(co2_g, 1),
            "green_kwh": round(green_kwh, 3),
            "brown_kwh": round(brown_kwh, 3),
        })

    # Daily totals
    daily_co2_kg = total_co2_g / 1000
    daily_kwh = total_kwh

    # Period totals
    period_co2_kg = daily_co2_kg * period_days
    period_kwh = daily_kwh * period_days

    # Average grid carbon intensity (flat usage as baseline)
    avg_carbon = sum(
        grid.get("carbon_intensity", 400) for grid in hourly_map.values()
    ) / max(len(hourly_map), 1)

    # What would flat usage produce?
    flat_hourly = daily_kwh / 24
    flat_co2_g = sum(
        flat_hourly * hourly_map.get(h, {}).get("carbon_intensity", 400)
        for h in range(24)
    )
    flat_co2_kg = flat_co2_g / 1000

    # Comparison: negative means better than average
    vs_average_pct = ((daily_co2_kg - flat_co2_kg) / flat_co2_kg * 100) if flat_co2_kg > 0 else 0

    return {
        "hourly_breakdown": hourly_breakdown,
        "daily_co2_kg": round(daily_co2_kg, 2),
        "daily_kwh": round(daily_kwh, 2),
        "period_co2_kg": round(period_co2_kg, 2),
        "period_kwh": round(period_kwh, 2),
        "period_days": period_days,
        "green_kwh_pct": round((total_green_kwh / total_kwh * 100) if total_kwh > 0 else 0, 1),
        "avg_grid_carbon": round(avg_carbon, 1),
        "vs_average_pct": round(vs_average_pct, 1),
    }


def optimize_usage(
    usage_profile: list[float],
    fuel_mix_records: list[dict],
    period_days: int = 7,
) -> dict:
    """Calculate optimized usage schedule and savings.

    Shifts flexible load to lowest-carbon hours while preserving total kWh.
    Strategy: sort hours by carbon intensity, fill from greenest first.

    Args:
        usage_profile: 24 float values representing hourly kWh usage
        fuel_mix_records: Raw EIA API fuel mix records
        period_days: Number of days to project over

    Returns:
        Dict with optimized schedule, savings in CO2 and cost.
    """
    if len(usage_profile) != 24:
        raise ValueError(f"Usage profile must have 24 values, got {len(usage_profile)}")

    hourly_map = _build_hourly_carbon_map(fuel_mix_records)
    if not hourly_map:
        return {"error": "No fuel mix data available for analysis"}

    total_kwh = sum(usage_profile)

    # Minimum base load per hour (can't shift everything -- keep 20% as fixed)
    base_load_fraction = 0.2
    base_loads = [kwh * base_load_fraction for kwh in usage_profile]
    flexible_kwh = total_kwh - sum(base_loads)

    # Sort hours by carbon intensity (ascending = greenest first)
    hours_by_carbon = sorted(
        range(24),
        key=lambda h: hourly_map.get(h, {}).get("carbon_intensity", 999),
    )

    # Distribute flexible load to greenest hours
    # Cap each hour at a reasonable max (no more than 3x the max original hourly usage)
    max_per_hour = max(usage_profile) * 3
    optimized = list(base_loads)
    remaining = flexible_kwh

    for h in hours_by_carbon:
        if remaining <= 0:
            break
        available = max_per_hour - optimized[h]
        if available > 0:
            add = min(available, remaining)
            optimized[h] += add
            remaining -= add

    # If any remaining, distribute evenly
    if remaining > 0:
        per_hour = remaining / 24
        for h in range(24):
            optimized[h] += per_hour

    # Calculate carbon for optimized profile
    original_result = calculate_personal_carbon(usage_profile, fuel_mix_records, period_days)
    optimized_result = calculate_personal_carbon(optimized, fuel_mix_records, period_days)

    co2_saved_kg = original_result["period_co2_kg"] - optimized_result["period_co2_kg"]
    co2_saved_pct = (
        (co2_saved_kg / original_result["period_co2_kg"] * 100)
        if original_result["period_co2_kg"] > 0
        else 0
    )

    # Estimated cost savings (carbon price proxy: marginal cost difference)
    # Using a simplified model: greener hours tend to have more supply, lower prices
    cost_saved = co2_saved_kg * 0.05  # ~$0.05 per kg CO2 as proxy

    return {
        "optimized_profile": [round(v, 2) for v in optimized],
        "optimized_hourly": optimized_result["hourly_breakdown"],
        "original_co2_kg": original_result["period_co2_kg"],
        "optimized_co2_kg": optimized_result["period_co2_kg"],
        "co2_saved_kg": round(co2_saved_kg, 2),
        "co2_saved_pct": round(co2_saved_pct, 1),
        "estimated_cost_saved": round(cost_saved, 2),
        "period_days": period_days,
        "greenest_hours": hours_by_carbon[:6],
        "dirtiest_hours": hours_by_carbon[-6:][::-1],
    }


def get_typical_profiles() -> dict:
    """Return preset usage profiles for the UI."""
    return {
        key: {
            "name": profile["name"],
            "description": profile["description"],
            "hourly_kwh": profile["hourly_kwh"],
            "daily_total": round(sum(profile["hourly_kwh"]), 1),
        }
        for key, profile in PRESET_PROFILES.items()
    }
