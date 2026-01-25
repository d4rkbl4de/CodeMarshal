"""
lens/navigation/workflow.py

CRITICAL CONSTITUTIONAL GUARD: Primary Investigative Workflow
=============================================================
Workflow is structure, not behavior. A constitution, not a suggestion.

This file makes the canonical investigative sequence executable law:
orientation → examination → connections → patterns → thinking

WORKFLOW IS NOT:
- User intent guessing
- Heuristic optimization
- UI convenience features
- Recovery logic

WORKFLOW IS:
- Formal state model of epistemic progress
- Explicit allowed forward transitions
- Encoded prohibition of illegal jumps
- Deterministic navigation foundation

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 4: Progressive Disclosure (sequential stages)
- Article 6: Linear Investigation (canonical order)
- Article 7: Clear Affordances (explicit allowed actions)
- Article 16: Truth-Preserving Aesthetics (structure preserves truth)

ALLOWED IMPORTS:
- lens.philosophy.* (mandatory)
- lens.views.* (types only)
- inquiry.session.context (read-only)
- typing, enum, dataclasses

PROHIBITED IMPORTS:
- bridge.commands.*
- observations.*
- patterns.*
- storage.*
- Any UI code or widgets
"""

import enum
from dataclasses import dataclass
from typing import ClassVar
from uuid import UUID

# Allowed imports
from lens.views import ViewType  # Type only, no implementation


class WorkflowStage(enum.Enum):
    """
    Canonical stages of investigative progress.

    These represent epistemic levels, not UI screens.
    Each stage builds upon understanding gained in previous stages.
    """

    ORIENTATION = "orientation"
    """Establish context: What exists? Where am I looking?"""

    EXAMINATION = "examination"
    """Examine details: What is this specifically?"""

    CONNECTIONS = "connections"
    """Understand relationships: How is this connected?"""

    PATTERNS = "patterns"
    """Detect patterns: What regularities or anomalies exist?"""

    THINKING = "thinking"
    """Record human thoughts: What do I think about this?"""

    # Stage metadata for validation
    @property
    def display_name(self) -> str:
        """Human-readable name for this stage."""
        return {
            WorkflowStage.ORIENTATION: "Orientation",
            WorkflowStage.EXAMINATION: "Examination",
            WorkflowStage.CONNECTIONS: "Connections",
            WorkflowStage.PATTERNS: "Patterns",
            WorkflowStage.THINKING: "Thinking",
        }[self]

    @property
    def question_type(self) -> str:
        """Canonical question this stage answers."""
        return {
            WorkflowStage.ORIENTATION: "What exists here?",
            WorkflowStage.EXAMINATION: "What is this specifically?",
            WorkflowStage.CONNECTIONS: "How is this connected?",
            WorkflowStage.PATTERNS: "What patterns or anomalies exist?",
            WorkflowStage.THINKING: "What do I think?",
        }[self]

    @property
    def required_previous_stages(self) -> tuple["WorkflowStage", ...]:
        """Stages that must be completed before this one."""
        stage_order = list(WorkflowStage)
        current_index = stage_order.index(self)
        return tuple(stage_order[:current_index])


