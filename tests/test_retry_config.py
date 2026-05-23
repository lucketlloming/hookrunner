"""Tests for hookrunner.retry_config."""

import pytest

from hookrunner.retry import RetryPolicy
from hookrunner.retry_config import RetryConfigError, parse_retry_policy


def test_no_retry_key_returns_none():
    assert parse_retry_policy({"name": "lint", "run": "./lint.sh"}) is None


def test_empty_retry_block_returns_none():
    assert parse_retry_policy({"retry": None}) is None


def test_minimal_retry_config():
    cfg = {"retry": {"max_attempts": 3}}
    policy = parse_retry_policy(cfg)
    assert isinstance(policy, RetryPolicy)
    assert policy.max_attempts == 3
    assert policy.delay_seconds == 0.0
    assert policy.backoff_factor == 1.0


def test_full_retry_config():
    cfg = {
        "retry": {
            "max_attempts": 4,
            "delay_seconds": 0.5,
            "backoff_factor": 2.0,
            "retry_on": ["OSError", "RuntimeError"],
        }
    }
    policy = parse_retry_policy(cfg)
    assert policy.max_attempts == 4
    assert policy.delay_seconds == 0.5
    assert policy.backoff_factor == 2.0
    assert OSError in policy.retry_on
    assert RuntimeError in policy.retry_on


def test_retry_on_as_string():
    cfg = {"retry": {"max_attempts": 2, "retry_on": "IOError"}}
    policy = parse_retry_policy(cfg)
    assert IOError in policy.retry_on


def test_unknown_key_raises():
    cfg = {"retry": {"max_attempts": 2, "unknown_key": True}}
    with pytest.raises(RetryConfigError, match="Unknown retry keys"):
        parse_retry_policy(cfg)


def test_invalid_retry_on_name_raises():
    cfg = {"retry": {"retry_on": ["PermissionError"]}}
    with pytest.raises(RetryConfigError, match="Unsupported retry_on"):
        parse_retry_policy(cfg)


def test_retry_not_a_dict_raises():
    cfg = {"retry": "yes"}
    with pytest.raises(RetryConfigError, match="must be a mapping"):
        parse_retry_policy(cfg)


def test_invalid_max_attempts_raises():
    cfg = {"retry": {"max_attempts": 0}}
    with pytest.raises(ValueError, match="max_attempts"):
        parse_retry_policy(cfg)
