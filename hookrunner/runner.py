"""High-level hook runner that ties together config, git, and executor."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from hookrunner.config import load_config, get_hooks_for_branch
from hookrunner.executor import HookExecutor, HookExecutionError
from hookrunner.git import get_current_branch, GitError
from hookrunner.logger import get_logger

log = get_logger(__name__)


class RunnerError(Exception):
    """Raised when the runner encounters a fatal problem."""


def run_hooks_for_event(
    hook_name: str,
    repo_path: Path,
    config_path: Path,
    args: Optional[List[str]] = None,
    *,
    dry_run: bool = False,
) -> int:
    """Run all hooks registered for *hook_name* on the current branch.

    Returns the number of hooks executed (0 if none matched).
    Raises RunnerError on configuration or git problems.
    Raises HookExecutionError if any hook exits with a non-zero status.
    """
    args = args or []

    try:
        branch = get_current_branch(repo_path)
    except GitError as exc:
        raise RunnerError(f"Cannot determine current branch: {exc}") from exc

    log.debug("Current branch: %s", branch)

    try:
        config = load_config(config_path)
    except FileNotFoundError as exc:
        raise RunnerError(f"Config file not found: {config_path}") from exc
    except Exception as exc:
        raise RunnerError(f"Failed to load config: {exc}") from exc

    hooks = get_hooks_for_branch(config, branch, hook_name)

    if not hooks:
        log.debug("No hooks configured for event '%s' on branch '%s'", hook_name, branch)
        return 0

    log.info(
        "Running %d hook(s) for event '%s' on branch '%s'",
        len(hooks),
        hook_name,
        branch,
    )

    executor = HookExecutor(repo_path=repo_path)

    for hook_cmd in hooks:
        if dry_run:
            log.info("[dry-run] would execute: %s %s", hook_cmd, " ".join(args))
            continue
        log.debug("Executing hook: %s", hook_cmd)
        executor.run_hook(hook_cmd, args)

    return len(hooks)
