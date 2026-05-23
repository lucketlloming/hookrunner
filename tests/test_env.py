"""Tests for hookrunner.env."""

import os
import pytest

from hookrunner.env import EnvError, build_hook_env, merge_hook_env


# ---------------------------------------------------------------------------
# build_hook_env
# ---------------------------------------------------------------------------

def test_build_hook_env_injects_standard_keys(tmp_path):
    env = build_hook_env("pre-commit", "main", str(tmp_path))
    assert env["HOOKRUNNER"] == "1"
    assert env["HOOKRUNNER_EVENT"] == "pre-commit"
    assert env["HOOKRUNNER_BRANCH"] == "main"
    assert env["HOOKRUNNER_ROOT"] == str(tmp_path.resolve())


def test_build_hook_env_inherits_os_environ(tmp_path, monkeypatch):
    monkeypatch.setenv("MY_CUSTOM_VAR", "hello")
    env = build_hook_env("commit-msg", "dev", str(tmp_path))
    assert env["MY_CUSTOM_VAR"] == "hello"


def test_build_hook_env_extra_values(tmp_path):
    env = build_hook_env("pre-push", "feature", str(tmp_path), extra={"MY_FLAG": True})
    assert env["MY_FLAG"] == "1"


def test_build_hook_env_extra_false_bool(tmp_path):
    env = build_hook_env("pre-push", "feature", str(tmp_path), extra={"SKIP": False})
    assert env["SKIP"] == "0"


def test_build_hook_env_extra_numeric(tmp_path):
    env = build_hook_env("pre-commit", "main", str(tmp_path), extra={"TIMEOUT": 30})
    assert env["TIMEOUT"] == "30"


def test_build_hook_env_extra_invalid_key_skipped(tmp_path):
    env = build_hook_env("pre-commit", "main", str(tmp_path), extra={"bad-key": "x"})
    assert "bad-key" not in env


def test_build_hook_env_raises_on_empty_event(tmp_path):
    with pytest.raises(EnvError, match="event"):
        build_hook_env("", "main", str(tmp_path))


def test_build_hook_env_raises_on_empty_branch(tmp_path):
    with pytest.raises(EnvError, match="branch"):
        build_hook_env("pre-commit", "", str(tmp_path))


def test_build_hook_env_raises_on_empty_root(tmp_path):
    with pytest.raises(EnvError, match="repo_root"):
        build_hook_env("pre-commit", "main", "")


def test_build_hook_env_root_is_absolute(tmp_path):
    env = build_hook_env("pre-commit", "main", str(tmp_path))
    assert os.path.isabs(env["HOOKRUNNER_ROOT"])


# ---------------------------------------------------------------------------
# merge_hook_env
# ---------------------------------------------------------------------------

def test_merge_hook_env_none_returns_copy():
    base = {"A": "1", "B": "2"}
    result = merge_hook_env(base, None)
    assert result == base
    assert result is not base


def test_merge_hook_env_empty_dict_returns_copy():
    base = {"A": "1"}
    result = merge_hook_env(base, {})
    assert result == base


def test_merge_hook_env_overrides_key():
    base = {"PATH": "/usr/bin", "HOOKRUNNER": "1"}
    result = merge_hook_env(base, {"HOOKRUNNER": "0"})
    assert result["HOOKRUNNER"] == "0"
    assert result["PATH"] == "/usr/bin"


def test_merge_hook_env_adds_new_key():
    base = {"A": "1"}
    result = merge_hook_env(base, {"EXTRA": "yes"})
    assert result["EXTRA"] == "yes"


def test_merge_hook_env_invalid_key_raises():
    base = {"A": "1"}
    with pytest.raises(EnvError, match="Invalid environment variable name"):
        merge_hook_env(base, {"bad-key": "value"})


def test_merge_hook_env_does_not_mutate_base():
    base = {"A": "1"}
    merge_hook_env(base, {"B": "2"})
    assert "B" not in base
