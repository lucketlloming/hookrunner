"""Tests for hookrunner.cache."""

import time
import pytest
from pathlib import Path

from hookrunner.cache import (
    CacheError,
    set_value,
    get_value,
    invalidate,
    clear_all,
    _cache_dir,
)


@pytest.fixture()
def fake_repo(tmp_path: Path) -> Path:
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    return tmp_path


def test_set_and_get_value(fake_repo):
    set_value(str(fake_repo), "my-key", {"status": "ok"})
    result = get_value(str(fake_repo), "my-key")
    assert result == {"status": "ok"}


def test_get_missing_key_returns_none(fake_repo):
    assert get_value(str(fake_repo), "nonexistent") is None


def test_expired_entry_returns_none(fake_repo):
    set_value(str(fake_repo), "short-lived", "data", ttl=-1)
    assert get_value(str(fake_repo), "short-lived") is None


def test_expired_entry_file_is_removed(fake_repo):
    set_value(str(fake_repo), "short-lived", "data", ttl=-1)
    get_value(str(fake_repo), "short-lived")  # triggers removal
    cache_file = _cache_dir(str(fake_repo)) / "short-lived.json"
    assert not cache_file.exists()


def test_invalidate_existing_key(fake_repo):
    set_value(str(fake_repo), "to-delete", 42)
    removed = invalidate(str(fake_repo), "to-delete")
    assert removed is True
    assert get_value(str(fake_repo), "to-delete") is None


def test_invalidate_missing_key_returns_false(fake_repo):
    assert invalidate(str(fake_repo), "ghost") is False


def test_clear_all_removes_entries(fake_repo):
    set_value(str(fake_repo), "a", 1)
    set_value(str(fake_repo), "b", 2)
    set_value(str(fake_repo), "c", 3)
    count = clear_all(str(fake_repo))
    assert count == 3
    assert get_value(str(fake_repo), "a") is None


def test_clear_all_no_cache_dir(fake_repo):
    assert clear_all(str(fake_repo)) == 0


def test_key_with_slashes(fake_repo):
    set_value(str(fake_repo), "feature/my-branch", "branch-data")
    assert get_value(str(fake_repo), "feature/my-branch") == "branch-data"


def test_set_value_stores_various_types(fake_repo):
    for val in [None, 0, False, [1, 2, 3], {"nested": True}]:
        set_value(str(fake_repo), "typed", val)
        assert get_value(str(fake_repo), "typed") == val
