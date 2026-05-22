"""Branch watcher: detects branch changes and triggers hook re-evaluation."""

import os
from pathlib import Path
from typing import Optional

from hookrunner.git import GitError, get_current_branch, is_git_repo
from hookrunner.logger import get_logger

logger = get_logger(__name__)

HEAD_FILE = "HEAD"
_BRANCH_CACHE: dict[str, str] = {}


class WatcherError(Exception):
    """Raised when the watcher encounters an unrecoverable problem."""


def _head_path(repo_root: str) -> Path:
    return Path(repo_root) / ".git" / HEAD_FILE


def _read_head(repo_root: str) -> str:
    """Return the raw contents of .git/HEAD."""
    path = _head_path(repo_root)
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise WatcherError(f"Cannot read {path}: {exc}") from exc


def get_cached_branch(repo_root: str) -> Optional[str]:
    """Return the last recorded branch for *repo_root*, or None."""
    return _BRANCH_CACHE.get(repo_root)


def update_branch_cache(repo_root: str, branch: str) -> None:
    """Persist *branch* as the current branch for *repo_root*."""
    _BRANCH_CACHE[repo_root] = branch


def clear_branch_cache(repo_root: Optional[str] = None) -> None:
    """Clear the in-process branch cache (all repos or a specific one)."""
    if repo_root is None:
        _BRANCH_CACHE.clear()
    else:
        _BRANCH_CACHE.pop(repo_root, None)


def detect_branch_change(repo_root: str) -> tuple[Optional[str], str, bool]:
    """Check whether the active branch has changed since the last call.

    Returns
    -------
    (previous_branch, current_branch, changed)
        *previous_branch* is ``None`` when no cached value exists.
        *changed* is ``True`` when the branch differs from the cache.
    """
    if not is_git_repo(repo_root):
        raise WatcherError(f"{repo_root!r} is not a git repository")

    try:
        current = get_current_branch(repo_root)
    except GitError as exc:
        raise WatcherError(str(exc)) from exc

    previous = get_cached_branch(repo_root)
    changed = previous != current

    if changed:
        logger.debug(
            "Branch changed in %s: %s -> %s",
            repo_root,
            previous or "<none>",
            current,
        )
        update_branch_cache(repo_root, current)

    return previous, current, changed
