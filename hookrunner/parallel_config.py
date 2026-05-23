"""Parse parallel-execution settings from a hookrunner config dict."""

from typing import Any, Dict, Optional


class ParallelConfigError(Exception):
    """Raised when the parallel config block is malformed."""


_DEFAULT_MAX_WORKERS = 4
_MAX_WORKERS_LIMIT = 32


def parse_parallel_config(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Extract and validate the ``parallel`` block from *config*.

    Returns a normalised dict with keys:
      - ``enabled`` (bool)
      - ``max_workers`` (int)

    Returns ``None`` when no ``parallel`` key is present or when the block
    explicitly sets ``enabled: false``.

    Raises:
        ParallelConfigError: On type or value violations.
    """
    raw = config.get("parallel")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise ParallelConfigError(
            f"'parallel' must be a mapping, got {type(raw).__name__}"
        )

    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ParallelConfigError(
            f"'parallel.enabled' must be a boolean, got {type(enabled).__name__}"
        )
    if not enabled:
        return None

    max_workers = raw.get("max_workers", _DEFAULT_MAX_WORKERS)
    if not isinstance(max_workers, int) or isinstance(max_workers, bool):
        raise ParallelConfigError(
            f"'parallel.max_workers' must be an integer, got {type(max_workers).__name__}"
        )
    if max_workers < 1:
        raise ParallelConfigError(
            f"'parallel.max_workers' must be >= 1, got {max_workers}"
        )
    if max_workers > _MAX_WORKERS_LIMIT:
        raise ParallelConfigError(
            f"'parallel.max_workers' must be <= {_MAX_WORKERS_LIMIT}, got {max_workers}"
        )

    return {"enabled": True, "max_workers": max_workers}
