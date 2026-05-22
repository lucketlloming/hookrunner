"""Tests for hookrunner.config module."""

import os
import textwrap
import pytest

from hookrunner.config import load_config, get_hooks_for_branch, DEFAULT_CONFIG_FILE


@pytest.fixture()
def config_file(tmp_path):
    """Return a helper that writes a .hookrunner.yml in tmp_path."""
    def _write(content: str) -> str:
        path = tmp_path / DEFAULT_CONFIG_FILE
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return str(path)
    return _write


def test_load_config_basic(config_file):
    path = config_file("""
        version: 1
        hooks:
          pre-commit:
            - ruff check .
            - pytest -q
        branches: {}
    """)
    config = load_config(path)
    assert config["version"] == 1
    assert config["hooks"]["pre-commit"] == ["ruff check .", "pytest -q"]


def test_load_config_file_not_found(tmp_path):
    missing = str(tmp_path / "nonexistent.yml")
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_config(missing)


def test_load_config_invalid_yaml(config_file):
    path = config_file("hooks: [unclosed")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_config(path)


def test_load_config_not_a_mapping(config_file):
    path = config_file("- just\n- a\n- list\n")
    with pytest.raises(ValueError, match="must contain a YAML mapping"):
        load_config(path)


def test_load_config_invalid_hooks_type(config_file):
    path = config_file("hooks: not-a-dict\nbranches: {}\n")
    with pytest.raises(ValueError, match="'hooks' must be a mapping"):
        load_config(path)


def test_get_hooks_for_branch_global_fallback(config_file):
    path = config_file("""
        hooks:
          pre-push:
            - make test
        branches: {}
    """)
    config = load_config(path)
    cmds = get_hooks_for_branch(config, "feature/xyz", "pre-push")
    assert cmds == ["make test"]


def test_get_hooks_for_branch_override(config_file):
    path = config_file("""
        hooks:
          pre-commit:
            - ruff check .
        branches:
          main:
            pre-commit:
              - ruff check .
              - pytest --cov
    """)
    config = load_config(path)
    cmds = get_hooks_for_branch(config, "main", "pre-commit")
    assert cmds == ["ruff check .", "pytest --cov"]


def test_get_hooks_for_branch_missing_hook(config_file):
    path = config_file("hooks: {}\nbranches: {}\n")
    config = load_config(path)
    cmds = get_hooks_for_branch(config, "develop", "pre-commit")
    assert cmds == []
