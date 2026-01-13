"""
inquiry/session/context.py

CRITICAL CONSTITUTIONAL GUARD: Session Context
=============================================
SessionContext is a bookmark, not a journal.

Context is NOT:
- The full investigation state
- A cache of observations
- A workspace for computation
- A container for navigation logic

Context IS:
- An immutable pointer to what's being looked at
- A reference to specific observations
- A declaration of current inquiry mode
- A truth-preserving focus anchor

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 4: Progressive Disclosure (single focus)
- Article 6: Linear Investigation (current position)
- Article 9: Immutable Observations (references only)
- Article 15: Session Integrity (recoverable state)

ALLOWED IMPORTS:
- observations.record.version
- observations.record.anchors
- typing, dataclasses, uuid, datetime, pathlib

PROHIBITED IMPORTS:
- history.py (context does not know the past)
- recovery.py (no recovery logic)
- patterns.* (no analysis)
- notebook.* (no thinking content)
- lens.* (no UI concerns)
"""

import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID, uuid4

# Allowed imports from observations.record
from observations.record.version import SnapshotVersion, get_snapshot_version
from observations.record.anchors import Anchor, get_anchor, validate_anchor_reference

logger = logging.getLogger(__name__)


class QuestionType(enum.Enum):
    """Valid inquiry modes for human investigation."""
    
    STRUCTURE = "structure"
    """What's here? Examining composition and organization."""
    
    PURPOSE = "purpose"
    """What does this do? Understanding function and intent."""
    
    CONNECTIONS = "connections"
    """How is it connected? Seeing relationships and dependencies."""
    
    ANOMALIES = "anomalies"
    """What seems unusual? Noticing deviations and exceptions."""
    
    THINKING = "thinking"
    """What do I think? Recording human thoughts and questions."""


