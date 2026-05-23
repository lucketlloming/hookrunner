"""Snapshot module: capture and compare file-state digests for change detection."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Dict, Optional


class SnapshotError(Exception):
    """Raised when snapshot operations fail."""


_SNAPSHOT_FILENAME = ".hookrunner_snapshot.json"


def _snapshot_path(repo: str) -> Path:
    return Path(repo) / ".git" / _SNAPSHOT_FILENAME


def _file_digest(path: str) -> Optional[str]:
    """Return SHA-256 hex digest of *path*, or None if unreadable."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def take_snapshot(repo: str, files: list[str]) -> Dict[str, Optional[str]]:
    """Compute digests for *files* and persist them under *repo*."""
    digests: Dict[str, Optional[str]] = {f: _file_digest(f) for f in files}
    dest = _snapshot_path(repo)
    try:
        dest.write_text(json.dumps(digests, indent=2))
    except OSError as exc:
        raise SnapshotError(f"Cannot write snapshot to {dest}: {exc}") from exc
    return digests


def load_snapshot(repo: str) -> Dict[str, Optional[str]]:
    """Load a previously saved snapshot.  Returns empty dict if none exists."""
    dest = _snapshot_path(repo)
    if not dest.exists():
        return {}
    try:
        return json.loads(dest.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SnapshotError(f"Cannot read snapshot from {dest}: {exc}") from exc


def diff_snapshot(
    old: Dict[str, Optional[str]], new: Dict[str, Optional[str]]
) -> Dict[str, str]:
    """Return a mapping of filepath -> change-type ('added'|'modified'|'removed')."""
    changes: Dict[str, str] = {}
    all_keys = set(old) | set(new)
    for key in all_keys:
        if key not in old:
            changes[key] = "added"
        elif key not in new or new[key] is None:
            changes[key] = "removed"
        elif old[key] != new[key]:
            changes[key] = "modified"
    return changes


def clear_snapshot(repo: str) -> bool:
    """Delete the snapshot file.  Returns True if deleted, False if absent."""
    dest = _snapshot_path(repo)
    try:
        dest.unlink()
        return True
    except FileNotFoundError:
        return False
    except OSError as exc:
        raise SnapshotError(f"Cannot remove snapshot at {dest}: {exc}") from exc
