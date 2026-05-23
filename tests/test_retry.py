"""Tests for hookrunner.retry."""

import pytest

from hookrunner.retry import RetryError, RetryPolicy, run_with_retry


# ---------------------------------------------------------------------------
# RetryPolicy validation
# ---------------------------------------------------------------------------

def test_policy_defaults():
    p = RetryPolicy()
    assert p.max_attempts == 1
    assert p.delay_seconds == 0.0
    assert p.backoff_factor == 1.0


def test_policy_invalid_attempts():
    with pytest.raises(ValueError, match="max_attempts"):
        RetryPolicy(max_attempts=0).validate()


def test_policy_invalid_delay():
    with pytest.raises(ValueError, match="delay_seconds"):
        RetryPolicy(delay_seconds=-1).validate()


def test_policy_invalid_backoff():
    with pytest.raises(ValueError, match="backoff_factor"):
        RetryPolicy(backoff_factor=0.5).validate()


# ---------------------------------------------------------------------------
# run_with_retry — success paths
# ---------------------------------------------------------------------------

def test_success_on_first_attempt():
    result = run_with_retry(lambda: 42, hook_name="myhook")
    assert result == 42


def test_success_after_retry():
    calls = []

    def flaky():
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("not yet")
        return "ok"

    policy = RetryPolicy(max_attempts=3, delay_seconds=0)
    result = run_with_retry(flaky, hook_name="flaky", policy=policy)
    assert result == "ok"
    assert len(calls) == 3


# ---------------------------------------------------------------------------
# run_with_retry — failure paths
# ---------------------------------------------------------------------------

def test_raises_retry_error_after_exhaustion():
    policy = RetryPolicy(max_attempts=2, delay_seconds=0)

    def always_fail():
        raise ValueError("boom")

    with pytest.raises(RetryError) as exc_info:
        run_with_retry(always_fail, hook_name="bad", policy=policy)

    err = exc_info.value
    assert err.hook_name == "bad"
    assert err.attempts == 2
    assert isinstance(err.last_error, ValueError)


def test_retry_error_message_contains_hook_name():
    policy = RetryPolicy(max_attempts=1, delay_seconds=0)

    with pytest.raises(RetryError, match="'myhook'"):
        run_with_retry(lambda: (_ for _ in ()).throw(OSError("oops")), hook_name="myhook", policy=policy)


def test_non_retryable_exception_propagates_immediately():
    """Exceptions not in retry_on must bubble up without retry."""
    calls = []
    policy = RetryPolicy(max_attempts=5, delay_seconds=0, retry_on=(OSError,))

    def raises_value_error():
        calls.append(1)
        raise ValueError("unexpected")

    with pytest.raises(ValueError):
        run_with_retry(raises_value_error, hook_name="hook", policy=policy)

    assert len(calls) == 1


def test_no_delay_when_zero(monkeypatch):
    slept = []
    monkeypatch.setattr("hookrunner.retry.time.sleep", lambda s: slept.append(s))
    policy = RetryPolicy(max_attempts=3, delay_seconds=0)

    with pytest.raises(RetryError):
        run_with_retry(lambda: (_ for _ in ()).throw(RuntimeError("x")), hook_name="h", policy=policy)

    assert slept == []
