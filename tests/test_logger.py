"""Tests for hookrunner.logger."""

import logging

import pytest

from hookrunner.logger import (
    configure_logging,
    get_logger,
    hook_logger,
    _loggers,
)


@pytest.fixture(autouse=True)
def reset_loggers():
    """Clear cached loggers and reset handlers between tests."""
    _loggers.clear()
    # Remove any handlers added to the logging module's root logger
    root = logging.getLogger("hookrunner")
    root.handlers.clear()
    yield
    _loggers.clear()
    root.handlers.clear()


def test_get_logger_returns_logger():
    logger = get_logger()
    assert isinstance(logger, logging.Logger)
    assert logger.name == "hookrunner"


def test_get_logger_cached():
    logger1 = get_logger("hookrunner")
    logger2 = get_logger("hookrunner")
    assert logger1 is logger2


def test_get_logger_has_stderr_handler():
    import sys
    logger = get_logger("hookrunner")
    assert len(logger.handlers) == 1
    handler = logger.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    assert handler.stream is sys.stderr


def test_configure_logging_default():
    configure_logging()
    logger = get_logger("hookrunner")
    assert logger.level == logging.INFO


def test_configure_logging_verbose():
    configure_logging(verbose=True)
    logger = get_logger("hookrunner")
    assert logger.level == logging.DEBUG


def test_configure_logging_quiet():
    configure_logging(quiet=True)
    logger = get_logger("hookrunner")
    assert logger.level == logging.ERROR


def test_configure_logging_verbose_updates_format():
    configure_logging(verbose=True)
    logger = get_logger("hookrunner")
    handler = logger.handlers[0]
    fmt = handler.formatter._fmt
    # Verbose format should include asctime
    assert "asctime" in fmt


def test_hook_logger_is_child():
    logger = hook_logger("pre-commit")
    assert logger.name == "hookrunner.hooks.pre-commit"


def test_hook_logger_different_hooks():
    l1 = hook_logger("pre-commit")
    l2 = hook_logger("post-merge")
    assert l1 is not l2
    assert l1.name != l2.name
