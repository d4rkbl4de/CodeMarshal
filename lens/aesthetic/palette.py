"""
lens.aesthetic.palette.py

Semantic color system for truth preservation.
Colors encode epistemic state, not preference or emotion.

CONSTRAINTS:
1. No gradients, accents, or branding colors
2. Colors must have clear, singular meanings
3. No ambiguous or context-dependent colors
4. Color combinations must not create false confidence
5. Uncertainty must always be visually distinct
"""

from dataclasses import dataclass, field
from enum import Enum, auto


class SemanticColor(Enum):
    """Semantic colors representing epistemic states, not aesthetics."""

    # Core truth states
    CERTAINTY = auto()  # Observation is complete and unambiguous
    UNCERTAINTY = auto()  # Observation has known limitations
    ERROR = auto()  # Observation failed or cannot be made

    # Information categories
    NEUTRAL = auto()  # Factual information without judgment
    FOCUS = auto()  # Current object of investigation
    SECONDARY = auto()  # Supporting or contextual information

    # System states
    WARNING = auto()  # Caution about interpretation or limitations
    STATUS = auto()  # System operation state
    METADATA = auto()  # Ancillary information about observations

    # User interaction
    USER_ACTION = auto()  # User input or commands
    SYSTEM_RESPONSE = auto()  # System acknowledgment of user action

    # Primitive states (for indicators)
    ACTIVE = auto()
    ATTENTION = auto()
    CRITICAL = auto()


@dataclass(frozen=True)
class ColorRule:
    """Immutable rule defining a semantic color's meaning and constraints."""

    color: SemanticColor
    meaning: str  # Epistemic meaning, not visual description
    precedence: int  # Higher number overrides lower (for conflicts)
    must_be_alone: bool = False  # Cannot appear with other colors
    prohibited_with: set[SemanticColor] = field(default_factory=lambda: set())
    required_with: set[SemanticColor] = field(default_factory=lambda: set())

    def __post_init__(self) -> None:
        """Validate color rule consistency."""
        if self.must_be_alone and (self.prohibited_with or self.required_with):
            raise ValueError(
                f"Color {self.color} cannot have companions if must_be_alone is True"
            )


