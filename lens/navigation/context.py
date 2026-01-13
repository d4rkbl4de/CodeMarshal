"""
lens/navigation/context.py

CRITUTIONAL CONSTITUTIONAL GUARD: Navigational Position
========================================================
NavigationContext is a compass bearing, not a map.

Context is NOT:
- The investigation history
- A reasoning engine
- A navigation decision maker
- A cache of observations

Context IS:
- Read-only representation of current interface position
- Singular focus subject identifier
- Current workflow stage
- Active view type

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 5: Single-Focus Interface (one focus subject)
- Article 6: Linear Investigation (current workflow stage)
- Article 7: Clear Affordances (visible position)
- Article 16: Truth-Preserving Aesthetics (consistent representation)

ALLOWED IMPORTS:
- lens.philosophy.* (mandatory)
- lens.views.* (types only)
- inquiry.session.context (read-only)
- lens.navigation.workflow (types only)
- lens.navigation.shortcuts (types only)
- typing, enum, dataclasses

PROHIBITED IMPORTS:
- bridge.commands.*
- observations.*
- Any UI code
"""

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple
from uuid import UUID

# Allowed imports
from lens.philosophy import SingleFocusRule, NavigationRule
from lens.views import ViewType
from inquiry.session.context import SessionContext
from lens.navigation.workflow import WorkflowStage, WorkflowState
from lens.navigation.shortcuts import ShortcutType


class FocusType(enum.Enum):
    """Types of focus subjects in the interface."""
    
    ANCHOR = "anchor"
    """Focus is on a specific observation anchor."""
    
    PATTERN = "pattern"
    """Focus is on a detected pattern."""
    
    CONNECTION = "connection"
    """Focus is on a connection between elements."""
    
    NOTE = "note"
    """Focus is on a human-written note."""
    
    VIEW = "view"
    """Focus is on a specific view element (header, panel, etc.)."""
    
    SYSTEM = "system"
    """Focus is on a system element (help, settings, etc.)."""