class WorkflowTransition:
    """
    Immutable record of a legal workflow transition.

    Contains validation that the transition preserves epistemic integrity.
    """

    def __init__(
        self,
        from_stage: WorkflowStage,
        to_stage: WorkflowStage,
        reason: str,
        required_view: ViewType | None = None,
    ) -> None:
        """
        Create a workflow transition.

        Args:
            from_stage: Current workflow stage
            to_stage: Target workflow stage
            reason: Epistemic justification for this transition
            required_view: Optional view type required for this transition

        Raises:
            ValueError: If transition violates workflow rules
        """
        self._validate_transition(from_stage, to_stage)

        self.from_stage = from_stage
        self.to_stage = to_stage
        self.reason = reason
        self.required_view = required_view

        # Transition ID for deterministic reference
        self.transition_id = f"{from_stage.value}→{to_stage.value}"

    def _validate_transition(
        self, from_stage: WorkflowStage, to_stage: WorkflowStage
    ) -> None:
        """Validate transition against constitutional principles."""
        # Article 4: Progressive Disclosure
        # Must not skip stages
        stage_order = list(WorkflowStage)
        from_index = stage_order.index(from_stage)
        to_index = stage_order.index(to_stage)

        if to_index > from_index + 1:
            raise ValueError(
                f"Cannot skip from {from_stage} to {to_stage}. "
                f"Must progress through stages sequentially (Article 4)."
            )

        # Article 6: Linear Investigation
        # Must not go backward in primary workflow (backward jumps are shortcuts, not workflow)
        if to_index < from_index:
            raise ValueError(
                f"Cannot go backward from {from_stage} to {to_stage} in primary workflow. "
                f"Backward jumps must be defined as shortcuts (Article 6)."
            )

        # Self-transitions are allowed (staying in same stage)
        if from_stage == to_stage:
            return

        # Transition must be explicitly allowed
        allowed_transitions = self._get_allowed_transitions()
        if (from_stage, to_stage) not in allowed_transitions:
            raise ValueError(
                f"Transition from {from_stage} to {to_stage} is not allowed. "
                f"Allowed transitions: {allowed_transitions}"
            )

    @classmethod
    def _get_allowed_transitions(cls) -> set[tuple[WorkflowStage, WorkflowStage]]:
        """Define ALL allowed primary workflow transitions."""
        return {
            # Primary canonical sequence
            (WorkflowStage.ORIENTATION, WorkflowStage.EXAMINATION),
            (WorkflowStage.EXAMINATION, WorkflowStage.CONNECTIONS),
            (WorkflowStage.CONNECTIONS, WorkflowStage.PATTERNS),
            (WorkflowStage.PATTERNS, WorkflowStage.THINKING),
            # Self-transitions are implicitly allowed
            # (for staying in same stage with different content)
        }

    def is_valid(self, current_view: ViewType | None = None) -> tuple[bool, str | None]:
        """
        Check if this transition is valid given current context.

        Args:
            current_view: Current view type (if known)

        Returns:
            Tuple of (is_valid, optional_error_message)
        """
        # Check required view
        if self.required_view and current_view != self.required_view:
            return False, f"Transition requires {self.required_view} view"

        return True, None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, WorkflowTransition):
            return False
        return self.transition_id == other.transition_id

    def __hash__(self) -> int:
        return hash(self.transition_id)

    def __str__(self) -> str:
        return f"{self.from_stage.value}→{self.to_stage.value}: {self.reason}"


