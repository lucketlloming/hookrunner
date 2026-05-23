"""High-level helpers for resolving concurrency settings from hook/global config."""

from __future__ import annotations

from typing import Optional

from hookrunner.concurrency import ConcurrencyError, parse_concurrency_limit


DEFAULT_GLOBAL_LIMIT: Optional[int] = None  # no limit by default


def get_global_concurrency(config: dict) -> Optional[int]:
    """Return the global concurrency limit from the top-level config, or None."""
    raw = config.get("concurrency")
    if raw is None:
        return DEFAULT_GLOBAL_LIMIT
    if not isinstance(raw, int) or isinstance(raw, bool):
        raise ConcurrencyError(
            f"global 'concurrency' must be an integer, got {type(raw).__name__!r}"
        )
    if raw < 1:
        raise ConcurrencyError(f"global 'concurrency' must be >= 1, got {raw}")
    return raw


def resolve_concurrency(hook_cfg: dict, global_cfg: dict) -> Optional[int]:
    """Return the effective concurrency limit for a hook.

    Hook-level setting takes precedence over the global setting.
    Returns *None* when no limit applies.
    """
    hook_limit = parse_concurrency_limit(hook_cfg)
    if hook_limit is not None:
        return hook_limit
    return get_global_concurrency(global_cfg)
