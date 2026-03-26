"""HTTP response cache backed by SQLite."""

import hashlib
import json
import sqlite3
import time
from pathlib import Path


class Cache:
    """Simple SQLite-backed cache with TTL support."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at REAL NOT NULL
                )
            """)

    @staticmethod
    def _make_key(url: str, params: dict | None = None) -> str:
        raw = url + json.dumps(params or {}, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, url: str, params: dict | None = None) -> dict | list | None:
        """Get cached response if not expired."""
        key = self._make_key(url, params)
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute(
                "SELECT value, expires_at FROM cache WHERE key = ?", (key,)
            ).fetchone()
        if row is None:
            return None
        value, expires_at = row
        if time.time() > expires_at:
            return None
        return json.loads(value)

    def set(
        self,
        url: str,
        data: dict | list,
        ttl_seconds: int = 3600,
        params: dict | None = None,
    ) -> None:
        """Cache a response with TTL."""
        key = self._make_key(url, params)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, json.dumps(data), time.time() + ttl_seconds),
            )

    def clear_expired(self) -> int:
        """Remove expired entries. Returns count of removed entries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?", (time.time(),)
            )
            return cursor.rowcount