class PaletteSystem:
    """
    Central authority for semantic color usage.

    Enforces:
    1. Colors have fixed, unambiguous meanings
    2. Color conflicts are prevented
    3. Uncertainty is never hidden
    4. No emotional or persuasive coloring
    """

    def __init__(self) -> None:
        self._rules = self._build_rules()
        self._color_meanings = self._build_meanings()

    def _build_rules(self) -> dict[SemanticColor, ColorRule]:
        """Construct the immutable color rule system."""

        return {
            SemanticColor.ERROR: ColorRule(
                color=SemanticColor.ERROR,
                meaning="Observation failed or cannot be made",
                precedence=100,  # Highest precedence - always wins conflicts
                must_be_alone=True,  # Error cannot be combined with anything
            ),
            SemanticColor.UNCERTAINTY: ColorRule(
                color=SemanticColor.UNCERTAINTY,
                meaning="Observation has known limitations or incompleteness",
                precedence=90,
                prohibited_with={
                    SemanticColor.CERTAINTY,  # Cannot appear certain and uncertain
                },
            ),
            SemanticColor.WARNING: ColorRule(
                color=SemanticColor.WARNING,
                meaning="Caution about interpretation or system limitations",
                precedence=80,
                prohibited_with={
                    SemanticColor.CERTAINTY,
                    SemanticColor.FOCUS,  # Warning should not be focus
                },
            ),
            SemanticColor.CERTAINTY: ColorRule(
                color=SemanticColor.CERTAINTY,
                meaning="Observation is complete and unambiguous",
                precedence=70,
                prohibited_with={
                    SemanticColor.UNCERTAINTY,
                    SemanticColor.WARNING,
                },
            ),
            SemanticColor.FOCUS: ColorRule(
                color=SemanticColor.FOCUS,
                meaning="Current object of investigation",
                precedence=60,
                prohibited_with={
                    SemanticColor.WARNING,
                    SemanticColor.SECONDARY,  # Cannot be both focus and secondary
                },
            ),
            SemanticColor.USER_ACTION: ColorRule(
                color=SemanticColor.USER_ACTION,
                meaning="User input or command",
                precedence=50,
                prohibited_with={
                    SemanticColor.SYSTEM_RESPONSE,  # Distinguish user from system
                },
            ),
            SemanticColor.SYSTEM_RESPONSE: ColorRule(
                color=SemanticColor.SYSTEM_RESPONSE,
                meaning="System acknowledgment or reaction",
                precedence=40,
                prohibited_with={
                    SemanticColor.USER_ACTION,
                },
            ),
            SemanticColor.SECONDARY: ColorRule(
                color=SemanticColor.SECONDARY,
                meaning="Supporting or contextual information",
                precedence=30,
                prohibited_with={
                    SemanticColor.FOCUS,
                    SemanticColor.CERTAINTY,  # Secondary shouldn't look certain
                },
            ),
            SemanticColor.NEUTRAL: ColorRule(
                color=SemanticColor.NEUTRAL,
                meaning="Factual information without judgment",
                precedence=20,
                prohibited_with={
                    SemanticColor.CERTAINTY,
                    SemanticColor.UNCERTAINTY,
                    SemanticColor.WARNING,
                },
            ),
            SemanticColor.STATUS: ColorRule(
                color=SemanticColor.STATUS,
                meaning="System operation state",
                precedence=10,
                prohibited_with={
                    SemanticColor.ERROR,  # Status should not look like error
                    SemanticColor.WARNING,
                },
            ),
            SemanticColor.METADATA: ColorRule(
                color=SemanticColor.METADATA,
                meaning="Ancillary information about observations",
                precedence=0,  # Lowest precedence - always yields
                prohibited_with={
                    SemanticColor.FOCUS,
                    SemanticColor.ERROR,
                    SemanticColor.WARNING,
                },
            ),
            SemanticColor.ACTIVE: ColorRule(
                color=SemanticColor.ACTIVE,
                meaning="System is actively processing",
                precedence=15,
            ),
            SemanticColor.ATTENTION: ColorRule(
                color=SemanticColor.ATTENTION,
                meaning="Requires human attention for decision",
                precedence=85,
            ),
            SemanticColor.CRITICAL: ColorRule(
                color=SemanticColor.CRITICAL,
                meaning="Critical failure or boundary violation",
                precedence=110,
                must_be_alone=True,
            ),
        }

    def _build_meanings(self) -> dict[SemanticColor, str]:
        """Create a direct mapping of color to meaning for quick reference."""
        return {rule.color: rule.meaning for rule in self._rules.values()}

    def get_meaning(self, color: SemanticColor) -> str:
        """Get the unambiguous meaning of a semantic color."""
        return self._color_meanings[color]

    def validate_composition(self, colors: set[SemanticColor]) -> list[str]:
        """
        Validate that colors can appear together without semantic conflict.

        Returns:
            List of violation messages, empty if valid.
        """
        violations: list[str] = []

        # Check each color against others
        for color in colors:
            rule = self._rules[color]

            # Check if must be alone
            if rule.must_be_alone and len(colors) > 1:
                violations.append(
                    f"{color.name} must appear alone (cannot combine with other colors)"
                )
                continue

            # Check prohibited combinations
            for other_color in colors:
                if other_color == color:
                    continue

                if other_color in rule.prohibited_with:
                    violations.append(
                        f"{color.name} cannot appear with {other_color.name}"
                    )

            # Check required companions (if any)
            for required_color in rule.required_with:
                if required_color not in colors:
                    violations.append(
                        f"{color.name} requires {required_color.name} to be present"
                    )

        # Resolve precedence conflicts
        if not violations and len(colors) > 1:
            # Find the highest precedence color
            precedences = [(c, self._rules[c].precedence) for c in colors]
            precedences.sort(key=lambda x: x[1], reverse=True)

            highest_color = precedences[0][0]

            # Check if any colors conflict with highest
            for color, _ in precedences[1:]:
                if color in self._rules[highest_color].prohibited_with:
                    violations.append(
                        f"{highest_color.name} conflicts with {color.name}"
                    )

        return violations

    def resolve_conflict(self, colors: set[SemanticColor]) -> SemanticColor | None:
        """
        When colors conflict, determine which should be shown.

        Returns:
            The color that should be displayed, or None if no resolution possible.
        """
        if not colors:
            return None

        # Single color - no conflict
        if len(colors) == 1:
            return next(iter(colors))

        # Check for must-be-alone colors
        for color in colors:
            if self._rules[color].must_be_alone:
                return color

        # Use precedence
        precedences = [(c, self._rules[c].precedence) for c in colors]
        precedences.sort(key=lambda x: x[1], reverse=True)

        highest_color = precedences[0][0]

        # Verify highest doesn't conflict with others (should be caught by validate)
        for color, _ in precedences[1:]:
            if color in self._rules[highest_color].prohibited_with:
                # Conflict - cannot resolve
                return None

        return highest_color

    def get_allowed_combinations(self) -> list[tuple[SemanticColor, ...]]:
        """
        Get all pre-approved color combinations.

        Useful for UI components that need to know valid combinations.
        """
        allowed: list[tuple[SemanticColor, ...]] = []

        # Single colors are always allowed
        for color in SemanticColor:
            allowed.append((color,))

        # Pre-approved combinations that preserve meaning
        approved_combinations = [
            (SemanticColor.FOCUS, SemanticColor.SECONDARY),
            (SemanticColor.USER_ACTION, SemanticColor.SYSTEM_RESPONSE),
            (SemanticColor.NEUTRAL, SemanticColor.METADATA),
        ]

        for combo in approved_combinations:
            if not self.validate_composition(set(combo)):
                allowed.append(combo)

        return allowed

    def get_precedence_order(self) -> list[tuple[SemanticColor, int]]:
        """
        Get all colors ordered by precedence (highest first).

        Returns:
            List of (color, precedence) tuples
        """
        items = [(c, r.precedence) for c, r in self._rules.items()]
        return sorted(items, key=lambda x: x[1], reverse=True)


