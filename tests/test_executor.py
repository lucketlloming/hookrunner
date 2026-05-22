"""Tests for hookrunner.executor module."""

import stat
import textwrap
from pathlib import Path

import pytest

from hookrunner.executor import HookExecutionError, run_hook, run_hooks


@pytest.fixture()
def script_dir(tmp_path: Path) -> Path:
    return tmp_path


def _make_script(directory: Path, name: str, body: str, exit_code: int = 0) -> str:
    """Write a small shell script and make it executable."""
    content = textwrap.dedent(f"""#!/bin/sh
    {body}
    exit {exit_code}
    """)
    path = directory / name
    path.write_text(content)
    path.chmod(path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return str(path)


def test_run_hook_success(script_dir):
    script = _make_script(script_dir, "pass.sh", "echo 'ok'")
    code = run_hook(script, cwd=str(script_dir))
    assert code == 0


def test_run_hook_failure_raises(script_dir):
    script = _make_script(script_dir, "fail.sh", "echo 'boom' >&2", exit_code=1)
    with pytest.raises(HookExecutionError) as exc_info:
        run_hook(script, cwd=str(script_dir))
    err = exc_info.value
    assert err.returncode == 1
    assert err.hook == script


def test_run_hook_passes_args(script_dir, capsys):
    script = _make_script(script_dir, "echo_args.sh", "echo \"$@\"")
    run_hook(script, args=["hello", "world"], cwd=str(script_dir))
    # stdout is forwarded to sys.stdout so we just assert no exception


def test_run_hooks_all_succeed(script_dir):
    s1 = _make_script(script_dir, "s1.sh", "echo s1")
    s2 = _make_script(script_dir, "s2.sh", "echo s2")
    executed = run_hooks([s1, s2], cwd=str(script_dir))
    assert executed == [s1, s2]


def test_run_hooks_stops_on_first_failure(script_dir):
    s1 = _make_script(script_dir, "ok.sh", "echo ok")
    s2 = _make_script(script_dir, "bad.sh", "", exit_code=2)
    s3 = _make_script(script_dir, "never.sh", "echo never")
    with pytest.raises(HookExecutionError) as exc_info:
        run_hooks([s1, s2, s3], cwd=str(script_dir))
    assert exc_info.value.returncode == 2


def test_hook_execution_error_str():
    err = HookExecutionError("myscript.sh", 127, "not found")
    assert "myscript.sh" in str(err)
    assert "127" in str(err)
    assert "not found" in str(err)
