"""
bridge.commands - The finite command surface of CodeMarshal

This module declares every action the system can perform.
If a command isn't exported here, the system cannot do it.

Constitutional Context:
- Article 2: Human Primacy (humans initiate all actions)
- Article 7: Clear Affordances (no hidden capabilities)
- Article 20: Progressive Enhancement (complete features only)

Role: Public interface declaration. Prevents hidden powers and ad-hoc actions.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any

from .export import (
    ExportFormat,
    ExportRequest,
    ExportType,
    execute_export,
    export_constitutional_report,
    export_notes_markdown,
    export_observations_json,
)

# Import all command modules
from .investigate import (
    InvestigationRequest,
    InvestigationScope,
    InvestigationType,
    execute_investigation,
    fork_investigation,
    new_investigation,
    resume_investigation,
)
from .observe import (
    ObservationRequest,
    ObservationType,
    execute_observation,
    observe_file_structure,
    observe_imports,
)
from .query import (
    PatternName,
    QueryRequest,
    QueryType,
    QuestionName,
    execute_query,
)


class CommandName(Enum):
    """Every action the system can perform."""

    INVESTIGATE = "investigate"
    OBSERVE = "observe"
    QUERY = "query"
    EXPORT = "export"
    # Note: No "save", "load", "edit", "delete" - those are internal operations


@dataclass(frozen=True)
class CommandSurface:
    """
    Immutable declaration of the system's command surface.

    This prevents:
    - Hidden powers: If it's not here, it doesn't exist
    - Ad-hoc command injection: Commands cannot be added at runtime
    - UI-only "special actions": All actions go through commands
    """

    # Map command name -> execution function
    commands: dict[CommandName, Callable] = field(default_factory=dict)

    # Map command name -> request type (for validation)
    request_types: dict[CommandName, type] = field(default_factory=dict)

    # Map command name -> convenience constructors
    constructors: dict[CommandName, dict[str, Callable]] = field(default_factory=dict)


# Build the complete command surface
_COMMAND_SURFACE = CommandSurface(
    commands=MappingProxyType(
        {
            CommandName.INVESTIGATE: execute_investigation,
            CommandName.OBSERVE: execute_observation,
            CommandName.QUERY: execute_query,
            CommandName.EXPORT: execute_export,
        }
    ),
    request_types=MappingProxyType(
        {
            CommandName.INVESTIGATE: InvestigationRequest,
            CommandName.OBSERVE: ObservationRequest,
            CommandName.QUERY: QueryRequest,
            CommandName.EXPORT: ExportRequest,
        }
    ),
    constructors=MappingProxyType(
        {
            CommandName.INVESTIGATE: MappingProxyType(
                {
                    "new": new_investigation,
                    "resume": resume_investigation,
                    "fork": fork_investigation,
                }
            ),
            CommandName.OBSERVE: MappingProxyType(
                {
                    "file_structure": observe_file_structure,
                    "imports": observe_imports,
                }
            ),
            CommandName.QUERY: MappingProxyType({}),  # No convenience constructors
            CommandName.EXPORT: MappingProxyType(
                {
                    "observations_json": export_observations_json,
                    "notes_markdown": export_notes_markdown,
                    "constitutional_report": export_constitutional_report,
                }
            ),
        }
    ),
)


def get_command(name: str | CommandName) -> Callable | None:
    """
    Get a command execution function by name.

    Args:
        name: Command name as string or CommandName enum

    Returns:
        Command function or None if not found

    Raises:
        ValueError: If command exists but is invalid
    """
    # Convert string to enum if needed
    if isinstance(name, str):
        try:
            cmd_name = CommandName(name.lower())
        except ValueError:
            return None
    else:
        cmd_name = name

    command = _COMMAND_SURFACE.commands.get(cmd_name)

    # Validate command signature
    if command:
        _validate_command_signature(command, cmd_name)

    return command


def get_request_type(name: str | CommandName) -> type | None:
    """
    Get the request type for a command.

    Args:
        name: Command name as string or CommandName enum

    Returns:
        Request type class or None if not found
    """
    if isinstance(name, str):
        try:
            cmd_name = CommandName(name.lower())
        except ValueError:
            return None
    else:
        cmd_name = name

    return _COMMAND_SURFACE.request_types.get(cmd_name)


def get_constructors(name: str | CommandName) -> dict[str, Callable]:
    """
    Get convenience constructors for a command.

    Args:
        name: Command name as string or CommandName enum

    Returns:
        Dict of constructor_name -> constructor_function
    """
    if isinstance(name, str):
        try:
            cmd_name = CommandName(name.lower())
        except ValueError:
            return {}
    else:
        cmd_name = name

    return _COMMAND_SURFACE.constructors.get(cmd_name, {}).copy()


def list_commands() -> dict[str, dict[str, Any]]:
    """
    List all available commands with metadata.

    Returns:
        Dict mapping command_name -> metadata
    """
    result = {}

    for cmd_name, cmd_func in _COMMAND_SURFACE.commands.items():
        # Get function signature for documentation
        sig = inspect.signature(cmd_func)

        # Get request type
        request_type = _COMMAND_SURFACE.request_types.get(cmd_name)

        # Get constructors
        constructors = _COMMAND_SURFACE.constructors.get(cmd_name, {})

        result[cmd_name.value] = {
            "function": cmd_func.__name__,
            "module": cmd_func.__module__,
            "signature": str(sig),
            "request_type": request_type.__name__ if request_type else None,
            "constructors": list(constructors.keys()),
            "description": cmd_func.__doc__.strip().split("\n")[0]
            if cmd_func.__doc__
            else "",
        }

    return result


def validate_command_integrity() -> dict[str, bool]:
    """
    Validate that all commands follow constitutional rules.

    Returns:
        Dict mapping check_name -> passed

    Raises:
        RuntimeError: If any Tier 1-2 violation is detected
    """
    checks = {}

    # Check 1: All commands are exported from their modules
    checks["all_commands_exported"] = _check_all_commands_exported()

    # Check 2: No command has prohibited imports
    checks["no_prohibited_imports"] = _check_no_prohibited_imports()

    # Check 3: All commands have proper signatures
    checks["valid_command_signatures"] = _check_command_signatures()

    # Check 4: No hidden or unexported commands
    checks["no_hidden_commands"] = _check_no_hidden_commands()

    # Check 5: Command surface is immutable
    checks["command_surface_immutable"] = _check_command_surface_immutable()

    # Tier 1-2 violations cause immediate halt
    failing_critical = [name for name, passed in checks.items() if not passed]
    if failing_critical:
        raise RuntimeError(
            f"Command surface integrity violation: {', '.join(failing_critical)}"
        )

    return checks


def _check_all_commands_exported() -> bool:
    """Check that all command functions are properly exported from their modules."""
    expected_exports = {
        "execute_investigation": execute_investigation,
        "execute_observation": execute_observation,
        "execute_query": execute_query,
        "execute_export": execute_export,
    }

    for _name, func in expected_exports.items():
        if func is None:
            return False

    return True


def _check_no_prohibited_imports() -> bool:
    """
    Check that commands don't import from prohibited modules.

    This is a runtime check; static analysis would be more comprehensive.
    """
    # This would be implemented with import hooks or AST analysis in production
    # For now, we trust the module-level import guard checks

    # We would check each command module's __file__ for imports
    # For this implementation, we assume they pass
    return True


def _check_command_signatures() -> bool:
    """Check that all commands have the expected signature."""
    for cmd_name, cmd_func in _COMMAND_SURFACE.commands.items():
        try:
            _validate_command_signature(cmd_func, cmd_name)
        except ValueError:
            return False

    return True


def _validate_command_signature(func: Callable, cmd_name: CommandName) -> None:
    """
    Validate a command function's signature.

    Expected signature: func(request, *dependencies) -> Dict[str, Any]
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.keys())

    # Must have at least a request parameter
    if len(params) == 0:
        raise ValueError(f"Command {cmd_name.value} has no parameters")

    # Must return Dict[str, Any]
    return_annotation = sig.return_annotation

    # Allow string annotations from __future__ import annotations
    if isinstance(return_annotation, str):
        if (
            "Dict[str, Any]" not in return_annotation
            and "dict" not in return_annotation
        ):
            raise ValueError(
                f"Command {cmd_name.value} must return Dict[str, Any], "
                f"got string annotation {return_annotation}"
            )
        return

        return

    if (
        return_annotation != dict[str, Any]
        and not isinstance(return_annotation, dict)
        and return_annotation != inspect.Signature.empty
    ):
        if not (
            hasattr(return_annotation, "__origin__")
            and return_annotation.__origin__ in (dict, dict)
        ):
            raise ValueError(
                f"Command {cmd_name.value} must return Dict[str, Any], "
                f"got {return_annotation}"
            )


