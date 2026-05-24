"""Rollback support: record hook execution checkpoints and restore on failure."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

ROLLBACK_DIR = ".hookrunner" + os.sep + "rollback"


class RollbackError(Exception):
    """Raised when a rollback operation fails."""


def _rollback_path(repo: str, event: str) -> Path:
    return Path(repo) / ROLLBACK_DIR / f"{event}.json"


def save_checkpoint(repo: str, event: str, state: dict[str, Any]) -> None:
    """Persist a checkpoint for *event* inside *repo*."""
    path = _rollback_path(repo, event)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError as exc:
        raise RollbackError(f"Cannot save checkpoint: {exc}") from exc


def load_checkpoint(repo: str, event: str) -> dict[str, Any] | None:
    """Return the saved checkpoint for *event*, or ``None`` if absent."""
    path = _rollback_path(repo, event)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RollbackError(f"Cannot load checkpoint: {exc}") from exc


def clear_checkpoint(repo: str, event: str) -> None:
    """Remove the checkpoint file for *event* if it exists."""
    path = _rollback_path(repo, event)
    try:
        path.unlink(missing_ok=True)
    except OSError as exc:
        raise RollbackError(f"Cannot clear checkpoint: {exc}") from exc


def list_checkpoints(repo: str) -> list[str]:
    """Return event names that have a saved checkpoint in *repo*."""
    base = Path(repo) / ROLLBACK_DIR
    if not base.is_dir():
        return []
    return [p.stem for p in sorted(base.glob("*.json"))]
