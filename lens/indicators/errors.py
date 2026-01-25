"""
errors.py — Failure Without Drama

Defines error signaling semantics—not messages, not stack traces.

This file decides:
- How serious a failure is
- Whether continuation is allowed
- Whether recovery is possible

Nothing else.

Strict Rules:
- No user advice ❌
- No technical detail ❌
- No blame language ❌
- No auto-dismiss ❌
- Errors are statements of state, not conversations
"""

import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, ClassVar

# Import from allowed modules only
from lens.aesthetic.palette import SemanticColor as Color
from lens.aesthetic.typography import Glyph
from lens.philosophy.clarity import RequirementLevel


class ErrorSeverity(Enum):
    """
    Finite set of error severity levels.

    Severity is operational, not emotional. Each level defines:
    - Whether continuation is allowed
    - Whether recovery is possible
    - Required human attention level
    """

    INFORMATIONAL = auto()  # Something happened, but system continues
    RECOVERABLE = auto()  # Failure occurred, but system can retry/continue
    BLOCKING = auto()  # Cannot continue current operation
    INTEGRITY_VIOLATION = auto()  # System integrity compromised, must halt
    UNKNOWN = auto()  # State cannot be classified, maximum caution

    # --- Severity Ordering (Operational, Not Emotional) ---
    def __lt__(self, other: "ErrorSeverity") -> bool:
        order = list(ErrorSeverity)
        return order.index(self) < order.index(other)

    @property
    def indicator(self) -> str:
        """Get uncertainty indicator for this severity."""
        return {
            ErrorSeverity.INFORMATIONAL: "ℹ️",
            ErrorSeverity.RECOVERABLE: "⚠️",
            ErrorSeverity.BLOCKING: "🚫",
            ErrorSeverity.INTEGRITY_VIOLATION: "❌",
            ErrorSeverity.UNKNOWN: "❓",
        }.get(self, "❓")

    def __le__(self, other: "ErrorSeverity") -> bool:
        order = list(ErrorSeverity)
        return order.index(self) <= order.index(other)

    # --- Operational Properties ---
    @property
    def can_continue(self) -> bool:
        """Whether system can continue processing after this error."""
        return self in {ErrorSeverity.INFORMATIONAL, ErrorSeverity.RECOVERABLE}

    @property
    def can_recover(self) -> bool:
        """Whether automatic recovery is possible."""
        return self == ErrorSeverity.RECOVERABLE

    @property
    def requires_halt(self) -> bool:
        """Whether system must halt immediately."""
        return self == ErrorSeverity.INTEGRITY_VIOLATION

    @property
    def description(self) -> str:
        """Operational description of severity."""
        descriptions = {
            ErrorSeverity.INFORMATIONAL: "System continues normally",
            ErrorSeverity.RECOVERABLE: "System can retry or use fallback",
            ErrorSeverity.BLOCKING: "Current operation cannot continue",
            ErrorSeverity.INTEGRITY_VIOLATION: "System integrity compromised",
            ErrorSeverity.UNKNOWN: "Error state cannot be classified",
        }
        return descriptions[self]

    @property
    def required_attention_level(self) -> RequirementLevel:
        """Required human attention level for this severity."""
        mapping = {
            ErrorSeverity.INFORMATIONAL: RequirementLevel.INFORMATIONAL,
            ErrorSeverity.RECOVERABLE: RequirementLevel.ATTENTION,
            ErrorSeverity.BLOCKING: RequirementLevel.ACTION,
            ErrorSeverity.INTEGRITY_VIOLATION: RequirementLevel.CRITICAL,
            ErrorSeverity.UNKNOWN: RequirementLevel.ACTION,
        }
        return mapping[self]