# Singleton instance for system-wide consistency
PALETTE = PaletteSystem()


def validate_color_usage(
    primary_color: SemanticColor, context_colors: set[SemanticColor] | None = None
) -> list[str]:
    """
    Validate that a color can be used in the given context.

    Args:
        primary_color: The main color to validate
        context_colors: Other colors present in the same view

    Returns:
        List of violation messages, empty if valid
    """
    violations: list[str] = []

    if context_colors is None:
        context_colors = set()

    all_colors = context_colors.union({primary_color})
    violations.extend(PALETTE.validate_composition(all_colors))

    return violations


def get_color_for_state(state_type: str) -> SemanticColor:
    """
    Map common observation/inquiry states to semantic colors.

    This ensures consistent mapping across the system.
    """
    mapping: dict[str, SemanticColor] = {
        # Observation states
        "complete_observation": SemanticColor.CERTAINTY,
        "partial_observation": SemanticColor.UNCERTAINTY,
        "failed_observation": SemanticColor.ERROR,
        "observation_limitation": SemanticColor.WARNING,
        # Inquiry states
        "current_focus": SemanticColor.FOCUS,
        "supporting_info": SemanticColor.SECONDARY,
        "user_question": SemanticColor.USER_ACTION,
        "system_response": SemanticColor.SYSTEM_RESPONSE,
        # Pattern states
        "clear_pattern": SemanticColor.NEUTRAL,
        "ambiguous_pattern": SemanticColor.UNCERTAINTY,
        "violation_pattern": SemanticColor.WARNING,
        # System states
        "system_status": SemanticColor.STATUS,
        "metadata": SemanticColor.METADATA,
    }

    return mapping.get(state_type, SemanticColor.NEUTRAL)


# Export the public API
__all__ = [
    "SemanticColor",
    "PaletteSystem",
    "PALETTE",
    "validate_color_usage",
    "get_color_for_state",
]
