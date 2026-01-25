"""
config/ — CONFIGURATION DISCIPLINE (NOT A FEATURE LAYER)

This directory exists for one reason only:
to make configuration boring, explicit, validated, and constitutionally safe.

PUBLIC INTERFACE:
This module defines what "configuration" means to the rest of the system.
It provides safe, immutable, validated configuration objects.

USAGE:
    from config import load_config, Config

    # Load from CLI arguments
    config = load_config(cli_args)

    # Or get defaults only
    default_config = get_default_config()

DESIGN AXIOMS:
1. Configuration is data, not logic
2. Defaults are immutable
3. User input is untrusted
4. Validation is mandatory
5. No runtime mutation after load
6. No imports from core execution or observation layers

This is a one-way dependency: everything may read config, config reads almost nothing.
"""

from typing import Any

from .loader import Config, get_default_config, load_config
from .user import BoundaryStrictness, CommandType, OutputFormat

CLIArgs = dict[str, Any]
ConfigDict = dict[str, Any]
ConfigPath = str


def config_to_dict(config: Config) -> ConfigDict:
    """Convert a Config object to a dictionary for debugging."""
    return config.to_dict()


def describe_config(config: Config) -> str:
    """Get a human-readable description of the configuration."""
    return (
        f"Config("
        f"command={config.command.value}, "
        f"source={config.config_source}, "
        f"version={config.config_version}"
        f")"
    )


def is_verbose(config: Config) -> bool:
    """Check if verbose output is enabled."""
    return config.global_config.verbose


def is_quiet(config: Config) -> bool:
    """Check if quiet output is enabled."""
    return config.global_config.quiet


def should_use_color(config: Config) -> bool:
    """Determine if color output should be used."""
    if config.global_config.no_color:
        return False
    return config.global_config.color


def validate_cli_args(args: CLIArgs) -> tuple[bool, list[str]]:
    """Perform quick validation on CLI arguments before loading."""
    from .schema import ConfigSchema

    schema = ConfigSchema()
    result = schema.validate_cli_args(args)

    errors: list[str] = []
    for error in result.errors:
        errors.append(str(error))
    for violation in result.constitutional_violations:
        errors.append(f"CONSTITUTIONAL: {violation}")

    is_valid = len(errors) == 0
    return is_valid, errors


def get_config_version() -> str:
    """Get the current configuration system version."""
    from .defaults import SystemDefaults

    defaults = SystemDefaults()
    return defaults.CONFIG_VERSION


__version__ = "1.0.0"
__all__ = [
    "load_config",
    "get_default_config",
    "Config",
    "CommandType",
    "OutputFormat",
    "BoundaryStrictness",
    "config_to_dict",
    "describe_config",
    "is_verbose",
    "is_quiet",
    "should_use_color",
    "validate_cli_args",
    "get_config_version",
]
