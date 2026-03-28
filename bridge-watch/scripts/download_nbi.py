"""Download and parse FHWA NBI fixed-width bridge data into SQLite.

Data source: https://www.fhwa.dot.gov/bridge/nbi/ascii2024.cfm
Format: Fixed-width text per NBI Recording Guide
"""

import sqlite3
import sys
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "bridges.db"

# State FIPS -> state file code mapping
# FHWA uses 2-letter abbreviations in filenames
STATE_FILES = {
    "06": "CA", "36": "NY", "48": "TX", "12": "FL", "53": "WA",
    "17": "IL", "42": "PA", "39": "OH", "37": "NC", "13": "GA",
}

# NBI field positions (1-indexed in the spec, 0-indexed here)
# Reference: https://www.fhwa.dot.gov/bridge/mtguide.pdf
FIELDS = {
    "state_code": (0, 2),  # 2-char FIPS state code
    "structure_number": (3, 18),
    "facility_carried": (18, 43),
    "feature_intersected": (43, 68),
    "location": (68, 93),
    "lat": (129, 137),       # Item 16: latitude DDMMSSss
    "lng": (137, 146),       # Item 17: longitude DDDMMSSss
    "year_built": (156, 160),
    "adt": (164, 170),       # Item 29: average daily traffic
    "deck_cond": (200, 201),    # Best distribution: ~2% good, 80% fair, 15% poor
    "super_cond": (203, 204),   # Item 59
    "sub_cond": (204, 205),     # Item 60 (skip channel cond at 202)
}


def parse_coord_lat(raw: str) -> float | None:
    """Parse NBI latitude DDMMSSss to decimal degrees."""
    raw = raw.strip()
    if not raw or len(raw) < 6:
        return None
    try:
        dd = int(raw[:2])
        mm = int(raw[2:4])
        ss = int(raw[4:6])
        hs = int(raw[6:8]) if len(raw) >= 8 else 0
        return dd + mm / 60 + (ss + hs / 100) / 3600
    except (ValueError, IndexError):
        return None


def parse_coord_lng(raw: str) -> float | None:
    """Parse NBI longitude DDDMMSSss to decimal degrees (negated for US)."""
    raw = raw.strip()
    if not raw or len(raw) < 7:
        return None
    try:
        ddd = int(raw[:3])
        mm = int(raw[3:5])
        ss = int(raw[5:7])
        hs = int(raw[7:9]) if len(raw) >= 9 else 0
        return -(ddd + mm / 60 + (ss + hs / 100) / 3600)
    except (ValueError, IndexError):
        return None


def safe_int(s: str) -> int | None:
    s = s.strip()
    if not s or s == 'N':
        return None
    try:
        return int(s)
    except ValueError:
        return None


def classify_condition(deck, super_, sub) -> str:
    # Use deck condition as primary indicator (most reliable field position)
    # Exclude 0 and None as "not rated"
    if deck is not None and deck > 0:
        if deck >= 7:
            return "good"
        if deck >= 5:
            return "fair"
        return "poor"
    # Fallback to superstructure
    if super_ is not None and super_ > 0:
        if super_ >= 7:
            return "good"
        if super_ >= 5:
            return "fair"
        return "poor"
    return "unknown"


def init_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DROP TABLE IF EXISTS bridges")
    conn.execute("""
        CREATE TABLE bridges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code TEXT,
            structure_number TEXT,
            name TEXT,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            year_built INTEGER,
            adt INTEGER,
            deck_cond INTEGER,
            super_cond INTEGER,
            sub_cond INTEGER,
            condition TEXT
        )
    """)
    conn.execute("CREATE INDEX idx_bridges_state ON bridges(state_code)")
    return conn


def download_and_parse(state_fips: str, state_abbr: str) -> list[tuple]:
    url = f"https://www.fhwa.dot.gov/bridge/nbi/2024/{state_abbr}24.txt"
    print(f"  Downloading {state_abbr} ({state_fips})...", end=" ", flush=True)

    resp = httpx.get(url, timeout=60, follow_redirects=True)
    resp.raise_for_status()

    bridges = []
    for line in resp.text.splitlines():
        if len(line) < 203:
            continue

        lat = parse_coord_lat(line[FIELDS["lat"][0]:FIELDS["lat"][1]])
        lng = parse_coord_lng(line[FIELDS["lng"][0]:FIELDS["lng"][1]])

        if lat is None or lng is None or (lat == 0 and lng == 0):
            continue

        deck = safe_int(line[FIELDS["deck_cond"][0]:FIELDS["deck_cond"][1]])
        super_ = safe_int(line[FIELDS["super_cond"][0]:FIELDS["super_cond"][1]])
        sub = safe_int(line[FIELDS["sub_cond"][0]:FIELDS["sub_cond"][1]])
        condition = classify_condition(deck, super_, sub)

        bridges.append((
            line[FIELDS["state_code"][0]:FIELDS["state_code"][1]].strip(),
            line[FIELDS["structure_number"][0]:FIELDS["structure_number"][1]].strip(),
            line[FIELDS["facility_carried"][0]:FIELDS["facility_carried"][1]].strip(),
            lat, lng,
            safe_int(line[FIELDS["year_built"][0]:FIELDS["year_built"][1]]),
            safe_int(line[FIELDS["adt"][0]:FIELDS["adt"][1]]),
            deck, super_, sub, condition,
        ))

    print(f"{len(bridges)} bridges")
    return bridges


def main():
    conn = init_db()
    total = 0

    states = STATE_FILES
    if len(sys.argv) > 1:
        # Allow specifying states: python download_nbi.py CA TX
        states = {k: v for k, v in STATE_FILES.items() if v in sys.argv[1:]}

    for fips, abbr in states.items():
        try:
            bridges = download_and_parse(fips, abbr)
            conn.executemany(
                "INSERT INTO bridges (state_code, structure_number, name, lat, lng, year_built, adt, deck_cond, super_cond, sub_cond, condition) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                bridges,
            )
            conn.commit()
            total += len(bridges)
        except Exception as e:
            print(f"ERROR: {e}")

    print(f"\nTotal: {total} bridges saved to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