class ErrorCategory(Enum):
    """
    Finite set of error categories.

    Categories describe the type of failure, not the cause.
    They are mutually exclusive and collectively exhaustive.
    """

    OBSERVATION_FAILED = auto()  # Cannot observe/read
    VALIDATION_FAILED = auto()  # Data violates constraints
    INTEGRITY_FAILED = auto()  # Truth preservation compromised
    RESOURCE_FAILED = auto()  # Missing/insufficient resources
    BOUNDARY_VIOLATION = auto()  # Architectural boundary crossed
    UNCLASSIFIED = auto()  # Cannot be categorized

    @property
    def description(self) -> str:
        """What failed, not why."""
        descriptions = {
            ErrorCategory.OBSERVATION_FAILED: "Could not observe reality",
            ErrorCategory.VALIDATION_FAILED: "Data violates system constraints",
            ErrorCategory.INTEGRITY_FAILED: "Truth preservation compromised",
            ErrorCategory.RESOURCE_FAILED: "Required resource unavailable",
            ErrorCategory.BOUNDARY_VIOLATION: "Architectural boundary violation",
            ErrorCategory.UNCLASSIFIED: "Failure type unknown",
        }
        return descriptions[self]


@dataclass(frozen=True)
class ErrorIndicator:
    """
    Immutable representation of an error indicator.

    Frozen to prevent mutation. Contains only what is needed to:
    1. Determine severity
    2. Decide continuation
    3. Signal to user

    No explanations, no suggestions, no causes.
    """

    # --- Core Error State (Required) ---
    severity: ErrorSeverity
    category: ErrorCategory

    # --- Context (What, Not Why) ---
    affected_component: str | None = None
    """Which component reported the error, not why it failed."""

    timestamp: float = field(default_factory=time.time)
    """When error occurred, for sequencing only."""

    # --- Display Properties ---
    display_color: Color = field(init=False)
    display_glyph: Glyph = field(init=False)

    # --- State-to-Display Mapping ---
    _COLOR_MAP: ClassVar[dict[ErrorSeverity, Color]] = {
        ErrorSeverity.INFORMATIONAL: Color.NEUTRAL,
        ErrorSeverity.RECOVERABLE: Color.WARNING,
        ErrorSeverity.BLOCKING: Color.ATTENTION,
        ErrorSeverity.INTEGRITY_VIOLATION: Color.CRITICAL,
        ErrorSeverity.UNKNOWN: Color.WARNING,
    }

    _GLYPH_MAP: ClassVar[dict[ErrorSeverity, Glyph]] = {
        ErrorSeverity.INFORMATIONAL: Glyph.WARNING,
        ErrorSeverity.RECOVERABLE: Glyph.WARNING,
        ErrorSeverity.BLOCKING: Glyph.ERROR,
        ErrorSeverity.INTEGRITY_VIOLATION: Glyph.STOP,
        ErrorSeverity.UNKNOWN: Glyph.QUESTION,
    }

    def __post_init__(self) -> None:
        """Set display properties based on severity after initialization."""
        # Use object.__setattr__ for frozen dataclass
        object.__setattr__(self, "display_color", self._COLOR_MAP[self.severity])
        object.__setattr__(self, "display_glyph", self._GLYPH_MAP[self.severity])

        # Validate category/severity consistency
        if self.category == ErrorCategory.INTEGRITY_FAILED:
            if self.severity != ErrorSeverity.INTEGRITY_VIOLATION:
                raise ValueError(
                    "INTEGRITY_FAILED category must have INTEGRITY_VIOLATION severity"
                )

    # --- Operational Properties ---

    @property
    def requires_action(self) -> RequirementLevel:
        """What level of human attention is required."""
        return self.severity.required_attention_level

    @property
    def can_continue_operations(self) -> bool:
        """Whether system can continue processing."""
        return self.severity.can_continue

    @property
    def allows_recovery(self) -> bool:
        """Whether automatic recovery is permitted."""
        return self.severity.can_recover

    @property
    def must_halt_system(self) -> bool:
        """Whether system must halt immediately."""
        return self.severity.requires_halt

    # --- Factory Methods ---

    @classmethod
    def create_observation_failed(
        cls,
        severity: ErrorSeverity = ErrorSeverity.BLOCKING,
        affected_component: str | None = None,
    ) -> "ErrorIndicator":
        """Create observation failed error."""
        if severity == ErrorSeverity.INTEGRITY_VIOLATION:
            severity = ErrorSeverity.BLOCKING  # Downgrade - observation ≠ integrity

        return cls(
            severity=severity,
            category=ErrorCategory.OBSERVATION_FAILED,
            affected_component=affected_component,
        )

    @classmethod
    def create_validation_failed(
        cls,
        severity: ErrorSeverity = ErrorSeverity.BLOCKING,
        affected_component: str | None = None,
    ) -> "ErrorIndicator":
        """Create validation failed error."""
        return cls(
            severity=severity,
            category=ErrorCategory.VALIDATION_FAILED,
            affected_component=affected_component,
        )

    @classmethod
    def create_integrity_violation(
        cls, affected_component: str | None = None
    ) -> "ErrorIndicator":
        """Create integrity violation error (must halt)."""
        return cls(
            severity=ErrorSeverity.INTEGRITY_VIOLATION,
            category=ErrorCategory.INTEGRITY_FAILED,
            affected_component=affected_component,
        )

    @classmethod
    def create_resource_failed(
        cls,
        severity: ErrorSeverity = ErrorSeverity.BLOCKING,
        affected_component: str | None = None,
    ) -> "ErrorIndicator":
        """Create resource failed error."""
        return cls(
            severity=severity,
            category=ErrorCategory.RESOURCE_FAILED,
            affected_component=affected_component,
        )

    @classmethod
    def create_boundary_violation(
        cls,
        severity: ErrorSeverity = ErrorSeverity.BLOCKING,
        affected_component: str | None = None,
    ) -> "ErrorIndicator":
        """Create boundary violation error."""
        return cls(
            severity=severity,
            category=ErrorCategory.BOUNDARY_VIOLATION,
            affected_component=affected_component,
        )

    @classmethod
    def create_unknown(cls, affected_component: str | None = None) -> "ErrorIndicator":
        """Create unknown error (maximum caution)."""
        return cls(
            severity=ErrorSeverity.UNKNOWN,
            category=ErrorCategory.UNCLASSIFIED,
            affected_component=affected_component,
        )

    # --- Serialization ---

    def to_dict(self) -> dict[str, Any]:
        """Export error state for logging or persistence."""
        return {
            "severity": self.severity.name,
            "severity_description": self.severity.description,
            "category": self.category.name,
            "category_description": self.category.description,
            "affected_component": self.affected_component,
            "timestamp": self.timestamp,
            "requires_action": self.requires_action.name,
            "can_continue": self.can_continue_operations,
            "allows_recovery": self.allows_recovery,
            "must_halt": self.must_halt_system,
            "display_color": self.display_color.name,
            "display_glyph": self.display_glyph.name,
            "uncertainty_indicator": self.severity.indicator,
        }

    @property
    def display_message(self) -> str:
        """Get display message with uncertainty indicator."""
        return f"{self.severity.indicator} {self.category.description}"


