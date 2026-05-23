"""Tests for hookrunner.snapshot."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from hookrunner.snapshot import (
    SnapshotError,
    clear_snapshot,
    diff_snapshot,
    load_snapshot,
    take_snapshot,
)


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


def _write(path: Path, content: str = "hello") -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# take_snapshot / load_snapshot
# ---------------------------------------------------------------------------

def test_take_snapshot_returns_digests(fake_repo: Path, tmp_path: Path) -> None:
    f = _write(tmp_path / "a.py")
    result = take_snapshot(str(fake_repo), [str(f)])
    assert str(f) in result
    assert result[str(f)] is not None


def test_take_snapshot_persists(fake_repo: Path, tmp_path: Path) -> None:
    f = _write(tmp_path / "b.py")
    take_snapshot(str(fake_repo), [str(f)])
    loaded = load_snapshot(str(fake_repo))
    assert str(f) in loaded


def test_load_snapshot_missing_returns_empty(fake_repo: Path) -> None:
    assert load_snapshot(str(fake_repo)) == {}


def test_load_snapshot_corrupt_raises(fake_repo: Path) -> None:
    snap = fake_repo / ".git" / ".hookrunner_snapshot.json"
    snap.write_text("{bad json")
    with pytest.raises(SnapshotError):
        load_snapshot(str(fake_repo))


def test_unreadable_file_digest_is_none(fake_repo: Path) -> None:
    result = take_snapshot(str(fake_repo), ["/nonexistent/file.py"])
    assert result["/nonexistent/file.py"] is None


# ---------------------------------------------------------------------------
# diff_snapshot
# ---------------------------------------------------------------------------

def test_diff_added() -> None:
    changes = diff_snapshot({}, {"x.py": "abc"})
    assert changes == {"x.py": "added"}


def test_diff_removed() -> None:
    changes = diff_snapshot({"x.py": "abc"}, {})
    assert changes == {"x.py": "removed"}


def test_diff_modified() -> None:
    changes = diff_snapshot({"x.py": "abc"}, {"x.py": "xyz"})
    assert changes == {"x.py": "modified"}


def test_diff_unchanged_not_reported() -> None:
    changes = diff_snapshot({"x.py": "abc"}, {"x.py": "abc"})
    assert changes == {}


# ---------------------------------------------------------------------------
# clear_snapshot
# ---------------------------------------------------------------------------

def test_clear_snapshot_returns_true(fake_repo: Path, tmp_path: Path) -> None:
    f = _write(tmp_path / "c.py")
    take_snapshot(str(fake_repo), [str(f)])
    assert clear_snapshot(str(fake_repo)) is True


def test_clear_snapshot_absent_returns_false(fake_repo: Path) -> None:
    assert clear_snapshot(str(fake_repo)) is False
