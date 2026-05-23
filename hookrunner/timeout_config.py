"""Parse per-hook and global timeout settings from hook config dicts."""

from typing import Any, Dict, Optional

from hookrunner.timeout import parse_timeout


class TimeoutConfigError(Exception):
    """Raised when timeout configuration is invalid."""


_GLOBAL_KEY = "timeout"
_HOOK_KEY = "timeout"


def get_global_timeout(config: Dict[str, Any]) -> Optional[int]:
    """Return the global default timeout from the top-level config dict.

    Returns None if not set.
    """
    raw = config.get(_GLOBAL_KEY)
    try:
        return parse_timeout(raw)
    except ValueError as exc:
        raise TimeoutConfigError(f"Global timeout error: {exc}") from exc


def get_hook_timeout(
    hook: Dict[str, Any],
    global_timeout: Optional[int] = None,
) -> Optional[int]:
    """Return the effective timeout for a single hook definition.

    Hook-level ``timeout`` overrides *global_timeout*.
    Returns None when no timeout applies.
    """
    raw = hook.get(_HOOK_KEY)
    if raw is None:
        return global_timeout
    try:
        return parse_timeout(raw)
    except ValueError as exc:
        name = hook.get("name", "<unnamed>")
        raise TimeoutConfigError(f"Hook '{name}' timeout error: {exc}") from exc


def resolve_timeouts(
    hooks: list,
    config: Dict[str, Any],
) -> list:
    """Attach resolved ``_timeout`` values to each hook dict (copy).

    Returns a new list of hook dicts with ``_timeout`` populated.
    """
    global_timeout = get_global_timeout(config)
    resolved = []
    for hook in hooks:
        hook_copy = dict(hook)
        hook_copy["_timeout"] = get_hook_timeout(hook_copy, global_timeout)
        resolved.append(hook_copy)
    return resolved
