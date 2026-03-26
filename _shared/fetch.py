"""Async HTTP client with retry, rate-limiting, and cache integration."""

import asyncio
import time

import httpx

from _shared.cache import Cache


class RateLimiter:
    """Simple token bucket rate limiter."""

    def __init__(self, requests_per_second: float = 1.0):
        self.min_interval = 1.0 / requests_per_second
        self._last_request = 0.0

    async def wait(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_request
        if elapsed < self.min_interval:
            await asyncio.sleep(self.min_interval - elapsed)
        self._last_request = time.monotonic()


class Fetcher:
    """HTTP client with caching and rate limiting."""

    def __init__(
        self,
        cache: Cache | None = None,
        requests_per_second: float = 2.0,
        default_ttl: int = 3600,
    ):
        self.cache = cache
        self.rate_limiter = RateLimiter(requests_per_second)
        self.default_ttl = default_ttl
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def get_json(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
        ttl: int | None = None,
        skip_cache: bool = False,
    ) -> dict | list:
        """Fetch JSON with caching and rate limiting."""
        ttl = ttl if ttl is not None else self.default_ttl

        # Check cache
        if self.cache and not skip_cache:
            cached = self.cache.get(url, params)
            if cached is not None:
                return cached

        # Rate limit and fetch
        await self.rate_limiter.wait()
        client = await self._get_client()

        response = await client.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()

        # Store in cache
        if self.cache and not skip_cache:
            self.cache.set(url, data, ttl_seconds=ttl, params=params)

        return data

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
