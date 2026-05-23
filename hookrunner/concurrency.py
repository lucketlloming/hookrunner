"""Concurrency limit support for hook execution."""

from __future__ import annotations

import threading
from typing import Optional


class ConcurrencyError(Exception):
    """Raised when concurrency configuration is invalid."""


_semaphores: dict[str, threading.Semaphore] = {}
_lock = threading.Lock()


def _semaphore_key(repo: str, event: str) -> str:
    return f"{repo}:{event}"


def get_semaphore(repo: str, event: str, limit: int) -> threading.Semaphore:
    """Return (or create) a semaphore for the given repo+event with *limit* slots."""
    if limit < 1:
        raise ConcurrencyError(f"concurrency limit must be >= 1, got {limit}")
    key = _semaphore_key(repo, event)
    with _lock:
        if key not in _semaphores:
            _semaphores[key] = threading.Semaphore(limit)
        return _semaphores[key]


def clear_semaphore(repo: str, event: str) -> None:
    """Remove a cached semaphore (useful in tests)."""
    key = _semaphore_key(repo, event)
    with _lock:
        _semaphores.pop(key, None)


def clear_all_semaphores() -> None:
    """Remove all cached semaphores."""
    with _lock:
        _semaphores.clear()


def parse_concurrency_limit(hook_cfg: dict) -> Optional[int]:
    """Extract an integer concurrency limit from a hook config dict.

    Returns *None* if the key is absent (meaning no limit).
    Raises *ConcurrencyError* on invalid values.
    """
    if "concurrency" not in hook_cfg:
        return None
    raw = hook_cfg["concurrency"]
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise ConcurrencyError(
            f"'concurrency' must be an integer, got {type(raw).__name__!r}"
        )
    if raw < 1:
        raise ConcurrencyError(f"'concurrency' must be >= 1, got {raw}")
    return raw
