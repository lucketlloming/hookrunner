"""Hook execution profiling and timing utilities."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from hookrunner.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HookTiming:
    """Stores timing information for a single hook execution."""

    hook_name: str
    event: str
    duration_seconds: float
    exit_code: int
    branch: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def __str__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.event}/{self.hook_name} "
            f"on '{self.branch}' took {self.duration_seconds:.3f}s"
        )


@dataclass
class ProfilerSession:
    """Accumulates timing data for a run session."""

    event: str
    branch: Optional[str] = None
    timings: List[HookTiming] = field(default_factory=list)
    _start: float = field(default_factory=time.monotonic, repr=False)

    def record(self, hook_name: str, duration: float, exit_code: int) -> HookTiming:
        timing = HookTiming(
            hook_name=hook_name,
            event=self.event,
            duration_seconds=duration,
            exit_code=exit_code,
            branch=self.branch,
        )
        self.timings.append(timing)
        logger.debug(str(timing))
        return timing

    @property
    def total_duration(self) -> float:
        return sum(t.duration_seconds for t in self.timings)

    @property
    def failed_hooks(self) -> List[HookTiming]:
        return [t for t in self.timings if not t.passed]

    def summary(self) -> Dict:
        return {
            "event": self.event,
            "branch": self.branch,
            "total_hooks": len(self.timings),
            "passed": len([t for t in self.timings if t.passed]),
            "failed": len(self.failed_hooks),
            "total_duration_seconds": round(self.total_duration, 4),
        }


def timed_hook(session: ProfilerSession, hook_name: str):
    """Context manager that records hook execution time into a session."""

    class _Timer:
        def __init__(self):
            self.exit_code = 0

        def __enter__(self):
            self._start = time.monotonic()
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            duration = time.monotonic() - self._start
            session.record(hook_name, duration, self.exit_code)
            return False

    return _Timer()
