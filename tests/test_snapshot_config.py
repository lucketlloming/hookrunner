"""Tests for hookrunner.snapshot_config."""

from __future__ import annotations

import pytest

from hookrunner.snapshot_config import SnapshotConfigError, parse_snapshot_config


def test_no_snapshot_key_returns_none() -> None:
    assert parse_snapshot_config({"cmd": "echo hi"}) is None


def test_empty_snapshot_block_returns_none() -> None:
    assert parse_snapshot_config({"snapshot": {}}) is None


def test_minimal_snapshot_config() -> None:
    cfg = parse_snapshot_config({"snapshot": {"watch": ["src/"]}})
    assert cfg is not None
    assert cfg["enabled"] is True
    assert cfg["watch"] == ["src/"]


def test_full_snapshot_config() -> None:
    cfg = parse_snapshot_config(
        {"snapshot": {"enabled": False, "watch": ["a.py", "b.py"]}}
    )
    assert cfg is not None
    assert cfg["enabled"] is False
    assert cfg["watch"] == ["a.py", "b.py"]


def test_snapshot_not_a_dict_raises() -> None:
    with pytest.raises(SnapshotConfigError, match="mapping"):
        parse_snapshot_config({"snapshot": "yes"})


def test_unknown_key_raises() -> None:
    with pytest.raises(SnapshotConfigError, match="Unknown keys"):
        parse_snapshot_config({"snapshot": {"watch": [], "oops": True}})


def test_watch_not_a_list_raises() -> None:
    with pytest.raises(SnapshotConfigError, match="list"):
        parse_snapshot_config({"snapshot": {"watch": "src/"}})


def test_watch_item_not_string_raises() -> None:
    with pytest.raises(SnapshotConfigError, match="string"):
        parse_snapshot_config({"snapshot": {"watch": [42]}})


def test_watch_empty_list_ok() -> None:
    cfg = parse_snapshot_config({"snapshot": {"watch": []}})
    assert cfg is not None
    assert cfg["watch"] == []
