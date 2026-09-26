"""A tiny in-process TTL cache with stale-on-error fallback.

Vercel Fluid compute reuses warm instances, so this absorbs bursts of traffic
without hammering BMKG. The CDN (`Cache-Control: s-maxage`) is the first layer;
this is the second.
"""

import asyncio
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, max_stale: float = 3600.0) -> None:
        self._data: dict[str, _Entry] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._max_stale = max_stale

    async def get_or_set[T](self, key: str, ttl: float, factory: Callable[[], Awaitable[T]]) -> T:
        now = time.monotonic()
        entry = self._data.get(key)
        if entry and entry.expires_at > now:
            return entry.value

        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            entry = self._data.get(key)
            now = time.monotonic()
            if entry and entry.expires_at > now:
                return entry.value
            try:
                value = await factory()
            except Exception:
                # Serve stale data rather than fail, within a bounded window.
                if entry and now - entry.expires_at < self._max_stale:
                    return entry.value
                raise
            self._data[key] = _Entry(value, now + ttl)
            return value

    def clear(self) -> None:
        self._data.clear()
