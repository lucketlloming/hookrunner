"""Hook executor module for running git hook scripts."""

import os
import subprocess
import sys
from typing import List, Optional


class HookExecutionError(Exception):
    """Raised when a hook script exits with a non-zero status."""

    def __init__(self, hook: str, returncode: int, stderr: str = ""):
        self.hook = hook
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(
            f"Hook '{hook}' failed with exit code {returncode}"
            + (f": {stderr}" if stderr else "")
        )


def run_hook(script: str, args: Optional[List[str]] = None, cwd: Optional[str] = None) -> int:
    """Run a single hook script and return its exit code.

    Args:
        script: Path to the hook script or shell command to execute.
        args: Optional list of arguments to pass to the script.
        cwd: Working directory for the hook process. Defaults to current directory.

    Returns:
        The exit code of the hook process.

    Raises:
        FileNotFoundError: If the script does not exist or is not executable.
        HookExecutionError: If the hook exits with a non-zero status.
    """
    cmd = [script] + (args or [])
    cwd = cwd or os.getcwd()

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            env=os.environ.copy(),
            stdout=sys.stdout,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError:
        raise FileNotFoundError(f"Hook script not found or not executable: '{script}'")

    if result.returncode != 0:
        raise HookExecutionError(script, result.returncode, result.stderr.strip())

    return result.returncode


def run_hooks(hooks: List[str], args: Optional[List[str]] = None, cwd: Optional[str] = None) -> List[str]:
    """Run a list of hook scripts sequentially.

    Stops on the first failure.

    Args:
        hooks: List of hook script paths or commands.
        args: Optional arguments forwarded to each hook.
        cwd: Working directory for all hooks.

    Returns:
        List of hooks that were successfully executed.

    Raises:
        FileNotFoundError: If any hook script does not exist or is not executable.
        HookExecutionError: On the first hook that fails.
    """
    executed = []
    for hook in hooks:
        run_hook(hook, args=args, cwd=cwd)
        executed.append(hook)
    return executed
