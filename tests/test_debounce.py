"""Tests for hookrunner.debounce."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from hookrunner import debounce as db
from hookrunner.cache import _cache_dir


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    return repo


@pytest.fixture(autouse=True)
def _clean_cache(fake_repo: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Redirect cache writes to tmp dir so tests are isolated."""
    cache_root = fake_repo / ".hookrunner_cache"
    monkeypatch.setattr("hookrunner.cache._CACHE_ROOT", cache_root)


# ------------------------------------------------------------------ helpers --

REPO = "/tmp/testrepo"
EVENT = "pre-commit"
HOOK = "lint"


# ------------------------------------------------------------------- tests ---

def test_not_debounced_initially(fake_repo: Path) -> None:
    assert db.is_debounced(str(fake_repo), EVENT, HOOK, window=5.0) is False


def test_debounced_immediately_after_record(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    assert db.is_debounced(str(fake_repo), EVENT, HOOK, window=5.0, _now=t + 1) is True


def test_not_debounced_after_window_expires(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    assert db.is_debounced(str(fake_repo), EVENT, HOOK, window=2.0, _now=t + 3) is False


def test_zero_window_never_debounces(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    assert db.is_debounced(str(fake_repo), EVENT, HOOK, window=0, _now=t) is False


def test_negative_window_never_debounces(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    assert db.is_debounced(str(fake_repo), EVENT, HOOK, window=-1, _now=t) is False


def test_clear_debounce_allows_immediate_rerun(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    db.clear_debounce(str(fake_repo), EVENT, HOOK)
    assert db.is_debounced(str(fake_repo), EVENT, HOOK, window=5.0, _now=t + 1) is False


def test_different_hooks_are_independent(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    assert db.is_debounced(str(fake_repo), EVENT, "format", window=5.0, _now=t + 1) is False


def test_different_events_are_independent(fake_repo: Path) -> None:
    t = 1_000.0
    db.record_run(str(fake_repo), EVENT, HOOK, _now=t)
    assert db.is_debounced(str(fake_repo), "post-commit", HOOK, window=5.0, _now=t + 1) is False
