"""Parallel hook execution support for hookrunner."""

import concurrent.futures
from typing import List, Tuple

from hookrunner.executor import HookExecutionError
from hookrunner.logger import get_logger
from hookrunner.profiler import HookTiming

logger = get_logger(__name__)


class ParallelError(Exception):
    """Raised when parallel execution encounters a configuration or runtime error."""


def _run_single(hook: str, args: List[str], cwd: str) -> HookTiming:
    """Execute a single hook and return a HookTiming result."""
    import time
    from hookrunner.executor import HookRunner

    start = time.monotonic()
    runner = HookRunner(cwd)
    passed = True
    message = None
    try:
        runner.run_hook(hook, args)
    except HookExecutionError as exc:
        passed = False
        message = str(exc)
        logger.debug("Hook %s failed: %s", hook, message)
    elapsed = time.monotonic() - start
    return HookTiming(name=hook, duration=elapsed, passed=passed, message=message)


def run_hooks_parallel(
    hooks: List[str],
    args: List[str],
    cwd: str,
    max_workers: int = 4,
) -> List[HookTiming]:
    """Run *hooks* concurrently and return a list of :class:`HookTiming` results.

    Args:
        hooks: Ordered list of hook script paths to execute.
        args:  Arguments forwarded to every hook.
        cwd:   Working directory for hook execution.
        max_workers: Maximum number of threads to use.

    Returns:
        List of :class:`HookTiming` objects in submission order.

    Raises:
        ParallelError: If *max_workers* is less than 1.
    """
    if max_workers < 1:
        raise ParallelError(f"max_workers must be >= 1, got {max_workers}")
    if not hooks:
        return []

    results: List[Tuple[int, HookTiming]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_idx = {
            pool.submit(_run_single, hook, args, cwd): idx
            for idx, hook in enumerate(hooks)
        }
        for future in concurrent.futures.as_completed(future_to_idx):
            idx = future_to_idx[future]
            timing = future.result()  # _run_single never raises
            results.append((idx, timing))

    results.sort(key=lambda t: t[0])
    return [timing for _, timing in results]
