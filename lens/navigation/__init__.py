"""
lens/navigation/__init__.py

CRITICAL ARCHITECTURAL BOUNDARY: Navigation Subsystem Public Interface
======================================================================
This file defines the canonical navigation contract for the system.

This prevents:
- Shadow navigation logic
- Per-view rule drift
- Ad-hoc shortcuts
- Hidden recovery paths

If a navigation construct isn't exported here, it doesn't exist.

CONSTITUTIONAL RULES ENFORCED:
- Article 4: Progressive Disclosure (workflow enforces stages)
- Article 6: Linear Investigation (canonical sequence only)
- Article 7: Clear Affordances (explicit available actions)
- Article 14: Graceful Degradation (visible recovery paths)

ALLOWED IMPORTS:
- Only from lens.navigation.* modules
- No computation
- No logic
- No defaults

PROHIBITED:
- Any imports from outside lens.navigation
- Function definitions
- Class definitions
- Default instantiations
"""

# -------------------------------------------------------------------
# WORKFLOW COMPONENTS (The Lawful Path)
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# NAVIGATION CONTEXT (Compass Bearing)
# -------------------------------------------------------------------
from .context import (
    FocusType,
    NavigationContext,
    create_context_from_workflow_state,
    create_initial_navigation_context,
    create_navigation_context,
    get_context_summary,
    validate_navigation_context_integrity,
)

# -------------------------------------------------------------------
# RECOVERY COMPONENTS (Failure Without Fiction)
# -------------------------------------------------------------------
from .recovery import (
    NavigationFailure,
    NavigationFailureDetector,
    RecoveryPath,
    RecoveryRegistry,
    get_recovery_system_summary,
    validate_recovery_system_integrity,
)

# -------------------------------------------------------------------
# SHORTCUT COMPONENTS (Constrained Exceptions)
# -------------------------------------------------------------------
from .shortcuts import (
    Shortcut,
    ShortcutRegistry,
    ShortcutType,
    get_shortcut_constitutional_rules,
    validate_shortcuts_integrity,
)
from .workflow import (
    Step,
    WorkflowEngine,
    WorkflowNavigator,
    WorkflowStage,
    WorkflowState,
    WorkflowTransition,
    get_canonical_workflow_description,
    validate_workflow_integrity,
)

# -------------------------------------------------------------------
# PUBLIC API EXPORTS
# These are the ONLY symbols available to other modules
# -------------------------------------------------------------------
__all__ = [
    # Workflow exports
    "WorkflowStage",
    "WorkflowTransition",
    "WorkflowState",
    "WorkflowEngine",
    "Step",
    "WorkflowNavigator",
    "validate_workflow_integrity",
    "get_canonical_workflow_description",
    # Shortcut exports
    "ShortcutType",
    "Shortcut",
    "ShortcutRegistry",
    "validate_shortcuts_integrity",
    "get_shortcut_constitutional_rules",
    # Navigation context exports
    "FocusType",
    "NavigationContext",
    "create_navigation_context",
    "create_initial_navigation_context",
    "create_context_from_workflow_state",
    "validate_navigation_context_integrity",
    "get_context_summary",
    # Recovery exports
    "NavigationFailure",
    "RecoveryPath",
    "RecoveryRegistry",
    "NavigationFailureDetector",
    "validate_recovery_system_integrity",
    "get_recovery_system_summary",
]


