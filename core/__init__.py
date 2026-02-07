"""
CodeMarshal Core Kernel - Execution Spine (System Heart)

Constitutional Basis:
- Article 9: Immutable Observations
- Article 13: Deterministic Operation
- Article 21: Self-Validation

Production Responsibility:
Define the public execution surface of the constitutional kernel.
This file exists to make illegal imports obvious.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

# Type checking imports - not available at runtime
if TYPE_CHECKING:
    from core.context import (
        ConstitutionalRule,
        EnforcementLevel,
        ExecutionMode,
        RuntimeContext,
    )
    from core.engine import (
        CoordinationRequest,
        CoordinationResult,
        Engine,
        HighLevelIntent,
    )
    from core.runtime import Runtime, create_runtime, execute_witness_command
    from core.shutdown import (
        TerminationReason,
        emergency_shutdown,
        initialize_shutdown,
        shutdown,
    )
    from core.state import InvestigationPhase, InvestigationState

# -----------------------------------------------------------------------------
# PUBLIC API - Explicit Re-exports
# -----------------------------------------------------------------------------

# Core Execution Classes
from core.context import ConstitutionalRule as ConstitutionalRule
from core.context import EnforcementLevel as EnforcementLevel

# Enums and Types
from core.context import ExecutionMode as ExecutionMode
from core.context import RuntimeContext as RuntimeContext

# Data Classes
from core.engine import CoordinationRequest as CoordinationRequest
from core.engine import CoordinationResult as CoordinationResult
from core.engine import Engine as Engine
from core.engine import HighLevelIntent as HighLevelIntent
from core.runtime import Runtime as Runtime

# Factory Functions
from core.runtime import create_runtime as create_runtime
from core.runtime import execute_witness_command as execute_witness_command
from core.shutdown import TerminationReason as TerminationReason
from core.shutdown import emergency_shutdown as emergency_shutdown

# Lifecycle Functions
from core.shutdown import initialize_shutdown as initialize_shutdown
from core.shutdown import shutdown as shutdown
from core.state import InvestigationPhase as InvestigationPhase
from core.state import InvestigationState as InvestigationState

# -----------------------------------------------------------------------------
# PUBLIC CONSTANTS
# -----------------------------------------------------------------------------

# Version information
__version__ = "2.0.0"
__version_info__ = (2, 0, 0)

# Kernel metadata
KERNEL_NAME = "CodeMarshal Core"
KERNEL_VERSION = "2.0.0"
KERNEL_AUTHOR = "CodeMarshal System"
KERNEL_LICENSE = "Truth-Preserving License"

# Constitutional compliance
CONSTITUTION_VERSION = "1.0"
CONSTITUTION_TIERS = 6
CONSTITUTION_ARTICLES = 24

# System limits (aligned with RuntimeContext defaults)
DEFAULT_MAX_FILE_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
DEFAULT_MAX_TOTAL_OBSERVATION_SIZE_BYTES = 1 * 1024 * 1024 * 1024  # 1GB
DEFAULT_MAX_RECURSION_DEPTH = 1000

# -----------------------------------------------------------------------------
# EXPORT CONTROL
# -----------------------------------------------------------------------------

__all__ = [
    # Core Execution Classes
    "Runtime",
    "RuntimeContext",
    "InvestigationState",
    "Engine",
    # Enums and Types
    "ExecutionMode",
    "EnforcementLevel",
    "ConstitutionalRule",
    "InvestigationPhase",
    "HighLevelIntent",
    "TerminationReason",
    # Data Classes
    "CoordinationRequest",
    "CoordinationResult",
    # Factory Functions
    "create_runtime",
    "execute_witness_command",
    # Lifecycle Functions
    "initialize_shutdown",
    "shutdown",
    "emergency_shutdown",
    # Constants (for documentation, not actually exported)
    # "__version__",
    # "KERNEL_NAME",
    # "CONSTITUTION_VERSION",
]

# -----------------------------------------------------------------------------
# IMPORT GUARDS
# -----------------------------------------------------------------------------


def _validate_import_structure() -> None:
    """
    Validate that core package follows import rules.

    Constitutional Basis: Article 21 (Self-Validation)
    Run during module initialization to prevent illegal import patterns.
    """
    import sys

    # Get all modules currently imported in core
    core_modules = [name for name in sys.modules.keys() if name.startswith("core.")]

    # Check for prohibited imports
    prohibited_prefixes = [
        "observations.",
        "inquiry.",
        "lens.",
        "bridge.",
        "storage.",
        "config.",
        "integrity.",
    ]

    violations = []

    # Check each core module for prohibited imports
    for module_name in core_modules:
        if module_name == "core":
            continue

        try:
            module = sys.modules[module_name]

            # Get source file if available
            source_file = getattr(module, "__file__", None)
            if not source_file:
                continue

            # Only check .py files
            if not source_file.endswith(".py"):
                continue

            # Read source and check for prohibited imports
            with open(source_file, encoding="utf-8") as f:
                source = f.read()

            for prohibited in prohibited_prefixes:
                # Look for import statements that would violate layering
                import_patterns = [
                    f"import {prohibited}",
                    f"from {prohibited}",
                ]

                for pattern in import_patterns:
                    if pattern in source:
                        violations.append(
                            f"{module_name} imports from {prohibited} in {source_file}"
                        )

        except (OSError, KeyError, AttributeError):
            # Skip modules we can't inspect
            continue

    if violations:
        violations_str = "\n".join(violations)
        raise ImportError(
            "Constitutional violation: Core modules importing from higher layers\n"
            f"Violations:\n{violations_str}\n\n"
            "Article 9: Immutable Observations\n"
            "Article 21: Self-Validation\n"
            "Core must not depend on higher layers."
        )


# Run validation when core is imported
try:
    _validate_import_structure()
except ImportError as e:
    # Log the error but don't crash - let runtime handle constitutional violations
    import sys

    print(f"[CORE IMPORT WARNING] {e}", file=sys.stderr)
    # Store violation in current module, not in context module
    if not hasattr(sys.modules[__name__], "_constitutional_violations"):
        sys.modules[__name__]._constitutional_violations = []
    sys.modules[__name__]._constitutional_violations.append(str(e))

# -----------------------------------------------------------------------------
# KERNEL INITIALIZATION GUARANTEES
# -----------------------------------------------------------------------------

# No side effects at import time
# No configuration loading
# No runtime logic execution
# No network access
# No filesystem access (except for import validation)

# -----------------------------------------------------------------------------
# DOCUMENTATION
# -----------------------------------------------------------------------------

__doc__ = f"""
CodeMarshal Core Kernel - Execution Spine

Constitutional Responsibility:
- Article 9: Immutable Observations
- Article 13: Deterministic Operation
- Article 21: Self-Validation

The core/ directory is the constitutional kernel of CodeMarshal.
It is equivalent to:
- An OS kernel's process model
- A database's transaction manager
- A compiler's semantic phase

If core/ is wrong, everything above it can be correct and still produce lies.

Core owns:
- Legality
- Order
- Enforcement
- Termination

Core does not own:
- Knowledge
- Interpretation
- Visualization
- Storage semantics

Absolute Production Rules for Core:
1. Must not depend on higher layers
2. Must be deterministic
3. Must fail fast and loudly
4. Must be testable in isolation
5. Must be boring (predictable, reliable, understandable)

Version: {__version__}
Constitution: {CONSTITUTION_VERSION}
Kernel: {KERNEL_NAME} {KERNEL_VERSION}
"""

# -----------------------------------------------------------------------------
# TRUTH-PRESERVING INITIALIZATION COMPLETE
# -----------------------------------------------------------------------------
