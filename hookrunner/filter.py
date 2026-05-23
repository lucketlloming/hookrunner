"""Hook filtering logic based on file patterns and branch conditions."""

import fnmatch
import os
from typing import List, Optional

from hookrunner.logger import get_logger

logger = get_logger(__name__)


class FilterError(Exception):
    """Raised when hook filtering encounters an error."""


def _get_staged_files(repo_path: str) -> List[str]:
    """Return list of staged file paths relative to repo root."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True,
        )
        return [line for line in result.stdout.splitlines() if line]
    except subprocess.CalledProcessError as exc:
        raise FilterError(f"Failed to list staged files: {exc.stderr.strip()}") from exc


def matches_patterns(filepath: str, patterns: List[str]) -> bool:
    """Return True if *filepath* matches any of the given glob *patterns*."""
    for pattern in patterns:
        if fnmatch.fnmatch(filepath, pattern) or fnmatch.fnmatch(
            os.path.basename(filepath), pattern
        ):
            return True
    return False


def filter_hooks_by_files(
    hooks: List[dict],
    repo_path: str,
    staged_files: Optional[List[str]] = None,
) -> List[dict]:
    """Filter *hooks* to only those whose ``files`` pattern matches staged files.

    Hooks without a ``files`` key are always included.
    """
    if staged_files is None:
        staged_files = _get_staged_files(repo_path)

    filtered: List[dict] = []
    for hook in hooks:
        patterns = hook.get("files")
        if not patterns:
            filtered.append(hook)
            continue
        if isinstance(patterns, str):
            patterns = [patterns]
        matched = any(matches_patterns(f, patterns) for f in staged_files)
        if matched:
            logger.debug("Hook '%s' matched file patterns %s", hook.get("id", "?"), patterns)
            filtered.append(hook)
        else:
            logger.debug("Hook '%s' skipped — no staged files match %s", hook.get("id", "?"), patterns)
    return filtered