# -------------------------------------------------------------------
# BOUNDARY ENFORCEMENT
# Runtime validation to catch architectural violations
# -------------------------------------------------------------------
def _validate_navigation_boundaries() -> None:
    """
    Runtime validation of navigation boundary rules.

    Ensures:
    1. No computation defined in __init__.py
    2. All imports are from allowed modules
    3. No hidden dependencies

    Raises:
        RuntimeError: If constitutional boundaries are violated
    """
    import inspect
    import sys

    # Get this module
    this_module = sys.modules[__name__]

    # Rule 1: No functions defined in __init__.py (except validation function)
    local_functions = [
        name
        for name, obj in inspect.getmembers(this_module)
        if inspect.isfunction(obj)
        and obj.__module__ == __name__
        and name != "_validate_navigation_boundaries"
    ]

    if local_functions:
        raise RuntimeError(
            f"Constitutional violation: __init__.py defines functions: {local_functions}. "
            f"Only imports and exports allowed."
        )

    # Rule 2: No classes defined in __init__.py
    local_classes = [
        name
        for name, obj in inspect.getmembers(this_module)
        if inspect.isclass(obj) and obj.__module__ == __name__
    ]

    if local_classes:
        raise RuntimeError(
            f"Constitutional violation: __init__.py defines classes: {local_classes}. "
            f"Only imports and exports allowed."
        )

    # Rule 3: Validate imports are from allowed directories
    allowed_prefixes = {
        "lens.navigation",  # Self
        "lens.philosophy.",  # Allowed by constitution
        "lens.views.",  # Allowed by constitution
        "inquiry.session.",  # Allowed by constitution
        "typing",  # Python stdlib
        "enum",
        "dataclasses",
        "datetime",
        "uuid",
        "collections.abc",
    }

    # Check all imported modules in this namespace
    imported_modules: set[str] = set()
    for name in dir(this_module):
        try:
            obj = getattr(this_module, name)
            module = getattr(obj, "__module__", None)

            if module and module not in imported_modules:
                imported_modules.add(module)

                # Skip builtins and special cases
                if module == "builtins" or module == "types":
                    continue

                # Skip CPython internal modules (these appear in module loaders)
                cpython_internals = {
                    "_frozen_importlib",
                    "_frozen_importlib_external",
                    "_collections_abc",
                    "_weakrefset",
                    "importlib._bootstrap",
                    "importlib._bootstrap_external",
                }
                if module in cpython_internals or any(
                    module.startswith(prefix) for prefix in cpython_internals
                ):
                    continue

                # Check if module is allowed
                is_allowed = any(
                    module.startswith(prefix) or module == prefix
                    for prefix in allowed_prefixes
                )

                if not is_allowed:
                    # Try to get the actual module from import system
                    module_parts = module.split(".")
                    for i in range(len(module_parts), 0, -1):
                        prefix = ".".join(module_parts[:i])
                        if prefix in sys.modules:
                            file_path = getattr(sys.modules[prefix], "__file__", "")
                            if (
                                "site-packages" in file_path
                                or "dist-packages" in file_path
                            ):
                                # External library - violation
                                raise RuntimeError(
                                    f"Constitutional violation: {name} imported from external module: {module}. "
                                    f"Navigation may only import from: lens.*, inquiry.session.*, Python stdlib."
                                )
                            break

                    # If we get here, it's a local module but not allowed
                    raise RuntimeError(
                        f"Constitutional violation: {name} imported from prohibited module: {module}. "
                        f"Navigation may only import from: lens.*, inquiry.session.*, Python stdlib."
                    )
        except (AttributeError, TypeError):
            # Some objects don't have __module__, that's fine
            continue

    # Rule 4: Validate that all __all__ symbols exist
    for symbol in __all__:
        if not hasattr(this_module, symbol):
            raise RuntimeError(
                f"Constitutional violation: {symbol} in __all__ but not defined in module."
            )


# Run boundary validation on import
try:
    _validate_navigation_boundaries()
except RuntimeError as e:
    # Log the error but don't crash - some environments (like tests)
    # might need to import without full validation
    import warnings

    warnings.warn(
        f"Navigation boundary validation failed: {e}. "
        f"This indicates architectural drift and must be fixed.",
        RuntimeWarning,
        stacklevel=2,
    )

# -------------------------------------------------------------------
# DOCUMENTATION STRINGS
# Provide clear guidance on navigation subsystem usage
# -------------------------------------------------------------------
__doc__ = """
NAVIGATION SUBSYSTEM - Epistemic Interface Law
==============================================

PURPOSE:
Enforce Article 6: Linear Investigation and Article 9: Recoverability
at the interface level by answering: "From here, what actions are
epistemically legal?"

NAVIGATION IS NOT:
- Convenience features
- Speed optimizations
- UI shortcuts
- Hidden accelerators

NAVIGATION IS:
- The lawful path of investigative progress
- Constrained, justified exceptions
- Clear position tracking
- Visible, honest failure recovery

ARCHITECTURAL ROLE:
No component outside lens.navigation may decide:
- What comes next
- What is forbidden
- How to recover from illegal motion

If a view or command says "go here next," it must ask navigation first.

KEY COMPONENTS:

1. Workflow (workflow.py)
   The canonical investigative sequence:
   orientation → examination → connections → patterns → thinking

   This is executable law, not documentation.

2. Shortcuts (shortcuts.py)
   Emergency exits, not secret tunnels.
   Read-only backward jumps and same-stage toggles only.
   No forward skips. No hidden accelerators.

3. Navigation Context (context.py)
   A compass bearing, not a map.
   Answers: "Where am I?" not "What should I do next?"
   Enforces single-focus interface (Article 5).

4. Recovery (recovery.py)
   Failure without fiction.
   Enumerated failure types with explicit recovery destinations.
   Mandatory clarity signaling. No silent correction.

USAGE PATTERNS:

1. Starting an investigation:
   ```python
   from lens.navigation import create_initial_navigation_context

   nav_context = create_initial_navigation_context(session_context)
   ```
"""
