"""Tests for hookrunner.notifier."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hookrunner.notifier import NotificationEvent, Notifier, stderr_handler
from hookrunner.profiler import HookTiming


# ---------------------------------------------------------------------------
# NotificationEvent
# ---------------------------------------------------------------------------

def _timing(passed: bool = True) -> HookTiming:
    return HookTiming(hook_name="demo", start=0.0, end=1.25, passed=passed)


def test_event_str_minimal():
    ev = NotificationEvent(hook_name="lint", event_type="start")
    assert str(ev) == "[START] lint"


def test_event_str_with_message():
    ev = NotificationEvent(hook_name="lint", event_type="failure", message="exit 1")
    assert "[FAILURE] lint" in str(ev)
    assert "exit 1" in str(ev)


def test_event_str_with_timing():
    ev = NotificationEvent(hook_name="fmt", event_type="success", timing=_timing())
    text = str(ev)
    assert "[SUCCESS] fmt" in text
    assert "1.250s" in text


# ---------------------------------------------------------------------------
# Notifier.register / unregister
# ---------------------------------------------------------------------------

def test_register_and_dispatch():
    n = Notifier()
    received = []
    n.register(received.append)
    n.on_start("myhook")
    assert len(received) == 1
    assert received[0].event_type == "start"


def test_register_non_callable_raises():
    n = Notifier()
    with pytest.raises(TypeError):
        n.register("not_callable")  # type: ignore[arg-type]


def test_unregister_stops_dispatch():
    n = Notifier()
    calls = []
    n.register(calls.append)
    n.unregister(calls.append)
    n.on_start("x")
    assert calls == []


def test_multiple_handlers_all_called():
    n = Notifier()
    a, b = MagicMock(), MagicMock()
    n.register(a)
    n.register(b)
    n.on_success("hook")
    a.assert_called_once()
    b.assert_called_once()


def test_faulty_handler_does_not_crash_others():
    n = Notifier()

    def bad(_ev):
        raise RuntimeError("boom")

    good = MagicMock()
    n.register(bad)
    n.register(good)
    n.on_start("safe")  # must not raise
    good.assert_called_once()


# ---------------------------------------------------------------------------
# Convenience methods
# ---------------------------------------------------------------------------

def test_on_failure_carries_message():
    n = Notifier()
    events = []
    n.register(events.append)
    n.on_failure("check", message="non-zero exit")
    assert events[0].message == "non-zero exit"
    assert events[0].event_type == "failure"


def test_on_skip_carries_reason():
    n = Notifier()
    events = []
    n.register(events.append)
    n.on_skip("fmt", reason="no staged files")
    assert events[0].event_type == "skip"
    assert events[0].message == "no staged files"


# ---------------------------------------------------------------------------
# Built-in stderr_handler
# ---------------------------------------------------------------------------

def test_stderr_handler_writes_to_stderr(capsys):
    ev = NotificationEvent(hook_name="lint", event_type="start")
    stderr_handler(ev)
    captured = capsys.readouterr()
    assert "[START] lint" in captured.err
