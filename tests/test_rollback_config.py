"""Tests for hookrunner.rollback_config."""

import pytest

from hookrunner.rollback_config import RollbackConfig, RollbackConfigError, parse_rollback_config


def test_no_rollback_key_returns_none():
    assert parse_rollback_config({}) is None


def test_empty_rollback_block_returns_none():
    assert parse_rollback_config({"rollback": {}}) is None


def test_minimal_rollback_config():
    cfg = parse_rollback_config({"rollback": {"enabled": True}})
    assert isinstance(cfg, RollbackConfig)
    assert cfg.enabled is True
    assert cfg.save_on == ["success"]
    assert cfg.clear_on == ["success"]


def test_full_rollback_config():
    raw = {"rollback": {"enabled": True, "save_on": ["success", "failure"], "clear_on": ["failure"]}}
    cfg = parse_rollback_config(raw)
    assert cfg.save_on == ["success", "failure"]
    assert cfg.clear_on == ["failure"]


def test_save_on_as_string():
    cfg = parse_rollback_config({"rollback": {"enabled": False, "save_on": "failure"}})
    assert cfg.save_on == ["failure"]


def test_rollback_not_a_dict_raises():
    with pytest.raises(RollbackConfigError, match="must be a mapping"):
        parse_rollback_config({"rollback": "yes"})


def test_enabled_not_bool_raises():
    with pytest.raises(RollbackConfigError, match="boolean"):
        parse_rollback_config({"rollback": {"enabled": "yes"}})


def test_unknown_event_raises():
    with pytest.raises(RollbackConfigError, match="Unknown rollback event"):
        parse_rollback_config({"rollback": {"enabled": True, "save_on": "unknown"}})


def test_save_on_invalid_type_raises():
    with pytest.raises(RollbackConfigError, match="save_on"):
        parse_rollback_config({"rollback": {"enabled": True, "save_on": 42}})
