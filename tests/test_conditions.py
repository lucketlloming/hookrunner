"""Tests for hookrunner.conditions."""

import os
import pytest

from hookrunner.conditions import (
    ConditionError,
    _match_branch,
    evaluate_conditions,
)


# ---------------------------------------------------------------------------
# _match_branch
# ---------------------------------------------------------------------------

def test_match_branch_glob_exact():
    assert _match_branch("main", "main") is True


def test_match_branch_glob_wildcard():
    assert _match_branch("feature/*", "feature/login") is True
    assert _match_branch("feature/*", "hotfix/x") is False


def test_match_branch_regex_match():
    assert _match_branch("regex:release-\\d+", "release-42") is True


def test_match_branch_regex_no_match():
    assert _match_branch("regex:release-\\d+", "release-abc") is False


def test_match_branch_invalid_regex():
    with pytest.raises(ConditionError, match="Invalid regex"):
        _match_branch("regex:[unclosed", "main")


# ---------------------------------------------------------------------------
# evaluate_conditions – no conditions
# ---------------------------------------------------------------------------

def test_no_conditions_always_true():
    assert evaluate_conditions({}) is True
    assert evaluate_conditions({"cmd": "echo hi"}) is True


# ---------------------------------------------------------------------------
# evaluate_conditions – branch only/exclude
# ---------------------------------------------------------------------------

def test_only_branch_matches():
    cfg = {"conditions": {"only": "main"}}
    assert evaluate_conditions(cfg, branch="main") is True


def test_only_branch_no_match():
    cfg = {"conditions": {"only": "main"}}
    assert evaluate_conditions(cfg, branch="develop") is False


def test_only_list_of_branches():
    cfg = {"conditions": {"only": ["main", "develop"]}}
    assert evaluate_conditions(cfg, branch="develop") is True
    assert evaluate_conditions(cfg, branch="feature/x") is False


def test_exclude_branch():
    cfg = {"conditions": {"exclude": "dependabot/*"}}
    assert evaluate_conditions(cfg, branch="dependabot/npm-1") is False
    assert evaluate_conditions(cfg, branch="main") is True


def test_only_without_branch_returns_false():
    cfg = {"conditions": {"only": "main"}}
    assert evaluate_conditions(cfg, branch=None) is False


# ---------------------------------------------------------------------------
# evaluate_conditions – env
# ---------------------------------------------------------------------------

def test_env_string_truthy(monkeypatch):
    monkeypatch.setenv("CI", "true")
    cfg = {"conditions": {"env": "CI"}}
    assert evaluate_conditions(cfg) is True


def test_env_string_falsy(monkeypatch):
    monkeypatch.delenv("CI", raising=False)
    cfg = {"conditions": {"env": "CI"}}
    assert evaluate_conditions(cfg) is False


def test_env_dict_match(monkeypatch):
    monkeypatch.setenv("HOOKRUNNER_ENV", "production")
    cfg = {"conditions": {"env": {"HOOKRUNNER_ENV": "production"}}}
    assert evaluate_conditions(cfg) is True


def test_env_dict_mismatch(monkeypatch):
    monkeypatch.setenv("HOOKRUNNER_ENV", "staging")
    cfg = {"conditions": {"env": {"HOOKRUNNER_ENV": "production"}}}
    assert evaluate_conditions(cfg) is False


def test_invalid_conditions_type():
    with pytest.raises(ConditionError, match="must be a mapping"):
        evaluate_conditions({"conditions": ["main"]})


def test_invalid_env_type():
    with pytest.raises(ConditionError, match="Unsupported"):
        evaluate_conditions({"conditions": {"env": 42}})