@dataclass(frozen=True)
class SessionContext:
    """
    Immutable pointer to current investigative focus.
    
    This is a bookmark: it tells you where to look,
    not what you'll find when you look there.
    
    FIELDS:
    - snapshot_id: Which observation snapshot to use
    - anchor_id: Which specific point in the snapshot is in focus
    - question_type: What kind of question is being asked
    - created_at: When this context was created (for ordering)
    - context_id: Unique identifier for this specific context
    """
    
    # Primary references (must exist in storage)
    snapshot_id: UUID
    """Reference to active observation snapshot."""
    
    anchor_id: str
    """Reference to specific anchor within snapshot."""
    
    # Current investigation mode
    question_type: QuestionType
    """What kind of question the human is asking."""
    
    # Metadata (for ordering and uniqueness)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    """When this context was created (timezone-aware)."""
    
    context_id: UUID = field(default_factory=uuid4)
    """Unique identifier for this specific context instance."""
    
    # Bridge command compatibility fields
    active: bool = True
    """Whether the investigation session is active."""
    
    has_observations: bool = False
    """Whether the session has collected observations."""
    
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    """Maximum file size for observations."""
    
    observations_incomplete: bool = False
    """Whether observations are incomplete."""
    
    patterns_partial: bool = False
    """Whether patterns are partially computed."""
    
    current_stage: str = "orientation"
    """Current investigation stage."""
    
    observation_count: int = 0
    """Number of observations collected."""
    
    note_count: int = 0
    """Number of notes created."""
    
    def is_path_accessible(self, path: Path) -> bool:
        """Check if a path is accessible within session boundaries."""
        try:
            # Basic accessibility check - can be expanded
            return path.exists() and path.is_file() or path.is_dir()
        except (PermissionError, OSError):
            return False
    
    def __post_init__(self) -> None:
        """Validate SessionContext invariants."""
        # Type validation
        if not isinstance(self.snapshot_id, UUID):
            raise TypeError("snapshot_id must be UUID")
        
        if not isinstance(self.anchor_id, str):
            raise TypeError("anchor_id must be str")
        
        if not isinstance(self.question_type, QuestionType):
            raise TypeError("question_type must be QuestionType")
        
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be datetime")
        
        if not isinstance(self.context_id, UUID):
            raise TypeError("context_id must be UUID")
        
        # Value validation
        if not self.anchor_id:
            raise ValueError("anchor_id cannot be empty")
        
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
    
    def validate_existence(self, storage_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that referenced snapshot and anchor exist.
        
        This checks existence only, not meaning or correctness.
        Returns (is_valid, error_message) tuple.
        
        Args:
            storage_path: Path to observation storage
            
        Returns:
            Tuple of (is_valid, optional_error_message)
        """
        try:
            # Check if snapshot exists
            snapshot_version = get_snapshot_version(
                storage_path=storage_path,
                snapshot_id=self.snapshot_id
            )
            
            if snapshot_version is None:
                return False, f"Snapshot {self.snapshot_id} not found"
            
            # Check if anchor exists in snapshot
            anchor = get_anchor(
                storage_path=storage_path,
                snapshot_id=self.snapshot_id,
                anchor_id=self.anchor_id
            )
            
            if anchor is None:
                return False, f"Anchor {self.anchor_id} not found in snapshot {self.snapshot_id}"
            
            # Validate anchor reference integrity
            is_valid_ref = validate_anchor_reference(anchor, self.snapshot_id)
            if not is_valid_ref:
                return False, f"Anchor {self.anchor_id} has invalid reference to snapshot"
            
            return True, None
            
        except (OSError, ValueError, TypeError) as e:
            logger.debug("Failed to validate context existence: %s", e)
            return False, f"Validation error: {e}"
    
    def with_question_type(self, new_question_type: QuestionType) -> "SessionContext":
        """
        Create new context with different question type.
        
        This creates a new context pointing to the same snapshot and anchor,
        but with a different investigative focus.
        
        Args:
            new_question_type: New question type for investigation
            
        Returns:
            New SessionContext with updated question_type
        """
        if not isinstance(new_question_type, QuestionType):
            raise TypeError("new_question_type must be QuestionType")
        
        return SessionContext(
            snapshot_id=self.snapshot_id,
            anchor_id=self.anchor_id,
            question_type=new_question_type,
            # New timestamp for ordering
            created_at=datetime.now(timezone.utc),
            # New ID since this is a different context
            context_id=uuid4()
        )
    
    def with_anchor(self, new_anchor_id: str) -> "SessionContext":
        """
        Create new context pointing to different anchor.
        
        This creates a new context pointing to the same snapshot,
        but with a different anchor in focus.
        
        Args:
            new_anchor_id: ID of anchor to focus on
            
        Returns:
            New SessionContext with updated anchor_id
        """
        if not isinstance(new_anchor_id, str):
            raise TypeError("new_anchor_id must be str")
        
        if not new_anchor_id:
            raise ValueError("new_anchor_id cannot be empty")
        
        return SessionContext(
            snapshot_id=self.snapshot_id,
            anchor_id=new_anchor_id,
            question_type=self.question_type,
            created_at=datetime.now(timezone.utc),
            context_id=uuid4()
        )
    
    def with_snapshot(self, new_snapshot_id: UUID, new_anchor_id: Optional[str] = None) -> "SessionContext":
        """
        Create new context pointing to different snapshot.
        
        This creates a new context pointing to a different snapshot.
        If anchor_id is not provided, uses the same anchor_id (may not exist).
        
        Args:
            new_snapshot_id: ID of snapshot to use
            new_anchor_id: Optional new anchor ID (uses current if None)
            
        Returns:
            New SessionContext with updated snapshot reference
        """
        if not isinstance(new_snapshot_id, UUID):
            raise TypeError("new_snapshot_id must be UUID")
        
        anchor_id = new_anchor_id if new_anchor_id is not None else self.anchor_id
        
        return SessionContext(
            snapshot_id=new_snapshot_id,
            anchor_id=anchor_id,
            question_type=self.question_type,
            created_at=datetime.now(timezone.utc),
            context_id=uuid4()
        )
    
    def to_dict(self) -> dict:
        """Serialize context to dictionary for storage."""
        return {
            "snapshot_id": str(self.snapshot_id),
            "anchor_id": self.anchor_id,
            "question_type": self.question_type.value,
            "created_at": self.created_at.isoformat(),
            "context_id": str(self.context_id)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SessionContext":
        """Deserialize context from dictionary."""
        try:
            return cls(
                snapshot_id=UUID(data["snapshot_id"]),
                anchor_id=data["anchor_id"],
                question_type=QuestionType(data["question_type"]),
                created_at=datetime.fromisoformat(data["created_at"]),
                context_id=UUID(data["context_id"])
            )
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"Invalid context data: {e}") from e
    
    def __eq__(self, other: object) -> bool:
        """Equality based on context_id only."""
        if not isinstance(other, SessionContext):
            return False
        return self.context_id == other.context_id
    
    def __hash__(self) -> int:
        """Hash based on context_id only."""
        return hash(self.context_id)
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"SessionContext("
            f"snapshot={self.snapshot_id.hex[:8]}, "
            f"anchor={self.anchor_id[:20] + ('...' if len(self.anchor_id) > 20 else '')}, "
            f"question={self.question_type.value}"
            f")"
        )


# Factory functions for creating contexts
# These ensure contexts are created with proper validation

def create_context(
    snapshot_id: UUID,
    anchor_id: str,
    question_type: QuestionType,
    storage_path: Optional[str] = None
) -> SessionContext:
    """
    Create a new session context with existence validation.
    
    If storage_path is provided, validates that snapshot and anchor exist.
    If not provided, creates context without validation (use with caution).
    
    Args:
        snapshot_id: ID of snapshot to reference
        anchor_id: ID of anchor within snapshot
        question_type: Type of question being asked
        storage_path: Optional path to validate existence
        
    Returns:
        New SessionContext
        
    Raises:
        ValueError: If validation fails or invalid arguments
    """
    # Create context without validation first
    context = SessionContext(
        snapshot_id=snapshot_id,
        anchor_id=anchor_id,
        question_type=question_type
    )
    
    # Validate existence if storage path provided
    if storage_path is not None:
        is_valid, error = context.validate_existence(storage_path)
        if not is_valid:
            raise ValueError(f"Cannot create context: {error}")
    
    return context


def create_initial_context(
    storage_path: str,
    initial_anchor_id: str = "root"
) -> SessionContext:
    """
    Create initial context for new investigation.
    
    Finds the most recent snapshot and creates context pointing to it.
    
    Args:
        storage_path: Path to observation storage
        initial_anchor_id: Anchor to start with (defaults to "root")
        
    Returns:
        Initial SessionContext
        
    Raises:
        ValueError: If no snapshots found or validation fails
    """
    # TODO: Implement get_latest_snapshot in observations.record.version
    # For now, we'll use a placeholder implementation
    # This should be replaced when observations.record.version is implemented
    
    try:
        # This is a temporary implementation
        # In production, we would call:
        # latest_snapshot = get_latest_snapshot(storage_path)
        # if latest_snapshot is None:
        #     raise ValueError("No observation snapshots found")
        
        # For now, create a mock snapshot ID
        # This will be replaced with real implementation
        import uuid
        mock_snapshot_id = uuid.uuid4()
        
        logger.warning(
            "Using mock snapshot ID %s. Replace with real implementation "
            "when observations.record.version is available.",
            mock_snapshot_id
        )
        
        # Create context
        context = create_context(
            snapshot_id=mock_snapshot_id,
            anchor_id=initial_anchor_id,
            question_type=QuestionType.STRUCTURE,
            storage_path=storage_path
        )
        
        return context
        
    except (OSError, ValueError, TypeError) as e:
        raise ValueError(f"Cannot create initial context: {e}") from e


# Validation utilities (no inference, only existence checks)

def validate_context_references(
    context: SessionContext,
    storage_path: str
) -> bool:
    """
    Validate that context references exist in storage.
    
    This is a standalone version of context.validate_existence().
    Useful when you have a context but want to check it separately.
    
    Args:
        context: SessionContext to validate
        storage_path: Path to observation storage
        
    Returns:
        True if references exist, False otherwise
    """
    is_valid, _ = context.validate_existence(storage_path)
    return is_valid


def get_context_age(context: SessionContext) -> float:
    """
    Get age of context in seconds.
    
    Useful for determining if context is stale.
    
    Args:
        context: SessionContext to check
        
    Returns:
        Age in seconds as float
    """
    now = datetime.now(timezone.utc)
    age = (now - context.created_at).total_seconds()
    return max(age, 0.0)  # Ensure non-negative


def is_context_stale(context: SessionContext, max_age_seconds: float = 3600.0) -> bool:
    """
    Check if context is stale (older than threshold).
    
    Args:
        context: SessionContext to check
        max_age_seconds: Maximum age in seconds (default 1 hour)
        
    Returns:
        True if context is stale, False otherwise
    """
    age = get_context_age(context)
    return age > max_age_seconds