"""Tests for hookrunner.parallel and hookrunner.parallel_config."""

import os
import stat
import textwrap
from pathlib import Path

import pytest

from hookrunner.parallel import ParallelError, run_hooks_parallel
from hookrunner.parallel_config import ParallelConfigError, parse_parallel_config


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def script_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_script(directory: Path, name: str, exit_code: int = 0) -> str:
    script = directory / name
    script.write_text(
        textwrap.dedent(f"""\
            #!/bin/sh
            exit {exit_code}
        """)
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


# ---------------------------------------------------------------------------
# parallel_config tests
# ---------------------------------------------------------------------------

def test_no_parallel_key_returns_none():
    assert parse_parallel_config({}) is None


def test_parallel_disabled_returns_none():
    assert parse_parallel_config({"parallel": {"enabled": False}}) is None


def test_parallel_defaults():
    result = parse_parallel_config({"parallel": {}})
    assert result == {"enabled": True, "max_workers": 4}


def test_parallel_custom_workers():
    result = parse_parallel_config({"parallel": {"max_workers": 8}})
    assert result["max_workers"] == 8


def test_parallel_invalid_type_raises():
    with pytest.raises(ParallelConfigError, match="mapping"):
        parse_parallel_config({"parallel": "yes"})


def test_parallel_workers_too_low_raises():
    with pytest.raises(ParallelConfigError, match=">= 1"):
        parse_parallel_config({"parallel": {"max_workers": 0}})


def test_parallel_workers_too_high_raises():
    with pytest.raises(ParallelConfigError, match="<= 32"):
        parse_parallel_config({"parallel": {"max_workers": 99}})


def test_parallel_enabled_non_bool_raises():
    with pytest.raises(ParallelConfigError, match="boolean"):
        parse_parallel_config({"parallel": {"enabled": "yes"}})


# ---------------------------------------------------------------------------
# parallel execution tests
# ---------------------------------------------------------------------------

def test_empty_hooks_returns_empty(tmp_path):
    result = run_hooks_parallel([], [], str(tmp_path))
    assert result == []


def test_invalid_max_workers_raises(tmp_path):
    with pytest.raises(ParallelError, match="max_workers"):
        run_hooks_parallel(["hook"], [], str(tmp_path), max_workers=0)


def test_all_passing_hooks(script_dir, tmp_path):
    hooks = [_make_script(script_dir, f"hook{i}.sh", 0) for i in range(3)]
    timings = run_hooks_parallel(hooks, [], str(tmp_path), max_workers=2)
    assert len(timings) == 3
    assert all(t.passed for t in timings)
    assert [t.name for t in timings] == hooks


def test_failing_hook_recorded(script_dir, tmp_path):
    hooks = [
        _make_script(script_dir, "ok.sh", 0),
        _make_script(script_dir, "fail.sh", 1),
    ]
    timings = run_hooks_parallel(hooks, [], str(tmp_path))
    by_name = {t.name: t for t in timings}
    assert by_name[hooks[0]].passed is True
    assert by_name[hooks[1]].passed is False


def test_results_preserve_order(script_dir, tmp_path):
    hooks = [_make_script(script_dir, f"h{i}.sh", 0) for i in range(5)]
    timings = run_hooks_parallel(hooks, [], str(tmp_path), max_workers=5)
    assert [t.name for t in timings] == hooks
