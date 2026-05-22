"""Git utilities for hookrunner."""

import subprocess
from typing import Optional


class GitError(Exception):
    """Raised when a git command fails."""


def get_current_branch(cwd: Optional[str] = None) -> str:
    """Return the name of the currently checked-out git branch.

    Args:
        cwd: Directory in which to run the git command. Defaults to cwd.

    Returns:
        The branch name as a string.

    Raises:
        GitError: If the git command fails or the repo is in a detached HEAD state.
    """
    try:
        result = subprocess.run(
            ["git", "symbolic-ref", "--short", "HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
    except FileNotFoundError as exc:
        raise GitError("git executable not found") from exc

    if result.returncode != 0:
        stderr = result.stderr.strip()
        raise GitError(f"Could not determine current branch: {stderr}")

    return result.stdout.strip()


def is_git_repo(cwd: Optional[str] = None) -> bool:
    """Return True if the given directory is inside a git repository.

    Args:
        cwd: Directory to check. Defaults to current working directory.
    """
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"
