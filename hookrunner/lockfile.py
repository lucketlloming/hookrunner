"""Lockfile support to prevent concurrent hook execution for the same event."""

import os
import time
import errno
from pathlib import Path


class LockfileError(Exception):
    """Raised when a lock cannot be acquired or released."""


_DEFAULT_TIMEOUT = 30  # seconds
_LOCK_DIR = ".hookrunner" + os.sep + "locks"


def _lock_path(repo: str, event: str) -> Path:
    """Return the path to the lockfile for a given repo and hook event."""
    safe_event = event.replace("/", "_").replace("\\", "_")
    return Path(repo) / _LOCK_DIR / f"{safe_event}.lock"


def acquire_lock(repo: str, event: str, timeout: int = _DEFAULT_TIMEOUT) -> Path:
    """Acquire a lockfile for the given repo and event.

    Polls until the lock is free or *timeout* seconds have elapsed.
    Raises LockfileError if the lock cannot be acquired in time.
    Returns the Path of the created lockfile on success.
    """
    lock = _lock_path(repo, event)
    lock.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.monotonic() + timeout
    while True:
        try:
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            with os.fdopen(fd, "w") as fh:
                fh.write(str(os.getpid()))
            return lock
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise LockfileError(f"Failed to create lockfile {lock}: {exc}") from exc
            if time.monotonic() >= deadline:
                raise LockfileError(
                    f"Could not acquire lock for event '{event}' within {timeout}s. "
                    f"Lock file: {lock}"
                )
            time.sleep(0.1)


def release_lock(lock: Path) -> None:
    """Release (delete) a previously acquired lockfile.

    Silently ignores the case where the file is already gone.
    """
    try:
        lock.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise LockfileError(f"Failed to release lockfile {lock}: {exc}") from exc


def is_locked(repo: str, event: str) -> bool:
    """Return True if a lockfile currently exists for the given repo and event."""
    return _lock_path(repo, event).exists()
