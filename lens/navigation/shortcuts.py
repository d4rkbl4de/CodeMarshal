"""
lens/navigation/shortcuts.py

CRITICAL CONSTITUTIONAL GUARD: Constrained Navigation Shortcuts
===============================================================
Shortcuts are emergency exits, not secret tunnels.

Shortcuts are NOT:
- Forward skips (violates Article 4)
- Hidden accelerators (violates Article 7)
- Implicit permissions (violates Article 6)
- Convenience features

Shortcuts ARE:
- Read-only jumps backward (preserves epistemic safety)
- View toggles at same epistemic level (maintains clarity)
- Re-inspection paths (no information skipped)
- Explicitly justified by constitutional principles

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 4: Progressive Disclosure (no skipping forward)
- Article 6: Linear Investigation (explicit backward jumps only)
- Article 7: Clear Affordances (visible, justified shortcuts)
- Article 14: Graceful Degradation (recovery via shortcuts)

ALLOWED IMPORTS:
- lens.philosophy.* (mandatory for justification)
- lens.views.* (types only)
- inquiry.session.context (read-only)
- typing, enum, dataclasses, uuid

PROHIBITED IMPORTS:
- bridge.commands.*
- observations.*
- patterns.*
- storage.*
- Any UI code
"""

import enum
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, ClassVar

from inquiry.session.context import SessionContext
from lens.navigation.workflow import WorkflowStage, WorkflowState

# Allowed imports
from lens.views import ViewType


class ShortcutType(enum.Enum):
    """
    Explicit enumeration of ALL allowed shortcut types.

    Each type must have a constitutional justification.
    """

    # Read-only jumps backward
    BACK_TO_ORIENTATION = "back_to_orientation"
    """Return to orientation from any stage. Justification: Context re-establishment."""

    BACK_TO_EXAMINATION = "back_to_examination"
    """Return to examination from connections/patterns/thinking. Justification: Detail review."""

    BACK_TO_CONNECTIONS = "back_to_connections"
    """Return to connections from patterns/thinking. Justification: Relationship review."""

    BACK_TO_PATTERNS = "back_to_patterns"
    """Return to patterns from thinking. Justification: Pattern review."""

    # View toggles at same epistemic level
    TOGGLE_OVERVIEW_DETAIL = "toggle_overview_detail"
    """Switch between overview and detailed view in same stage. Justification: Focus adjustment."""

    TOGGLE_GRAPH_TABLE = "toggle_graph_table"
    """Switch between graph and table views. Justification: Representation preference."""

    TOGGLE_CODE_VISUAL = "toggle_code_visual"
    """Switch between code and visualization views. Justification: Cognitive mode."""

    # Re-inspection paths
    REINSPECT_SAME_ANCHOR = "reinspect_same_anchor"
    """Re-examine same anchor with fresh observation. Justification: Observation refresh."""

    REINSPECT_PARENT = "reinspect_parent"
    """Examine parent of current focus. Justification: Context expansion."""

    REINSPECT_CHILD = "reinspect_child"
    """Examine child of current focus. Justification: Detail expansion."""

    REINSPECT_SIBLING = "reinspect_sibling"
    """Examine sibling of current focus. Justification: Comparative analysis."""

    # Navigation recovery
    RETURN_TO_LAST_VALID = "return_to_last_valid"
    """Return to last known valid state. Justification: Error recovery."""

    RESET_TO_INITIAL = "reset_to_initial"
    """Reset to initial investigation state. Justification: Complete restart."""


