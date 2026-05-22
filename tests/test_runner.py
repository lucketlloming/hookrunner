"""Tests for hookrunner.runner."""

from __future__ import annotations

import stat
from pathlib import Path

import pytest
import yaml

from hookrunner.executor import HookExecutionError
from hookrunner.runner import RunnerError, run_hooks_for_event


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    """Minimal fake git repo with HEAD pointing to 'main'."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    (git_dir / "HEAD").write_text("ref: refs/heads/main\n")
    return tmp_path


@pytest.fixture()
def config_path(repo: Path) -> Path:
    return repo / ".hookrunner.yml"


def _write_config(path: Path, data: dict) -> None:
    path.write_text(yaml.safe_dump(data))


def _make_script(repo: Path, name: str, exit_code: int = 0) -> Path:
    script = repo / name
    script.write_text(f"#!/bin/sh\nexit {exit_code}\n")
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return script


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_no_hooks_returns_zero(repo, config_path):
    _write_config(config_path, {"hooks": {}})
    count = run_hooks_for_event("pre-commit", repo, config_path)
    assert count == 0


def test_matching_hook_executed(repo, config_path):
    script = _make_script(repo, "check.sh")
    _write_config(
        config_path,
        {"hooks": {"pre-commit": {"branches": ["main"], "run": [str(script)]}}},
    )
    count = run_hooks_for_event("pre-commit", repo, config_path)
    assert count == 1


def test_hook_failure_raises(repo, config_path):
    script = _make_script(repo, "bad.sh", exit_code=1)
    _write_config(
        config_path,
        {"hooks": {"pre-commit": {"branches": ["main"], "run": [str(script)]}}},
    )
    with pytest.raises(HookExecutionError):
        run_hooks_for_event("pre-commit", repo, config_path)


def test_dry_run_does_not_execute(repo, config_path):
    script = _make_script(repo, "bad.sh", exit_code=1)
    _write_config(
        config_path,
        {"hooks": {"pre-commit": {"branches": ["main"], "run": [str(script)]}}},
    )
    # Should NOT raise even though the script would fail
    count = run_hooks_for_event("pre-commit", repo, config_path, dry_run=True)
    assert count == 1


def test_missing_config_raises_runner_error(repo, config_path):
    with pytest.raises(RunnerError, match="Config file not found"):
        run_hooks_for_event("pre-commit", repo, config_path)


def test_branch_mismatch_skips_hooks(repo, config_path):
    script = _make_script(repo, "check.sh")
    _write_config(
        config_path,
        {"hooks": {"pre-commit": {"branches": ["develop"], "run": [str(script)]}}},
    )
    count = run_hooks_for_event("pre-commit", repo, config_path)
    assert count == 0
