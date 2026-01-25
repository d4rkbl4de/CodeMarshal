"""
lens.aesthetic.typography.py

Typography hierarchy for truth preservation.
Typography answers: "What deserves attention first?" without drama.

CONSTRAINTS:
1. No expressive fonts or decorative weights
2. Hierarchy must be semantic, not stylistic
3. Emphasis requires epistemic justification
4. Monotony is preserved - important things should not look accidentally important
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class TextRole(Enum):
    """Semantic roles for text, ordered by decreasing importance."""

    # Primary observation - what is currently being examined
    PRIMARY = auto()

    # Secondary supporting information
    SECONDARY = auto()

    # Annotations, footnotes, references
    ANNOTATION = auto()

    # Warnings about uncertainty or limitations
    WARNING = auto()

    # Metadata, timestamps, version information
    METADATA = auto()

    # User input or commands
    USER_INPUT = auto()

    # System status or progress indicators
    STATUS = auto()


class Glyph(Enum):
    """Low-level visual primitives for indicators."""

    WARNING = auto()
    ERROR = auto()
    STOP = auto()
    QUESTION = auto()
    CHECK = auto()
    SPINNER = auto()
    PAUSE = auto()
    ATTENTION = auto()
    CRITICAL = auto()
    NEUTRAL = auto()
    ACTIVE = auto()


@dataclass(frozen=True)
class TypographicRule:
    """Immutable rule defining how a text role should be treated."""

    role: TextRole
    purpose: str  # Epistemic purpose, not visual style
    allowed_emphasis: bool
    allowed_deemphasis: bool
    max_per_view: int | None = None  # Cognitive load control
    requires_anchor: bool = False  # Must be anchored to specific observation
    prohibited_with: set[TextRole] = field(
        default_factory=lambda: set()
    )  # Explicit type

    def __post_init__(self) -> None:
        """Validate that emphasis rules are consistent."""
        if self.allowed_emphasis and self.allowed_deemphasis:
            raise ValueError(
                f"Role {self.role} cannot be both emphasized and de-emphasized"
            )


class TypographySystem:
    """
    Central authority for typographic truth preservation.

    Enforces:
    1. One primary focus at a time
    2. No hidden emphasis
    3. No competition for attention
    4. Clear information hierarchy
    """

    def __init__(self) -> None:
        self._rules = self._build_rules()
        self._current_primary: TextRole | None = None

    def _build_rules(self) -> dict[TextRole, TypographicRule]:
        """Construct the immutable rule system."""

        return {
            TextRole.PRIMARY: TypographicRule(
                role=TextRole.PRIMARY,
                purpose="The single object of current investigation",
                allowed_emphasis=True,
                allowed_deemphasis=False,
                max_per_view=1,  # Only one primary at a time
                requires_anchor=True,
                prohibited_with={
                    TextRole.WARNING,  # Warnings cannot obscure primary
                },
            ),
            TextRole.SECONDARY: TypographicRule(
                role=TextRole.SECONDARY,
                purpose="Directly supports the primary observation",
                allowed_emphasis=False,
                allowed_deemphasis=True,
                max_per_view=3,  # Limit supporting information
                requires_anchor=True,
                prohibited_with=set(),  # Explicit empty set with type
            ),
            TextRole.ANNOTATION: TypographicRule(
                role=TextRole.ANNOTATION,
                purpose="Reference or citation of evidence",
                allowed_emphasis=False,
                allowed_deemphasis=True,
                max_per_view=None,  # Can be many, but must be visually quiet
                requires_anchor=True,
                prohibited_with={
                    TextRole.PRIMARY,  # Must not compete with primary
                },
            ),
            TextRole.WARNING: TypographicRule(
                role=TextRole.WARNING,
                purpose="Signal uncertainty, limitation, or caution",
                allowed_emphasis=True,  # Warnings must be visible
                allowed_deemphasis=False,
                max_per_view=None,  # All warnings must be shown
                requires_anchor=True,
                prohibited_with={
                    TextRole.PRIMARY,  # Warnings cannot be primary content
                },
            ),
            TextRole.METADATA: TypographicRule(
                role=TextRole.METADATA,
                purpose="Contextual information about the observation",
                allowed_emphasis=False,
                allowed_deemphasis=True,
                max_per_view=None,
                requires_anchor=True,
                prohibited_with={
                    TextRole.PRIMARY,
                    TextRole.WARNING,  # Must not obscure important content
                },
            ),
            TextRole.USER_INPUT: TypographicRule(
                role=TextRole.USER_INPUT,
                purpose="User questions or commands",
                allowed_emphasis=True,
                allowed_deemphasis=False,
                max_per_view=1,
                requires_anchor=False,  # Input doesn't need evidence anchor
                prohibited_with={
                    TextRole.PRIMARY,  # Input and observation compete
                },
            ),
            TextRole.STATUS: TypographicRule(
                role=TextRole.STATUS,
                purpose="System state or progress indicators",
                allowed_emphasis=False,
                allowed_deemphasis=True,
                max_per_view=2,
                requires_anchor=False,
                prohibited_with={
                    TextRole.PRIMARY,
                    TextRole.USER_INPUT,
                },
            ),
        }

    def validate_composition(self, roles: list[TextRole]) -> list[str]:
        """
        Validate that a set of roles can appear together without truth distortion.

        Returns:
            List of violation messages, empty if valid.
        """
        violations: list[str] = []

        # Count occurrences
        role_counts: dict[TextRole, int] = {}
        for role in roles:
            role_counts[role] = role_counts.get(role, 0) + 1

        # Check each rule
        for role, count in role_counts.items():
            rule = self._rules[role]

            # Check max per view
            if rule.max_per_view is not None and count > rule.max_per_view:
                violations.append(
                    f"Too many {role.name} elements ({count} > {rule.max_per_view})"
                )

            # Check for prohibited combinations
            for other_role in role_counts:
                if other_role in rule.prohibited_with:
                    violations.append(
                        f"{role.name} cannot appear with {other_role.name}"
                    )

        # Ensure exactly one primary when needed
        primary_count = role_counts.get(TextRole.PRIMARY, 0)
        if primary_count > 1:
            violations.append(f"Multiple primary elements ({primary_count})")

        return violations

    def get_role_purpose(self, role: TextRole) -> str:
        """Get the epistemic purpose of a role (for documentation/auditing)."""
        return self._rules[role].purpose

    def get_emphasis_rules(self) -> list[tuple[TextRole, bool, bool]]:
        """
        Get all emphasis/de-emphasis rules for auditing.

        Returns:
            List of (role, can_emphasize, can_deemphasize) tuples
        """
        return [
            (role, rule.allowed_emphasis, rule.allowed_deemphasis)
            for role, rule in self._rules.items()
        ]

    def requires_evidence_anchor(self, role: TextRole) -> bool:
        """Check if text of this role must be anchored to specific observation."""
        return self._rules[role].requires_anchor

    def get_hierarchy(self) -> list[TextRole]:
        """
        Get the canonical hierarchy of roles by importance.

        This defines the visual stacking order and attention flow.
        """
        return [
            TextRole.WARNING,  # Warnings must be seen first
            TextRole.PRIMARY,  # Then the primary focus
            TextRole.USER_INPUT,  # Then user's question
            TextRole.SECONDARY,  # Then supporting information
            TextRole.STATUS,  # Then system status
            TextRole.ANNOTATION,  # Then references
            TextRole.METADATA,  # Finally metadata
        ]


# Singleton instance for system-wide consistency
TYPEOGRAPHY = TypographySystem()


def validate_text_role(
    role: TextRole,
    requires_anchor: bool = True,
    context_roles: list[TextRole] | None = None,
) -> list[str]:
    """
    Validate that a text role can be used in the given context.

    Args:
        role: The role to validate
        requires_anchor: Whether this text must be anchored to evidence
        context_roles: Other roles present in the same view

    Returns:
        List of violation messages, empty if valid
    """
    violations: list[str] = []

    # Check anchoring requirement
    if requires_anchor and not TYPEOGRAPHY.requires_evidence_anchor(role):
        violations.append(
            f"Role {role.name} requires evidence anchor but cannot have one"
        )

    # Check context if provided
    if context_roles:
        context_with_new = context_roles + [role]
        violations.extend(TYPEOGRAPHY.validate_composition(context_with_new))

    return violations


def get_roles_for_content_type(content_type: str) -> list[TextRole]:
    """
    Map content types to appropriate roles.

    This ensures consistent semantic mapping across the system.
    """
    mapping: dict[str, list[TextRole]] = {
        "observation": [TextRole.PRIMARY, TextRole.SECONDARY],
        "limitation": [TextRole.WARNING, TextRole.ANNOTATION],
        "user_question": [TextRole.USER_INPUT],
        "pattern": [TextRole.SECONDARY, TextRole.ANNOTATION],
        "metadata": [TextRole.METADATA],
        "status": [TextRole.STATUS],
    }

    return mapping.get(content_type, [TextRole.SECONDARY])


# Export the public API
__all__ = [
    "TextRole",
    "TypographySystem",
    "TYPEOGRAPHY",
    "validate_text_role",
    "get_roles_for_content_type",
]
