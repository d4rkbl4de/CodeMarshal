"""
LIMITATIONS PACKAGE - WHAT WE CANNOT SEE

Formally declare, validate, and surface known observational blind spots.
This layer does not attempt to solve limitations.
It names them, tracks them, and makes them impossible to ignore.

CORE PRINCIPLES:
1. Limitations are first-class data, not comments
2. Absence of evidence is never misrepresented as evidence of absence
3. Every snapshot must be contextualized by its limitations
4. Limits are declared, not inferred

MODULES:
- declared: Machine-readable contract of ignorance
- documented: Human-readable explanations of limits
- validation: Consistency and enforcement of honesty
"""

from __future__ import annotations

# Re-export main public API
from .declared import (
    Limitation,
    LimitationCategory,
    LimitationScope,
    get_active_limitations,
    get_limitation_by_id,
)
from .documented import (
    LimitationDoc,
    generate_full_documentation,
    get_doc_for_limitation,
    get_limitation_docs,
)
from .scope import (
    ScopeValidationResult,
    get_limitations_for_eye,
    validate_observation_scope,
)
from .validation import (
    LimitationSet,
    LimitationValidationError,
    SnapshotLimitations,
    get_validation_report,
    validate_during_snapshot,
    validate_limitations,
)

# Package version
__version__ = "0.1.0"
__all__ = [
    # From declared
    "Limitation",
    "LimitationCategory",
    "LimitationScope",
    "get_active_limitations",
    "get_limitation_by_id",
    # From documented
    "LimitationDoc",
    "get_doc_for_limitation",
    "get_limitation_docs",
    "generate_full_documentation",
    # From validation
    "LimitationSet",
    "SnapshotLimitations",
    "LimitationValidationError",
    "validate_limitations",
    "validate_during_snapshot",
    "get_validation_report",
    # From scope
    "validate_observation_scope",
    "get_limitations_for_eye",
    "ScopeValidationResult",
]
