"""Tests for hookrunner.watcher."""

import pytest

import hookrunner.watcher as watcher_mod
from hookrunner.watcher import (
    WatcherError,
    clear_branch_cache,
    detect_branch_change,
    get_cached_branch,
    update_branch_cache,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_cache():
    """Ensure the branch cache is empty before every test."""
    clear_branch_cache()
    yield
    clear_branch_cache()


@pytest.fixture()
def fake_repo(tmp_path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    return str(tmp_path)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def test_cache_empty_initially(fake_repo):
    assert get_cached_branch(fake_repo) is None


def test_update_and_read_cache(fake_repo):
    update_branch_cache(fake_repo, "feature-x")
    assert get_cached_branch(fake_repo) == "feature-x"


def test_clear_specific_repo(fake_repo):
    update_branch_cache(fake_repo, "main")
    clear_branch_cache(fake_repo)
    assert get_cached_branch(fake_repo) is None


def test_clear_all_repos(fake_repo, tmp_path):
    repo2 = str(tmp_path / "other")
    update_branch_cache(fake_repo, "main")
    update_branch_cache(repo2, "dev")
    clear_branch_cache()
    assert get_cached_branch(fake_repo) is None
    assert get_cached_branch(repo2) is None


# ---------------------------------------------------------------------------
# detect_branch_change
# ---------------------------------------------------------------------------

def test_first_detection_not_changed(fake_repo, monkeypatch):
    monkeypatch.setattr(watcher_mod, "is_git_repo", lambda _: True)
    monkeypatch.setattr(watcher_mod, "get_current_branch", lambda _: "main")

    prev, current, changed = detect_branch_change(fake_repo)
    assert prev is None
    assert current == "main"
    assert changed is True  # None -> "main" counts as a change


def test_no_change_when_same_branch(fake_repo, monkeypatch):
    monkeypatch.setattr(watcher_mod, "is_git_repo", lambda _: True)
    monkeypatch.setattr(watcher_mod, "get_current_branch", lambda _: "main")

    detect_branch_change(fake_repo)  # prime the cache
    prev, current, changed = detect_branch_change(fake_repo)
    assert prev == "main"
    assert current == "main"
    assert changed is False


def test_change_detected(fake_repo, monkeypatch):
    monkeypatch.setattr(watcher_mod, "is_git_repo", lambda _: True)
    branches = iter(["main", "feature-y"])
    monkeypatch.setattr(watcher_mod, "get_current_branch", lambda _: next(branches))

    detect_branch_change(fake_repo)
    prev, current, changed = detect_branch_change(fake_repo)
    assert prev == "main"
    assert current == "feature-y"
    assert changed is True


def test_raises_watcher_error_not_a_repo(fake_repo, monkeypatch):
    monkeypatch.setattr(watcher_mod, "is_git_repo", lambda _: False)
    with pytest.raises(WatcherError, match="not a git repository"):
        detect_branch_change(fake_repo)


def test_raises_watcher_error_on_git_error(fake_repo, monkeypatch):
    from hookrunner.git import GitError
    monkeypatch.setattr(watcher_mod, "is_git_repo", lambda _: True)
    monkeypatch.setattr(watcher_mod, "get_current_branch", lambda _: (_ for _ in ()).throw(GitError("detached HEAD")))
    with pytest.raises(WatcherError, match="detached HEAD"):
        detect_branch_change(fake_repo)
