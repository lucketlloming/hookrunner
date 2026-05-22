"""Configuration loader for hookrunner.

Supports per-branch hook configurations via a YAML file (.hookrunner.yml).
"""

import os
from typing import Any

try:
    import yaml
except ImportError:
    raise ImportError("PyYAML is required: pip install pyyaml")

DEFAULT_CONFIG_FILE = ".hookrunner.yml"

DEFAULT_CONFIG: dict[str, Any] = {
    "version": 1,
    "hooks": {},
    "branches": {},
}


def load_config(config_path: str = DEFAULT_CONFIG_FILE) -> dict[str, Any]:
    """Load hookrunner configuration from a YAML file.

    Args:
        config_path: Path to the configuration file.

    Returns:
        Parsed configuration dictionary merged with defaults.

    Raises:
        FileNotFoundError: If the config file does not exist.
        ValueError: If the config file is invalid YAML or has wrong structure.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as fh:
        try:
            raw = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in config file: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError("Config file must contain a YAML mapping at the top level.")

    config = {**DEFAULT_CONFIG, **raw}
    _validate_config(config)
    return config


def _validate_config(config: dict[str, Any]) -> None:
    """Perform basic structural validation on the loaded config."""
    if not isinstance(config.get("hooks"), dict):
        raise ValueError("'hooks' must be a mapping of hook-name to command list.")
    if not isinstance(config.get("branches"), dict):
        raise ValueError("'branches' must be a mapping of branch patterns to hook overrides.")


def get_hooks_for_branch(
    config: dict[str, Any], branch: str, hook_name: str
) -> list[str]:
    """Resolve the list of commands for a given hook and branch.

    Branch-specific overrides take precedence over global hooks.

    Args:
        config: Loaded configuration dictionary.
        branch: Current git branch name.
        hook_name: Git hook name (e.g. 'pre-commit').

    Returns:
        List of shell command strings to execute.
    """
    global_commands: list[str] = config["hooks"].get(hook_name, [])
    branch_overrides: dict[str, Any] = config["branches"].get(branch, {})
    branch_commands: list[str] = branch_overrides.get(hook_name, global_commands)
    return branch_commands
