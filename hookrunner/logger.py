"""Logging utilities for hookrunner."""

import logging
import sys
from typing import Optional

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
SIMPLE_FORMAT = "[%(levelname)s] %(message)s"

_loggers: dict = {}


def get_logger(name: str = "hookrunner") -> logging.Logger:
    """Return a named logger, creating it if necessary."""
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter(SIMPLE_FORMAT))
        logger.addHandler(handler)
        logger.propagate = False

    _loggers[name] = logger
    return logger


def configure_logging(verbose: bool = False, quiet: bool = False) -> None:
    """Configure root hookrunner logger verbosity.

    Args:
        verbose: If True, set level to DEBUG.
        quiet:   If True, set level to ERROR (suppresses warnings/info).
    """
    logger = get_logger("hookrunner")

    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
        # Switch to detailed format when verbose
        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(LOG_FORMAT))
    else:
        level = logging.INFO

    logger.setLevel(level)


def hook_logger(hook_name: str) -> logging.Logger:
    """Return a child logger scoped to a specific hook name."""
    return get_logger(f"hookrunner.hooks.{hook_name}")
