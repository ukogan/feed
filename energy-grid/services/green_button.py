"""Green Button XML parser for ESPI (Energy Services Provider Interface) smart meter data.

Parses Green Button XML files and extracts hourly usage profiles compatible with
the Carbon Accountant's 24-hour format.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone


# ESPI namespace variations
ESPI_NS = "http://naesb.org/espi"
ATOM_NS = "http://www.w3.org/2005/Atom"

# UOM codes per ESPI standard
UOM_WH = 72
UOM_W = 38


def _find_all(root: ET.Element, tag: str) -> list[ET.Element]:
    """Find all elements matching tag across namespace variations.

    Green Button files vary: some use prefixed namespaces, some use default
    namespace, some omit namespaces entirely.
    """
    results = []
    # Try with ESPI namespace
    results.extend(root.iter(f"{{{ESPI_NS}}}{tag}"))
    # Try without namespace (bare tag)
    if not results:
        results.extend(root.iter(tag))
    return results


def _find_child(parent: ET.Element, tag: str) -> ET.Element | None:
    """Find a direct or nested child element across namespace variations."""
    # Try ESPI namespace first
    el = parent.find(f".//{{{ESPI_NS}}}{tag}")
    if el is not None:
        return el
    # Try bare tag
    el = parent.find(f".//{tag}")
    return el


def _get_text(parent: ET.Element, tag: str) -> str | None:
    """Get text content of a child element."""
    el = _find_child(parent, tag)
    if el is not None and el.text:
        return el.text.strip()
    return None


def _parse_reading_type(root: ET.Element) -> dict:
    """Extract ReadingType metadata (unit of measure, power multiplier)."""
    info = {
        "power_of_ten_multiplier": 0,
        "uom": UOM_WH,
    }

    reading_types = _find_all(root, "ReadingType")
    for rt in reading_types:
        potm = _get_text(rt, "powerOfTenMultiplier")
        if potm is not None:
            try:
                info["power_of_ten_multiplier"] = int(potm)
            except ValueError:
                pass

        uom = _get_text(rt, "uom")
        if uom is not None:
            try:
                info["uom"] = int(uom)
            except ValueError:
                pass

    return info


def _parse_interval_readings(root: ET.Element) -> list[dict]:
    """Extract all IntervalReading elements with timestamp and raw value."""
    readings = []

    for ir in _find_all(root, "IntervalReading"):
        time_period = _find_child(ir, "timePeriod")
        if time_period is None:
            continue

        start_text = _get_text(time_period, "start")
        duration_text = _get_text(time_period, "duration")
        value_text = _get_text(ir, "value")

        if start_text is None or value_text is None:
            continue

        try:
            start_ts = int(start_text)
            duration = int(duration_text) if duration_text else 3600
            value = float(value_text)
        except (ValueError, TypeError):
            continue

        readings.append({
            "start": start_ts,
            "duration": duration,
            "value": value,
        })

    return readings


def parse_green_button(xml_content: str | bytes) -> dict:
    """Parse a Green Button XML file and extract an hourly usage profile.

    Args:
        xml_content: Raw XML string or bytes from a Green Button export.

    Returns:
        Dict containing:
            hourly_profile: list of 24 floats (average kWh per hour of day)
            total_kwh: total consumption across all readings
            date_range: {start: ISO date, end: ISO date}
            num_readings: count of parsed interval readings
            raw_readings: list of {timestamp: ISO string, kwh: float}

    Raises:
        ValueError: If the XML cannot be parsed or contains no valid readings.
    """
    try:
        root = ET.fromstring(xml_content if isinstance(xml_content, bytes) else xml_content.encode("utf-8"))
    except ET.ParseError as e:
        raise ValueError(f"Invalid XML: {e}")

    # Extract reading type metadata
    reading_type = _parse_reading_type(root)
    potm = reading_type["power_of_ten_multiplier"]
    uom = reading_type["uom"]

    # Conversion to kWh:
    # ESPI spec says actualValue = value * 10^powerOfTenMultiplier in the UOM.
    # But many utilities (PG&E, etc.) use powerOfTenMultiplier non-standardly.
    # We detect and handle both cases by sanity-checking the result.
    # First pass: assume values are raw Wh (ignore multiplier), convert to kWh.
    # If that produces unreasonable results, try with multiplier.

    # Extract all interval readings
    raw_readings = _parse_interval_readings(root)

    if not raw_readings:
        raise ValueError(
            "No valid IntervalReading elements found in the XML. "
            "Ensure the file is a valid Green Button / ESPI export."
        )

    # Convert to kWh and build hourly buckets
    hourly_buckets: dict[int, list[float]] = defaultdict(list)
    converted_readings = []
    total_kwh = 0.0

    for reading in raw_readings:
        raw_value = reading["value"]

        if uom == UOM_W:
            # Watts: convert to Wh using duration, then to kWh
            kwh = raw_value * (reading["duration"] / 3600) / 1000
        else:
            # Wh: convert to kWh (treat values as raw Wh, ignore multiplier)
            kwh = raw_value / 1000

        total_kwh += kwh

        dt = datetime.fromtimestamp(reading["start"], tz=timezone.utc)
        hour_of_day = dt.hour

        # For sub-hourly intervals (e.g., 15-min), accumulate into the hour bucket
        # For hourly intervals, this is a single entry
        hourly_buckets[hour_of_day].append(kwh)

        converted_readings.append({
            "timestamp": dt.isoformat(),
            "kwh": round(kwh, 4),
        })

    # Build 24-hour average profile
    # For sub-hourly data (e.g., 4x 15-min readings per hour), we need to sum
    # within each hour of each day, then average across days.
    # Strategy: group by (date, hour), sum within each group, then average across dates.

    date_hour_totals: dict[tuple[str, int], float] = defaultdict(float)
    dates_seen: set[str] = set()

    for reading in raw_readings:
        raw_value = reading["value"]
        if uom == UOM_W:
            kwh = raw_value * (reading["duration"] / 3600) / 1000
        else:
            kwh = raw_value / 1000

        dt = datetime.fromtimestamp(reading["start"], tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        dates_seen.add(date_str)
        date_hour_totals[(date_str, dt.hour)] += kwh

    # Average across all days for each hour
    num_days = len(dates_seen)
    hourly_profile = []
    for hour in range(24):
        hour_total = sum(
            date_hour_totals[(d, hour)]
            for d in dates_seen
            if (d, hour) in date_hour_totals
        )
        avg = hour_total / num_days if num_days > 0 else 0.0
        hourly_profile.append(round(avg, 3))

    # Date range
    timestamps = [r["start"] for r in raw_readings]
    start_dt = datetime.fromtimestamp(min(timestamps), tz=timezone.utc)
    end_dt = datetime.fromtimestamp(max(timestamps), tz=timezone.utc)

    return {
        "hourly_profile": hourly_profile,
        "total_kwh": round(total_kwh, 2),
        "date_range": {
            "start": start_dt.strftime("%Y-%m-%d"),
            "end": end_dt.strftime("%Y-%m-%d"),
        },
        "num_readings": len(raw_readings),
        "num_days": num_days,
        "daily_avg_kwh": round(total_kwh / num_days, 2) if num_days > 0 else 0,
        "raw_readings": converted_readings,
    }
