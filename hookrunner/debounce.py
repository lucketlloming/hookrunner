"""Debounce support: suppress repeated hook runs within a cooldown window."""

from __future__ import annotations

import time
from typing import Optional

from hookrunner.cache import get_value, set_value


class DebounceError(Exception):
    """Raised when debounce configuration is invalid."""


_DEFAULT_WINDOW: float = 2.0  # seconds


def _debounce_key(repo: str, event: str, hook_id: str) -> str:
    safe = repo.replace("/", "_").replace("\\", "_")
    return f"debounce:{safe}:{event}:{hook_id}"


def is_debounced(
    repo: str,
    event: str,
    hook_id: str,
    window: float = _DEFAULT_WINDOW,
    *,
    _now: Optional[float] = None,
) -> bool:
    """Return True if the hook fired too recently and should be suppressed."""
    if window <= 0:
        return False
    key = _debounce_key(repo, event, hook_id)
    raw = get_value(repo, key)
    if raw is None:
        return False
    try:
        last = float(raw)
    except (TypeError, ValueError):
        return False
    now = _now if _now is not None else time.monotonic()
    return (now - last) < window


def record_run(
    repo: str,
    event: str,
    hook_id: str,
    *,
    _now: Optional[float] = None,
) -> None:
    """Record that a hook ran right now for debounce tracking."""
    key = _debounce_key(repo, event, hook_id)
    now = _now if _now is not None else time.monotonic()
    # TTL of 60 s is generous; debounce windows are much shorter.
    set_value(repo, key, str(now), ttl=60)


def clear_debounce(repo: str, event: str, hook_id: str) -> None:
    """Remove the debounce record so the hook can run immediately."""
    from hookrunner.cache import _cache_file
    import os

    key = _debounce_key(repo, event, hook_id)
    path = _cache_file(repo, key)
    if path.exists():
        os.remove(path)
