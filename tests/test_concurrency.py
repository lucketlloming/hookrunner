"""Tests for hookrunner.concurrency and hookrunner.concurrency_config."""

import threading
import pytest

from hookrunner.concurrency import (
    ConcurrencyError,
    clear_all_semaphores,
    clear_semaphore,
    get_semaphore,
    parse_concurrency_limit,
)
from hookrunner.concurrency_config import get_global_concurrency, resolve_concurrency


@pytest.fixture(autouse=True)
def reset():
    clear_all_semaphores()
    yield
    clear_all_semaphores()


# ---------------------------------------------------------------------------
# get_semaphore
# ---------------------------------------------------------------------------

def test_get_semaphore_returns_semaphore():
    sem = get_semaphore("repo", "pre-commit", 3)
    assert isinstance(sem, threading.Semaphore)


def test_get_semaphore_cached():
    sem1 = get_semaphore("repo", "pre-commit", 3)
    sem2 = get_semaphore("repo", "pre-commit", 3)
    assert sem1 is sem2


def test_get_semaphore_invalid_limit():
    with pytest.raises(ConcurrencyError, match=">= 1"):
        get_semaphore("repo", "pre-commit", 0)


def test_clear_semaphore_removes_entry():
    sem1 = get_semaphore("repo", "pre-commit", 2)
    clear_semaphore("repo", "pre-commit")
    sem2 = get_semaphore("repo", "pre-commit", 2)
    assert sem1 is not sem2


# ---------------------------------------------------------------------------
# parse_concurrency_limit
# ---------------------------------------------------------------------------

def test_parse_concurrency_limit_absent():
    assert parse_concurrency_limit({}) is None


def test_parse_concurrency_limit_valid():
    assert parse_concurrency_limit({"concurrency": 4}) == 4


def test_parse_concurrency_limit_invalid_type():
    with pytest.raises(ConcurrencyError, match="integer"):
        parse_concurrency_limit({"concurrency": "many"})


def test_parse_concurrency_limit_bool_rejected():
    with pytest.raises(ConcurrencyError, match="integer"):
        parse_concurrency_limit({"concurrency": True})


def test_parse_concurrency_limit_zero_rejected():
    with pytest.raises(ConcurrencyError, match=">= 1"):
        parse_concurrency_limit({"concurrency": 0})


# ---------------------------------------------------------------------------
# concurrency_config helpers
# ---------------------------------------------------------------------------

def test_get_global_concurrency_absent():
    assert get_global_concurrency({}) is None


def test_get_global_concurrency_valid():
    assert get_global_concurrency({"concurrency": 2}) == 2


def test_get_global_concurrency_invalid():
    with pytest.raises(ConcurrencyError):
        get_global_concurrency({"concurrency": -1})


def test_resolve_concurrency_hook_takes_precedence():
    assert resolve_concurrency({"concurrency": 5}, {"concurrency": 2}) == 5


def test_resolve_concurrency_falls_back_to_global():
    assert resolve_concurrency({}, {"concurrency": 3}) == 3


def test_resolve_concurrency_both_absent():
    assert resolve_concurrency({}, {}) is None
