"""Hook execution throttling to prevent rapid re-runs within a time window."""

import time
from typing import Dict, Optional


class ThrottleError(Exception):
    """Raised when throttle configuration is invalid."""


# In-memory store: (repo, hook_name) -> last_run_timestamp
_last_run: Dict[tuple, float] = {}


def _throttle_key(repo: str, hook_name: str) -> tuple:
    return (repo, hook_name)


def get_last_run(repo: str, hook_name: str) -> Optional[float]:
    """Return the timestamp of the last run for a hook, or None."""
    return _last_run.get(_throttle_key(repo, hook_name))


def record_run(repo: str, hook_name: str, ts: Optional[float] = None) -> float:
    """Record that a hook was run. Returns the recorded timestamp."""
    ts = ts if ts is not None else time.time()
    _last_run[_throttle_key(repo, hook_name)] = ts
    return ts


def clear_run(repo: str, hook_name: str) -> None:
    """Clear the recorded run time for a hook."""
    _last_run.pop(_throttle_key(repo, hook_name), None)


def clear_all() -> None:
    """Clear all throttle state (useful for testing)."""
    _last_run.clear()


def is_throttled(repo: str, hook_name: str, window: float) -> bool:
    """Return True if the hook ran within the last *window* seconds.

    Args:
        repo: Absolute path to the git repository.
        hook_name: Name of the hook (e.g. 'pre-commit').
        window: Minimum seconds that must pass between runs. Must be >= 0.

    Raises:
        ThrottleError: If *window* is negative.
    """
    if window < 0:
        raise ThrottleError(f"Throttle window must be >= 0, got {window}")
    if window == 0:
        return False
    last = get_last_run(repo, hook_name)
    if last is None:
        return False
    return (time.time() - last) < window


def parse_throttle_window(hook_cfg: dict) -> Optional[float]:
    """Extract throttle window (seconds) from a hook config dict.

    Returns None if no throttle is configured.

    Raises:
        ThrottleError: If the value is present but invalid.
    """
    raw = hook_cfg.get("throttle")
    if raw is None:
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError) as exc:
        raise ThrottleError(f"Invalid throttle value {raw!r}: must be a number") from exc
    if value < 0:
        raise ThrottleError(f"Throttle window must be >= 0, got {value}")
    return value
