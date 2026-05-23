"""Conditional hook execution based on environment and branch patterns."""

import re
from fnmatch import fnmatch
from typing import Any, Dict, List, Optional


class ConditionError(Exception):
    """Raised when a hook condition cannot be evaluated."""


def _match_branch(pattern: str, branch: str) -> bool:
    """Return True if *branch* matches *pattern* (glob or regex)."""
    if pattern.startswith("regex:"):
        raw = pattern[len("regex:"):]
        try:
            return bool(re.fullmatch(raw, branch))
        except re.error as exc:
            raise ConditionError(f"Invalid regex pattern {raw!r}: {exc}") from exc
    return fnmatch(branch, pattern)


def _check_branch_condition(
    condition: Dict[str, Any], branch: Optional[str]
) -> bool:
    """Evaluate a branch-based condition block."""
    only = condition.get("only")
    exclude = condition.get("exclude")

    if only is not None:
        patterns: List[str] = [only] if isinstance(only, str) else list(only)
        if branch is None:
            return False
        if not any(_match_branch(p, branch) for p in patterns):
            return False

    if exclude is not None:
        patterns = [exclude] if isinstance(exclude, str) else list(exclude)
        if branch is not None and any(_match_branch(p, branch) for p in patterns):
            return False

    return True


def _check_env_condition(condition: Dict[str, Any]) -> bool:
    """Evaluate an environment-variable condition block."""
    import os

    env_block = condition.get("env")
    if env_block is None:
        return True

    if isinstance(env_block, str):
        return os.environ.get(env_block) not in (None, "", "0", "false", "False")

    if isinstance(env_block, dict):
        for key, expected in env_block.items():
            actual = os.environ.get(key)
            if str(expected) != str(actual):
                return False
        return True

    raise ConditionError(f"Unsupported 'env' condition type: {type(env_block).__name__}")


def evaluate_conditions(
    hook_cfg: Dict[str, Any], branch: Optional[str] = None
) -> bool:
    """Return True when all conditions defined in *hook_cfg* are satisfied.

    Supported keys inside ``conditions``:
      - ``only``    – glob / ``regex:`` pattern or list thereof
      - ``exclude`` – glob / ``regex:`` pattern or list thereof
      - ``env``     – env-var name (truthy check) or ``{KEY: value}`` mapping
    """
    condition_block = hook_cfg.get("conditions")
    if not condition_block:
        return True

    if not isinstance(condition_block, dict):
        raise ConditionError("'conditions' must be a mapping")

    if not _check_branch_condition(condition_block, branch):
        return False

    if not _check_env_condition(condition_block):
        return False

    return True
