"""
bridge.entry — Official human entry points for CodeMarshal.

ROLE: Declare the official human entry points and prevent:
- Shadow interfaces
- Undocumented invocation paths
- Internal-only backdoors

If a human can do something, it must pass through here.
"""

from .api import CodeMarshalAPI, create_http_server
from .cli import CodeMarshalCLI
from .cli import main as cli_main

# Public API: These are the only official entry points
__all__ = [
    # Command Line Interface
    "cli_main",
    "CodeMarshalCLI",
    # Terminal User Interface
    "launch_tui",
    "TruthPreservingTUI",
    # Desktop GUI
    "launch_gui",
    # Programmatic API
    "CodeMarshalAPI",
    "create_http_server",
    # Version information
    "__version__",
]

# Version information
__version__ = "0.1.0"
__author__ = "CodeMarshal Team"
__license__ = "MIT"


def launch_tui(*args, **kwargs):
    """Lazy TUI launcher to avoid importing curses/TUI at package import time."""
    from .tui import launch_tui as _launch_tui

    return _launch_tui(*args, **kwargs)


def launch_gui(*args, **kwargs):
    """Lazy GUI launcher to avoid importing PySide6 at package import time."""
    from .gui import launch_gui as _launch_gui

    return _launch_gui(*args, **kwargs)


# Import guards to prevent unauthorized access
# These modules should NOT be imported directly from outside
_PRIVATE_MODULES = {
    "bridge.entry.cli": "Use cli_main() or CodeMarshalCLI instead",
    "bridge.entry.tui": "Use launch_tui() or TruthPreservingTUI instead",
    "bridge.entry.gui": "Use launch_gui() instead",
    "bridge.entry.api": "Use CodeMarshalAPI or create_http_server instead",
}

# Constants for entry point configuration
ENTRY_POINTS = {
    "cli": {
        "function": "bridge.entry:cli_main",
        "description": "Command Line Interface for truth-preserving code investigation",
    },
    "tui": {
        "function": "bridge.entry:launch_tui",
        "description": "Terminal User Interface for guided investigation",
    },
    "gui": {
        "function": "bridge.entry:launch_gui",
        "description": "Desktop GUI for single-focus investigation",
    },
    "api": {
        "class": "bridge.entry:CodeMarshalAPI",
        "description": "Programmatic API for integration with other tools",
    },
}


# Utility function to get available entry points
def get_entry_points() -> dict:
    """
    Return information about all available entry points.

    Returns:
        Dictionary containing entry point metadata.
    """
    return ENTRY_POINTS.copy()


def validate_entry_point(entry_point: str) -> bool:
    """
    Validate that an entry point exists and is accessible.

    Args:
        entry_point: Name of entry point to validate.

    Returns:
        True if entry point is valid, False otherwise.

    Raises:
        ImportError: If entry point cannot be imported.
    """
    if entry_point not in ENTRY_POINTS:
        return False

    try:
        if entry_point == "cli":
            # Verify CLI is importable
            from .cli import main

            return callable(main)
        elif entry_point == "tui":
            # Verify TUI is importable
            from .tui import launch_tui

            return callable(launch_tui)
        elif entry_point == "gui":
            from .gui import launch_gui

            return callable(launch_gui)
        elif entry_point == "api":
            # Verify API is importable
            from .api import CodeMarshalAPI

            return CodeMarshalAPI is not None
    except ImportError as e:
        raise ImportError(f"Entry point '{entry_point}' is not accessible: {e}") from e

    return False


class EntryPointRegistry:
    """
    Registry of all official entry points.

    This ensures that:
    1. No entry point is added without being declared
    2. All entry points follow constitutional constraints
    3. Entry points cannot be bypassed
    """

    _registry: dict = {}

    @classmethod
    def register(cls, name: str, function=None, description: str = ""):
        """
        Register an official entry point.

        Args:
            name: Unique name for the entry point
            function: Callable that implements the entry point
            description: Human-readable description

        Raises:
            ValueError: If entry point already exists or name is invalid
        """
        if not name or not isinstance(name, str):
            raise ValueError(f"Invalid entry point name: {name}")

        if name in cls._registry:
            raise ValueError(f"Entry point already registered: {name}")

        if function and not callable(function):
            raise ValueError(f"Entry point must be callable: {name}")

        cls._registry[name] = {
            "function": function,
            "description": description,
            "registered_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ),
        }

    @classmethod
    def get(cls, name: str):
        """
        Get a registered entry point.

        Args:
            name: Name of entry point to retrieve

        Returns:
            Registered entry point information

        Raises:
            KeyError: If entry point is not registered
        """
        if name not in cls._registry:
            raise KeyError(f"Entry point not registered: {name}")
        return cls._registry[name]

    @classmethod
    def list(cls) -> list:
        """
        List all registered entry points.

        Returns:
            List of entry point names in registration order
        """
        return list(cls._registry.keys())

    @classmethod
    def validate_all(cls) -> bool:
        """
        Validate all registered entry points.

        Returns:
            True if all entry points are valid, False otherwise
        """
        for name in cls._registry:
            entry = cls._registry[name]
            if entry["function"] and not callable(entry["function"]):
                return False
        return True


