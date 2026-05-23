"""Tests for hookrunner.reporter module."""

import io

import pytest

from hookrunner.profiler import HookTiming, ProfilerSession
from hookrunner.reporter import Reporter


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_timing(hook_id: str, passed: bool, duration_ms: float = 42.0) -> HookTiming:
    return HookTiming(hook_id=hook_id, passed=passed, duration_ms=duration_ms)


def _make_session(*timings: HookTiming) -> ProfilerSession:
    session = ProfilerSession()
    for t in timings:
        session.timings.append(t)
    return session


# ---------------------------------------------------------------------------
# exit_code
# ---------------------------------------------------------------------------

def test_exit_code_all_pass():
    session = _make_session(_make_timing("lint", passed=True))
    reporter = Reporter(session, stream=io.StringIO())
    assert reporter.exit_code() == 0


def test_exit_code_any_fail():
    session = _make_session(
        _make_timing("lint", passed=True),
        _make_timing("test", passed=False),
    )
    reporter = Reporter(session, stream=io.StringIO())
    assert reporter.exit_code() == 1


def test_exit_code_empty_session():
    session = _make_session()
    reporter = Reporter(session, stream=io.StringIO())
    assert reporter.exit_code() == 0


# ---------------------------------------------------------------------------
# print_summary output
# ---------------------------------------------------------------------------

def test_summary_contains_hook_id():
    session = _make_session(_make_timing("my-hook", passed=True, duration_ms=10))
    buf = io.StringIO()
    Reporter(session, stream=buf).print_summary()
    assert "my-hook" in buf.getvalue()


def test_summary_pass_label():
    session = _make_session(_make_timing("lint", passed=True))
    buf = io.StringIO()
    Reporter(session, stream=buf).print_summary()
    assert "PASS" in buf.getvalue()


def test_summary_fail_label():
    session = _make_session(_make_timing("test", passed=False))
    buf = io.StringIO()
    Reporter(session, stream=buf).print_summary()
    assert "FAIL" in buf.getvalue()


def test_summary_totals_line():
    session = _make_session(
        _make_timing("a", passed=True, duration_ms=100),
        _make_timing("b", passed=False, duration_ms=200),
    )
    buf = io.StringIO()
    Reporter(session, stream=buf).print_summary()
    output = buf.getvalue()
    assert "2 hook(s)" in output
    assert "1 failed" in output
    assert "300 ms" in output


def test_summary_multiple_hooks_all_present():
    session = _make_session(
        _make_timing("hook-a", passed=True),
        _make_timing("hook-b", passed=True),
        _make_timing("hook-c", passed=False),
    )
    buf = io.StringIO()
    Reporter(session, stream=buf).print_summary()
    output = buf.getvalue()
    for name in ("hook-a", "hook-b", "hook-c"):
        assert name in output
