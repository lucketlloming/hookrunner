"""Tests for hookrunner.lockfile."""

import os
import pytest
from pathlib import Path

from hookrunner.lockfile import (
    LockfileError,
    acquire_lock,
    release_lock,
    is_locked,
    _lock_path,
)


@pytest.fixture()
def fake_repo(tmp_path):
    """Return a temporary directory that acts as a git repo root."""
    return str(tmp_path)


# ---------------------------------------------------------------------------
# _lock_path
# ---------------------------------------------------------------------------

def test_lock_path_structure(fake_repo):
    p = _lock_path(fake_repo, "pre-commit")
    assert p.name == "pre-commit.lock"
    assert ".hookrunner" in str(p)


def test_lock_path_sanitises_slashes(fake_repo):
    p = _lock_path(fake_repo, "pre/commit")
    assert "/" not in p.name


# ---------------------------------------------------------------------------
# acquire_lock / release_lock
# ---------------------------------------------------------------------------

def test_acquire_creates_lockfile(fake_repo):
    lock = acquire_lock(fake_repo, "pre-commit")
    assert lock.exists()
    release_lock(lock)


def test_lockfile_contains_pid(fake_repo):
    lock = acquire_lock(fake_repo, "pre-commit")
    assert lock.read_text().strip() == str(os.getpid())
    release_lock(lock)


def test_release_removes_lockfile(fake_repo):
    lock = acquire_lock(fake_repo, "pre-commit")
    release_lock(lock)
    assert not lock.exists()


def test_release_missing_lock_is_noop(fake_repo):
    lock = _lock_path(fake_repo, "pre-commit")
    # Should not raise even though file doesn't exist
    release_lock(lock)


def test_acquire_times_out_when_locked(fake_repo):
    lock = acquire_lock(fake_repo, "pre-commit")
    try:
        with pytest.raises(LockfileError, match="Could not acquire lock"):
            acquire_lock(fake_repo, "pre-commit", timeout=0)
    finally:
        release_lock(lock)


def test_acquire_different_events_independent(fake_repo):
    lock1 = acquire_lock(fake_repo, "pre-commit")
    lock2 = acquire_lock(fake_repo, "pre-push")
    assert lock1 != lock2
    release_lock(lock1)
    release_lock(lock2)


# ---------------------------------------------------------------------------
# is_locked
# ---------------------------------------------------------------------------

def test_is_locked_false_initially(fake_repo):
    assert not is_locked(fake_repo, "pre-commit")


def test_is_locked_true_after_acquire(fake_repo):
    lock = acquire_lock(fake_repo, "pre-commit")
    assert is_locked(fake_repo, "pre-commit")
    release_lock(lock)


def test_is_locked_false_after_release(fake_repo):
    lock = acquire_lock(fake_repo, "pre-commit")
    release_lock(lock)
    assert not is_locked(fake_repo, "pre-commit")
