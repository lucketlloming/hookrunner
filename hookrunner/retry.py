"""Retry logic for hook execution with configurable backoff."""

import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from hookrunner.logger import get_logger

logger = get_logger(__name__)


class RetryError(Exception):
    """Raised when all retry attempts are exhausted."""

    def __init__(self, hook_name: str, attempts: int, last_error: Exception):
        self.hook_name = hook_name
        self.attempts = attempts
        self.last_error = last_error
        super().__init__(
            f"Hook '{hook_name}' failed after {attempts} attempt(s): {last_error}"
        )


@dataclass
class RetryPolicy:
    """Configuration for retry behaviour."""

    max_attempts: int = 1
    delay_seconds: float = 0.0
    backoff_factor: float = 1.0
    retry_on: tuple = field(default_factory=lambda: (Exception,))

    def validate(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be >= 1")
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds must be >= 0")
        if self.backoff_factor < 1.0:
            raise ValueError("backoff_factor must be >= 1.0")


def run_with_retry(
    func: Callable,
    hook_name: str,
    policy: Optional[RetryPolicy] = None,
    *args,
    **kwargs,
):
    """Execute *func* according to *policy*, retrying on allowed exceptions."""
    if policy is None:
        policy = RetryPolicy()
    policy.validate()

    delay = policy.delay_seconds
    last_exc: Optional[Exception] = None

    for attempt in range(1, policy.max_attempts + 1):
        try:
            logger.debug("[%s] attempt %d/%d", hook_name, attempt, policy.max_attempts)
            return func(*args, **kwargs)
        except tuple(policy.retry_on) as exc:  # type: ignore[misc]
            last_exc = exc
            logger.warning(
                "[%s] attempt %d failed: %s", hook_name, attempt, exc
            )
            if attempt < policy.max_attempts:
                if delay > 0:
                    logger.debug("[%s] retrying in %.2fs", hook_name, delay)
                    time.sleep(delay)
                delay *= policy.backoff_factor

    raise RetryError(hook_name, policy.max_attempts, last_exc)  # type: ignore[arg-type]
