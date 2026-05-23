"""Tests for hookrunner.throttle."""

import time
import pytest

from hookrunner.throttle import (
    ThrottleError,
    clear_all,
    clear_run,
    get_last_run,
    is_throttled,
    parse_throttle_window,
    record_run,
)

REPO = "/fake/repo"
HOOK = "pre-commit"


@pytest.fixture(autouse=True)
def reset():
    clear_all()
    yield
    clear_all()


def test_get_last_run_initially_none():
    assert get_last_run(REPO, HOOK) is None


def test_record_run_stores_timestamp():
    ts = record_run(REPO, HOOK, ts=1000.0)
    assert ts == 1000.0
    assert get_last_run(REPO, HOOK) == 1000.0


def test_record_run_uses_current_time_by_default():
    before = time.time()
    ts = record_run(REPO, HOOK)
    after = time.time()
    assert before <= ts <= after


def test_clear_run_removes_entry():
    record_run(REPO, HOOK, ts=500.0)
    clear_run(REPO, HOOK)
    assert get_last_run(REPO, HOOK) is None


def test_clear_run_missing_key_is_noop():
    clear_run(REPO, "nonexistent")  # should not raise


def test_is_throttled_no_prior_run():
    assert is_throttled(REPO, HOOK, window=60) is False


def test_is_throttled_within_window():
    record_run(REPO, HOOK, ts=time.time())
    assert is_throttled(REPO, HOOK, window=60) is True


def test_is_throttled_outside_window():
    record_run(REPO, HOOK, ts=time.time() - 120)
    assert is_throttled(REPO, HOOK, window=60) is False


def test_is_throttled_zero_window_never_throttles():
    record_run(REPO, HOOK, ts=time.time())
    assert is_throttled(REPO, HOOK, window=0) is False


def test_is_throttled_negative_window_raises():
    with pytest.raises(ThrottleError, match=">= 0"):
        is_throttled(REPO, HOOK, window=-1)


def test_parse_throttle_window_missing_key():
    assert parse_throttle_window({}) is None


def test_parse_throttle_window_none_value():
    assert parse_throttle_window({"throttle": None}) is None


def test_parse_throttle_window_valid_int():
    assert parse_throttle_window({"throttle": 30}) == 30.0


def test_parse_throttle_window_valid_string_float():
    assert parse_throttle_window({"throttle": "2.5"}) == 2.5


def test_parse_throttle_window_invalid_string():
    with pytest.raises(ThrottleError, match="Invalid throttle value"):
        parse_throttle_window({"throttle": "fast"})


def test_parse_throttle_window_negative():
    with pytest.raises(ThrottleError, match=">= 0"):
        parse_throttle_window({"throttle": -5})