@dataclass(frozen=True)
class WorkflowState:
    """
    Immutable representation of current workflow position.

    This is a compass bearing, not a map.
    Contains only current state, no history or future predictions.
    """

    current_stage: WorkflowStage
    """Current stage in the investigative workflow."""

    current_view: ViewType | None = None
    """Current view type, if applicable."""

    focus_id: str | None = None
    """ID of current focus subject (anchor, observation, etc.)."""

    session_id: UUID | None = None
    """ID of current investigation session."""

    def __post_init__(self) -> None:
        """Validate workflow state invariants."""
        if not isinstance(self.current_stage, WorkflowStage):
            raise TypeError("current_stage must be WorkflowStage")

        # Article 5: Single-Focus Interface
        # At most one focus subject at a time
        if self.focus_id and ";" in self.focus_id:
            raise ValueError(
                "focus_id cannot contain multiple IDs (Article 5: Single-Focus Interface)"
            )

    def can_transition_to(self, target_stage: WorkflowStage) -> tuple[bool, str | None]:
        """
        Check if transition to target stage is allowed.

        Args:
            target_stage: Stage to transition to

        Returns:
            Tuple of (is_allowed, optional_reason)
        """
        if self.current_stage == target_stage:
            return True, "Remaining in current stage"

        try:
            transition = WorkflowTransition(
                from_stage=self.current_stage,
                to_stage=target_stage,
                reason=f"Primary workflow progression from {self.current_stage} to {target_stage}",
            )
            return transition.is_valid(self.current_view)
        except ValueError as e:
            return False, str(e)

    def get_next_stage(self) -> WorkflowStage | None:
        """
        Get the next stage in canonical sequence, if any.

        Returns None if at final stage.
        """
        stage_order = list(WorkflowStage)
        current_index = stage_order.index(self.current_stage)

        if current_index < len(stage_order) - 1:
            return stage_order[current_index + 1]
        return None

    def get_previous_stage(self) -> WorkflowStage | None:
        """
        Get the previous stage in canonical sequence, if any.

        Returns None if at first stage.
        """
        stage_order = list(WorkflowStage)
        current_index = stage_order.index(self.current_stage)

        if current_index > 0:
            return stage_order[current_index - 1]
        return None

    def with_stage(self, new_stage: WorkflowStage) -> "WorkflowState":
        """Create new state with updated stage."""
        return WorkflowState(
            current_stage=new_stage,
            current_view=self.current_view,
            focus_id=self.focus_id,
            session_id=self.session_id,
        )

    def with_view(self, new_view: ViewType) -> "WorkflowState":
        """Create new state with updated view."""
        return WorkflowState(
            current_stage=self.current_stage,
            current_view=new_view,
            focus_id=self.focus_id,
            session_id=self.session_id,
        )

    def with_focus(self, new_focus_id: str) -> "WorkflowState":
        """Create new state with updated focus."""
        return WorkflowState(
            current_stage=self.current_stage,
            current_view=self.current_view,
            focus_id=new_focus_id,
            session_id=self.session_id,
        )


