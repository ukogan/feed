"""Backfill monthly AQI averages from EPA AQS into SQLite.

Pulls daily AQI data and aggregates to monthly averages per station.
Uses the annualData endpoint for efficiency (one call per state per year).
"""

import os
import sqlite3
import sys
import time
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")

EPA_EMAIL = os.getenv("EPA_EMAIL", "")
if not EPA_EMAIL:
    print("ERROR: Set EPA_EMAIL in .env")
    sys.exit(1)

BASE_URL = "https://aqs.epa.gov/data/api"
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "aqi.db"

# PM2.5 FRM/FEM parameter code
PARAMETER = "88101"
PARAMETER_NAME = "PM2.5"

# Years to backfill
START_YEAR = 2024
END_YEAR = 2025

# TEMP: Only key states for quick initial data
US_STATES = [
    "06", "36", "48", "12", "53",  # CA, NY, TX, FL, WA
]


def fetch_daily_data(state_code: str, year: int) -> list[dict]:
    """Fetch daily PM2.5 data for a state and year."""
    url = f"{BASE_URL}/dailyData/byState"
    params = {
        "email": EPA_EMAIL,
        "key": "tealkit72",
        "param": PARAMETER,
        "bdate": f"{year}0101",
        "edate": f"{year}1231",
        "state": state_code,
    }
    response = httpx.get(url, params=params, timeout=60)
    response.raise_for_status()
    data = response.json()
    if data.get("Header", [{}])[0].get("status") == "Failed":
        return []
    return data.get("Data", [])


def aggregate_monthly(records: list[dict]) -> list[dict]:
    """Aggregate daily records to monthly averages per site."""
    from collections import defaultdict

    buckets = defaultdict(list)
    for r in records:
        date_str = r.get("date_local", "")
        if len(date_str) < 7:
            continue
        site_id = f"{r.get('state_code', '')}-{r.get('county_code', '')}-{r.get('site_number', '')}"
        year = int(date_str[:4])
        month = int(date_str[5:7])
        aqi = r.get("aqi")
        if aqi is None:
            continue
        buckets[(site_id, year, month)].append(float(aqi))

    results = []
    for (site_id, year, month), values in buckets.items():
        results.append({
            "site_id": site_id,
            "year": year,
            "month": month,
            "avg_aqi": sum(values) / len(values),
            "max_aqi": max(values),
            "obs_count": len(values),
        })
    return results


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    # Ensure table exists
    conn.execute("""
        CREATE TABLE IF NOT EXISTS monthly_aqi (
            site_id TEXT NOT NULL,
            year INTEGER NOT NULL,
            month INTEGER NOT NULL,
            parameter TEXT NOT NULL,
            avg_aqi REAL NOT NULL,
            max_aqi REAL,
            obs_count INTEGER,
            PRIMARY KEY (site_id, year, month, parameter)
        )
    """)

    total_records = 0
    for year in range(START_YEAR, END_YEAR + 1):
        for state in US_STATES:
            print(f"  {year} state {state}...", end=" ", flush=True)

            try:
                daily = fetch_daily_data(state, year)
            except Exception as e:
                print(f"ERROR: {e}")
                time.sleep(2)
                continue

            if not daily:
                print("no data")
                continue

            monthly = aggregate_monthly(daily)
            for m in monthly:
                conn.execute(
                    """INSERT OR REPLACE INTO monthly_aqi
                       (site_id, year, month, parameter, avg_aqi, max_aqi, obs_count)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (m["site_id"], m["year"], m["month"], PARAMETER_NAME,
                     m["avg_aqi"], m["max_aqi"], m["obs_count"]),
                )
            conn.commit()
            total_records += len(monthly)
            print(f"{len(monthly)} monthly records")

            # Rate limit: EPA AQS is slow, be polite
            time.sleep(1)

    print(f"\nTotal: {total_records} monthly records saved to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
