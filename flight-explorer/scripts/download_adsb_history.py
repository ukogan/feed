"""Download ADSB.lol daily archive files from GitHub releases.

Archives are hosted at github.com/adsblol/globe_history_{YYYY} as tarballs
containing gzip-compressed trace JSON files per aircraft.

Structure inside tarball:
    YYYY/MM/DD/traces/HH/trace_full_AAAAAA.json.gz
    (HH = last 2 hex digits of ICAO address)

Usage:
    python3 scripts/download_adsb_history.py --days 7
    python3 scripts/download_adsb_history.py --start 2026-03-20 --end 2026-03-25
"""

import argparse
import gzip
import io
import json
import logging
import os
import sys
import tarfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

APP_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = APP_DIR / "data" / "cache" / "adsb"

# San Francisco Bay Area bounding box (default)
DEFAULT_BBOX = {
    "min_lat": 37.0,
    "max_lat": 38.2,
    "min_lng": -122.8,
    "max_lng": -121.5,
}

GITHUB_API = "https://api.github.com"
RELEASE_REPO_TEMPLATE = "adsblol/globe_history_{year}"

# Rate limiting: seconds between GitHub API requests
API_DELAY = 1.0
# Seconds between large file downloads
DOWNLOAD_DELAY = 5.0


def get_release_assets(date: datetime) -> list[dict]:
    """Find GitHub release assets for a given date.

    Looks for the prod release first (most complete data).
    Falls back to staging, then mlat-only.
    """
    year = date.strftime("%Y")
    repo = RELEASE_REPO_TEMPLATE.format(year=year)
    date_str = date.strftime("%Y.%m.%d")

    # Prefer prod, then staging, then mlatonly
    variants = [
        f"v{date_str}-planes-readsb-prod-0",
        f"v{date_str}-planes-readsb-staging-0",
        f"v{date_str}-planes-readsb-mlatonly-0",
    ]

    for tag in variants:
        url = f"{GITHUB_API}/repos/{repo}/releases/tags/{tag}"
        log.info("Checking release: %s", tag)

        try:
            resp = httpx.get(url, follow_redirects=True, timeout=30)
            if resp.status_code == 404:
                continue
            resp.raise_for_status()
            data = resp.json()
            assets = data.get("assets", [])
            if assets:
                log.info(
                    "Found release %s with %d asset(s)", tag, len(assets)
                )
                return assets
        except httpx.HTTPError as e:
            log.warning("Error fetching release %s: %s", tag, e)

        time.sleep(API_DELAY)

    return []


def download_and_extract(
    assets: list[dict],
    date: datetime,
    bbox: dict,
    output_dir: Path,
) -> int:
    """Download tarball asset(s) and extract trace files within bounding box.

    Returns number of trace files extracted.
    """
    date_str = date.strftime("%Y/%m/%d")
    extracted = 0

    # Assets may be split (tar.aa, tar.ab, ...) or a single .tar
    asset_urls = sorted(
        [(a["name"], a["browser_download_url"]) for a in assets],
        key=lambda x: x[0],
    )

    # Check if this is a split archive
    is_split = any(name.endswith((".aa", ".ab", ".ac")) for name, _ in asset_urls)

    if is_split:
        log.info(
            "Split archive detected (%d parts). Downloading and concatenating...",
            len(asset_urls),
        )
        extracted = _process_split_archive(asset_urls, date_str, bbox, output_dir)
    else:
        # Single tar file
        for name, url in asset_urls:
            if not name.endswith(".tar"):
                continue
            log.info("Downloading %s ...", name)
            extracted += _process_tar_stream(url, date_str, bbox, output_dir)

    return extracted


def _process_tar_stream(
    url: str,
    date_str: str,
    bbox: dict,
    output_dir: Path,
) -> int:
    """Stream-download a tarball and extract matching trace files."""
    extracted = 0
    traces_prefix = f"{date_str}/traces/"

    with httpx.stream("GET", url, follow_redirects=True, timeout=600) as resp:
        resp.raise_for_status()
        # Read full response into memory (tarballs need seeking)
        log.info("Downloading tarball (this may take a while)...")
        content = resp.read()

    log.info("Downloaded %.1f MB, extracting traces...", len(content) / 1024 / 1024)

    with tarfile.open(fileobj=io.BytesIO(content), mode="r:*") as tar:
        for member in tar:
            if not member.isfile():
                continue
            if "trace_full_" not in member.name:
                continue

            # Extract and parse
            f = tar.extractfile(member)
            if f is None:
                continue

            raw = f.read()
            try:
                # Files may be gzip-compressed inside the tar
                try:
                    text = gzip.decompress(raw).decode("utf-8")
                except (gzip.BadGzipFile, OSError):
                    text = raw.decode("utf-8")

                trace_data = json.loads(text)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                log.debug("Skipping %s: %s", member.name, e)
                continue

            # Check if any position falls within bbox
            if not _trace_intersects_bbox(trace_data, bbox):
                continue

            # Save the trace file
            icao = trace_data.get("icao", "unknown")
            out_path = output_dir / date_str.replace("/", "-") / f"{icao}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(trace_data))
            extracted += 1

            if extracted % 100 == 0:
                log.info("Extracted %d traces so far...", extracted)

    return extracted