class WorkflowEngine:
    """
    Executable implementation of the workflow constitution.

    This class enforces workflow rules deterministically.
    No inference, no guessing, only rule application.
    """

    # Canonical workflow as immutable class variable
    CANONICAL_ORDER: ClassVar[tuple[WorkflowStage, ...]] = tuple(WorkflowStage)

    def __init__(self) -> None:
        """Initialize workflow engine with constitutional principles."""
        pass

    def validate_transition(
        self,
        current_state: WorkflowState,
        target_stage: WorkflowStage,
        target_view: ViewType | None = None,
    ) -> tuple[bool, str | None, WorkflowTransition | None]:
        """
        Validate a potential workflow transition.

        Args:
            current_state: Current workflow state
            target_stage: Desired target stage
            target_view: Desired target view (if changing view)

        Returns:
            Tuple of (is_valid, error_message, validated_transition)
        """
        # Check if staying in same stage (view change only)
        if current_state.current_stage == target_stage:
            if target_view and target_view != current_state.current_view:
                # View change within same stage is always allowed
                return (
                    True,
                    None,
                    WorkflowTransition(
                        from_stage=current_state.current_stage,
                        to_stage=target_stage,
                        reason=f"View change within {current_state.current_stage} stage",
                    ),
                )
            return True, None, None

        # Check primary workflow transition
        can_transition, reason = current_state.can_transition_to(target_stage)
        if not can_transition:
            return False, reason, None

        # Create validated transition
        try:
            transition = WorkflowTransition(
                from_stage=current_state.current_stage,
                to_stage=target_stage,
                reason=f"Primary workflow: {current_state.current_stage} → {target_stage}",
            )
            return True, None, transition
        except ValueError as e:
            return False, str(e), None

    def get_available_transitions(
        self, current_state: WorkflowState
    ) -> frozenset[WorkflowTransition]:
        """
        Get all valid transitions from current state.

        Args:
            current_state: Current workflow state

        Returns:
            Frozen set of valid WorkflowTransition objects
        """
        available = set()

        # Check next stage in canonical order
        next_stage = current_state.get_next_stage()
        if next_stage:
            can_transition, _ = current_state.can_transition_to(next_stage)
            if can_transition:
                available.add(
                    WorkflowTransition(
                        from_stage=current_state.current_stage,
                        to_stage=next_stage,
                        reason=f"Progress to next stage: {next_stage}",
                    )
                )

        # Self-transition (staying in same stage) is always available
        available.add(
            WorkflowTransition(
                from_stage=current_state.current_stage,
                to_stage=current_state.current_stage,
                reason="Remain in current stage",
            )
        )

        return frozenset(available)

    def enforce_progressive_disclosure(
        self, current_stage: WorkflowStage, requested_content_type: str
    ) -> tuple[bool, str | None]:
        """
        Enforce Article 4: Progressive Disclosure.

        Prevents showing content that requires understanding from later stages.

        Args:
            current_stage: Current workflow stage
            requested_content_type: Type of content being requested

        Returns:
            Tuple of (is_allowed, optional_reason)
        """
        # Define content maturity levels
        content_maturity = {
            "basic_observation": WorkflowStage.ORIENTATION,
            "detailed_observation": WorkflowStage.EXAMINATION,
            "connection_graph": WorkflowStage.CONNECTIONS,
            "pattern_report": WorkflowStage.PATTERNS,
            "human_notes": WorkflowStage.THINKING,
            "export_full": WorkflowStage.THINKING,
        }

        required_stage = content_maturity.get(requested_content_type)
        if required_stage is None:
            # Unknown content type - assume it's allowed
            # (safer to allow than to incorrectly block)
            return True, None

        # Check if current stage is at least as advanced as required stage
        stage_order = list(WorkflowStage)
        current_index = stage_order.index(current_stage)
        required_index = stage_order.index(required_stage)

        if current_index >= required_index:
            return True, None
        else:
            return False, (
                f"Cannot show {requested_content_type} content at {current_stage} stage. "
                f"Requires at least {required_stage} stage (Article 4: Progressive Disclosure)."
            )

    def get_initial_state(self, session_id: UUID | None = None) -> WorkflowState:
        """
        Get initial workflow state for new investigation.

        Args:
            session_id: Optional session identifier

        Returns:
            Initial workflow state at ORIENTATION stage
        """
        return WorkflowState(
            current_stage=WorkflowStage.ORIENTATION,
            current_view=None,
            focus_id=None,
            session_id=session_id,
        )

    def is_complete_investigation(self, state: WorkflowState) -> bool:
        """
        Check if investigation has reached the final (THINKING) stage.

        This doesn't mean the investigation is "done" -
        just that the canonical workflow progression is complete.

        Args:
            state: Workflow state to check

        Returns:
            True if at THINKING stage, False otherwise
        """


@dataclass(frozen=True)
class Step:
    """
    Immutable representation of a single workflow step.

    Used by UI components to understand current position and affordances.
    """

    current: WorkflowStage
    next_up: WorkflowStage | None = None
    previous: WorkflowStage | None = None
    guidance: str | None = None