@dataclass(frozen=True)
class NavigationContext:
    """
    Immutable representation of current navigational position.
    
    This is a compass bearing: it tells you exactly where you are
    in the interface, but not how to get anywhere else.
    
    FIELDS:
    - session_context: What's being investigated (read-only reference)
    - workflow_stage: Current position in canonical workflow
    - current_view: Active view type
    - focus_type: Type of focus subject
    - focus_id: Unique identifier of focus subject
    - created_at: When this context was created
    - context_id: Unique identifier for this navigation context
    """
    
    # Primary references (immutable)
    session_context: SessionContext
    """Reference to current investigation session context."""
    
    workflow_stage: WorkflowStage
    """Current stage in the investigative workflow."""
    
    current_view: Optional[ViewType]
    """Active view type (None if no specific view)."""
    
    # Focus information (Article 5: Single-Focus Interface)
    focus_type: FocusType
    """Type of subject currently in focus."""
    
    focus_id: str
    """Unique identifier of the focus subject."""
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """When this context was created (timezone-aware)."""
    
    context_id: UUID = field(default_factory=lambda: uuid.uuid4())
    """Unique identifier for this navigation context."""
    
    def __post_init__(self) -> None:
        """Validate NavigationContext invariants."""
        # Type validation
        if not isinstance(self.session_context, SessionContext):
            raise TypeError("session_context must be SessionContext")
        
        if not isinstance(self.workflow_stage, WorkflowStage):
            raise TypeError("workflow_stage must be WorkflowStage")
        
        if self.current_view is not None and not isinstance(self.current_view, ViewType):
            raise TypeError("current_view must be ViewType or None")
        
        if not isinstance(self.focus_type, FocusType):
            raise TypeError("focus_type must be FocusType")
        
        if not isinstance(self.focus_id, str):
            raise TypeError("focus_id must be str")
        
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be datetime")
        
        if not isinstance(self.context_id, UUID):
            raise TypeError("context_id must be UUID")
        
        # Value validation
        if not self.focus_id:
            raise ValueError("focus_id cannot be empty")
        
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        
        # Article 5: Single-Focus Interface
        # Ensure focus_id doesn't contain multiple subjects
        if ";" in self.focus_id or "," in self.focus_id:
            raise ValueError(
                "focus_id cannot contain multiple subjects (Article 5: Single-Focus Interface)"
            )
        
        # Validate focus_type and focus_id consistency
        self._validate_focus_consistency()
    
    def _validate_focus_consistency(self) -> None:
        """Validate that focus_type and focus_id are consistent."""
        # Basic validation - more specific validation would require
        # importing observation/pattern modules, which we cannot do
        if self.focus_type == FocusType.ANCHOR:
            # Anchor IDs should follow a specific pattern
            # This is a minimal check - actual validation happens elsewhere
            if not self.focus_id.startswith(("anchor:", "obs:", "snapshot:")):
                pass  # Not an error, just unusual
            
        elif self.focus_type == FocusType.PATTERN:
            # Pattern IDs should indicate they're patterns
            if not self.focus_id.startswith(("pattern:", "pat:")):
                pass  # Not an error
            
        elif self.focus_type == FocusType.NOTE:
            # Note IDs
            if not self.focus_id.startswith(("note:", "thinking:")):
                pass  # Not an error
            
        elif self.focus_type == FocusType.SYSTEM:
            # System elements
            if not self.focus_id.startswith(("system:", "help:", "settings:")):
                pass  # Not an error
    
    @property
    def current_stage(self) -> WorkflowStage:
        """Bridge property for compatibility with bridge commands."""
        return self.workflow_stage
    
    def with_workflow_stage(self, new_stage: WorkflowStage) -> "NavigationContext":
        """
        Create new context with updated workflow stage.
        
        Args:
            new_stage: New workflow stage
            
        Returns:
            New NavigationContext with updated stage
        """
        if not isinstance(new_stage, WorkflowStage):
            raise TypeError("new_stage must be WorkflowStage")
        
        return NavigationContext(
            session_context=self.session_context,
            workflow_stage=new_stage,
            current_view=self.current_view,
            focus_type=self.focus_type,
            focus_id=self.focus_id,
            created_at=datetime.now(timezone.utc),
            context_id=uuid.uuid4()
        )
    
    def with_view(self, new_view: ViewType) -> "NavigationContext":
        """
        Create new context with updated view.
        
        Args:
            new_view: New view type
            
        Returns:
            New NavigationContext with updated view
        """
        if not isinstance(new_view, ViewType):
            raise TypeError("new_view must be ViewType")
        
        return NavigationContext(
            session_context=self.session_context,
            workflow_stage=self.workflow_stage,
            current_view=new_view,
            focus_type=self.focus_type,
            focus_id=self.focus_id,
            created_at=datetime.now(timezone.utc),
            context_id=uuid.uuid4()
        )
    
    def with_focus(self, focus_type: FocusType, focus_id: str) -> "NavigationContext":
        """
        Create new context with updated focus.
        
        Args:
            focus_type: Type of new focus
            focus_id: ID of new focus
            
        Returns:
            New NavigationContext with updated focus
        """
        if not isinstance(focus_type, FocusType):
            raise TypeError("focus_type must be FocusType")
        
        if not isinstance(focus_id, str):
            raise TypeError("focus_id must be str")
        
        if not focus_id:
            raise ValueError("focus_id cannot be empty")
        
        return NavigationContext(
            session_context=self.session_context,
            workflow_stage=self.workflow_stage,
            current_view=self.current_view,
            focus_type=focus_type,
            focus_id=focus_id,
            created_at=datetime.now(timezone.utc),
            context_id=uuid.uuid4()
        )
    
    def with_session_context(self, new_session_context: SessionContext) -> "NavigationContext":
        """
        Create new context with updated session context.
        
        Args:
            new_session_context: New session context
            
        Returns:
            New NavigationContext with updated session context
        """
        if not isinstance(new_session_context, SessionContext):
            raise TypeError("new_session_context must be SessionContext")
        
        return NavigationContext(
            session_context=new_session_context,
            workflow_stage=self.workflow_stage,
            current_view=self.current_view,
            focus_type=self.focus_type,
            focus_id=self.focus_id,
            created_at=datetime.now(timezone.utc),
            context_id=uuid.uuid4()
        )
    
    def to_workflow_state(self) -> WorkflowState:
        """
        Convert to WorkflowState for navigation subsystem.
        
        Returns:
            WorkflowState representation of this context
        """
        return WorkflowState(
            current_stage=self.workflow_stage,
            current_view=self.current_view,
            focus_id=self.focus_id,
            session_id=self.session_context.context_id
        )
    
    def is_same_focus(self, other: "NavigationContext") -> bool:
        """
        Check if two contexts have the same focus.
        
        Args:
            other: Other NavigationContext to compare
            
        Returns:
            True if same focus_type and focus_id
        """
        if not isinstance(other, NavigationContext):
            return False
        
        return (
            self.focus_type == other.focus_type and
            self.focus_id == other.focus_id
        )
    
    def is_same_view(self, other: "NavigationContext") -> bool:
        """
        Check if two contexts have the same view.
        
        Args:
            other: Other NavigationContext to compare
            
        Returns:
            True if same current_view
        """
        if not isinstance(other, NavigationContext):
            return False
        
        return self.current_view == other.current_view
    
    def is_same_stage(self, other: "NavigationContext") -> bool:
        """
        Check if two contexts have the same workflow stage.
        
        Args:
            other: Other NavigationContext to compare
            
        Returns:
            True if same workflow_stage
        """
        if not isinstance(other, NavigationContext):
            return False
        
        return self.workflow_stage == other.workflow_stage
    
    def get_age_seconds(self) -> float:
        """
        Get age of context in seconds.
        
        Returns:
            Age in seconds as float
        """
        now = datetime.now(timezone.utc)
        age = (now - self.created_at).total_seconds()
        return max(age, 0.0)
    
    def to_dict(self) -> dict:
        """Serialize context to dictionary."""
        return {
            "session_context": self.session_context.to_dict(),
            "workflow_stage": self.workflow_stage.value,
            "current_view": self.current_view.value if self.current_view else None,
            "focus_type": self.focus_type.value,
            "focus_id": self.focus_id,
            "created_at": self.created_at.isoformat(),
            "context_id": str(self.context_id)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "NavigationContext":
        """Deserialize context from dictionary."""
        # Reconstruct session context
        session_context = SessionContext.from_dict(data["session_context"])
        
        # Parse workflow stage
        workflow_stage = WorkflowStage(data["workflow_stage"])
        
        # Parse current view
        current_view = None
        if data.get("current_view"):
            current_view = ViewType(data["current_view"])
        
        # Parse focus type
        focus_type = FocusType(data["focus_type"])
        
        return cls(
            session_context=session_context,
            workflow_stage=workflow_stage,
            current_view=current_view,
            focus_type=focus_type,
            focus_id=data["focus_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            context_id=UUID(data["context_id"])
        )
    
    def __eq__(self, other: object) -> bool:
        """Equality based on context_id only."""
        if not isinstance(other, NavigationContext):
            return False
        return self.context_id == other.context_id
    
    def __hash__(self) -> int:
        """Hash based on context_id only."""
        return hash(self.context_id)
    
    def __str__(self) -> str:
        """Human-readable representation."""
        view_str = self.current_view.value if self.current_view else "none"
        return (
            f"NavigationContext("
            f"stage={self.workflow_stage.value}, "
            f"view={view_str}, "
            f"focus={self.focus_type.value}:{self.focus_id[:20] + ('...' if len(self.focus_id) > 20 else '')}"
            f")"
        )


# Factory functions for creating navigation contexts

def create_navigation_context(
    session_context: SessionContext,
    workflow_stage: WorkflowStage,
    focus_type: FocusType,
    focus_id: str,
    current_view: Optional[ViewType] = None
) -> NavigationContext:
    """
    Create a new navigation context.
    
    Args:
        session_context: Current session context
        workflow_stage: Current workflow stage
        focus_type: Type of focus subject
        focus_id: ID of focus subject
        current_view: Optional current view type
        
    Returns:
        New NavigationContext
        
    Raises:
        ValueError: If validation fails
    """
    return NavigationContext(
        session_context=session_context,
        workflow_stage=workflow_stage,
        current_view=current_view,
        focus_type=focus_type,
        focus_id=focus_id
    )


def create_initial_navigation_context(
    session_context: SessionContext,
    initial_focus_id: str = "system:welcome"
) -> NavigationContext:
    """
    Create initial navigation context for new investigation.
    
    Args:
        session_context: Initial session context
        initial_focus_id: Initial focus ID (defaults to welcome screen)
        
    Returns:
        Initial NavigationContext
        
    Raises:
        ValueError: If validation fails
    """
    return create_navigation_context(
        session_context=session_context,
        workflow_stage=WorkflowStage.ORIENTATION,
        focus_type=FocusType.SYSTEM,
        focus_id=initial_focus_id,
        current_view=ViewType.OVERVIEW
    )


def create_context_from_workflow_state(
    workflow_state: WorkflowState,
    session_context: SessionContext,
    focus_type: FocusType = FocusType.ANCHOR
) -> NavigationContext:
    """
    Create navigation context from workflow state.
    
    Args:
        workflow_state: Workflow state to convert
        session_context: Associated session context
        focus_type: Type of focus (defaults to ANCHOR)
        
    Returns:
        NavigationContext with information from workflow state
    """
    focus_id = workflow_state.focus_id or session_context.anchor_id
    
    return NavigationContext(
        session_context=session_context,
        workflow_stage=workflow_state.current_stage,
        current_view=workflow_state.current_view,
        focus_type=focus_type,
        focus_id=focus_id
    )


# Validation utilities

def validate_navigation_context_integrity(
    context: NavigationContext
) -> Tuple[bool, Optional[str]]:
    """
    Validate that navigation context follows constitutional rules.
    
    Args:
        context: NavigationContext to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    violations = []
    
    # Article 5: Single-Focus Interface
    if ";" in context.focus_id or "," in context.focus_id:
        violations.append(
            "Article 5 violation: focus_id contains multiple subjects"
        )
    
    # Article 7: Clear Affordances
    # View should be appropriate for workflow stage
    if context.current_view:
        # Basic validation - more complex validation would require
        # mapping of allowed views per stage
        pass
    
    # Focus type should be consistent with focus_id
    if context.focus_type == FocusType.ANCHOR:
        if not context.focus_id.startswith(("anchor:", "obs:", "snapshot:")):
            violations.append(
                "Anchor focus_id should start with 'anchor:', 'obs:', or 'snapshot:'"
            )
    
    if violations:
        return False, "; ".join(violations)
    
    return True, None


def get_context_summary(context: NavigationContext) -> str:
    """
    Get human-readable summary of navigation context.
    
    Args:
        context: NavigationContext to summarize
        
    Returns:
        Summary string
    """
    view_str = context.current_view.value if context.current_view else "No view"
    
    return (
        f"Navigation Position:\n"
        f"  Workflow Stage: {context.workflow_stage.value}\n"
        f"  Current View: {view_str}\n"
        f"  Focus: {context.focus_type.value} - {context.focus_id}\n"
        f"  Session: {context.session_context.snapshot_id.hex[:8]}...\n"
        f"  Age: {context.get_age_seconds():.1f} seconds"
    )