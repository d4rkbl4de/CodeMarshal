"""
Navigation Constraint (Article 6 Enforcement)

This module defines the permitted transitions in an investigation, enforcing
the natural flow of human curiosity while preventing random jumps.

CRITICAL: This defines the SHAPE of curiosity, not the path taken.
It answers "Where can curiosity go from here?" not "How do we get there?"
Violations are Tier-2 (immediate halt).
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Protocol, runtime_checkable

# ------------------------------------------------------------------------------
# SESSION CONTEXT: WHERE WE ARE NOW
# ------------------------------------------------------------------------------


# Import only the type definition, not implementation
@runtime_checkable
class InvestigationContext(Protocol):
    """Read-only view of the current investigation state."""

    @property
    def current_question_type(self) -> str | None:
        """Type of the most recent human question, if any."""
        ...

    @property
    def current_focus_anchor(self) -> str | None:
        """Specific observation or pattern being examined, if any."""
        ...

    @property
    def visited_question_types(self) -> frozenset[str]:
        """All question types asked in this session."""
        ...

    @property
    def is_initial_state(self) -> bool:
        """True if no questions have been asked yet."""
        ...


# ------------------------------------------------------------------------------
# QUESTION TYPES: WHAT HUMANS CAN ASK (TYPES ONLY)
# ------------------------------------------------------------------------------


class QuestionType(Enum):
    """Canonical question types with fixed ordering."""

    STRUCTURE = auto()  # "What's here?" - First question
    PURPOSE = auto()  # "What does this do?" - Second
    CONNECTIONS = auto()  # "How is it connected?" - Third
    ANOMALIES = auto()  # "What seems unusual?" - Fourth
    THINKING = auto()  # "What do I think?" - Fifth

    @classmethod
    def get_order(cls) -> list["QuestionType"]:
        """Fixed investigation sequence (Article 6)."""
        return [
            cls.STRUCTURE,
            cls.PURPOSE,
            cls.CONNECTIONS,
            cls.ANOMALIES,
            cls.THINKING,
        ]

    @classmethod
    def is_valid_type(cls, question_type: str) -> bool:
        """Check if a string represents a valid question type."""
        try:
            cls[question_type.upper()]
            return True
        except KeyError:
            return False

    @classmethod
    def from_string(cls, question_type: str) -> Optional["QuestionType"]:
        """Convert string to enum, returns None if invalid."""
        try:
            return cls[question_type.upper()]
        except KeyError:
            return None


# ------------------------------------------------------------------------------
# TRANSITION RULES: WHERE CURIOSITY CAN GO
# ------------------------------------------------------------------------------


@dataclass(frozen=True)
class TransitionRule:
    """
    Immutable rule defining a permitted state transition.

    These rules encode Article 6: "Follow natural human curiosity"
    and "Never skip ahead or jump randomly."
    """

    from_type: QuestionType | None  # None = initial state
    to_type: QuestionType
    allowed: bool
    explanation: str  # Why this is allowed/prohibited

    @property
    def is_forward(self) -> bool:
        """Whether this moves forward in the investigation sequence."""
        if self.from_type is None:
            return True  # Starting is always forward

        order = QuestionType.get_order()
        from_idx = order.index(self.from_type)
        to_idx = order.index(self.to_type)
        return to_idx > from_idx

    @property
    def is_backward(self) -> bool:
        """Whether this moves backward in the investigation sequence."""
        if self.from_type is None:
            return False

        order = QuestionType.get_order()
        from_idx = order.index(self.from_type)
        to_idx = order.index(self.to_type)
        return to_idx < from_idx

    @property
    def is_lateral(self) -> bool:
        """Whether this stays at the same stage."""
        if self.from_type is None:
            return False

        return self.from_type == self.to_type


class NavigationViolation(Exception):
    """Raised when an attempted transition violates Article 6."""

    def __init__(
        self,
        from_type: QuestionType | None,
        to_type: QuestionType,
        rule: TransitionRule | None = None,
    ) -> None:
        self.from_type = from_type
        self.to_type = to_type
        self.rule = rule

        if rule and not rule.allowed:
            msg = rule.explanation
        elif from_type is None:
            msg = f"Cannot start investigation with '{to_type.name}' question. Must begin with STRUCTURE."
        else:
            order = QuestionType.get_order()
            from_name = from_type.name if from_type else "START"
            from_idx = order.index(from_type) if from_type else -1
            to_idx = order.index(to_type)

            if to_idx > from_idx + 1:
                skipped = [qt.name for qt in order[from_idx + 1 : to_idx]]
                msg = (
                    f"Cannot skip from '{from_name}' to '{to_type.name}'. "
                    f"Must address {', '.join(skipped)} first."
                )
            else:
                msg = f"Transition from '{from_name}' to '{to_type.name}' violates linear investigation."

        super().__init__(msg)


# ------------------------------------------------------------------------------
# CORE RULE: LINEAR INVESTIGATION VALIDATOR
# ------------------------------------------------------------------------------


class NavigationRule:
    """
    Enforces Article 6: Linear Investigation.

    This rule ensures that:
    1. Investigations must start with STRUCTURE questions
    2. Questions must follow the natural sequence (cannot skip stages)
    3. Backward movement is allowed only to previously visited stages
    4. Lateral movement (same question type) is always allowed
    5. Random jumps are prohibited

    The rule is STATELESS - it uses the session context to determine
    what has been visited, but doesn't modify it.
    """

    # Define all transition rules (immutable system configuration)
    _TRANSITION_RULES: dict[QuestionType | None, dict[QuestionType, TransitionRule]] = {
        # From initial state (None)
        None: {
            QuestionType.STRUCTURE: TransitionRule(
                from_type=None,
                to_type=QuestionType.STRUCTURE,
                allowed=True,
                explanation="Investigations must begin with 'What's here?' (STRUCTURE)",
            ),
            QuestionType.PURPOSE: TransitionRule(
                from_type=None,
                to_type=QuestionType.PURPOSE,
                allowed=False,
                explanation="Cannot start with purpose questions. Must establish what exists first.",
            ),
            QuestionType.CONNECTIONS: TransitionRule(
                from_type=None,
                to_type=QuestionType.CONNECTIONS,
                allowed=False,
                explanation="Cannot start with connection questions. Must understand what exists and does first.",
            ),
            QuestionType.ANOMALIES: TransitionRule(
                from_type=None,
                to_type=QuestionType.ANOMALIES,
                allowed=False,
                explanation="Cannot start with anomaly detection. Must establish baseline understanding first.",
            ),
            QuestionType.THINKING: TransitionRule(
                from_type=None,
                to_type=QuestionType.THINKING,
                allowed=False,
                explanation="Cannot start with reflective thinking. Must have observations to reflect upon.",
            ),
        },
        # From STRUCTURE
        QuestionType.STRUCTURE: {
            QuestionType.STRUCTURE: TransitionRule(
                from_type=QuestionType.STRUCTURE,
                to_type=QuestionType.STRUCTURE,
                allowed=True,
                explanation="Can ask more structure questions about different aspects",
            ),
            QuestionType.PURPOSE: TransitionRule(
                from_type=QuestionType.STRUCTURE,
                to_type=QuestionType.PURPOSE,
                allowed=True,
                explanation="Natural progression: After seeing what exists, ask what it does",
            ),
            QuestionType.CONNECTIONS: TransitionRule(
                from_type=QuestionType.STRUCTURE,
                to_type=QuestionType.CONNECTIONS,
                allowed=False,
                explanation="Cannot skip from structure to connections. Must understand purpose first.",
            ),
            QuestionType.ANOMALIES: TransitionRule(
                from_type=QuestionType.STRUCTURE,
                to_type=QuestionType.ANOMALIES,
                allowed=False,
                explanation="Cannot skip from structure to anomalies. Must understand normal structure and purpose first.",
            ),
            QuestionType.THINKING: TransitionRule(
                from_type=QuestionType.STRUCTURE,
                to_type=QuestionType.THINKING,
                allowed=False,
                explanation="Cannot jump to thinking from structure alone. Need deeper investigation first.",
            ),
        },
        # From PURPOSE
        QuestionType.PURPOSE: {
            QuestionType.STRUCTURE: TransitionRule(
                from_type=QuestionType.PURPOSE,
                to_type=QuestionType.STRUCTURE,
                allowed=True,
                explanation="Can return to structure to re-examine foundations",
            ),
            QuestionType.PURPOSE: TransitionRule(
                from_type=QuestionType.PURPOSE,
                to_type=QuestionType.PURPOSE,
                allowed=True,
                explanation="Can ask more purpose questions about different elements",
            ),
            QuestionType.CONNECTIONS: TransitionRule(
                from_type=QuestionType.PURPOSE,
                to_type=QuestionType.CONNECTIONS,
                allowed=True,
                explanation="Natural progression: After understanding purpose, examine connections",
            ),
            QuestionType.ANOMALIES: TransitionRule(
                from_type=QuestionType.PURPOSE,
                to_type=QuestionType.ANOMALIES,
                allowed=False,
                explanation="Cannot skip from purpose to anomalies. Must examine connections first.",
            ),
            QuestionType.THINKING: TransitionRule(
                from_type=QuestionType.PURPOSE,
                to_type=QuestionType.THINKING,
                allowed=False,
                explanation="Cannot jump to thinking from purpose alone. Need to see connections and anomalies first.",
            ),
        },
        # From CONNECTIONS
        QuestionType.CONNECTIONS: {
            QuestionType.STRUCTURE: TransitionRule(
                from_type=QuestionType.CONNECTIONS,
                to_type=QuestionType.STRUCTURE,
                allowed=True,
                explanation="Can return to structure to verify foundations",
            ),
            QuestionType.PURPOSE: TransitionRule(
                from_type=QuestionType.CONNECTIONS,
                to_type=QuestionType.PURPOSE,
                allowed=True,
                explanation="Can return to purpose to clarify intent",
            ),
            QuestionType.CONNECTIONS: TransitionRule(
                from_type=QuestionType.CONNECTIONS,
                to_type=QuestionType.CONNECTIONS,
                allowed=True,
                explanation="Can examine different connection aspects",
            ),
            QuestionType.ANOMALIES: TransitionRule(
                from_type=QuestionType.CONNECTIONS,
                to_type=QuestionType.ANOMALIES,
                allowed=True,
                explanation="Natural progression: After seeing connections, look for unusual patterns",
            ),
            QuestionType.THINKING: TransitionRule(
                from_type=QuestionType.CONNECTIONS,
                to_type=QuestionType.THINKING,
                allowed=False,
                explanation="Cannot jump to thinking from connections alone. Must examine anomalies first.",
            ),
        },
        # From ANOMALIES
        QuestionType.ANOMALIES: {
            QuestionType.STRUCTURE: TransitionRule(
                from_type=QuestionType.ANOMALIES,
                to_type=QuestionType.STRUCTURE,
                allowed=True,
                explanation="Can return to structure to verify anomaly foundations",
            ),
            QuestionType.PURPOSE: TransitionRule(
                from_type=QuestionType.ANOMALIES,
                to_type=QuestionType.PURPOSE,
                allowed=True,
                explanation="Can return to purpose to understand anomaly context",
            ),
            QuestionType.CONNECTIONS: TransitionRule(
                from_type=QuestionType.ANOMALIES,
                to_type=QuestionType.CONNECTIONS,
                allowed=True,
                explanation="Can return to connections to trace anomaly paths",
            ),
            QuestionType.ANOMALIES: TransitionRule(
                from_type=QuestionType.ANOMALIES,
                to_type=QuestionType.ANOMALIES,
                allowed=True,
                explanation="Can examine different anomalies",
            ),
            QuestionType.THINKING: TransitionRule(
                from_type=QuestionType.ANOMALIES,
                to_type=QuestionType.THINKING,
                allowed=True,
                explanation="Natural progression: After finding anomalies, reflect on their meaning",
            ),
        },
        # From THINKING
        QuestionType.THINKING: {
            QuestionType.STRUCTURE: TransitionRule(
                from_type=QuestionType.THINKING,
                to_type=QuestionType.STRUCTURE,
                allowed=True,
                explanation="Can return to structure to verify thinking foundations",
            ),
            QuestionType.PURPOSE: TransitionRule(
                from_type=QuestionType.THINKING,
                to_type=QuestionType.PURPOSE,
                allowed=True,
                explanation="Can return to purpose to re-examine intent",
            ),
            QuestionType.CONNECTIONS: TransitionRule(
                from_type=QuestionType.THINKING,
                to_type=QuestionType.CONNECTIONS,
                allowed=True,
                explanation="Can return to connections to re-trace relationships",
            ),
            QuestionType.ANOMALIES: TransitionRule(
                from_type=QuestionType.THINKING,
                to_type=QuestionType.ANOMALIES,
                allowed=True,
                explanation="Can return to anomalies to re-examine unusual patterns",
            ),
            QuestionType.THINKING: TransitionRule(
                from_type=QuestionType.THINKING,
                to_type=QuestionType.THINKING,
                allowed=True,
                explanation="Can continue reflective thinking",
            ),
        },
    }

    def __init__(self) -> None:
        # Validate that all rules are properly defined
        self._validate_rule_consistency()

    def _validate_rule_consistency(self) -> None:
        """Ensure all transitions are properly defined."""
        all_types = list(QuestionType) + [None]

        for from_type in all_types:
            if from_type not in self._TRANSITION_RULES:
                raise ValueError(f"Missing transition rules for {from_type}")

            rules = self._TRANSITION_RULES[from_type]
            for to_type in QuestionType:
                if to_type not in rules:
                    raise ValueError(f"Missing rule for {from_type} -> {to_type}")

    def get_transition_rule(
        self, from_type: QuestionType | None, to_type: QuestionType
    ) -> TransitionRule:
        """
        Get the rule governing a specific transition.

        Raises:
            ValueError: If the transition is not defined (should never happen)
        """
        try:
            return self._TRANSITION_RULES[from_type][to_type]
        except KeyError:
            # This indicates a bug in rule definition
            from_name = from_type.name if from_type else "START"
            raise ValueError(
                f"No transition rule defined for {from_name} -> {to_type.name}"
            ) from None

    def validate_transition(
        self, context: InvestigationContext, target_question_type: str
    ) -> None:
        """
        Validate that moving to a new question type is permitted.

        Args:
            context: Current investigation state (read-only)
            target_question_type: The question type being requested

        Raises:
            NavigationViolation: If transition violates Article 6
            ValueError: If target_question_type is invalid
        """
        # Convert target to enum
        target_enum = QuestionType.from_string(target_question_type)
        if target_enum is None:
            raise ValueError(f"Invalid question type: {target_question_type}")

        # Get current question type
        current_str = context.current_question_type
        current_enum = None
        if current_str:
            current_enum = QuestionType.from_string(current_str)
            if current_enum is None:
                # This indicates corrupted session state
                raise ValueError(
                    f"Invalid current question type in context: {current_str}"
                )

        # Get the transition rule
        rule = self.get_transition_rule(current_enum, target_enum)

        # Check if allowed by basic rule
        if not rule.allowed:
            raise NavigationViolation(current_enum, target_enum, rule)

        # Additional constraint: Can only move backward to visited stages
        # (except for STRUCTURE which is always allowed to return to)
        if rule.is_backward and target_enum != QuestionType.STRUCTURE:
            visited_enums = {
                QuestionType.from_string(qt)
                for qt in context.visited_question_types
                if QuestionType.from_string(qt) is not None
            }

            if target_enum not in visited_enums:
                raise NavigationViolation(
                    current_enum,
                    target_enum,
                    TransitionRule(
                        from_type=current_enum,
                        to_type=target_enum,
                        allowed=False,
                        explanation=f"Cannot return to '{target_enum.name}' as it hasn't been visited yet in this investigation.",
                    ),
                )

    def get_allowed_transitions(
        self, context: InvestigationContext
    ) -> dict[QuestionType, str]:
        """
        Get all question types that can be asked next from current state.

        Returns dict of {question_type: explanation} for allowed transitions.
        """
        # Get current question type
        current_str = context.current_question_type
        current_enum = None
        if current_str:
            current_enum = QuestionType.from_string(current_str)
            if current_enum is None:
                # Corrupted state - return empty
                return {}

        # Get visited question types as enums
        visited_enums = {
            qt_enum
            for qt_str in context.visited_question_types
            if (qt_enum := QuestionType.from_string(qt_str)) is not None
        }

        allowed: dict[QuestionType, str] = {}

        for target_enum in QuestionType:
            rule = self.get_transition_rule(current_enum, target_enum)

            # Check basic rule
            if not rule.allowed:
                continue

            # Check backward constraint
            if rule.is_backward and target_enum != QuestionType.STRUCTURE:
                if target_enum not in visited_enums:
                    continue

            allowed[target_enum] = rule.explanation

        return allowed


# ------------------------------------------------------------------------------
# VALIDATION UTILITIES (FOR INTERFACE IMPLEMENTERS)
# ------------------------------------------------------------------------------


def can_ask_question(context: InvestigationContext, question_type: str) -> bool:
    """
    Helper for interfaces to check if a question can be asked.

    Returns True if the transition is allowed.
    Use this to enable/disable question options.

    Example:
        can_ask = can_ask_question(context, "purpose")
    """
    rule = NavigationRule()

    try:
        rule.validate_transition(context, question_type)
        return True
    except (NavigationViolation, ValueError):
        return False


def get_next_natural_question(context: InvestigationContext) -> QuestionType | None:
    """
    Get the next question type in the natural sequence.

    Returns None if:
    - No natural next exists (at thinking stage)
    - Session is in invalid state

    Useful for interfaces suggesting "What to ask next?"
    """
    current_str = context.current_question_type
    if not current_str:
        return QuestionType.STRUCTURE

    current_enum = QuestionType.from_string(current_str)
    if current_enum is None:
        return None

    order = QuestionType.get_order()
    try:
        current_idx = order.index(current_enum)
        if current_idx + 1 < len(order):
            return order[current_idx + 1]
    except ValueError:
        pass

    return None


# ------------------------------------------------------------------------------
# TEST UTILITIES (FOR INTEGRITY GUARDIAN)
# ------------------------------------------------------------------------------


@dataclass
class MockInvestigationContext:
    """Minimal implementation for testing."""

    current_question_type: str | None = None
    current_focus_anchor: str | None = None
    visited_question_types: frozenset[str] = frozenset()
    is_initial_state: bool = True

    def __post_init__(self) -> None:
        if self.current_question_type is None:
            self.is_initial_state = True
            self.visited_question_types = frozenset()
        else:
            self.is_initial_state = False
            if self.current_question_type not in self.visited_question_types:
                # This shouldn't happen in real contexts, but for testing
                self.visited_question_types = frozenset([self.current_question_type])


# ------------------------------------------------------------------------------
# EXPORTED CONTRACT
# ------------------------------------------------------------------------------

__all__ = [
    # Context Protocol
    "InvestigationContext",
    # Question Types
    "QuestionType",
    # Transition Rules
    "TransitionRule",
    "NavigationViolation",
    # Core Rule
    "NavigationRule",
    # Utilities
    "can_ask_question",
    "get_next_natural_question",
    # Test Utilities (exported for integrity tests only)
    "MockInvestigationContext",
]
