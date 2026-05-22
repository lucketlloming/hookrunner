"""Tests for hookrunner.profiler."""

import time

import pytest

from hookrunner.profiler import HookTiming, ProfilerSession, timed_hook


# ---------------------------------------------------------------------------
# HookTiming
# ---------------------------------------------------------------------------

def test_hook_timing_passed():
    t = HookTiming(hook_name="lint", event="pre-commit", duration_seconds=0.5, exit_code=0)
    assert t.passed is True


def test_hook_timing_failed():
    t = HookTiming(hook_name="lint", event="pre-commit", duration_seconds=0.5, exit_code=1)
    assert t.passed is False


def test_hook_timing_str_pass():
    t = HookTiming(hook_name="lint", event="pre-commit", duration_seconds=1.0, exit_code=0, branch="main")
    s = str(t)
    assert "PASS" in s
    assert "lint" in s
    assert "main" in s


def test_hook_timing_str_fail():
    t = HookTiming(hook_name="test", event="pre-push", duration_seconds=2.0, exit_code=2, branch="dev")
    assert "FAIL" in str(t)


# ---------------------------------------------------------------------------
# ProfilerSession
# ---------------------------------------------------------------------------

def test_session_record_adds_timing():
    session = ProfilerSession(event="pre-commit", branch="main")
    session.record("lint", 0.3, 0)
    assert len(session.timings) == 1
    assert session.timings[0].hook_name == "lint"


def test_session_total_duration():
    session = ProfilerSession(event="pre-commit")
    session.record("a", 1.0, 0)
    session.record("b", 2.0, 0)
    assert abs(session.total_duration - 3.0) < 1e-9


def test_session_failed_hooks():
    session = ProfilerSession(event="pre-push")
    session.record("ok", 0.1, 0)
    session.record("bad", 0.2, 1)
    assert len(session.failed_hooks) == 1
    assert session.failed_hooks[0].hook_name == "bad"


def test_session_summary_keys():
    session = ProfilerSession(event="pre-commit", branch="feature")
    session.record("lint", 0.5, 0)
    session.record("fmt", 0.2, 1)
    summary = session.summary()
    assert summary["event"] == "pre-commit"
    assert summary["branch"] == "feature"
    assert summary["total_hooks"] == 2
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert "total_duration_seconds" in summary


# ---------------------------------------------------------------------------
# timed_hook context manager
# ---------------------------------------------------------------------------

def test_timed_hook_records_duration():
    session = ProfilerSession(event="pre-commit", branch="main")
    with timed_hook(session, "slow-hook") as t:
        t.exit_code = 0
        time.sleep(0.05)
    assert len(session.timings) == 1
    assert session.timings[0].duration_seconds >= 0.05


def test_timed_hook_records_exit_code():
    session = ProfilerSession(event="pre-push")
    with timed_hook(session, "failing") as t:
        t.exit_code = 127
    assert session.timings[0].exit_code == 127
    assert not session.timings[0].passed


def test_timed_hook_does_not_suppress_exceptions():
    session = ProfilerSession(event="pre-commit")
    with pytest.raises(RuntimeError):
        with timed_hook(session, "boom"):
            raise RuntimeError("oops")
