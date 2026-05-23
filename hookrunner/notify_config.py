"""Parse notification settings from hookrunner config."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class NotifyConfigError(ValueError):
    """Raised when the notifications block is malformed."""


_VALID_EVENTS = frozenset({"start", "success", "failure", "skip"})
_VALID_CHANNELS = frozenset({"stderr"})


def parse_notify_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate the ``notifications`` block from *config*.

    Returns a normalised dict::

        {
            "enabled": bool,
            "events": ["start", "success", "failure", "skip"],
            "channels": ["stderr"],
        }

    Returns ``None`` when the block is absent or empty.
    """
    raw: Any = config.get("notifications")
    if not raw:
        return None

    if not isinstance(raw, dict):
        raise NotifyConfigError(
            f"'notifications' must be a mapping, got {type(raw).__name__}"
        )

    enabled: bool = bool(raw.get("enabled", True))

    events: List[str] = _parse_list(raw, "events", _VALID_EVENTS, default=list(_VALID_EVENTS))
    channels: List[str] = _parse_list(raw, "channels", _VALID_CHANNELS, default=["stderr"])

    return {"enabled": enabled, "events": events, "channels": channels}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _parse_list(
    raw: Dict[str, Any],
    key: str,
    valid: frozenset,
    default: List[str],
) -> List[str]:
    value = raw.get(key)
    if value is None:
        return default

    if isinstance(value, str):
        value = [value]

    if not isinstance(value, list):
        raise NotifyConfigError(
            f"'notifications.{key}' must be a list or string, got {type(value).__name__}"
        )

    unknown = [v for v in value if v not in valid]
    if unknown:
        raise NotifyConfigError(
            f"'notifications.{key}' contains unknown values: {unknown}. "
            f"Valid options: {sorted(valid)}"
        )

    return value
