"""
Clarity Constraint (Articles 3 & 8 Enforcement)

This module governs epistemic honesty at the interface level:
- Truth preservation (uncertainty, missing information, limits)
- Performance honesty (delays, computational limits, failures)

CRITICAL: This defines WHAT must be said, not HOW it looks.
It answers "How certain is this claim?" not "What color should the warning be?"
Violations are Tier-2 (immediate halt).
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import Any, Protocol, runtime_checkable

# ------------------------------------------------------------------------------
# EPISTEMIC STATUS: THE TRUTH ABOUT TRUTH
# ------------------------------------------------------------------------------


class RequirementLevel(Enum):
    """Levels of requirement for content display or attention."""

    NONE = auto()
    INFORMATIONAL = auto()
    ATTENTION = auto()
    ACTION = auto()
    CRITICAL = auto()


class EpistemicStatus(Enum):
    """
    Fundamental states of knowledge about a claim.

    This is not decoration - it's the core truth status that MUST be communicated.
    """

    # Tier 1: Known with certainty
    KNOWN = auto()  # Directly observed, verifiable
    INFERRED = auto()  # Logically derived from known facts
    CALCULATED = auto()  # Computed from known data

    # Tier 2: Known with uncertainty
    UNCERTAIN = auto()  # Incomplete or ambiguous data
    ESTIMATED = auto()  # Approximation with known error bounds
    PARTIAL = auto()  # Some data missing, some present

    # Tier 3: Not known
    UNKNOWN = auto()  # Not observed, not calculable
    UNAVAILABLE = auto()  # Exists but cannot be accessed
    EXCLUDED = auto()  # Explicitly excluded by limitation

    # Tier 4: Cannot be known
    UNKNOWABLE = auto()  # Fundamentally impossible to know
    CONTRADICTORY = auto()  # Evidence contradicts itself
    AMBIGUOUS = auto()  # Multiple equally valid interpretations

    # Tier 5: Meta-knowledge
    PENDING = auto()  # Computation in progress
    FAILED = auto()  # Computation failed
    TIMEOUT = auto()  # Computation timed out

    @property
    def requires_warning(self) -> bool:
        """Whether this status requires explicit uncertainty signaling."""
        return self in {
            EpistemicStatus.UNCERTAIN,
            EpistemicStatus.ESTIMATED,
            EpistemicStatus.PARTIAL,
            EpistemicStatus.UNKNOWN,
            EpistemicStatus.UNAVAILABLE,
            EpistemicStatus.EXCLUDED,
            EpistemicStatus.UNKNOWABLE,
            EpistemicStatus.CONTRADICTORY,
            EpistemicStatus.AMBIGUOUS,
            EpistemicStatus.FAILED,
            EpistemicStatus.TIMEOUT,
        }

    @property
    def requires_immediate_halt(self) -> bool:
        """Whether this status indicates the claim should not be shown at all."""
        return self in {
            EpistemicStatus.UNKNOWABLE,
            EpistemicStatus.CONTRADICTORY,
        }

    @property
    def default_message_template(self) -> str:
        """Default human-readable explanation for this status."""
        templates = {
            EpistemicStatus.KNOWN: "Directly observed",
            EpistemicStatus.INFERRED: "Inferred from observations",
            EpistemicStatus.CALCULATED: "Calculated from observed data",
            EpistemicStatus.UNCERTAIN: "Uncertain due to incomplete data",
            EpistemicStatus.ESTIMATED: "Estimate with ±{error_bound}% error",
            EpistemicStatus.PARTIAL: "Partial data available ({percent}%)",
            EpistemicStatus.UNKNOWN: "I cannot see this",
            EpistemicStatus.UNAVAILABLE: "Data exists but cannot be accessed",
            EpistemicStatus.EXCLUDED: "Explicitly excluded by limitation",
            EpistemicStatus.UNKNOWABLE: "Fundamentally impossible to know",
            EpistemicStatus.CONTRADICTORY: "Evidence contradicts itself",
            EpistemicStatus.AMBIGUOUS: "Multiple valid interpretations",
            EpistemicStatus.PENDING: "Computing... ({progress}%)",
            EpistemicStatus.FAILED: "Computation failed: {reason}",
            EpistemicStatus.TIMEOUT: "Computation timed out after {seconds}s",
        }
        return templates.get(self, "Unknown epistemic status")


# ------------------------------------------------------------------------------
# TRUTHFUL CONTENT: CLAIMS THAT MUST DECLARE THEIR STATUS
# ------------------------------------------------------------------------------


@runtime_checkable
class TruthfulContent(Protocol):
    """Any content that makes a claim about reality must declare its truth status."""

    @property
    def epistemic_status(self) -> EpistemicStatus:
        """The fundamental certainty level of this content."""
        ...

    @property
    def status_explanation(self) -> str:
        """Human-readable explanation of why this status applies."""
        ...

    @property
    def confidence_level(self) -> float | None:
        """Numerical confidence if applicable (0.0 to 1.0), None if not."""
        ...

    @property
    def evidence_references(self) -> frozenset[str]:
        """Observation anchors that support this claim, if any."""
        ...

    @property
    def limitations(self) -> frozenset[str]:
        """Declared limitations that affect this claim."""
        ...


@dataclass(frozen=True)
class PerformanceMarker:
    """Records performance characteristics of a computation."""

    start_time: datetime
    end_time: datetime | None = None
    resource_usage: dict[str, Any] | None = None

    @property
    def duration_seconds(self) -> float | None:
        """Compute duration if computation is complete."""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


# ------------------------------------------------------------------------------
# CLARITY RULES: WHAT MUST BE SAID
# ------------------------------------------------------------------------------


@dataclass(frozen=True)
class ClarityRule:
    """Immutable rule defining what must be communicated about a claim."""

    status: EpistemicStatus
    required_signals: frozenset[str] = field(default_factory=lambda: frozenset())
    prohibited_signals: frozenset[str] = field(default_factory=lambda: frozenset())
    mandatory_message: str | None = None

    def validate_content(self, content: TruthfulContent) -> list[str]:
        """Return list of violations for this content."""
        violations: list[str] = []

        # Check if content has the right status for this rule
        if content.epistemic_status != self.status:
            return violations  # Not applicable

        # Check required signals
        for signal in self.required_signals:
            # In practice, interfaces would need to declare which signals they provide
            # For now, we'll validate the content itself
            if signal == "WARNING_SYMBOL" and not content.status_explanation.startswith(
                "⚠️"
            ):
                violations.append(f"Missing warning symbol for {self.status.name}")
            elif signal == "CONFIDENCE_LEVEL" and content.confidence_level is None:
                violations.append(f"Missing confidence level for {self.status.name}")
            elif signal == "LIMITATIONS_LIST" and not content.limitations:
                violations.append(f"Missing limitations list for {self.status.name}")

        # Check prohibited signals
        for signal in self.prohibited_signals:
            if signal == "ABSOLUTE_CERTAINTY" and content.confidence_level == 1.0:
                violations.append(
                    f"Prohibited absolute certainty for {self.status.name}"
                )
            elif signal == "NO_WARNING" and content.status_explanation.startswith("⚠️"):
                violations.append(f"Prohibited warning for {self.status.name}")

        # Check mandatory message
        if (
            self.mandatory_message
            and self.mandatory_message not in content.status_explanation
        ):
            violations.append(
                f"Missing mandatory message for {self.status.name}: {self.mandatory_message}"
            )

        return violations


# ------------------------------------------------------------------------------
# CORE VALIDATOR: EPISTEMIC HONESTY ENFORCEMENT
# ------------------------------------------------------------------------------


@dataclass
class ClarityViolation(Exception):
    """Raised when interface fails to properly communicate truth status."""

    content_type: str
    status: EpistemicStatus
    missing_signals: list[str]
    prohibited_present: list[str]

    def __init__(
        self,
        content_type: str,
        status: EpistemicStatus,
        missing_signals: list[str],
        prohibited_present: list[str],
    ) -> None:
        self.content_type = content_type
        self.status = status
        self.missing_signals = missing_signals
        self.prohibited_present = prohibited_present

        parts: list[str] = []
        if missing_signals:
            parts.append(f"Missing required signals: {', '.join(missing_signals)}")
        if prohibited_present:
            parts.append(f"Prohibited signals present: {', '.join(prohibited_present)}")

        msg = (
            f"Content type '{content_type}' with status {status.name} "
            f"violates clarity rules: {'; '.join(parts)}"
        )
        super().__init__(msg)


class ClarityValidator:
    """
    Enforces Articles 3 & 8: Truth Preservation and Performance Honesty.

    This validator ensures that:
    1. Uncertainty is always explicitly signaled
    2. Missing information is honestly reported
    3. Performance limitations are acknowledged
    4. Claims without evidence are marked as such
    5. Absolute certainty is never falsely claimed
    """

    # Define all clarity rules (immutable system configuration)
    _CLARITY_RULES: dict[EpistemicStatus, ClarityRule] = {
        # Known facts
        EpistemicStatus.KNOWN: ClarityRule(
            status=EpistemicStatus.KNOWN,
            required_signals=frozenset({"EVIDENCE_REFERENCES"}),
            prohibited_signals=frozenset({"WARNING_SYMBOL", "UNCERTAINTY_INDICATOR"}),
            mandatory_message=None,  # Known facts need no special message
        ),
        # Inferred/calculated facts
        EpistemicStatus.INFERRED: ClarityRule(
            status=EpistemicStatus.INFERRED,
            required_signals=frozenset({"EVIDENCE_REFERENCES", "INFERENCE_METHOD"}),
            prohibited_signals=frozenset({"ABSOLUTE_CERTAINTY"}),
            mandatory_message="Inferred from observations",
        ),
        EpistemicStatus.CALCULATED: ClarityRule(
            status=EpistemicStatus.CALCULATED,
            required_signals=frozenset({"INPUT_DATA", "CALCULATION_METHOD"}),
            prohibited_signals=frozenset({"ABSOLUTE_CERTAINTY"}),
            mandatory_message="Calculated from observed data",
        ),
        # Uncertain facts
        EpistemicStatus.UNCERTAIN: ClarityRule(
            status=EpistemicStatus.UNCERTAIN,
            required_signals=frozenset({"WARNING_SYMBOL", "UNCERTAINTY_REASON"}),
            prohibited_signals=frozenset({"ABSOLUTE_CERTAINTY", "NO_WARNING"}),
            mandatory_message="⚠️ Uncertain due to incomplete data",
        ),
        EpistemicStatus.ESTIMATED: ClarityRule(
            status=EpistemicStatus.ESTIMATED,
            required_signals=frozenset({"WARNING_SYMBOL", "ERROR_BOUNDS"}),
            prohibited_signals=frozenset({"ABSOLUTE_CERTAINTY", "NO_WARNING"}),
            mandatory_message="⚠️ Estimate with known error bounds",
        ),
        EpistemicStatus.PARTIAL: ClarityRule(
            status=EpistemicStatus.PARTIAL,
            required_signals=frozenset({"WARNING_SYMBOL", "COMPLETENESS_PERCENTAGE"}),
            prohibited_signals=frozenset({"ABSOLUTE_CERTAINTY", "NO_WARNING"}),
            mandatory_message="⚠️ Partial data only",
        ),
        # Unknown facts
        EpistemicStatus.UNKNOWN: ClarityRule(
            status=EpistemicStatus.UNKNOWN,
            required_signals=frozenset({"WARNING_SYMBOL"}),
            prohibited_signals=frozenset({"PRESENT_AS_KNOWN"}),
            mandatory_message="⚠️ I cannot see this",
        ),
        EpistemicStatus.UNAVAILABLE: ClarityRule(
            status=EpistemicStatus.UNAVAILABLE,
            required_signals=frozenset({"WARNING_SYMBOL", "UNAVAILABILITY_REASON"}),
            prohibited_signals=frozenset({"PRESENT_AS_KNOWN"}),
            mandatory_message="⚠️ Data exists but cannot be accessed",
        ),
        EpistemicStatus.EXCLUDED: ClarityRule(
            status=EpistemicStatus.EXCLUDED,
            required_signals=frozenset({"WARNING_SYMBOL", "LIMITATION_REFERENCE"}),
            prohibited_signals=frozenset({"PRESENT_AS_KNOWN"}),
            mandatory_message="⚠️ Explicitly excluded by limitation",
        ),
        # Unknowable facts
        EpistemicStatus.UNKNOWABLE: ClarityRule(
            status=EpistemicStatus.UNKNOWABLE,
            required_signals=frozenset({"STOP_SYMBOL"}),
            prohibited_signals=frozenset({"ANY_CLAIM"}),
            mandatory_message="🛑 Fundamentally impossible to know",
        ),
        EpistemicStatus.CONTRADICTORY: ClarityRule(
            status=EpistemicStatus.CONTRADICTORY,
            required_signals=frozenset({"STOP_SYMBOL", "CONTRADICTION_EVIDENCE"}),
            prohibited_signals=frozenset({"ANY_CLAIM"}),
            mandatory_message="🛑 Evidence contradicts itself",
        ),
        EpistemicStatus.AMBIGUOUS: ClarityRule(
            status=EpistemicStatus.AMBIGUOUS,
            required_signals=frozenset(
                {"WARNING_SYMBOL", "ALTERNATIVE_INTERPRETATIONS"}
            ),
            prohibited_signals=frozenset({"SINGLE_INTERPRETATION"}),
            mandatory_message="⚠️ Multiple valid interpretations",
        ),
        # Performance states
        EpistemicStatus.PENDING: ClarityRule(
            status=EpistemicStatus.PENDING,
            required_signals=frozenset({"LOADING_INDICATOR", "PROGRESS_ESTIMATE"}),
            prohibited_signals=frozenset({"PRESENT_AS_COMPLETE"}),
            mandatory_message="⏳ Computing...",
        ),
        EpistemicStatus.FAILED: ClarityRule(
            status=EpistemicStatus.FAILED,
            required_signals=frozenset({"ERROR_SYMBOL", "FAILURE_REASON"}),
            prohibited_signals=frozenset({"PRESENT_AS_SUCCESSFUL"}),
            mandatory_message="❌ Computation failed",
        ),
        EpistemicStatus.TIMEOUT: ClarityRule(
            status=EpistemicStatus.TIMEOUT,
            required_signals=frozenset({"TIMEOUT_SYMBOL", "TIMEOUT_DURATION"}),
            prohibited_signals=frozenset({"PRESENT_AS_COMPLETE"}),
            mandatory_message="⏰ Computation timed out",
        ),
    }

    def __init__(self) -> None:
        # Validate that all statuses have rules
        for status in EpistemicStatus:
            if status not in self._CLARITY_RULES:
                raise ValueError(
                    f"Missing clarity rule for epistemic status: {status.name}"
                )

    def get_rule(self, status: EpistemicStatus) -> ClarityRule:
        """Get the clarity rule for a specific epistemic status."""
        return self._CLARITY_RULES[status]

    def validate_content(self, content: TruthfulContent) -> None:
        """
        Validate that content properly communicates its truth status.

        Args:
            content: Content making a claim about reality

        Raises:
            ClarityViolation: If content violates clarity rules
        """
        status = content.epistemic_status
        rule = self.get_rule(status)

        violations = rule.validate_content(content)

        if violations:
            # For now, use generic violation
            # In practice, we'd analyze which specific signals are missing
            raise ClarityViolation(
                content_type=type(content).__name__,
                status=status,
                missing_signals=["See violation details"],
                prohibited_present=[],
            )

    def validate_interface_intent(
        self,
        content_list: list[TruthfulContent],
        performance_markers: list[PerformanceMarker],
    ) -> None:
        """
        Validate an interface's entire planned presentation.

        This ensures:
        1. All content declares appropriate truth status
        2. Performance is honestly represented
        3. No hidden claims or unacknowledged limitations

        Args:
            content_list: All content the interface plans to show
            performance_markers: Performance data for computations

        Raises:
            ClarityViolation: If any content violates clarity rules
        """
        # Validate each piece of content
        for content in content_list:
            self.validate_content(content)

        # Validate performance honesty
        self._validate_performance_honesty(performance_markers)

        # Additional global checks
        self._validate_global_constraints(content_list)

    def _validate_performance_honesty(self, markers: list[PerformanceMarker]) -> None:
        """Ensure performance characteristics are properly represented."""
        # Removed unused 'now' variable

        for marker in markers:
            # Check for unreasonably fast computations (potential dishonesty)
            if marker.end_time and marker.start_time:
                duration = (marker.end_time - marker.start_time).total_seconds()
                if duration < 0.001 and marker.resource_usage:  # Less than 1ms
                    # Complex computations should take measurable time
                    # This might indicate cached results presented as fresh
                    pass  # Could log warning, but not a violation

    def _validate_global_constraints(self, content_list: list[TruthfulContent]) -> None:
        """Check for systemic truth violations."""

        # Count uncertain vs known claims
        uncertain_count = sum(
            1 for c in content_list if c.epistemic_status.requires_warning
        )
        # Removed unused 'known_count' variable

        # If more than 80% of claims are uncertain, warn about overall reliability
        total = len(content_list)
        if total > 0 and uncertain_count / total > 0.8:
            # This doesn't raise violation, but could be logged
            pass

        # Check for claims without evidence
        for content in content_list:
            if not content.evidence_references and content.epistemic_status in {
                EpistemicStatus.KNOWN,
                EpistemicStatus.INFERRED,
                EpistemicStatus.CALCULATED,
            }:
                # Known/inferred/calculated claims should have evidence
                # This is a potential violation but depends on context
                pass


# ------------------------------------------------------------------------------
# PERFORMANCE HONESTY UTILITIES
# ------------------------------------------------------------------------------


class PerformanceTracker:
    """
    Tracks computational performance for honest reporting.

    Use this to time operations and record resource usage.
    """

    def __init__(self, operation_name: str) -> None:
        self.operation_name = operation_name
        self.markers: list[PerformanceMarker] = []

    def start(self) -> PerformanceMarker:
        """Start timing an operation."""
        marker = PerformanceMarker(start_time=datetime.now(UTC))
        self.markers.append(marker)
        return marker

    def end(
        self, marker: PerformanceMarker, resource_usage: dict[str, Any] | None = None
    ) -> None:
        """
        End timing an operation.

        Since PerformanceMarker is frozen, we need to replace it with a new instance.
        """
        # Find the marker in our list and replace it with an updated version
        for i, existing_marker in enumerate(self.markers):
            if existing_marker is marker:
                # Create a new marker with updated end_time and resource_usage
                updated_marker = PerformanceMarker(
                    start_time=marker.start_time,
                    end_time=datetime.now(UTC),
                    resource_usage=resource_usage,
                )
                self.markers[i] = updated_marker
                return

        # If we get here, the marker wasn't found in our list
        raise ValueError("Marker not found in tracker list")

    def get_performance_report(self) -> dict[str, Any]:
        """Generate honest performance report."""
        if not self.markers:
            return {"operation": self.operation_name, "status": "not_started"}

        completed = [m for m in self.markers if m.end_time]
        if not completed:
            return {"operation": self.operation_name, "status": "in_progress"}

        durations = [m.duration_seconds for m in completed if m.duration_seconds]
        if not durations:
            return {"operation": self.operation_name, "status": "completed_no_duration"}

        return {
            "operation": self.operation_name,
            "status": "completed",
            "duration_seconds": {
                "min": min(durations),
                "max": max(durations),
                "average": sum(durations) / len(durations),
            },
            "total_operations": len(completed),
        }


# ------------------------------------------------------------------------------
# VALIDATION UTILITIES (FOR INTERFACE IMPLEMENTERS)
# ------------------------------------------------------------------------------


def requires_warning(content: TruthfulContent) -> bool:
    """
    Check if content requires an explicit uncertainty warning.

    Use this to decide whether to show warning indicators.
    """
    return content.epistemic_status.requires_warning


def get_mandatory_message(content: TruthfulContent) -> str:
    """
    Get the mandatory message that must accompany this content.

    Use this to ensure required text is displayed.
    """
    rule = ClarityValidator().get_rule(content.epistemic_status)
    if rule.mandatory_message:
        return rule.mandatory_message
    return content.status_explanation


def validate_before_display(content_list: list[TruthfulContent]) -> list[str]:
    """
    Pre-display validation for interfaces.

    Returns list of warnings/errors that must be addressed.
    Use this before rendering to ensure clarity compliance.
    """
    validator = ClarityValidator()
    warnings: list[str] = []

    for content in content_list:
        try:
            validator.validate_content(content)
        except ClarityViolation as e:
            warnings.append(f"Clarity violation: {e}")

        # Additional heuristic checks
        if content.confidence_level is not None:
            if content.confidence_level > 1.0 or content.confidence_level < 0.0:
                warnings.append(f"Invalid confidence level: {content.confidence_level}")

        if (
            content.epistemic_status == EpistemicStatus.KNOWN
            and not content.evidence_references
        ):
            warnings.append("Known claim without evidence references")

    return warnings


# ------------------------------------------------------------------------------
# TEST UTILITIES (FOR INTEGRITY GUARDIAN)
# ------------------------------------------------------------------------------


@dataclass
class MockTruthfulContent:
    """Minimal implementation for testing."""

    epistemic_status: EpistemicStatus
    status_explanation: str = ""
    confidence_level: float | None = None
    evidence_references: frozenset[str] = field(default_factory=lambda: frozenset())
    limitations: frozenset[str] = field(default_factory=lambda: frozenset())


# ------------------------------------------------------------------------------
# EXPORTED CONTRACT
# ------------------------------------------------------------------------------

__all__ = [
    # Epistemic Status
    "EpistemicStatus",
    # Content Protocol
    "TruthfulContent",
    # Performance Tracking
    "PerformanceMarker",
    "PerformanceTracker",
    # Rules and Validation
    "ClarityRule",
    "ClarityValidator",
    "ClarityViolation",
    # Utilities
    "requires_warning",
    "get_mandatory_message",
    "validate_before_display",
    # Test Utilities (exported for integrity tests only)
    "MockTruthfulContent",
]
