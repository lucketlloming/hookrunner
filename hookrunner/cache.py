"""Simple file-based cache for hook execution results and branch metadata."""

import json
import os
import time
from pathlib import Path
from typing import Any, Optional

DEFAULT_TTL = 60  # seconds
_CACHE_DIR_NAME = ".hookrunner_cache"


class CacheError(Exception):
    """Raised when a cache operation fails."""


def _cache_dir(repo_path: str) -> Path:
    return Path(repo_path) / ".git" / _CACHE_DIR_NAME


def _cache_file(repo_path: str, key: str) -> Path:
    safe_key = key.replace("/", "__").replace("\\", "__")
    return _cache_dir(repo_path) / f"{safe_key}.json"


def set_value(repo_path: str, key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Store *value* under *key* with an expiry of *ttl* seconds."""
    cache_dir = _cache_dir(repo_path)
    try:
        cache_dir.mkdir(parents=True, exist_ok=True)
        payload = {"value": value, "expires_at": time.time() + ttl}
        cache_file = _cache_file(repo_path, key)
        cache_file.write_text(json.dumps(payload))
    except OSError as exc:
        raise CacheError(f"Failed to write cache entry '{key}': {exc}") from exc


def get_value(repo_path: str, key: str) -> Optional[Any]:
    """Return the cached value for *key*, or ``None`` if missing / expired."""
    cache_file = _cache_file(repo_path, key)
    if not cache_file.exists():
        return None
    try:
        payload = json.loads(cache_file.read_text())
    except (OSError, json.JSONDecodeError):
        return None
    if time.time() > payload.get("expires_at", 0):
        _try_remove(cache_file)
        return None
    return payload.get("value")


def invalidate(repo_path: str, key: str) -> bool:
    """Delete a single cache entry.  Returns ``True`` if it existed."""
    cache_file = _cache_file(repo_path, key)
    return _try_remove(cache_file)


def clear_all(repo_path: str) -> int:
    """Remove all cache entries for *repo_path*.  Returns the number removed."""
    cache_dir = _cache_dir(repo_path)
    if not cache_dir.exists():
        return 0
    removed = 0
    for entry in cache_dir.glob("*.json"):
        if _try_remove(entry):
            removed += 1
    return removed


def _try_remove(path: Path) -> bool:
    try:
        path.unlink()
        return True
    except OSError:
        return False
