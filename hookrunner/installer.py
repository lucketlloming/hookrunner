"""Manages installation and removal of git hooks into .git/hooks/."""

import os
import stat
from pathlib import Path

HOOK_TEMPLATE = """#!/bin/sh
# Managed by hookrunner — do not edit manually
# hookrunner:managed
exec hookrunner run {hook_name} "$@"
"""

MANAGED_MARKER = "# hookrunner:managed"


class InstallerError(Exception):
    """Raised when hook installation or removal fails."""


def _hooks_dir(repo_root: str) -> Path:
    return Path(repo_root) / ".git" / "hooks"


def install_hook(hook_name: str, repo_root: str = ".") -> Path:
    """Install a hookrunner-managed git hook script.

    Returns the path to the installed hook file.
    Raises InstallerError if the hooks directory does not exist or if a
    non-managed hook with the same name already exists.
    """
    hooks_dir = _hooks_dir(repo_root)
    if not hooks_dir.is_dir():
        raise InstallerError(
            f"Git hooks directory not found: {hooks_dir}. "
            "Is this a valid git repository?"
        )

    hook_path = hooks_dir / hook_name

    if hook_path.exists():
        content = hook_path.read_text()
        if MANAGED_MARKER not in content:
            raise InstallerError(
                f"Hook '{hook_name}' already exists and is not managed by "
                "hookrunner. Remove it manually before installing."
            )

    hook_path.write_text(HOOK_TEMPLATE.format(hook_name=hook_name))
    hook_path.chmod(
        hook_path.stat().st_mode
        | stat.S_IXUSR
        | stat.S_IXGRP
        | stat.S_IXOTH
    )
    return hook_path


def uninstall_hook(hook_name: str, repo_root: str = ".") -> bool:
    """Remove a hookrunner-managed git hook.

    Returns True if removed, False if the hook did not exist.
    Raises InstallerError if the hook exists but is not managed by hookrunner.
    """
    hook_path = _hooks_dir(repo_root) / hook_name

    if not hook_path.exists():
        return False

    content = hook_path.read_text()
    if MANAGED_MARKER not in content:
        raise InstallerError(
            f"Hook '{hook_name}' is not managed by hookrunner. "
            "Refusing to remove it."
        )

    hook_path.unlink()
    return True


def is_installed(hook_name: str, repo_root: str = ".") -> bool:
    """Return True if the named hook is installed and managed by hookrunner."""
    hook_path = _hooks_dir(repo_root) / hook_name
    if not hook_path.exists():
        return False
    return MANAGED_MARKER in hook_path.read_text()
