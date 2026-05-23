"""Hook run reporter — formats and emits a summary after all hooks execute."""

from __future__ import annotations

import sys
from typing import List, TextIO

from hookrunner.profiler import HookTiming, ProfilerSession

_PASS = "\033[32m✔\033[0m"
_FAIL = "\033[31m✘\033[0m"
_LINE = "-" * 48


class Reporter:
    """Collect hook results and print a human-readable summary."""

    def __init__(self, session: ProfilerSession, stream: TextIO = sys.stderr) -> None:
        self._session = session
        self._stream = stream

    # ------------------------------------------------------------------
    def _icon(self, timing: HookTiming) -> str:
        return _PASS if timing.passed else _FAIL

    def _format_row(self, timing: HookTiming) -> str:
        status = "PASS" if timing.passed else "FAIL"
        duration = f"{timing.duration_ms:.0f} ms"
        return f"  {self._icon(timing)}  {timing.hook_id:<30} {status:>4}  {duration:>8}"

    # ------------------------------------------------------------------
    def print_summary(self) -> None:
        """Write the full run summary to *stream*."""
        timings: List[HookTiming] = self._session.timings
        total = len(timings)
        failures = sum(1 for t in timings if not t.passed)

        print(_LINE, file=self._stream)
        print("hookrunner summary", file=self._stream)
        print(_LINE, file=self._stream)

        for timing in timings:
            print(self._format_row(timing), file=self._stream)

        print(_LINE, file=self._stream)
        total_ms = sum(t.duration_ms for t in timings)
        print(
            f"  {total} hook(s) — {failures} failed — {total_ms:.0f} ms total",
            file=self._stream,
        )
        print(_LINE, file=self._stream)

    # ------------------------------------------------------------------
    def exit_code(self) -> int:
        """Return 0 if all hooks passed, 1 otherwise."""
        return 1 if any(not t.passed for t in self._session.timings) else 0
