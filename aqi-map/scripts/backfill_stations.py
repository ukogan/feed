"""Download EPA AQS monitoring station metadata into SQLite.

EPA AQS API docs: https://aqs.epa.gov/aqsweb/documents/data_api.html
No API key needed, just an email address.
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

# Load .env from repo root
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

EPA_EMAIL = os.getenv("EPA_EMAIL", "")
if not EPA_EMAIL:
    print("ERROR: Set EPA_EMAIL in .env (any valid email works for EPA AQS API)")
    sys.exit(1)

BASE_URL = "https://aqs.epa.gov/data/api"
DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "aqi.db"

# US state FIPS codes
US_STATES = [
    "01", "02", "04", "05", "06", "08", "09", "10", "11", "12",
    "13", "15", "16", "17", "18", "19", "20", "21", "22", "23",
    "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
    "34", "35", "36", "37", "38", "39", "40", "41", "42", "44",
    "45", "46", "47", "48", "49", "50", "51", "53", "54", "55", "56",
]


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS stations (
            site_id TEXT PRIMARY KEY,
            name TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            state_code TEXT,
            county_code TEXT,
            state_name TEXT,
            county_name TEXT
        )
    """)
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


def fetch_monitors(state_code: str, parameter: str = "88101") -> list[dict]:
    """Fetch monitor list for a state. Parameter 88101 = PM2.5."""
    url = f"{BASE_URL}/monitors/byState"
    params = {
        "email": EPA_EMAIL,
        "key": "tealkit72",  # EPA AQS uses "test" as public key
        "param": parameter,
        "bdate": "20200101",
        "edate": "20201231",
        "state": state_code,
    }
    response = httpx.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("Header", [{}])[0].get("status") == "Failed":
        return []
    return data.get("Data", [])


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    total = 0
    for state in US_STATES:
        print(f"  Fetching monitors for state {state}...", end=" ", flush=True)
        try:
            monitors = fetch_monitors(state)
        except Exception as e:
            print(f"ERROR: {e}")
            continue

        count = 0
        for m in monitors:
            site_id = f"{m.get('state_code', '')}-{m.get('county_code', '')}-{m.get('site_number', '')}"
            lat = m.get("latitude")
            lng = m.get("longitude")
            if lat is None or lng is None:
                continue
            conn.execute(
                """INSERT OR REPLACE INTO stations
                   (site_id, name, lat, lng, state_code, county_code, state_name, county_name)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    site_id,
                    m.get("local_site_name", ""),
                    float(lat),
                    float(lng),
                    m.get("state_code", ""),
                    m.get("county_code", ""),
                    m.get("state_name", ""),
                    m.get("county_name", ""),
                ),
            )
            count += 1

        conn.commit()
        total += count
        print(f"{count} monitors")

    print(f"\nTotal: {total} stations saved to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
