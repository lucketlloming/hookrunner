"""Parse snapshot-related configuration from a hook definition."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class SnapshotConfigError(Exception):
    """Raised for invalid snapshot configuration."""


_KNOWN_KEYS = {"enabled", "watch"}


def parse_snapshot_config(hook_cfg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate the ``snapshot`` block from *hook_cfg*.

    Returns a normalised dict with keys:
      - ``enabled`` (bool, default True)
      - ``watch``   (list[str], default [])

    Returns *None* if the ``snapshot`` key is absent or the block is empty.
    """
    raw = hook_cfg.get("snapshot")
    if not raw:
        return None

    if not isinstance(raw, dict):
        raise SnapshotConfigError(
            f"'snapshot' must be a mapping, got {type(raw).__name__}"
        )

    unknown = set(raw) - _KNOWN_KEYS
    if unknown:
        raise SnapshotConfigError(
            f"Unknown keys in snapshot config: {sorted(unknown)}"
        )

    enabled: bool = bool(raw.get("enabled", True))

    watch_raw = raw.get("watch", [])
    if not isinstance(watch_raw, list):
        raise SnapshotConfigError(
            f"'snapshot.watch' must be a list, got {type(watch_raw).__name__}"
        )
    watch: List[str] = []
    for item in watch_raw:
        if not isinstance(item, str):
            raise SnapshotConfigError(
                f"Each entry in 'snapshot.watch' must be a string, got {type(item).__name__}"
            )
        watch.append(item)

    return {"enabled": enabled, "watch": watch}
