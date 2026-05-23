"""Tests for hookrunner.timeout."""

import time
import pytest

from hookrunner.timeout import TimeoutError, timeout_context, parse_timeout


# ---------------------------------------------------------------------------
# TimeoutError
# ---------------------------------------------------------------------------

def test_timeout_error_message():
    err = TimeoutError("lint", 30)
    assert "lint" in str(err)
    assert "30" in str(err)


def test_timeout_error_attributes():
    err = TimeoutError("pre-commit", 10)
    assert err.hook == "pre-commit"
    assert err.seconds == 10


# ---------------------------------------------------------------------------
# timeout_context
# ---------------------------------------------------------------------------

def test_timeout_context_none_is_noop():
    """None timeout should not raise."""
    with timeout_context(None, "test"):
        time.sleep(0.01)


def test_timeout_context_zero_is_noop():
    with timeout_context(0, "test"):
        time.sleep(0.01)


def test_timeout_context_passes_within_limit():
    with timeout_context(5, "fast-hook"):
        pass  # completes instantly


def test_timeout_context_raises_on_exceed():
    with pytest.raises(TimeoutError) as exc_info:
        with timeout_context(1, "slow-hook"):
            time.sleep(3)
    assert exc_info.value.hook == "slow-hook"
    assert exc_info.value.seconds == 1


def test_timeout_context_restores_alarm_after_success():
    import signal
    with timeout_context(5, "hook"):
        pass
    # alarm should be cancelled
    remaining = signal.alarm(0)
    assert remaining == 0


# ---------------------------------------------------------------------------
# parse_timeout
# ---------------------------------------------------------------------------

def test_parse_timeout_none():
    assert parse_timeout(None) is None


def test_parse_timeout_zero_returns_none():
    assert parse_timeout(0) is None


def test_parse_timeout_string_int():
    assert parse_timeout("30") == 30


def test_parse_timeout_int():
    assert parse_timeout(60) == 60


def test_parse_timeout_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        parse_timeout(-1)


def test_parse_timeout_invalid_string_raises():
    with pytest.raises(ValueError, match="Invalid timeout"):
        parse_timeout("fast")
