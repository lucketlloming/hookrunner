"""Environment variable injection for hook execution."""

from __future__ import annotations

import os
from typing import Dict, Optional


class EnvError(Exception):
    """Raised when environment configuration is invalid."""


def _safe_str(value: object) -> str:
    """Convert a value to a string suitable for an env var."""
    if isinstance(value, bool):
        return "1" if value else "0"
    return str(value)


def build_hook_env(
    event: str,
    branch: str,
    repo_root: str,
    extra: Optional[Dict[str, object]] = None,
) -> Dict[str, str]:
    """Return a copy of the current environment augmented with hook metadata.

    The following variables are always injected:
      HOOKRUNNER=1
      HOOKRUNNER_EVENT   – the git hook event name (e.g. "pre-commit")
      HOOKRUNNER_BRANCH  – the current branch name
      HOOKRUNNER_ROOT    – absolute path to the repository root

    Any key/value pairs in *extra* are merged in last, allowing per-hook
    overrides.  Keys that are not valid POSIX identifiers are silently
    skipped to avoid breaking subprocess calls.
    """
    if not event:
        raise EnvError("event must be a non-empty string")
    if not branch:
        raise EnvError("branch must be a non-empty string")
    if not repo_root:
        raise EnvError("repo_root must be a non-empty string")

    env = os.environ.copy()
    env["HOOKRUNNER"] = "1"
    env["HOOKRUNNER_EVENT"] = event
    env["HOOKRUNNER_BRANCH"] = branch
    env["HOOKRUNNER_ROOT"] = os.path.abspath(repo_root)

    if extra:
        for key, value in extra.items():
            if not isinstance(key, str) or not key.replace("_", "").isalnum():
                continue
            env[key] = _safe_str(value)

    return env


def merge_hook_env(
    base: Dict[str, str],
    hook_env: Optional[Dict[str, object]],
) -> Dict[str, str]:
    """Merge per-hook *env* block (from config) into *base* env dict.

    Returns a new dict; *base* is not mutated.
    """
    if not hook_env:
        return base.copy()
    result = base.copy()
    for key, value in hook_env.items():
        if not isinstance(key, str) or not key.replace("_", "").isalnum():
            raise EnvError(f"Invalid environment variable name: {key!r}")
        result[key] = _safe_str(value)
    return result