# --- Error Collection (For Batch Processing) ---


@dataclass
class ErrorCollection:
    """
    Collection of errors for batch processing.

    Maintains errors in chronological order and provides
    aggregate severity assessment.
    """

    errors: list[ErrorIndicator] = field(default_factory=list)

    def add(self, error: ErrorIndicator) -> None:
        """Add error to collection."""
        self.errors.append(error)

    def clear(self) -> None:
        """Clear all errors."""
        self.errors.clear()

    @property
    def has_errors(self) -> bool:
        """Whether any errors exist."""
        return len(self.errors) > 0

    @property
    def highest_severity(self) -> ErrorSeverity | None:
        """Highest severity error in collection."""
        if not self.errors:
            return None
        return max(error.severity for error in self.errors)

    @property
    def must_halt(self) -> bool:
        """Whether any error requires system halt."""
        return any(error.must_halt_system for error in self.errors)

    @property
    def can_continue(self) -> bool:
        """Whether system can continue despite errors."""
        if self.must_halt:
            return False
        return all(error.can_continue_operations for error in self.errors)

    @property
    def requires_action(self) -> RequirementLevel:
        """Highest required action level."""
        if not self.errors:
            return RequirementLevel.NONE

        highest = max(error.requires_action for error in self.errors)
        return highest

    def get_by_category(self, category: ErrorCategory) -> list[ErrorIndicator]:
        """Get all errors of specific category."""
        return [error for error in self.errors if error.category == category]

    def get_by_severity(self, severity: ErrorSeverity) -> list[ErrorIndicator]:
        """Get all errors of specific severity."""
        return [error for error in self.errors if error.severity == severity]

    def to_dict(self) -> list[dict[str, Any]]:
        """Export all errors for serialization."""
        return [error.to_dict() for error in self.errors]


