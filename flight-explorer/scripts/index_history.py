"""Parse downloaded ADSB.lol trace files and index into SQLite.

Reads JSON trace files from data/cache/adsb/ and populates data/flights.db
with aircraft tracks, bounding boxes, and metadata for spatial queries.

Usage:
    python3 scripts/index_history.py
    python3 scripts/index_history.py --date 2026-03-25
    python3 scripts/index_history.py --rebuild
"""

import argparse
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = APP_DIR / "data" / "cache" / "adsb"
DB_PATH = APP_DIR / "data" / "flights.db"

sys.path.insert(0, str(APP_DIR))
from services.adsb_client import get_seat_count

SCHEMA = """
CREATE TABLE IF NOT EXISTS tracks (
    id INTEGER PRIMARY KEY,
    hex TEXT NOT NULL,
    date TEXT NOT NULL,
    callsign TEXT,
    registration TEXT,
    type_code TEXT,
    description TEXT,
    positions TEXT,
    min_lat REAL,
    max_lat REAL,
    min_lng REAL,
    max_lng REAL,
    min_alt REAL,
    max_alt REAL,
    point_count INTEGER DEFAULT 0,
    UNIQUE(hex, date)
);

CREATE INDEX IF NOT EXISTS idx_tracks_date ON tracks(date);
CREATE INDEX IF NOT EXISTS idx_tracks_hex ON tracks(hex);
CREATE INDEX IF NOT EXISTS idx_tracks_callsign ON tracks(callsign);
CREATE INDEX IF NOT EXISTS idx_tracks_registration ON tracks(registration);
CREATE INDEX IF NOT EXISTS idx_tracks_bbox ON tracks(min_lat, max_lat, min_lng, max_lng);

CREATE TABLE IF NOT EXISTS index_meta (
    date TEXT PRIMARY KEY,
    indexed_at TEXT NOT NULL,
    track_count INTEGER DEFAULT 0
);
"""


