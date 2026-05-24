"""Parse rollback configuration from a hook's YAML definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class RollbackConfigError(Exception):
    """Raised when the rollback config block is malformed."""


@dataclass
class RollbackConfig:
    enabled: bool = False
    save_on: list[str] = field(default_factory=lambda: ["success"])
    clear_on: list[str] = field(default_factory=lambda: ["success"])


def parse_rollback_config(hook_cfg: dict[str, Any]) -> RollbackConfig | None:
    """Return a :class:`RollbackConfig` from *hook_cfg*, or ``None``.

    The expected YAML shape is::

        rollback:
          enabled: true
          save_on: [success, failure]
          clear_on: [success]
    """
    raw = hook_cfg.get("rollback")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise RollbackConfigError("'rollback' must be a mapping")
    if not raw:
        return None

    enabled = raw.get("enabled", False)
    if not isinstance(enabled, bool):
        raise RollbackConfigError("'rollback.enabled' must be a boolean")

    def _parse_list(key: str) -> list[str]:
        val = raw.get(key)
        if val is None:
            return []
        if isinstance(val, str):
            return [val]
        if isinstance(val, list) and all(isinstance(v, str) for v in val):
            return val
        raise RollbackConfigError(f"'rollback.{key}' must be a string or list of strings")

    valid_events = {"success", "failure"}
    save_on = _parse_list("save_on") or ["success"]
    clear_on = _parse_list("clear_on") or ["success"]

    for ev in save_on + clear_on:
        if ev not in valid_events:
            raise RollbackConfigError(
                f"Unknown rollback event '{ev}'; expected one of {sorted(valid_events)}"
            )

    return RollbackConfig(enabled=enabled, save_on=save_on, clear_on=clear_on)