def _process_split_archive(
    asset_urls: list[tuple[str, str]],
    date_str: str,
    bbox: dict,
    output_dir: Path,
) -> int:
    """Handle split tar archives (tar.aa, tar.ab, ...)."""
    parts = []
    for name, url in asset_urls:
        # Skip non-archive files (like LICENSE)
        if not (name.endswith(".tar") or name[-3:-1] == ".a" or
                any(name.endswith(f".a{c}") for c in "abcdefghij")):
            # Check with a simpler pattern
            if ".tar." not in name and not name.endswith(".tar"):
                continue

        log.info("Downloading part: %s", name)
        resp = httpx.get(url, follow_redirects=True, timeout=600)
        resp.raise_for_status()
        parts.append(resp.content)
        log.info("  Downloaded %.1f MB", len(resp.content) / 1024 / 1024)
        time.sleep(DOWNLOAD_DELAY)

    if not parts:
        return 0

    combined = b"".join(parts)
    log.info(
        "Combined archive: %.1f MB, extracting traces...",
        len(combined) / 1024 / 1024,
    )

    extracted = 0
    with tarfile.open(fileobj=io.BytesIO(combined), mode="r:*") as tar:
        for member in tar:
            if not member.isfile():
                continue
            if "trace_full_" not in member.name:
                continue

            f = tar.extractfile(member)
            if f is None:
                continue

            raw = f.read()
            try:
                try:
                    text = gzip.decompress(raw).decode("utf-8")
                except (gzip.BadGzipFile, OSError):
                    text = raw.decode("utf-8")

                trace_data = json.loads(text)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue

            if not _trace_intersects_bbox(trace_data, bbox):
                continue

            icao = trace_data.get("icao", "unknown")
            out_path = output_dir / date_str.replace("/", "-") / f"{icao}.json"
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(trace_data))
            extracted += 1

            if extracted % 100 == 0:
                log.info("Extracted %d traces so far...", extracted)

    return extracted


def _trace_intersects_bbox(trace_data: dict, bbox: dict) -> bool:
    """Check if any position in the trace falls within the bounding box."""
    trace = trace_data.get("trace", [])
    if not trace:
        return False

    min_lat = bbox["min_lat"]
    max_lat = bbox["max_lat"]
    min_lng = bbox["min_lng"]
    max_lng = bbox["max_lng"]

    for point in trace:
        if len(point) < 3:
            continue
        lat = point[1]
        lng = point[2]
        if lat is None or lng is None:
            continue
        if min_lat <= lat <= max_lat and min_lng <= lng <= max_lng:
            return True

    return False


def date_already_downloaded(date: datetime, output_dir: Path) -> bool:
    """Check if data for a date has already been downloaded."""
    date_str = date.strftime("%Y-%m-%d")
    day_dir = output_dir / date_str
    marker = day_dir / ".complete"
    return marker.exists()


def mark_date_complete(date: datetime, output_dir: Path, count: int) -> None:
    """Mark a date as fully downloaded."""
    date_str = date.strftime("%Y-%m-%d")
    day_dir = output_dir / date_str
    day_dir.mkdir(parents=True, exist_ok=True)
    marker = day_dir / ".complete"
    marker.write_text(json.dumps({
        "date": date_str,
        "extracted": count,
        "completed_at": datetime.utcnow().isoformat(),
    }))


def main():
    parser = argparse.ArgumentParser(
        description="Download ADSB.lol daily history archives"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to download (counting back from yesterday)",
    )
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--min-lat", type=float, default=DEFAULT_BBOX["min_lat"],
        help="Bounding box minimum latitude",
    )
    parser.add_argument(
        "--max-lat", type=float, default=DEFAULT_BBOX["max_lat"],
        help="Bounding box maximum latitude",
    )
    parser.add_argument(
        "--min-lng", type=float, default=DEFAULT_BBOX["min_lng"],
        help="Bounding box minimum longitude",
    )
    parser.add_argument(
        "--max-lng", type=float, default=DEFAULT_BBOX["max_lng"],
        help="Bounding box maximum longitude",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(CACHE_DIR),
        help="Output directory for cached trace files",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if data exists",
    )

    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    bbox = {
        "min_lat": args.min_lat,
        "max_lat": args.max_lat,
        "min_lng": args.min_lng,
        "max_lng": args.max_lng,
    }

    # Determine date range
    if args.start and args.end:
        start = datetime.strptime(args.start, "%Y-%m-%d")
        end = datetime.strptime(args.end, "%Y-%m-%d")
    else:
        end = datetime.utcnow() - timedelta(days=1)
        start = end - timedelta(days=args.days - 1)

    log.info(
        "Downloading history from %s to %s",
        start.strftime("%Y-%m-%d"),
        end.strftime("%Y-%m-%d"),
    )
    log.info(
        "Bounding box: lat [%.2f, %.2f], lng [%.2f, %.2f]",
        bbox["min_lat"], bbox["max_lat"], bbox["min_lng"], bbox["max_lng"],
    )

    current = start
    total_extracted = 0

    while current <= end:
        date_str = current.strftime("%Y-%m-%d")

        if not args.force and date_already_downloaded(current, output_dir):
            log.info("Skipping %s (already downloaded)", date_str)
            current += timedelta(days=1)
            continue

        log.info("Processing %s ...", date_str)

        assets = get_release_assets(current)
        if not assets:
            log.warning("No release found for %s", date_str)
            current += timedelta(days=1)
            time.sleep(API_DELAY)
            continue

        count = download_and_extract(assets, current, bbox, output_dir)
        log.info("Extracted %d traces for %s", count, date_str)

        mark_date_complete(current, output_dir, count)
        total_extracted += count

        current += timedelta(days=1)
        time.sleep(DOWNLOAD_DELAY)

    log.info("Done. Total traces extracted: %d", total_extracted)


if __name__ == "__main__":
    main()