def init_db(db_path: Path) -> sqlite3.Connection:
    """Create or open the SQLite database and ensure schema exists."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript(SCHEMA)
    return conn


def parse_trace_file(file_path: Path) -> dict | None:
    """Parse a single trace JSON file into a track record.

    Trace format (readsb):
        {
            "icao": "a12345",
            "r": "N12345",      # registration
            "t": "B738",        # type code
            "desc": "...",      # description
            "timestamp": 1234.5,
            "trace": [
                [sec_offset, lat, lng, alt, gs, track, flags, vrate, ac_obj, ...],
                ...
            ]
        }
    """
    try:
        data = json.loads(file_path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        log.debug("Skipping %s: %s", file_path, e)
        return None

    icao = data.get("icao", "").strip()
    if not icao:
        return None

    trace = data.get("trace", [])
    if not trace:
        return None

    base_ts = data.get("timestamp", 0)
    registration = data.get("r", "").strip() or None
    type_code = data.get("t", "").strip() or None
    description = data.get("desc", "").strip() or None

    # Extract callsign from aircraft objects in trace entries
    callsign = None
    for point in trace:
        if len(point) > 8 and isinstance(point[8], dict):
            cs = point[8].get("flight", "").strip()
            if cs:
                callsign = cs
                break

    # Build position array and compute bounding box
    positions = []
    lats = []
    lngs = []
    alts = []

    for point in trace:
        if len(point) < 3:
            continue

        sec_offset = point[0]
        lat = point[1]
        lng = point[2]

        if lat is None or lng is None:
            continue

        alt = point[3] if len(point) > 3 else None
        if alt == "ground":
            alt = 0

        ts = base_ts + sec_offset

        pos = {"lat": lat, "lng": lng, "ts": round(ts, 1)}
        if alt is not None:
            pos["alt"] = alt
            try:
                alts.append(float(alt))
            except (TypeError, ValueError):
                pass

        # Include ground speed if available
        if len(point) > 4 and point[4] is not None:
            pos["gs"] = point[4]

        positions.append(pos)
        lats.append(lat)
        lngs.append(lng)

    if not positions:
        return None

    return {
        "hex": icao,
        "callsign": callsign,
        "registration": registration,
        "type_code": type_code,
        "description": description,
        "positions": positions,
        "min_lat": min(lats),
        "max_lat": max(lats),
        "min_lng": min(lngs),
        "max_lng": max(lngs),
        "min_alt": min(alts) if alts else None,
        "max_alt": max(alts) if alts else None,
        "point_count": len(positions),
    }


def index_date(conn: sqlite3.Connection, date_str: str, cache_dir: Path, force: bool = False) -> int:
    """Index all trace files for a given date.

    Args:
        conn: SQLite connection
        date_str: Date string like "2026-03-25"
        cache_dir: Base cache directory
        force: If True, re-index even if already done

    Returns:
        Number of tracks indexed
    """
    # Check if already indexed
    if not force:
        row = conn.execute(
            "SELECT 1 FROM index_meta WHERE date = ?", (date_str,)
        ).fetchone()
        if row:
            log.info("Skipping %s (already indexed)", date_str)
            return 0

    day_dir = cache_dir / date_str
    if not day_dir.is_dir():
        log.warning("No data directory for %s at %s", date_str, day_dir)
        return 0

    json_files = list(day_dir.glob("*.json"))
    if not json_files:
        log.warning("No trace files found in %s", day_dir)
        return 0

    log.info("Indexing %d trace files for %s ...", len(json_files), date_str)

    # Clear existing data for this date if re-indexing
    conn.execute("DELETE FROM tracks WHERE date = ?", (date_str,))

    count = 0
    batch = []

    for file_path in json_files:
        track = parse_trace_file(file_path)
        if track is None:
            continue

        batch.append((
            track["hex"],
            date_str,
            track["callsign"],
            track["registration"],
            track["type_code"],
            track["description"],
            json.dumps(track["positions"]),
            track["min_lat"],
            track["max_lat"],
            track["min_lng"],
            track["max_lng"],
            track["min_alt"],
            track["max_alt"],
            track["point_count"],
        ))

        if len(batch) >= 500:
            _insert_batch(conn, batch)
            count += len(batch)
            batch = []

    if batch:
        _insert_batch(conn, batch)
        count += len(batch)

    # Record indexing metadata
    conn.execute(
        "INSERT OR REPLACE INTO index_meta (date, indexed_at, track_count) VALUES (?, ?, ?)",
        (date_str, datetime.utcnow().isoformat(), count),
    )
    conn.commit()

    log.info("Indexed %d tracks for %s", count, date_str)
    return count


def _insert_batch(conn: sqlite3.Connection, batch: list[tuple]) -> None:
    """Insert a batch of track records."""
    conn.executemany(
        """INSERT OR REPLACE INTO tracks
           (hex, date, callsign, registration, type_code, description,
            positions, min_lat, max_lat, min_lng, max_lng,
            min_alt, max_alt, point_count)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        batch,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Index downloaded ADSB history into SQLite"
    )
    parser.add_argument(
        "--date",
        type=str,
        help="Index a specific date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--db",
        type=str,
        default=str(DB_PATH),
        help="Path to SQLite database",
    )
    parser.add_argument(
        "--cache-dir",
        type=str,
        default=str(CACHE_DIR),
        help="Path to cached trace files",
    )
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Drop and rebuild all indexed data",
    )

    args = parser.parse_args()
    db_path = Path(args.db)
    cache_dir = Path(args.cache_dir)

    conn = init_db(db_path)

    if args.rebuild:
        log.info("Rebuilding database...")
        conn.execute("DELETE FROM tracks")
        conn.execute("DELETE FROM index_meta")
        conn.commit()

    total = 0

    if args.date:
        # Index a single date
        total = index_date(conn, args.date, cache_dir, force=args.rebuild)
    else:
        # Index all available dates
        if not cache_dir.is_dir():
            log.error("Cache directory does not exist: %s", cache_dir)
            sys.exit(1)

        # Find date directories (YYYY-MM-DD format)
        date_dirs = sorted(
            d.name for d in cache_dir.iterdir()
            if d.is_dir() and len(d.name) == 10 and d.name[4] == "-"
        )

        if not date_dirs:
            log.warning("No date directories found in %s", cache_dir)
            sys.exit(0)

        log.info("Found %d date(s) to index", len(date_dirs))

        for date_str in date_dirs:
            count = index_date(conn, date_str, cache_dir, force=args.rebuild)
            total += count

    conn.close()
    log.info("Done. Total tracks indexed: %d", total)


if __name__ == "__main__":
    main()
