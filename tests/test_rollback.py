"""Tests for hookrunner.rollback."""

import json
import pytest

from hookrunner.rollback import (
    RollbackError,
    clear_checkpoint,
    list_checkpoints,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture()
def fake_repo(tmp_path):
    return str(tmp_path)


def test_save_and_load_checkpoint(fake_repo):
    state = {"hook": "pre-commit", "exit_code": 0}
    save_checkpoint(fake_repo, "pre-commit", state)
    loaded = load_checkpoint(fake_repo, "pre-commit")
    assert loaded == state


def test_load_missing_returns_none(fake_repo):
    assert load_checkpoint(fake_repo, "pre-push") is None


def test_save_creates_parent_dirs(fake_repo):
    save_checkpoint(fake_repo, "commit-msg", {"ok": True})
    from pathlib import Path
    assert (Path(fake_repo) / ".hookrunner" / "rollback" / "commit-msg.json").exists()


def test_clear_removes_file(fake_repo):
    save_checkpoint(fake_repo, "pre-commit", {"x": 1})
    clear_checkpoint(fake_repo, "pre-commit")
    assert load_checkpoint(fake_repo, "pre-commit") is None


def test_clear_nonexistent_is_noop(fake_repo):
    # Should not raise
    clear_checkpoint(fake_repo, "nonexistent")


def test_list_checkpoints_empty(fake_repo):
    assert list_checkpoints(fake_repo) == []


def test_list_checkpoints_multiple(fake_repo):
    save_checkpoint(fake_repo, "pre-commit", {})
    save_checkpoint(fake_repo, "pre-push", {})
    names = list_checkpoints(fake_repo)
    assert sorted(names) == ["pre-commit", "pre-push"]


def test_load_corrupt_file_raises(fake_repo):
    from pathlib import Path
    path = Path(fake_repo) / ".hookrunner" / "rollback" / "bad.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("not json", encoding="utf-8")
    with pytest.raises(RollbackError, match="Cannot load checkpoint"):
        load_checkpoint(fake_repo, "bad")


def test_save_persists_correct_json(fake_repo):
    state = {"branch": "main", "hooks": ["lint", "test"]}
    save_checkpoint(fake_repo, "pre-commit", state)
    from pathlib import Path
    raw = (Path(fake_repo) / ".hookrunner" / "rollback" / "pre-commit.json").read_text()
    assert json.loads(raw) == state
