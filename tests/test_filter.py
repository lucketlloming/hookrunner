"""Tests for hookrunner.filter module."""

import pytest

from hookrunner.filter import (
    FilterError,
    filter_hooks_by_files,
    matches_patterns,
    _get_staged_files,
)


# ---------------------------------------------------------------------------
# matches_patterns
# ---------------------------------------------------------------------------

def test_matches_patterns_glob():
    assert matches_patterns("src/main.py", ["*.py"])


def test_matches_patterns_full_path():
    assert matches_patterns("src/main.py", ["src/*.py"])


def test_matches_patterns_no_match():
    assert not matches_patterns("README.md", ["*.py"])


def test_matches_patterns_multiple_patterns():
    assert matches_patterns("app.js", ["*.py", "*.js"])


def test_matches_patterns_basename_only():
    """Pattern without path separator should match on basename."""
    assert matches_patterns("deep/nested/file.py", ["file.py"])


# ---------------------------------------------------------------------------
# filter_hooks_by_files
# ---------------------------------------------------------------------------

HOOK_PY = {"id": "lint-py", "run": "flake8", "files": "*.py"}
HOOK_JS = {"id": "lint-js", "run": "eslint", "files": ["*.js", "*.ts"]}
HOOK_ALL = {"id": "run-tests", "run": "pytest"}


def test_hook_without_files_always_included(tmp_path):
    result = filter_hooks_by_files([HOOK_ALL], str(tmp_path), staged_files=[])
    assert result == [HOOK_ALL]


def test_hook_included_when_file_matches(tmp_path):
    result = filter_hooks_by_files([HOOK_PY], str(tmp_path), staged_files=["src/app.py"])
    assert HOOK_PY in result


def test_hook_excluded_when_no_file_matches(tmp_path):
    result = filter_hooks_by_files([HOOK_PY], str(tmp_path), staged_files=["README.md"])
    assert result == []


def test_multiple_hooks_filtered_correctly(tmp_path):
    staged = ["app.py", "README.md"]
    result = filter_hooks_by_files([HOOK_PY, HOOK_JS, HOOK_ALL], str(tmp_path), staged_files=staged)
    assert HOOK_PY in result
    assert HOOK_JS not in result
    assert HOOK_ALL in result


def test_hook_with_list_patterns(tmp_path):
    staged = ["index.ts"]
    result = filter_hooks_by_files([HOOK_JS], str(tmp_path), staged_files=staged)
    assert HOOK_JS in result


def test_empty_hooks_returns_empty(tmp_path):
    result = filter_hooks_by_files([], str(tmp_path), staged_files=["main.py"])
    assert result == []


# ---------------------------------------------------------------------------
# _get_staged_files error path
# ---------------------------------------------------------------------------

def test_get_staged_files_raises_on_non_repo(tmp_path):
    """Running outside a git repo should raise FilterError."""
    with pytest.raises(FilterError):
        _get_staged_files(str(tmp_path))
