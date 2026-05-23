"""Hook execution timeout support."""

import signal
from contextlib import contextmanager
from typing import Optional


class TimeoutError(Exception):
    """Raised when a hook exceeds its allowed execution time."""

    def __init__(self, hook: str, seconds: int) -> None:
        self.hook = hook
        self.seconds = seconds
        super().__init__(f"Hook '{hook}' timed out after {seconds}s")


def _timeout_handler(signum, frame):
    raise TimeoutError("<unknown>", 0)


@contextmanager
def timeout_context(seconds: Optional[int], hook_name: str = "<unknown>"):
    """Context manager that raises TimeoutError if block exceeds *seconds*.

    If *seconds* is None or zero the context is a no-op.
    Only works on Unix (uses SIGALRM).
    """
    if not seconds:
        yield
        return

    original = signal.getsignal(signal.SIGALRM)

    def _handler(signum, frame):
        raise TimeoutError(hook_name, seconds)

    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original)


def parse_timeout(value) -> Optional[int]:
    """Parse a timeout value from config (int, str, or None).

    Returns an integer number of seconds, or None if not set.
    Raises ValueError for invalid values.
    """
    if value is None:
        return None
    try:
        seconds = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid timeout value: {value!r}. Must be an integer.")
    if seconds < 0:
        raise ValueError(f"Timeout must be non-negative, got {seconds}.")
    return seconds if seconds > 0 else None