@dataclass(frozen=True)
class Shortcut:
    """
    Immutable, justified shortcut definition.

    Every shortcut must:
    1. Have explicit constitutional justification
    2. Preserve epistemic safety (no information skipped)
    3. Maintain clarity (purpose is obvious)
    4. Be deterministic (same conditions yield same availability)
    """

    shortcut_type: ShortcutType
    """Type of shortcut."""

    from_stage: WorkflowStage
    """Stage from which shortcut originates."""

    to_stage: WorkflowStage
    """Stage to which shortcut leads."""

    justification: str
    """Constitutional justification for this shortcut."""

    # Constraints
    requires_same_focus: bool = False
    """True if shortcut requires same focus (not changing focus)."""

    allows_focus_change: bool = True
    """True if shortcut allows changing focus (default True)."""

    requires_same_view: bool = False
    """True if shortcut requires same view type."""

    allowed_views: frozenset[ViewType] | None = None
    """Specific views where this shortcut is available."""

    maximum_uses: int | None = None
    """Maximum number of times this shortcut can be used in a session."""

    cooldown_seconds: int | None = None
    """Minimum seconds between uses (prevents rapid oscillation)."""

    # Metadata
    shortcut_id: str = ""
    """Unique identifier for this shortcut instance."""

    created_at: datetime = datetime.now(UTC)
    """When this shortcut was created."""

    def __post_init__(self) -> None:
        """Validate shortcut invariants."""
        if not isinstance(self.shortcut_type, ShortcutType):
            raise TypeError("shortcut_type must be ShortcutType")

        if not isinstance(self.from_stage, WorkflowStage):
            raise TypeError("from_stage must be WorkflowStage")

        if not isinstance(self.to_stage, WorkflowStage):
            raise TypeError("to_stage must be WorkflowStage")

        if not self.justification:
            raise ValueError("justification cannot be empty")

        # Validate constitutional justification
        self._validate_justification()

        # Set shortcut_id if not provided
        if not self.shortcut_id:
            object.__setattr__(
                self,
                "shortcut_id",
                f"{self.shortcut_type.value}_{self.from_stage.value}_{self.to_stage.value}",
            )

        # Validate timezone
        if self.created_at.tzinfo is None:
            object.__setattr__(self, "created_at", self.created_at.replace(tzinfo=UTC))

    def _validate_justification(self) -> None:
        """Validate that justification references constitutional principles."""
        principles = [
            "Article 4",
            "Article 6",
            "Article 7",
            "Article 14",
            "Progressive Disclosure",
            "Linear Investigation",
            "Clear Affordances",
            "Graceful Degradation",
        ]

        justification_lower = self.justification.lower()
        has_principle_reference = any(
            principle.lower() in justification_lower for principle in principles
        )

        if not has_principle_reference:
            raise ValueError(
                f"Shortcut justification must reference constitutional principles. "
                f"Justification: {self.justification}"
            )

    def is_available(
        self,
        current_state: WorkflowState,
        session_context: SessionContext | None = None,
        shortcut_history: list["Shortcut"] | None = None,
    ) -> tuple[bool, str | None]:
        """
        Check if this shortcut is available given current context.

        Args:
            current_state: Current workflow state
            session_context: Optional session context (for focus validation)
            shortcut_history: Optional history of shortcuts used in this session

        Returns:
            Tuple of (is_available, reason_if_unavailable)
        """
        # 1. Check current stage matches
        if current_state.current_stage != self.from_stage:
            return (
                False,
                f"Current stage {current_state.current_stage} does not match from_stage {self.from_stage}",
            )

        # 2. Check view constraints
        if self.allowed_views is not None:
            if current_state.current_view not in self.allowed_views:
                return (
                    False,
                    f"Current view {current_state.current_view} not in allowed views",
                )

        if self.requires_same_view and current_state.current_view is None:
            return False, "Requires specific view but current view is None"

        # 3. Check focus constraints
        if self.requires_same_focus:
            if not current_state.focus_id:
                return False, "Requires focus but none set"
            if session_context and session_context.anchor_id != current_state.focus_id:
                return (
                    False,
                    "Focus mismatch between workflow state and session context",
                )

        # 4. Check usage limits
        if shortcut_history and self.maximum_uses is not None:
            same_type_uses = sum(
                1 for s in shortcut_history if s.shortcut_type == self.shortcut_type
            )
            if same_type_uses >= self.maximum_uses:
                return False, f"Maximum uses ({self.maximum_uses}) exceeded"

        # 5. Check cooldown
        if shortcut_history and self.cooldown_seconds is not None:
            # Find most recent use of this shortcut type
            recent_uses = [
                s for s in shortcut_history if s.shortcut_type == self.shortcut_type
            ]
            if recent_uses:
                latest_use = max(s.created_at for s in recent_uses)
                time_since_use = (datetime.now(UTC) - latest_use).total_seconds()
                if time_since_use < self.cooldown_seconds:
                    return (
                        False,
                        f"Cooldown active ({int(self.cooldown_seconds - time_since_use)}s remaining)",
                    )

        # 6. Validate no forward skipping
        stage_order = list(WorkflowStage)
        from_index = stage_order.index(self.from_stage)
        to_index = stage_order.index(self.to_stage)

        # Article 4: No forward skipping in shortcuts
        if to_index > from_index:
            return (
                False,
                f"Cannot use shortcut to skip forward from {self.from_stage} to {self.to_stage} (Article 4)",
            )

        return True, None

    def create_target_state(
        self,
        current_state: WorkflowState,
        session_context: SessionContext | None = None,
    ) -> WorkflowState:
        """
        Create target workflow state after applying this shortcut.

        Args:
            current_state: Current workflow state
            session_context: Optional session context for focus determination

        Returns:
            New workflow state after shortcut application
        """
        # Determine focus for target state
        new_focus_id = current_state.focus_id

        # Handle focus-changing shortcuts
        if self.shortcut_type == ShortcutType.REINSPECT_PARENT:
            # Extract parent from focus_id (assuming format "type:path:to:parent/child")
            if new_focus_id and ":" in new_focus_id:
                parts = new_focus_id.split(":")
                if len(parts) > 1:
                    new_focus_id = ":".join(parts[:-1])

        elif self.shortcut_type == ShortcutType.REINSPECT_CHILD:
            # This would require knowing which child to inspect
            # For now, keep same focus (implementation detail for bridge layer)
            pass

        elif self.shortcut_type == ShortcutType.REINSPECT_SIBLING:
            # This would require sibling discovery
            # For now, keep same focus
            pass

        # Determine view for target state
        new_view = current_state.current_view

        # Handle view toggle shortcuts
        if self.shortcut_type == ShortcutType.TOGGLE_OVERVIEW_DETAIL:
            if new_view == ViewType.OVERVIEW:
                new_view = ViewType.EXAMINATION
            elif new_view == ViewType.EXAMINATION:
                new_view = ViewType.OVERVIEW

        elif self.shortcut_type == ShortcutType.TOGGLE_GRAPH_TABLE:
            if new_view == ViewType.CONNECTIONS_GRAPH:
                new_view = ViewType.CONNECTIONS_TABLE
            elif new_view == ViewType.CONNECTIONS_TABLE:
                new_view = ViewType.CONNECTIONS_GRAPH

        elif self.shortcut_type == ShortcutType.TOGGLE_CODE_VISUAL:
            if new_view == ViewType.CODE_VIEW:
                new_view = ViewType.VISUALIZATION
            elif new_view == ViewType.VISUALIZATION:
                new_view = ViewType.CODE_VIEW

        # Create new state
        return WorkflowState(
            current_stage=self.to_stage,
            current_view=new_view,
            focus_id=new_focus_id,
            session_id=current_state.session_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize shortcut to dictionary."""
        return {
            "shortcut_type": self.shortcut_type.value,
            "from_stage": self.from_stage.value,
            "to_stage": self.to_stage.value,
            "justification": self.justification,
            "requires_same_focus": self.requires_same_focus,
            "allows_focus_change": self.allows_focus_change,
            "requires_same_view": self.requires_same_view,
            "allowed_views": [v.value for v in self.allowed_views]
            if self.allowed_views
            else None,
            "maximum_uses": self.maximum_uses,
            "cooldown_seconds": self.cooldown_seconds,
            "shortcut_id": self.shortcut_id,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Shortcut":
        """Deserialize shortcut from dictionary."""
        allowed_views = None
        if data.get("allowed_views"):
            allowed_views = frozenset(ViewType(v) for v in data["allowed_views"])

        return cls(
            shortcut_type=ShortcutType(data["shortcut_type"]),
            from_stage=WorkflowStage(data["from_stage"]),
            to_stage=WorkflowStage(data["to_stage"]),
            justification=data["justification"],
            requires_same_focus=data.get("requires_same_focus", False),
            allows_focus_change=data.get("allows_focus_change", True),
            requires_same_view=data.get("requires_same_view", False),
            allowed_views=allowed_views,
            maximum_uses=data.get("maximum_uses"),
            cooldown_seconds=data.get("cooldown_seconds"),
            shortcut_id=data.get("shortcut_id", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class ShortcutRegistry:
    """
    Registry of all constitutionally-approved shortcuts.

    This is the single source of truth for what shortcuts exist.
    No shortcuts may be created outside this registry.
    """

    # Class variable holding all registered shortcuts
    _registered_shortcuts: ClassVar[dict[str, Shortcut]] = {}
    _initialized: ClassVar[bool] = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize the shortcut registry with all approved shortcuts."""
        if cls._initialized:
            return

        # Backward jumps
        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.BACK_TO_ORIENTATION,
                from_stage=WorkflowStage.EXAMINATION,
                to_stage=WorkflowStage.ORIENTATION,
                justification="Article 6: Allows re-establishing context when details become confusing.",
                requires_same_focus=True,
                maximum_uses=3,  # Prevent infinite oscillation
                cooldown_seconds=30,
            )
        )

        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.BACK_TO_ORIENTATION,
                from_stage=WorkflowStage.CONNECTIONS,
                to_stage=WorkflowStage.ORIENTATION,
                justification="Article 14: Graceful degradation when relationship analysis becomes overwhelming.",
                requires_same_focus=True,
                maximum_uses=2,
                cooldown_seconds=60,
            )
        )

        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.BACK_TO_EXAMINATION,
                from_stage=WorkflowStage.CONNECTIONS,
                to_stage=WorkflowStage.EXAMINATION,
                justification="Article 7: Clear affordance to review details when connections are unclear.",
                requires_same_focus=True,
                maximum_uses=5,
                cooldown_seconds=10,
            )
        )

        # View toggles
        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.TOGGLE_OVERVIEW_DETAIL,
                from_stage=WorkflowStage.EXAMINATION,
                to_stage=WorkflowStage.EXAMINATION,
                justification="Article 5: Single-focus interface allows zooming in/out without changing epistemic level.",
                requires_same_focus=True,
                allowed_views=frozenset([ViewType.OVERVIEW, ViewType.EXAMINATION]),
                maximum_uses=10,  # Allow reasonable toggling
                cooldown_seconds=2,  # Prevent rapid oscillation
            )
        )

        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.TOGGLE_GRAPH_TABLE,
                from_stage=WorkflowStage.CONNECTIONS,
                to_stage=WorkflowStage.CONNECTIONS,
                justification="Article 16: Different visual representations support different cognitive modes.",
                requires_same_focus=True,
                allowed_views=frozenset(
                    [ViewType.CONNECTIONS_GRAPH, ViewType.CONNECTIONS_TABLE]
                ),
                maximum_uses=10,
                cooldown_seconds=2,
            )
        )

        # Re-inspection paths
        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.REINSPECT_SAME_ANCHOR,
                from_stage=WorkflowStage.EXAMINATION,
                to_stage=WorkflowStage.EXAMINATION,
                justification="Article 9: Immutable observations allow fresh examination without data corruption.",
                requires_same_focus=True,
                maximum_uses=1,  # One refresh per anchor per session
                cooldown_seconds=None,
            )
        )

        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.REINSPECT_PARENT,
                from_stage=WorkflowStage.EXAMINATION,
                to_stage=WorkflowStage.EXAMINATION,
                justification="Article 4: Progressive disclosure supports moving up to broader context.",
                allows_focus_change=True,
                maximum_uses=5,
                cooldown_seconds=5,
            )
        )

        # Navigation recovery
        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.RETURN_TO_LAST_VALID,
                from_stage=WorkflowStage.ORIENTATION,  # Available from any stage
                to_stage=WorkflowStage.ORIENTATION,  # Returns to orientation
                justification="Article 15: Session integrity requires recovery from navigation errors.",
                requires_same_focus=False,
                maximum_uses=1,  # Emergency recovery can only be used once
                cooldown_seconds=None,
            )
        )

        cls._register_shortcut(
            Shortcut(
                shortcut_type=ShortcutType.RESET_TO_INITIAL,
                from_stage=WorkflowStage.ORIENTATION,  # Available from any stage
                to_stage=WorkflowStage.ORIENTATION,  # Resets to initial
                justification="Article 14: Graceful degradation when investigation becomes irretrievably confused.",
                requires_same_focus=False,
                maximum_uses=1,  # Only one reset per session
                cooldown_seconds=None,
            )
        )

        cls._initialized = True

    @classmethod
    def _register_shortcut(cls, shortcut: Shortcut) -> None:
        """Register a shortcut (internal use only)."""
        if shortcut.shortcut_id in cls._registered_shortcuts:
            raise ValueError(
                f"Shortcut with ID {shortcut.shortcut_id} already registered"
            )

        # Validate shortcut follows constitutional rules
        cls._validate_shortcut_constitutionality(shortcut)

        cls._registered_shortcuts[shortcut.shortcut_id] = shortcut

    @classmethod
    def _validate_shortcut_constitutionality(cls, shortcut: Shortcut) -> None:
        """Validate that shortcut follows all constitutional rules."""
        # Article 4: No forward skipping
        stage_order = list(WorkflowStage)
        from_index = stage_order.index(shortcut.from_stage)
        to_index = stage_order.index(shortcut.to_stage)

        if to_index > from_index:
            raise ValueError(
                f"Shortcut {shortcut.shortcut_id} violates Article 4: "
                f"Cannot skip forward from {shortcut.from_stage} to {shortcut.to_stage}"
            )

        # Article 6: Shortcuts must be explicit backward jumps or same-stage
        # (Already covered by no-forward-skipping, but explicit check)
        if to_index > from_index:
            raise ValueError(
                f"Shortcut {shortcut.shortcut_id} violates Article 6: "
                f"Shortcuts must be backward jumps or same-stage toggles"
            )

        # Article 7: Must have clear justification
        if not shortcut.justification:
            raise ValueError(
                f"Shortcut {shortcut.shortcut_id} violates Article 7: "
                f"Must have clear justification"
            )

        # Additional safety: same-stage shortcuts should not change focus unless explicitly allowed
        if shortcut.from_stage == shortcut.to_stage and shortcut.allows_focus_change:
            # This is allowed but should be justified
            if (
                "focus" not in shortcut.justification.lower()
                and "context" not in shortcut.justification.lower()
            ):
                raise ValueError(
                    f"Shortcut {shortcut.shortcut_id} changes focus within same stage "
                    f"but justification doesn't mention focus or context"
                )

    @classmethod
    def get_available_shortcuts(
        cls,
        current_state: WorkflowState,
        session_context: SessionContext | None = None,
        shortcut_history: list[Shortcut] | None = None,
    ) -> frozenset[Shortcut]:
        """
        Get all shortcuts available from current state.

        Args:
            current_state: Current workflow state
            session_context: Optional session context
            shortcut_history: Optional history of shortcuts used

        Returns:
            Frozen set of available shortcuts
        """
        if not cls._initialized:
            cls.initialize()

        available = set()

        for shortcut in cls._registered_shortcuts.values():
            # Special handling for recovery shortcuts (available from any stage)
            if shortcut.shortcut_type in [
                ShortcutType.RETURN_TO_LAST_VALID,
                ShortcutType.RESET_TO_INITIAL,
            ]:
                # Check availability with modified from_stage
                temp_shortcut = Shortcut(
                    shortcut_type=shortcut.shortcut_type,
                    from_stage=current_state.current_stage,  # Current stage
                    to_stage=shortcut.to_stage,
                    justification=shortcut.justification,
                    requires_same_focus=shortcut.requires_same_focus,
                    allows_focus_change=shortcut.allows_focus_change,
                    requires_same_view=shortcut.requires_same_view,
                    allowed_views=shortcut.allowed_views,
                    maximum_uses=shortcut.maximum_uses,
                    cooldown_seconds=shortcut.cooldown_seconds,
                )

                is_available, _ = temp_shortcut.is_available(
                    current_state, session_context, shortcut_history
                )
                if is_available:
                    available.add(temp_shortcut)

            else:
                # Normal shortcut - check with registered from_stage
                if shortcut.from_stage == current_state.current_stage:
                    is_available, _ = shortcut.is_available(
                        current_state, session_context, shortcut_history
                    )
                    if is_available:
                        available.add(shortcut)

        return frozenset(available)

    @classmethod
    def get_shortcut_by_id(cls, shortcut_id: str) -> Shortcut | None:
        """Get shortcut by ID."""
        if not cls._initialized:
            cls.initialize()

        return cls._registered_shortcuts.get(shortcut_id)

    @classmethod
    def get_shortcuts_by_type(cls, shortcut_type: ShortcutType) -> list[Shortcut]:
        """Get all shortcuts of a given type."""
        if not cls._initialized:
            cls.initialize()

        return [
            s
            for s in cls._registered_shortcuts.values()
            if s.shortcut_type == shortcut_type
        ]

    @classmethod
    def validate_shortcut_use(
        cls,
        shortcut_type: ShortcutType,
        current_state: WorkflowState,
        session_context: SessionContext | None = None,
        shortcut_history: list[Shortcut] | None = None,
    ) -> tuple[bool, Shortcut | None, str | None]:
        """
        Validate if a shortcut type can be used from current state.

        Args:
            shortcut_type: Type of shortcut to validate
            current_state: Current workflow state
            session_context: Optional session context
            shortcut_history: Optional history of shortcuts used

        Returns:
            Tuple of (is_valid, shortcut_instance, error_message)
        """
        if not cls._initialized:
            cls.initialize()

        # Get available shortcuts of this type
        available_shortcuts = [
            s
            for s in cls.get_available_shortcuts(
                current_state, session_context, shortcut_history
            )
            if s.shortcut_type == shortcut_type
        ]

        if not available_shortcuts:
            return (
                False,
                None,
                f"No available shortcuts of type {shortcut_type} from current state",
            )

        # For simplicity, return the first available shortcut
        # In practice, we might need to handle multiple shortcuts of same type
        # with different constraints
        shortcut = available_shortcuts[0]
        is_available, reason = shortcut.is_available(
            current_state, session_context, shortcut_history
        )

        if is_available:
            return True, shortcut, None
        else:
            return False, shortcut, reason