# --- Validation Functions ---


def validate_no_explanations(error: ErrorIndicator) -> bool:
    """
    Ensure error contains no explanations or suggestions.

    Returns True if error complies with truth-preserving rules.
    """
    # Rule: No user advice
    # (Implicitly enforced by data structure - no advice field)

    # Rule: No technical detail
    # (Implicitly enforced by data structure - no detail field)

    # Rule: No blame language in component name
    if error.affected_component:
        blame_terms = ["failed", "broken", "wrong", "incorrect", "bad"]
        component_lower = error.affected_component.lower()
        if any(term in component_lower for term in blame_terms):
            return False

    # Rule: Unknown errors cannot claim to know category
    if error.severity == ErrorSeverity.UNKNOWN:
        if error.category != ErrorCategory.UNCLASSIFIED:
            return False

    return True


def determine_continuation(errors: ErrorCollection) -> bool:
    """
    Determine if system can continue given current errors.

    Used by core runtime to decide whether to proceed.
    """
    if errors.must_halt:
        return False

    return errors.can_continue


# --- Global Defaults ---

NO_ERROR = ErrorIndicator(
    severity=ErrorSeverity.INFORMATIONAL, category=ErrorCategory.UNCLASSIFIED
)
"""Default no-error state."""

ERROR_SEVERITY_ORDER = list(ErrorSeverity)
"""Definitive severity ordering."""

# --- Mandatory Visibility Rules ---


def get_display_rules(error: ErrorIndicator) -> dict[str, Any]:
    """
    Get mandatory display rules for an error.

    Used by interface to determine how to show errors.
    """
    rules = {
        ErrorSeverity.INFORMATIONAL: {
            "must_show": False,
            "can_dismiss": True,
            "interrupts": False,
            "persists": False,
        },
        ErrorSeverity.RECOVERABLE: {
            "must_show": True,
            "can_dismiss": False,  # User must acknowledge
            "interrupts": False,
            "persists": True,  # Until acknowledged
        },
        ErrorSeverity.BLOCKING: {
            "must_show": True,
            "can_dismiss": False,
            "interrupts": True,  # Interrupt current workflow
            "persists": True,  # Until resolved
        },
        ErrorSeverity.INTEGRITY_VIOLATION: {
            "must_show": True,
            "can_dismiss": False,
            "interrupts": True,  # Force interruption
            "persists": True,  # Cannot be dismissed
        },
        ErrorSeverity.UNKNOWN: {
            "must_show": True,
            "can_dismiss": False,
            "interrupts": True,  # Maximum caution
            "persists": True,  # Until resolved
        },
    }

    base_rules = rules[error.severity]

    # Integrity violations cannot be dismissed at all
    if error.severity == ErrorSeverity.INTEGRITY_VIOLATION:
        base_rules["can_dismiss"] = False

    return base_rules