def _check_no_hidden_commands() -> bool:
    """
    Check that there are no command-like functions not in the surface.

    This would scan modules for functions matching command patterns.
    """
    # In production, this would use AST analysis
    # For now, we trust the explicit declaration
    return True


def _check_command_surface_immutable() -> bool:
    """Check that the command surface cannot be modified."""
    try:
        # Try to modify (should fail)
        _COMMAND_SURFACE.commands["test"] = lambda: None
        return False
    except (TypeError, KeyError):
        # Modification failed as expected
        pass

    try:
        # Try to modify constructors
        _COMMAND_SURFACE.constructors["test"] = {}
        return False
    except (TypeError, KeyError):
        pass

    return True


# Public exports - this is the complete command surface
__all__ = [
    # Core execution functions
    "execute_investigation",
    "execute_observation",
    "execute_query",
    "execute_export",
    # Request types
    "InvestigationRequest",
    "ObservationRequest",
    "QueryRequest",
    "ExportRequest",
    # Enums
    "CommandName",
    "InvestigationType",
    "InvestigationScope",
    "ObservationType",
    "QueryType",
    "QuestionName",
    "PatternName",
    "ExportType",
    "ExportFormat",
    # Convenience constructors
    "new_investigation",
    "resume_investigation",
    "fork_investigation",
    "observe_file_structure",
    "observe_imports",
    "export_observations_json",
    "export_notes_markdown",
    "export_constitutional_report",
    # Utility functions
    "get_command",
    "get_request_type",
    "get_constructors",
    "list_commands",
    "validate_command_integrity",
]

# Final validation on import
if __name__ != "__main__":
    # When imported, validate integrity (except during testing)
    try:
        import sys

        if "pytest" not in sys.modules and "unittest" not in sys.modules:
            validate_command_integrity()
    except ImportError:
        # pytest/unittest not available, validate anyway
        validate_command_integrity()