class WorkflowNavigator:
    """
    Guided navigation utility for workflow progression.

    This class maps application states to investigative stages,
    ensuring that the UI layer respects workflow law.
    """

    def __init__(self) -> None:
        """Initialize navigator with a workflow engine."""
        self._engine = WorkflowEngine()

    def get_step(self, status: str) -> Step | None:
        """
        Map a status or state string to a workflow Step.

        Args:
            status: String identifier for current application state

        Returns:
            Step object if mapping exists, else None
        """
        # Canonical mapping of TUI states to workflow stages
        mapping = {
            "initial": WorkflowStage.ORIENTATION,
            "awaiting_path": WorkflowStage.ORIENTATION,
            "observing": WorkflowStage.ORIENTATION,
            "observation": WorkflowStage.ORIENTATION,
            "orientation": WorkflowStage.ORIENTATION,
            "questioning": WorkflowStage.EXAMINATION,
            "examination": WorkflowStage.EXAMINATION,
            "connections": WorkflowStage.CONNECTIONS,
            "connecting": WorkflowStage.CONNECTIONS,
            "pattern_analysis": WorkflowStage.PATTERNS,
            "patterns": WorkflowStage.PATTERNS,
            "noting": WorkflowStage.THINKING,
            "thinking": WorkflowStage.THINKING,
            "notes": WorkflowStage.THINKING,
            "exporting": WorkflowStage.THINKING,
            "refusing": WorkflowStage.ORIENTATION,
        }

        stage = mapping.get(status.lower())
        if not stage:
            return None

        # Calculate context
        stage_order = list(WorkflowStage)
        idx = stage_order.index(stage)

        previous = stage_order[idx - 1] if idx > 0 else None
        next_up = stage_order[idx + 1] if idx < len(stage_order) - 1 else None

        # Provide guidance for each stage
        guidance_map = {
            WorkflowStage.ORIENTATION: "Enter path to begin investigation",
            WorkflowStage.EXAMINATION: "Ask questions about what you observe",
            WorkflowStage.CONNECTIONS: "Explore how elements are connected",
            WorkflowStage.PATTERNS: "Look for patterns and anomalies",
            WorkflowStage.THINKING: "Record your thoughts and insights",
        }

        return Step(
            current=stage,
            next_up=next_up,
            previous=previous,
            guidance=guidance_map.get(stage),
        )


def validate_workflow_integrity() -> tuple[bool, str | None]:
    """
    Validate that workflow implementation follows constitutional rules.

    Returns:
        Tuple of (is_valid, optional_error_message)
    """
    try:
        WorkflowEngine()

        # Test 1: Canonical order must be preserved
        for i in range(len(WorkflowEngine.CANONICAL_ORDER) - 1):
            current = WorkflowEngine.CANONICAL_ORDER[i]
            next_stage = WorkflowEngine.CANONICAL_ORDER[i + 1]

            state = WorkflowState(current_stage=current)
            can_transition, reason = state.can_transition_to(next_stage)

            if not can_transition:
                return (
                    False,
                    f"Canonical transition {current}→{next_stage} failed: {reason}",
                )

        # Test 2: No backward transitions in primary workflow
        for i in range(1, len(WorkflowEngine.CANONICAL_ORDER)):
            current = WorkflowEngine.CANONICAL_ORDER[i]
            previous = WorkflowEngine.CANONICAL_ORDER[i - 1]

            state = WorkflowState(current_stage=current)
            can_transition, _ = state.can_transition_to(previous)

            if can_transition:
                return (
                    False,
                    f"Backward transition {current}→{previous} should not be allowed",
                )

        # Test 3: No stage skipping
        for i in range(len(WorkflowEngine.CANONICAL_ORDER) - 2):
            current = WorkflowEngine.CANONICAL_ORDER[i]
            skip_target = WorkflowEngine.CANONICAL_ORDER[i + 2]

            state = WorkflowState(current_stage=current)
            can_transition, _ = state.can_transition_to(skip_target)

            if can_transition:
                return (
                    False,
                    f"Stage skipping {current}→{skip_target} should not be allowed",
                )

        return True, None

    except Exception as e:
        return False, f"Workflow integrity validation failed: {e}"


def get_canonical_workflow_description() -> str:
    """Get human-readable description of the canonical workflow."""
    stages = list(WorkflowStage)
    description_lines = ["CANONICAL INVESTIGATIVE WORKFLOW", "=" * 40]

    for i, stage in enumerate(stages):
        description_lines.append(f"{i + 1}. {stage.display_name}")
        description_lines.append(f"   Question: {stage.question_type}")

        if i < len(stages) - 1:
            next_stage = stages[i + 1]
            description_lines.append(f"   → Leads to: {next_stage.display_name}")

    description_lines.append("")
    description_lines.append("CONSTITUTIONAL RULES:")
    description_lines.append("- Must progress sequentially (Article 4)")
    description_lines.append("- Cannot skip stages (Article 6)")
    description_lines.append("- Each stage builds on previous understanding")
    description_lines.append(
        "- Completion of THINKING stage indicates workflow progress, not investigation completion"
    )

    return "\n".join(description_lines)
