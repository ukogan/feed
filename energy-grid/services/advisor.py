"""Smart timing advisor: recommends best hours for energy-intensive tasks.

Analyzes historical fuel mix patterns to find hours with highest renewable
percentage and lowest carbon intensity.
"""

from collections import defaultdict

from services.carbon import calculate_carbon_intensity, calculate_renewable_pct


def analyze_hourly_patterns(records: list[dict]) -> list[dict]:
    """Analyze fuel mix records to find best/worst hours.

    Args:
        records: EIA API fuel mix records with 'period', 'fueltype', 'value' fields

    Returns:
        List of 24 hourly summaries with carbon intensity and recommendation.
    """
    # Group by hour of day
    hourly_fuels = defaultdict(lambda: defaultdict(list))

    for r in records:
        period = r.get("period", "")
        fuel = r.get("fueltype", r.get("type-name", "OTH"))
        value = r.get("value")
        if not period or value is None:
            continue
        try:
            # period format: "2024-01-15T14" or similar
            hour = int(period.split("T")[1][:2]) if "T" in period else 0
            hourly_fuels[hour][fuel].append(float(value))
        except (ValueError, IndexError):
            continue

    # Average each fuel type per hour
    results = []
    for hour in range(24):
        fuel_avgs = {}
        for fuel, values in hourly_fuels[hour].items():
            fuel_avgs[fuel] = sum(values) / len(values) if values else 0

        carbon = calculate_carbon_intensity(fuel_avgs)
        renewable = calculate_renewable_pct(fuel_avgs)

        results.append({
            "hour": hour,
            "carbon_intensity": round(carbon, 1),
            "renewable_pct": round(renewable, 1),
            "fuel_breakdown": {k: round(v, 1) for k, v in fuel_avgs.items()},
        })

    # Rank and assign recommendations
    if results:
        carbons = [r["carbon_intensity"] for r in results if r["carbon_intensity"] > 0]
        if carbons:
            p25 = sorted(carbons)[len(carbons) // 4]
            p75 = sorted(carbons)[3 * len(carbons) // 4]

            for r in results:
                c = r["carbon_intensity"]
                if c <= p25:
                    r["recommendation"] = "best"
                    r["reason"] = "Lowest carbon intensity -- high renewable generation"
                elif c >= p75:
                    r["recommendation"] = "avoid"
                    r["reason"] = "Highest carbon intensity -- fossil-heavy generation"
                else:
                    r["recommendation"] = "good"
                    r["reason"] = "Moderate carbon intensity"

    return results


def get_best_windows(hourly_patterns: list[dict], window_size: int = 3) -> list[dict]:
    """Find the best N-hour windows for low-carbon energy use.

    Returns top 3 windows sorted by average carbon intensity.
    """
    if len(hourly_patterns) < window_size:
        return []

    windows = []
    for start in range(24):
        hours = [(start + i) % 24 for i in range(window_size)]
        window_data = [hourly_patterns[h] for h in hours]
        avg_carbon = sum(w["carbon_intensity"] for w in window_data) / window_size
        avg_renewable = sum(w["renewable_pct"] for w in window_data) / window_size

        windows.append({
            "start_hour": start,
            "end_hour": (start + window_size) % 24,
            "avg_carbon_intensity": round(avg_carbon, 1),
            "avg_renewable_pct": round(avg_renewable, 1),
            "hours": hours,
        })

    windows.sort(key=lambda w: w["avg_carbon_intensity"])
    return windows[:3]