# Register the official entry points on module import
try:
    # Register CLI entry point
    from .cli import main as cli_main_func

    EntryPointRegistry.register(
        name="cli",
        function=cli_main_func,
        description="Command Line Interface: Explicit, contract-based interaction",
    )

    # Register TUI entry point (lazy wrapper)
    launch_tui_func = launch_tui
    EntryPointRegistry.register(
        name="tui",
        function=launch_tui_func,
        description="Terminal User Interface: Guided, linear investigation",
    )

    # Register GUI entry point (lazy wrapper)
    launch_gui_func = launch_gui
    EntryPointRegistry.register(
        name="gui",
        function=launch_gui_func,
        description="Desktop GUI: Single-focus, local-only investigation",
    )

    # Register API entry point
    from .api import CodeMarshalAPI as APIClass

    EntryPointRegistry.register(
        name="api",
        function=APIClass,
        description="Programmatic API: Strict, schema-based programmatic access",
    )

except ImportError as e:
    # Log but don't fail - allows for partial installation
    import logging

    logging.getLogger(__name__).warning(f"Failed to register entry points: {e}")


# Security: Prevent direct import of internal modules
def __getattr__(name: str):
    """
    Prevent access to non-public attributes.

    This enforces that only items in __all__ are accessible.
    """
    if name in _PRIVATE_MODULES:
        raise AttributeError(f"Module '{name}' is private. {_PRIVATE_MODULES[name]}")
    if name == "TruthPreservingTUI":
        from .tui import TruthPreservingTUI as _TruthPreservingTUI

        return _TruthPreservingTUI
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


# Export validation
_EXPORTED_SYMBOLS = set(__all__)


def _validate_exports():
    """Validate that all exported symbols exist and are accessible."""
    # Symbols that are lazy-loaded via __getattr__ and don't exist in globals() at import time
    LAZY_SYMBOLS = {"TruthPreservingTUI"}

    missing = []
    for symbol in _EXPORTED_SYMBOLS:
        if symbol in LAZY_SYMBOLS:
            continue  # Skip validation for lazy-loaded symbols
        if symbol not in globals():
            missing.append(symbol)

    if missing:
        raise ImportError(
            f"Module '{__name__}' exports non-existent symbols: {missing}"
        )


# Run validation on import
_validate_exports()


# Documentation for developers
_DEVELOPER_NOTES = """
CONSTITUTIONAL CONSTRAINTS FOR ENTRY POINTS:

1. NO INFERENCE: Entry points must not guess user intent.
2. NO MAGIC: Every action must be explicit and deliberate.
3. NO SHORTCUTS: Entry points cannot bypass the command layer.
4. NO LEAKS: Entry points cannot access truth directly.

Each entry point must:
- Accept human input
- Make intent explicit
- Call exactly one command
- Surface refusal or success honestly

Entry points are NOT ALLOWED to:
- Perform logic beyond argument validation
- Decide what command to run
- Suppress refusal or uncertainty
- Retry silently

If you need a new entry point:
1. Add it to bridge/entry/
2. Register it in EntryPointRegistry
3. Add it to __all__
4. Document its constitutional compliance
"""


# Example usage patterns (for documentation)
_USAGE_EXAMPLES = """
EXAMPLE USAGE PATTERNS:

1. CLI (from command line):
   $ codemarshal investigate /path/to/code --scope=project --intent=initial_scan

2. CLI (programmatically):
   from bridge.entry import CodeMarshalCLI
   cli = CodeMarshalCLI()
   exit_code = cli.run(["investigate", "/path/to/code", "--scope=project"])

3. TUI (from command line):
   $ codemarshal-tui /path/to/code

4. TUI (programmatically):
   from bridge.entry import launch_tui
   from pathlib import Path
   launch_tui(Path("/path/to/code"))

5. API (programmatically):
   from bridge.entry import CodeMarshalAPI
   from bridge.entry.api import InvestigateRequest
   api = CodeMarshalAPI()
   request = InvestigateRequest(path="/path/to/code", scope="project", intent="initial_scan")
   response = api.investigate(request)

6. HTTP Server (optional):
   from bridge.entry import create_http_server
   app, host, port = create_http_server()
   app.run(host=host, port=port, debug=True)

7. Desktop GUI (from command line):
   $ codemarshal gui /path/to/code
"""