def validate_shortcuts_integrity() -> tuple[bool, str | None]:
    """
    Validate that all registered shortcuts follow constitutional rules.

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        ShortcutRegistry.initialize()

        for shortcut_id, shortcut in ShortcutRegistry._registered_shortcuts.items():
            # Re-validate each shortcut
            ShortcutRegistry._validate_shortcut_constitutionality(shortcut)

            # Check for duplicate IDs
            if (
                list(ShortcutRegistry._registered_shortcuts.values()).count(shortcut)
                > 1
            ):
                return False, f"Duplicate shortcut: {shortcut_id}"

        return True, None

    except Exception as e:
        return False, f"Shortcuts integrity validation failed: {e}"


def get_shortcut_constitutional_rules() -> str:
    """Get human-readable summary of shortcut constitutional rules."""
    rules = [
        "SHORTCUT CONSTITUTIONAL RULES",
        "=" * 40,
        "",
        "1. NO FORWARD SKIPPING (Article 4)",
        "   - Shortcuts cannot skip ahead in the canonical workflow",
        "   - Must be backward jumps or same-stage toggles",
        "",
        "2. EXPLICIT JUSTIFICATION (Article 6)",
        "   - Every shortcut must cite constitutional principle",
        "   - Justification must be visible to user",
        "",
        "3. CLEAR AFFORDANCES (Article 7)",
        "   - Shortcuts must be obviously available",
        "   - Cannot be hidden or implicit",
        "",
        "4. EPISTEMIC SAFETY (Article 14)",
        "   - Must not skip necessary understanding",
        "   - Backward jumps preserve accumulated knowledge",
        "",
        "5. USAGE LIMITS",
        "   - Maximum uses prevent infinite oscillation",
        "   - Cooldowns prevent rapid toggling",
        "",
        "Approved Shortcut Types:",
    ]

    for shortcut_type in ShortcutType:
        rules.append(f"  - {shortcut_type.value.replace('_', ' ').title()}")

    return "\n".join(rules)
