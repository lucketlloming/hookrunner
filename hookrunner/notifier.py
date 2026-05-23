"""Hook execution notification system for hookrunner."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from hookrunner.profiler import HookTiming


@dataclass
class NotificationEvent:
    """Represents a single hook lifecycle event."""

    hook_name: str
    event_type: str  # 'start' | 'success' | 'failure' | 'skip'
    message: Optional[str] = None
    timing: Optional[HookTiming] = None

    def __str__(self) -> str:
        parts = [f"[{self.event_type.upper()}] {self.hook_name}"]
        if self.message:
            parts.append(f": {self.message}")
        if self.timing:
            parts.append(f" ({self.timing.duration:.3f}s)")
        return "".join(parts)


HandlerFn = Callable[[NotificationEvent], None]


class Notifier:
    """Dispatches hook lifecycle events to registered handlers."""

    def __init__(self) -> None:
        self._handlers: List[HandlerFn] = []

    def register(self, handler: HandlerFn) -> None:
        """Register a callable that receives NotificationEvent instances."""
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler).__name__}")
        self._handlers.append(handler)

    def unregister(self, handler: HandlerFn) -> None:
        """Remove a previously registered handler."""
        self._handlers.remove(handler)

    def notify(self, event: NotificationEvent) -> None:
        """Dispatch *event* to all registered handlers."""
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:  # noqa: BLE001
                pass  # handlers must not crash the runner

    # -- convenience factories --------------------------------------------------

    def on_start(self, hook_name: str) -> None:
        self.notify(NotificationEvent(hook_name=hook_name, event_type="start"))

    def on_success(self, hook_name: str, timing: Optional[HookTiming] = None) -> None:
        self.notify(NotificationEvent(hook_name=hook_name, event_type="success", timing=timing))

    def on_failure(
        self, hook_name: str, message: str = "", timing: Optional[HookTiming] = None
    ) -> None:
        self.notify(
            NotificationEvent(
                hook_name=hook_name, event_type="failure", message=message, timing=timing
            )
        )

    def on_skip(self, hook_name: str, reason: str = "") -> None:
        self.notify(
            NotificationEvent(hook_name=hook_name, event_type="skip", message=reason)
        )


def stderr_handler(event: NotificationEvent) -> None:
    """Built-in handler that writes events to stderr."""
    print(str(event), file=sys.stderr)
