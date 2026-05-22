"""Command-line interface for hookrunner.

Provides the main entry point and CLI commands for installing,
running, and managing git hooks.
"""

import argparse
import sys
import os
from pathlib import Path

from hookrunner.config import load_config, get_hooks_for_branch
from hookrunner.executor import HookExecutionError, run_hooks
from hookrunner.git import GitError, get_current_branch, is_git_repo


DEFAULT_CONFIG = ".hookrunner.yml"
GIT_HOOKS_DIR = ".git/hooks"

# Hook types that hookrunner can manage
SUPPORTED_HOOKS = [
    "pre-commit",
    "pre-push",
    "commit-msg",
    "post-commit",
    "post-merge",
    "pre-rebase",
]


def cmd_run(args):
    """Run hooks for the given hook type on the current branch."""
    if not is_git_repo():
        print("error: not inside a git repository", file=sys.stderr)
        return 1

    try:
        branch = get_current_branch()
    except GitError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    config_path = args.config or DEFAULT_CONFIG
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: failed to load config: {e}", file=sys.stderr)
        return 1

    hooks = get_hooks_for_branch(config, branch, args.hook_type)
    if not hooks:
        # Nothing to run is not an error
        return 0

    print(f"[hookrunner] Running {args.hook_type} hooks for branch '{branch}'")
    try:
        run_hooks(hooks, extra_args=args.hook_args)
    except HookExecutionError as e:
        print(f"[hookrunner] Hook failed: {e}", file=sys.stderr)
        return e.returncode if hasattr(e, "returncode") else 1

    return 0


def cmd_install(args):
    """Install hookrunner as a git hook handler for supported hook types."""
    if not is_git_repo():
        print("error: not inside a git repository", file=sys.stderr)
        return 1

    hooks_dir = Path(GIT_HOOKS_DIR)
    if not hooks_dir.exists():
        print(f"error: git hooks directory not found: {hooks_dir}", file=sys.stderr)
        return 1

    hook_types = args.hook_types if args.hook_types else SUPPORTED_HOOKS
    installed = []

    for hook_type in hook_types:
        hook_path = hooks_dir / hook_type
        script = (
            "#!/bin/sh\n"
            f"# Managed by hookrunner\n"
            f'hookrunner run {hook_type} -- "$@"\n'
        )
        hook_path.write_text(script)
        hook_path.chmod(0o755)
        installed.append(hook_type)

    print(f"[hookrunner] Installed hooks: {', '.join(installed)}")
    return 0


def cmd_list(args):
    """List configured hooks for the current branch."""
    if not is_git_repo():
        print("error: not inside a git repository", file=sys.stderr)
        return 1

    try:
        branch = get_current_branch()
    except GitError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    config_path = args.config or DEFAULT_CONFIG
    try:
        config = load_config(config_path)
    except FileNotFoundError:
        print(f"error: config file not found: {config_path}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: failed to load config: {e}", file=sys.stderr)
        return 1

    print(f"Hooks configured for branch '{branch}':")
    for hook_type in SUPPORTED_HOOKS:
        hooks = get_hooks_for_branch(config, branch, hook_type)
        if hooks:
            print(f"  {hook_type}:")
            for hook in hooks:
                print(f"    - {hook}")

    return 0


def build_parser():
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="hookrunner",
        description="Lightweight git hook manager with per-branch configuration.",
    )
    parser.add_argument(
        "--config", "-c",
        metavar="FILE",
        help=f"path to config file (default: {DEFAULT_CONFIG})",
    )

    subparsers = parser.add_subparsers(dest="command", metavar="<command>")
    subparsers.required = True

    # run subcommand
    run_parser = subparsers.add_parser("run", help="run hooks for a given hook type")
    run_parser.add_argument("hook_type", metavar="HOOK_TYPE", help="e.g. pre-commit")
    run_parser.add_argument(
        "hook_args", nargs=argparse.REMAINDER, metavar="...",
        help="extra arguments forwarded to hook scripts",
    )
    run_parser.set_defaults(func=cmd_run)

    # install subcommand
    install_parser = subparsers.add_parser(
        "install", help="install hookrunner as git hook handler"
    )
    install_parser.add_argument(
        "hook_types", nargs="*", metavar="HOOK_TYPE",
        help="hook types to install (default: all supported hooks)",
    )
    install_parser.set_defaults(func=cmd_install)

    # list subcommand
    list_parser = subparsers.add_parser(
        "list", help="list configured hooks for the current branch"
    )
    list_parser.set_defaults(func=cmd_list)

    return parser


def main(argv=None):
    """Main entry point for the hookrunner CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    # Strip leading '--' separator from hook_args if present
    if hasattr(args, "hook_args") and args.hook_args and args.hook_args[0] == "--":
        args.hook_args = args.hook_args[1:]

    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
