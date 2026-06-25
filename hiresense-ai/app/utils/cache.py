"""Disk-backed cache factory used to memoize expensive embedding calls."""
from __future__ import annotations

from pathlib import Path

import diskcache


def build_cache(cache_dir: Path, ttl_seconds: int) -> diskcache.Cache:
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache = diskcache.Cache(str(cache_dir))
    cache.expire_default = ttl_seconds  # informational; set() calls pass expire explicitly if needed
    return cache
