"""
Single-Focus Interface Constraint (Article 5 Enforcement)

This module defines the abstract rule for ensuring only one primary content area
is visible at a time across ALL CodeMarshal interfaces (CLI, TUI, API, exports).

CRITICAL: This is NOT UI code. This defines the laws of optics for truth display.
Violations are Tier-2 (immediate halt).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol, Union, runtime_checkable

# ------------------------------------------------------------------------------
# PROTOCOLS: ABSTRACT INTERFACE REPRESENTATION
# ------------------------------------------------------------------------------


@runtime_checkable
class FocusableContent(Protocol):
    """Anything that could potentially claim primary focus in an interface."""

    @property
    def content_type(self) -> str:
        """Canonical identifier for this content type."""
        ...


@runtime_checkable
class InterfaceIntent(Protocol):
    """How an interface intends to present content at a given moment."""

    @property
    def primary_focus(self) -> FocusableContent | None:
        """The single element demanding user attention, or None."""
        ...

    @property
    def secondary_presentations(self) -> frozenset[FocusableContent]:
        """Elements allowed to be visible but not interactive as primary."""
        ...


# ------------------------------------------------------------------------------
# ENUMERATIONS: CANONICAL FOCUS TYPES
# ------------------------------------------------------------------------------


class PrimaryContentType(Enum):
    """The only types that can claim primary focus."""

    OBSERVATION_SNAPSHOT = auto()  # Raw observation data
    QUESTION_ANSWER = auto()  # Human question + system response
    PATTERN_REPORT = auto()  # Numeric pattern detection
    NOTEBOOK_ENTRY = auto()  # Human thinking anchored to evidence
    INVESTIGATION_OVERVIEW = auto()  # Session context
    HELP_CONTENT = auto()  # Documentation/guidance

    # These can NEVER be primary (they are indicators only)
    @classmethod
    def never_primary(cls) -> set["PrimaryContentType"]:
        """Content types that violate Article 5 if made primary."""
        return set()  # All defined types can be primary when appropriate


class SecondaryContentType(Enum):
    """Content types that may only appear as secondary elements."""

    BREADCRUMB_TRAIL = auto()  # Navigation context
    STATUS_INDICATOR = auto()  # Loading, errors, warnings
    KEYBOARD_SHORTCUTS = auto()  # Available actions
    SEARCH_RESULTS = auto()  # Filtered lists
    QUICK_REFERENCES = auto()  # Metadata, tags, anchors

    @classmethod
    def allowed_as_secondary(cls) -> set["SecondaryContentType"]:
        """All secondary types are valid as secondary."""
        return set(cls)


# ------------------------------------------------------------------------------
# CORE RULE: SINGLE FOCUS CONSTRAINT
# ------------------------------------------------------------------------------


@dataclass
class SingleFocusViolation(Exception):
    """Raised when interface attempts to show multiple primary foci."""

    primary_foci: Sequence[Union["PrimaryContentType", str]]
    allowed_primary: Optional["PrimaryContentType"] = None

    def __init__(
        self,
        primary_foci: Sequence[Union["PrimaryContentType", str]],
        allowed_primary: Optional["PrimaryContentType"] = None,
    ) -> None:
        self.primary_foci = primary_foci
        self.allowed_primary = allowed_primary

        if len(primary_foci) == 0:
            msg = "Interface has no primary focus (Article 5 requires exactly one)"
        elif len(primary_foci) > 1:
            foci_names = ", ".join(
                f.name if isinstance(f, PrimaryContentType) else f for f in primary_foci
            )
            msg = (
                f"Interface attempting to show {len(primary_foci)} primary foci: "
                f"{foci_names}. Article 5 permits exactly one."
            )
        else:
            focus = primary_foci[0]
            if isinstance(focus, PrimaryContentType):
                msg = f"Interface primary focus {focus.name} violates context rules"
            else:
                msg = f"Interface primary focus '{focus}' violates context rules"

        super().__init__(msg)


class SingleFocusRule:
    """
    Enforces Article 5: Only one primary content area visible at a time.

    This rule applies equally to:
    - CLI output (only one main section)
    - TUI panes (only one main pane)
    - API responses (only one primary data structure)
    - HTML exports (only one primary content div)

    USAGE:
        rule = SingleFocusRule()
        rule.validate_interface_intent(intent)  # Raises SingleFocusViolation
    """

    # Content types that can NEVER coexist (they compete for attention)
    COMPETING_PAIRS: frozenset[frozenset[PrimaryContentType]] = frozenset(
        {
            frozenset(
                {
                    PrimaryContentType.OBSERVATION_SNAPSHOT,
                    PrimaryContentType.QUESTION_ANSWER,
                }
            ),
            frozenset(
                {PrimaryContentType.PATTERN_REPORT, PrimaryContentType.NOTEBOOK_ENTRY}
            ),
            frozenset(
                {
                    PrimaryContentType.INVESTIGATION_OVERVIEW,
                    PrimaryContentType.QUESTION_ANSWER,
                }
            ),
        }
    )

    def __init__(self) -> None:
        pass  # No state - this is a pure validation rule

    def validate_interface_intent(self, intent: InterfaceIntent) -> None:
        """
        Validate that an interface's intended presentation obeys single-focus.

        Args:
            intent: How the interface plans to present content

        Raises:
            SingleFocusViolation: If Article 5 would be violated
        """
        primary = intent.primary_focus
        secondaries = intent.secondary_presentations

        # Rule 1: Must have exactly one primary focus (or preparing state with none)
        if primary is None:
            # Empty state is allowed (e.g., startup, between investigations)
            # but secondary content must also be minimal
            if len(secondaries) > 3:  # Arbitrary but reasonable limit
                raise SingleFocusViolation([])
            return

        # Rule 2: Primary must be a valid PrimaryContentType
        primary_type_str = self._extract_content_type(primary)
        try:
            primary_type = PrimaryContentType[primary_type_str]
        except KeyError:
            # Invalid primary type - treat as violation
            raise SingleFocusViolation([primary_type_str], None) from None

        # Rule 3: Check for competing primary content in secondaries
        competing_primaries = self._find_competing_primary_content(
            primary_type, secondaries
        )

        if competing_primaries:
            # Create a tuple instead of list to avoid invariance issues
            all_foci: Sequence[PrimaryContentType | str] = (primary_type,) + tuple(
                competing_primaries
            )
            raise SingleFocusViolation(all_foci, primary_type)

    def _extract_content_type(self, content: FocusableContent) -> str:
        """Extract normalized content type identifier."""
        return content.content_type.upper().replace(" ", "_")

    def _find_competing_primary_content(
        self, primary_type: PrimaryContentType, secondaries: frozenset[FocusableContent]
    ) -> list[PrimaryContentType]:
        """
        Find any secondary content that would compete with primary for attention.

        Returns empty list if secondaries are properly subordinate.
        """
        competing: list[PrimaryContentType] = []

        for secondary in secondaries:
            sec_type_str = self._extract_content_type(secondary)

            # Try to map to PrimaryContentType
            try:
                sec_type = PrimaryContentType[sec_type_str]
            except KeyError:
                # Not a primary type - check if it's a valid secondary type
                try:
                    SecondaryContentType[sec_type_str]
                    continue  # Valid secondary type, not competing
                except KeyError:
                    # Unknown type - conservatively treat as competing
                    competing.append(PrimaryContentType.OBSERVATION_SNAPSHOT)
                    continue

            # Check if this primary type competes with current primary
            pair = frozenset({primary_type, sec_type})
            if pair in self.COMPETING_PAIRS:
                competing.append(sec_type)

        return competing


# ------------------------------------------------------------------------------
# VALIDATION UTILITIES (FOR INTERFACE IMPLEMENTERS)
# ------------------------------------------------------------------------------


def validate_competing_primaries(
    primary_type: PrimaryContentType, candidate_secondary_types: list[str]
) -> list[str]:
    """
    Helper for interfaces to check planned content against rule.

    Returns list of candidate types that would violate single-focus.
    Use this during interface planning, not rendering.

    Example:
        violations = validate_competing_primaries(
            PrimaryContentType.QUESTION_ANSWER,
            ["observation_snapshot", "breadcrumb_trail"]
        )
        # Returns ["observation_snapshot"] - would compete
    """
    rule = SingleFocusRule()
    violations: list[str] = []

    for candidate in candidate_secondary_types:
        try:
            # Try as primary type first (most restrictive)
            cand_type = PrimaryContentType[candidate.upper().replace(" ", "_")]

            # Check if competes with primary
            pair = frozenset({primary_type, cand_type})
            if pair in rule.COMPETING_PAIRS:
                violations.append(candidate)

        except KeyError:
            # Not a primary type - try as secondary
            try:
                SecondaryContentType[candidate.upper().replace(" ", "_")]
                # Valid secondary type - allowed
                continue
            except KeyError:
                # Unknown type - violates clarity (Article 3)
                violations.append(f"UNKNOWN_TYPE:{candidate}")

    return violations


# ------------------------------------------------------------------------------
# TEST UTILITIES (FOR INTEGRITY GUARDIAN)
# ------------------------------------------------------------------------------


@dataclass
class MockFocusableContent:
    """Minimal implementation for testing."""

    content_type: str


@dataclass
class MockInterfaceIntent:
    """Minimal implementation for testing."""

    primary_focus: FocusableContent | None
    secondary_presentations: frozenset[FocusableContent] = frozenset()


# ------------------------------------------------------------------------------
# EXPORTED CONTRACT
# ------------------------------------------------------------------------------

__all__ = [
    # Protocols
    "FocusableContent",
    "InterfaceIntent",
    # Enums
    "PrimaryContentType",
    "SecondaryContentType",
    # Core Rule
    "SingleFocusRule",
    "SingleFocusViolation",
    # Utilities
    "validate_competing_primaries",
    # Test Utilities (exported for integrity tests only)
    "MockFocusableContent",
    "MockInterfaceIntent",
]
