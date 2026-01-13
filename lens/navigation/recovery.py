"""
lens/navigation/recovery.py

CRITICAL CONSTITUTIONAL GUARD: Navigation Failure Recovery
==========================================================
Admitting you're lost is not weakness. It's navigation.

Recovery is NOT:
- Silent correction
- Automatic guessing
- "Best effort" lies
- Convenience features

Recovery IS:
- Enumerated failure types
- Explicit allowed recovery destinations
- Mandatory clarity signaling
- Deterministic, visible fallback paths

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 3: Truth Preservation (declare uncertainty)
- Article 14: Graceful Degradation (show available paths)
- Article 7: Clear Affordances (visible recovery options)
- Article 8: Honest Performance (explain why recovery needed)

ALLOWED IMPORTS:
- lens.philosophy.* (mandatory)
- lens.views.* (types only)
- inquiry.session.context (read-only)
- lens.navigation.workflow (types only)
- lens.navigation.shortcuts (types only)
- typing, enum, dataclasses, datetime

PROHIBITED IMPORTS:
- bridge.commands.*
- observations.*
- patterns.*
- storage.*
- Any UI code or widgets
"""

import enum
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Tuple, Dict, Any, List, FrozenSet
from uuid import UUID

# Allowed imports
from lens.philosophy import (
    ProgressiveDisclosureRule, 
    SingleFocusRule, 
    ClarityRule, 
    NavigationRule
)
from lens.views import ViewType
from lens.navigation.workflow import WorkflowStage, WorkflowState
from lens.navigation.shortcuts import ShortcutType, Shortcut
from inquiry.session.context import SessionContext


class NavigationFailure(enum.Enum):
    """
    Explicit enumeration of ALL possible navigation failures.
    
    Each failure type must:
    1. Have a clear, human-readable description
    2. Specify whether recovery is mandatory or optional
    3. Declare what information is lost (if any)
    """
    
    # Data-related failures
    MISSING_OBSERVATIONS = "missing_observations"
    """Required observation data is unavailable or corrupted."""
    
    INVALID_ANCHOR_REFERENCE = "invalid_anchor_reference"
    """Anchor ID references non-existent or inaccessible observation."""
    
    SNAPSHOT_NOT_FOUND = "snapshot_not_found"
    """Observation snapshot does not exist or cannot be loaded."""
    
    # Workflow-related failures
    ILLEGAL_TRANSITION = "illegal_transition"
    """Attempted navigation violates workflow rules."""
    
    INVALID_STAGE_SEQUENCE = "invalid_stage_sequence"
    """Current stage progression violates canonical order."""
    
    MISSING_REQUIRED_VIEW = "missing_required_view"
    """Required view type for current stage is unavailable."""
    
    # State-related failures
    CORRUPTED_SESSION_STATE = "corrupted_session_state"
    """Session state is inconsistent or corrupted."""
    
    EXPIRED_CONTEXT = "expired_context"
    """Session context is too old (observation may be stale)."""
    
    FOCUS_OUT_OF_BOUNDS = "focus_out_of_bounds"
    """Current focus references non-existent or inaccessible element."""
    
    # System failures
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    """Required system resource (memory, storage) is unavailable."""
    
    PERMISSION_DENIED = "permission_denied"
    """Cannot access required data due to permissions."""
    
    INTEGRITY_VIOLATION = "integrity_violation"
    """System integrity check failed."""
    
    # Failure metadata
    @property
    def requires_immediate_recovery(self) -> bool:
        """Whether this failure requires immediate recovery action."""
        immediate_failures = {
            NavigationFailure.MISSING_OBSERVATIONS,
            NavigationFailure.INVALID_ANCHOR_REFERENCE,
            NavigationFailure.SNAPSHOT_NOT_FOUND,
            NavigationFailure.CORRUPTED_SESSION_STATE,
            NavigationFailure.INTEGRITY_VIOLATION,
        }
        return self in immediate_failures
    
    @property
    def allows_continuation(self) -> bool:
        """Whether investigation can continue (with limitations)."""
        continuation_allowed = {
            NavigationFailure.EXPIRED_CONTEXT,
            NavigationFailure.MISSING_REQUIRED_VIEW,
            NavigationFailure.RESOURCE_UNAVAILABLE,
        }
        return self in continuation_allowed
    
    @property
    def lost_information(self) -> str:
        """Description of what information is lost due to this failure."""
        lost_info = {
            NavigationFailure.MISSING_OBSERVATIONS: "Observation data",
            NavigationFailure.INVALID_ANCHOR_REFERENCE: "Specific anchor reference",
            NavigationFailure.SNAPSHOT_NOT_FOUND: "Entire observation snapshot",
            NavigationFailure.CORRUPTED_SESSION_STATE: "Session continuity and history",
            NavigationFailure.EXPIRED_CONTEXT: "Observation freshness guarantee",
            NavigationFailure.FOCUS_OUT_OF_BOUNDS: "Current focus context",
            NavigationFailure.INTEGRITY_VIOLATION: "System trust guarantees",
        }
        return lost_info.get(self, "None (navigation error only)")


@dataclass(frozen=True)
class RecoveryPath:
    """
    Explicit, deterministic recovery path for a specific failure.
    
    Each recovery path must:
    1. Have constitutional justification
    2. Specify exact destination
    3. Declare what capabilities are lost
    4. Provide clear message for human
    """
    
    failure_type: NavigationFailure
    """Type of failure this path addresses."""
    
    target_stage: WorkflowStage
    """Where to navigate for recovery."""
    
    target_view: Optional[ViewType]
    """Specific view to use (if applicable)."""
    
    required_focus: Optional[str] = None
    """Required focus for recovery (if any)."""
    
    justification: str = ""
    """Constitutional justification for this recovery path."""
    
    lost_capabilities: Tuple[str, ...] = ()
    """Specific capabilities that are lost in recovery."""
    
    recovery_message: str = ""
    """Human-readable message explaining recovery action."""
    
    is_safe_recovery: bool = True
    """Whether this recovery preserves epistemic integrity."""
    
    requires_confirmation: bool = False
    """Whether human confirmation is required before recovery."""
    
    # Metadata
    recovery_id: str = ""
    """Unique identifier for this recovery path."""
    
    created_at: datetime = datetime.now(timezone.utc)
    """When this recovery path was defined."""
    
    def __post_init__(self) -> None:
        """Validate recovery path invariants."""
        if not isinstance(self.failure_type, NavigationFailure):
            raise TypeError("failure_type must be NavigationFailure")
        
        if not isinstance(self.target_stage, WorkflowStage):
            raise TypeError("target_stage must be WorkflowStage")
        
        if self.target_view is not None and not isinstance(self.target_view, ViewType):
            raise TypeError("target_view must be ViewType or None")
        
        if not self.justification:
            raise ValueError("justification cannot be empty")
        
        if not self.recovery_message:
            raise ValueError("recovery_message cannot be empty")
        
        # Validate constitutional justification
        self._validate_justification()
        
        # Set recovery_id if not provided
        if not self.recovery_id:
            object.__setattr__(self, 'recovery_id',
                f"recovery_{self.failure_type.value}_{self.target_stage.value}")
        
        # Validate timezone
        if self.created_at.tzinfo is None:
            object.__setattr__(self, 'created_at',
                self.created_at.replace(tzinfo=timezone.utc))
    
    def _validate_justification(self) -> None:
        """Validate that justification references constitutional principles."""
        required_principles = ["Article 3", "Article 14", "Article 7", "Article 8"]
        justification_lower = self.justification.lower()
        
        has_required = any(
            principle.lower() in justification_lower
            for principle in required_principles
        )
        
        if not has_required:
            raise ValueError(
                f"Recovery justification must reference Article 3, 14, 7, or 8. "
                f"Got: {self.justification}"
            )
    
    def create_target_state(
        self,
        current_state: WorkflowState,
        session_context: Optional[SessionContext] = None
    ) -> WorkflowState:
        """
        Create target workflow state after recovery.
        
        Args:
            current_state: Current workflow state (before failure)
            session_context: Optional session context for focus determination
            
        Returns:
            New workflow state for recovery destination
        """
        # Determine focus for recovery
        focus_id = self.required_focus
        
        if focus_id is None and session_context:
            # Use session context anchor if available
            focus_id = session_context.anchor_id
        
        if focus_id is None:
            # Fall back to current focus
            focus_id = current_state.focus_id
        
        # Special handling for orientation recovery
        if self.target_stage == WorkflowStage.ORIENTATION:
            # Clear focus for fresh orientation
            focus_id = None
        
        return WorkflowState(
            current_stage=self.target_stage,
            current_view=self.target_view,
            focus_id=focus_id,
            session_id=current_state.session_id
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize recovery path to dictionary."""
        return {
            "failure_type": self.failure_type.value,
            "target_stage": self.target_stage.value,
            "target_view": self.target_view.value if self.target_view else None,
            "required_focus": self.required_focus,
            "justification": self.justification,
            "lost_capabilities": list(self.lost_capabilities),
            "recovery_message": self.recovery_message,
            "is_safe_recovery": self.is_safe_recovery,
            "requires_confirmation": self.requires_confirmation,
            "recovery_id": self.recovery_id,
            "created_at": self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RecoveryPath":
        """Deserialize recovery path from dictionary."""
        target_view = None
        if data.get("target_view"):
            target_view = ViewType(data["target_view"])
        
        return cls(
            failure_type=NavigationFailure(data["failure_type"]),
            target_stage=WorkflowStage(data["target_stage"]),
            target_view=target_view,
            required_focus=data.get("required_focus"),
            justification=data["justification"],
            lost_capabilities=tuple(data.get("lost_capabilities", [])),
            recovery_message=data["recovery_message"],
            is_safe_recovery=data.get("is_safe_recovery", True),
            requires_confirmation=data.get("requires_confirmation", False),
            recovery_id=data.get("recovery_id", ""),
            created_at=datetime.fromisoformat(data["created_at"])
        )


class RecoveryRegistry:
    """
    Registry of all constitutionally-approved recovery paths.
    
    This is the single source of truth for failure recovery.
    No recovery may be performed outside registered paths.
    """
    
    # Class variable holding all registered recovery paths
    _registered_paths: Dict[str, RecoveryPath] = {}
    _initialized: bool = False
    
    @classmethod
    def initialize(cls) -> None:
        """Initialize the recovery registry with all approved paths."""
        if cls._initialized:
            return
        
        # Missing observations recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.MISSING_OBSERVATIONS,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.OVERVIEW,
            justification="Article 14: Graceful degradation when observations are unavailable. "
                        "Return to orientation to establish what CAN be observed.",
            lost_capabilities=("Detailed examination", "Connection analysis", "Pattern detection"),
            recovery_message="⚠️ Required observations unavailable. Returning to overview "
                           "to show what CAN be observed.",
            is_safe_recovery=True,
            requires_confirmation=False
        ))
        
        # Invalid anchor reference recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.INVALID_ANCHOR_REFERENCE,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.OVERVIEW,
            required_focus="root",  # Default root anchor
            justification="Article 3: Truth preservation requires acknowledging "
                        "when references are invalid. Return to safe root.",
            lost_capabilities=("Previous focus context",),
            recovery_message="🔗 Invalid reference. Returning to root overview.",
            is_safe_recovery=True,
            requires_confirmation=False
        ))
        
        # Snapshot not found recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.SNAPSHOT_NOT_FOUND,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=None,  # No specific view - may need fresh observation
            justification="Article 8: Honest performance requires acknowledging "
                        "missing data rather than pretending it exists.",
            lost_capabilities=("All previous observations", "Investigation continuity"),
            recovery_message="📸 Snapshot unavailable. Starting fresh observation.",
            is_safe_recovery=True,
            requires_confirmation=True  # Confirm before losing all data
        ))
        
        # Illegal transition recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.ILLEGAL_TRANSITION,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.HELP,
            justification="Article 7: Clear affordances require explaining "
                        "why an action is not allowed and providing help.",
            lost_capabilities=("Current navigation context",),
            recovery_message="🚫 Navigation rule violation. Showing help.",
            is_safe_recovery=True,
            requires_confirmation=False
        ))
        
        # Invalid stage sequence recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.INVALID_STAGE_SEQUENCE,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.HELP,
            justification="Article 6: Linear investigation requires canonical "
                        "stage progression. Return to orientation for valid path.",
            lost_capabilities=("Current stage progress",),
            recovery_message="🔄 Invalid stage sequence. Returning to start of workflow.",
            is_safe_recovery=True,
            requires_confirmation=True
        ))
        
        # Corrupted session state recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.CORRUPTED_SESSION_STATE,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.OVERVIEW,
            justification="Article 15: Session integrity requires recovery "
                        "from corruption by returning to known-safe state.",
            lost_capabilities=("Session history", "Recent context", "Unsaved notes"),
            recovery_message="⚠️ Session corrupted. Starting fresh investigation.",
            is_safe_recovery=False,  # Loses data, not epistemically safe
            requires_confirmation=True
        ))
        
        # Expired context recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.EXPIRED_CONTEXT,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.OVERVIEW,
            justification="Article 3: Truth preservation requires acknowledging "
                        "when data may be stale and offering refresh.",
            lost_capabilities=("Observation freshness guarantee",),
            recovery_message="🕒 Context expired. Refreshing observations.",
            is_safe_recovery=True,
            requires_confirmation=False
        ))
        
        # Focus out of bounds recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.FOCUS_OUT_OF_BOUNDS,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=ViewType.OVERVIEW,
            required_focus=None,  # Clear focus
            justification="Article 5: Single-focus interface requires valid focus. "
                        "Clear invalid focus and return to overview.",
            lost_capabilities=("Current focus",),
            recovery_message="🎯 Invalid focus. Clearing and returning to overview.",
            is_safe_recovery=True,
            requires_confirmation=False
        ))
        
        # Integrity violation recovery
        cls._register_path(RecoveryPath(
            failure_type=NavigationFailure.INTEGRITY_VIOLATION,
            target_stage=WorkflowStage.ORIENTATION,
            target_view=None,  # System may be in degraded state
            justification="Article 3: Truth preservation requires halting "
                        "when system integrity cannot be guaranteed.",
            lost_capabilities=("System trust", "All active investigations"),
            recovery_message="🚨 System integrity violation. "
                           "Emergency recovery to safe state.",
            is_safe_recovery=False,
            requires_confirmation=False  # Emergency - no time for confirmation
        ))
        
        cls._initialized = True
    
    @classmethod
    def _register_path(cls, path: RecoveryPath) -> None:
        """Register a recovery path (internal use only)."""
        if path.recovery_id in cls._registered_paths:
            raise ValueError(f"Recovery path with ID {path.recovery_id} already registered")
        
        # Validate path follows constitutional rules
        cls._validate_recovery_constitutionality(path)
        
        cls._registered_paths[path.recovery_id] = path
    
    @classmethod
    def _validate_recovery_constitutionality(cls, path: RecoveryPath) -> None:
        """Validate that recovery path follows all constitutional rules."""
        # Article 3: Must declare uncertainty/lost capabilities
        if not path.lost_capabilities and path.failure_type.lost_information != "None":
            raise ValueError(
                f"Recovery path {path.recovery_id} violates Article 3: "
                f"Must declare lost capabilities for failure {path.failure_type}"
            )
        
        # Article 7: Must have clear recovery message
        if not path.recovery_message:
            raise ValueError(
                f"Recovery path {path.recovery_id} violates Article 7: "
                f"Must have clear recovery message"
            )
        
        # Article 8: Must not pretend performance that isn't there
        if path.is_safe_recovery and path.failure_type.requires_immediate_recovery:
            # Safe recovery for immediate failures should be carefully justified
            if "emergency" not in path.justification.lower() and "degradation" not in path.justification.lower():
                raise ValueError(
                    f"Recovery path {path.recovery_id} claims safe recovery "
                    f"for immediate failure {path.failure_type} without proper justification"
                )
    
    @classmethod
    def get_recovery_path(
        cls,
        failure_type: NavigationFailure,
        current_state: Optional[WorkflowState] = None,
        severity: Optional[str] = None
    ) -> RecoveryPath:
        """
        Get recovery path for a specific failure.
        
        Args:
            failure_type: Type of navigation failure
            current_state: Optional current workflow state
            severity: Optional severity level ("low", "medium", "high")
            
        Returns:
            RecoveryPath for the given failure
            
        Raises:
            ValueError: If no recovery path found for failure type
        """
        if not cls._initialized:
            cls.initialize()
        
        # Find all paths for this failure type
        matching_paths = [
            path for path in cls._registered_paths.values()
            if path.failure_type == failure_type
        ]
        
        if not matching_paths:
            raise ValueError(f"No recovery path registered for failure type: {failure_type}")
        
        # If multiple paths, select based on severity/state
        if len(matching_paths) > 1:
            # Apply selection logic
            selected_path = cls._select_recovery_path(matching_paths, current_state, severity)
            return selected_path
        
        return matching_paths[0]
    
    @classmethod
    def _select_recovery_path(
        cls,
        paths: List[RecoveryPath],
        current_state: Optional[WorkflowState],
        severity: Optional[str]
    ) -> RecoveryPath:
        """
        Select appropriate recovery path from multiple options.
        
        Defaults to first path that matches additional criteria.
        """
        # Filter by severity if specified
        if severity:
            severity_paths = [
                p for p in paths
                if ("emergency" in p.justification.lower() and severity == "high") or
                   ("degradation" in p.justification.lower() and severity == "medium") or
                   ("refresh" in p.justification.lower() and severity == "low")
            ]
            if severity_paths:
                return severity_paths[0]
        
        # Filter by current state if available
        if current_state:
            # Prefer paths that maintain current view if possible
            state_paths = [
                p for p in paths
                if p.target_view == current_state.current_view or p.target_view is None
            ]
            if state_paths:
                return state_paths[0]
        
        # Default to first path
        return paths[0]
    
    @classmethod
    def validate_recovery_possible(
        cls,
        failure_type: NavigationFailure,
        current_state: WorkflowState,
        session_context: Optional[SessionContext] = None
    ) -> Tuple[bool, Optional[RecoveryPath], Optional[str]]:
        """
        Validate if recovery is possible for a failure.
        
        Args:
            failure_type: Type of navigation failure
            current_state: Current workflow state
            session_context: Optional session context
            
        Returns:
            Tuple of (is_possible, recovery_path, error_message)
        """
        try:
            recovery_path = cls.get_recovery_path(failure_type, current_state)
            
            # Check if recovery path can create target state
            try:
                recovery_path.create_target_state(current_state, session_context)
                return True, recovery_path, None
            except Exception as e:
                return False, recovery_path, f"Cannot create recovery state: {e}"
            
        except ValueError as e:
            return False, None, str(e)
    
    @classmethod
    def get_all_recovery_paths(cls) -> List[RecoveryPath]:
        """Get all registered recovery paths."""
        if not cls._initialized:
            cls.initialize()
        
        return list(cls._registered_paths.values())


class NavigationFailureDetector:
    """
    Detects navigation failures without inference or guessing.
    
    Only detects failures that can be determined from available state.
    Never speculates about causes or intent.
    """
    
    @staticmethod
    def detect_failures(
        current_state: WorkflowState,
        session_context: Optional[SessionContext],
        attempted_transition: Optional[Tuple[WorkflowStage, Optional[ViewType]]] = None
    ) -> List[NavigationFailure]:
        """
        Detect navigation failures from current state.
        
        Args:
            current_state: Current workflow state
            session_context: Optional session context
            attempted_transition: Optional (target_stage, target_view) being attempted
            
        Returns:
            List of detected navigation failures (empty if none)
        """
        failures = []
        
        # Check session context validity
        if session_context:
            # Note: We cannot actually validate anchor/snapshot existence here
            # because we cannot import observations. This is a placeholder.
            # In practice, this would be called from bridge layer that has access.
            pass
        
        # Check workflow state consistency
        if current_state.focus_id and ";" in current_state.focus_id:
            failures.append(NavigationFailure.FOCUS_OUT_OF_BOUNDS)
        
        # Check for illegal transitions if attempted
        if attempted_transition:
            target_stage, target_view = attempted_transition
            
            # Simple validation (more complex validation in workflow.py)
            stage_order = list(WorkflowStage)
            current_index = stage_order.index(current_state.current_stage)
            target_index = stage_order.index(target_stage)
            
            # Check for backward jumps that aren't shortcuts
            if target_index < current_index:
                # This might be legal via shortcut, but we can't check here
                # Just note it as potential invalid sequence
                failures.append(NavigationFailure.INVALID_STAGE_SEQUENCE)
            
            # Check for skipping
            if target_index > current_index + 1:
                failures.append(NavigationFailure.ILLEGAL_TRANSITION)
        
        return failures


def validate_recovery_system_integrity() -> Tuple[bool, Optional[str]]:
    """
    Validate that recovery system follows constitutional rules.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        RecoveryRegistry.initialize()
        
        # Check each registered path
        for path in RecoveryRegistry.get_all_recovery_paths():
            # Verify failure type is valid
            if not isinstance(path.failure_type, NavigationFailure):
                return False, f"Invalid failure type in path {path.recovery_id}"
            
            # Verify recovery message is clear
            if not path.recovery_message or len(path.recovery_message.strip()) < 10:
                return False, f"Recovery message too short in path {path.recovery_id}"
            
            # Verify justification references articles
            if "Article" not in path.justification:
                return False, f"Justification missing Article reference in path {path.recovery_id}"
        
        # Verify all failure types have at least one recovery path
        for failure_type in NavigationFailure:
            try:
                RecoveryRegistry.get_recovery_path(failure_type)
            except ValueError:
                return False, f"No recovery path for failure type: {failure_type}"
        
        return True, None
        
    except Exception as e:
        return False, f"Recovery system integrity validation failed: {e}"


def get_recovery_system_summary() -> str:
    """Get human-readable summary of recovery system."""
    summary = [
        "NAVIGATION RECOVERY SYSTEM",
        "=" * 40,
        "",
        "Constitutional Basis:",
        "- Article 3: Truth Preservation (declare uncertainty)",
        "- Article 14: Graceful Degradation (show available paths)",
        "- Article 7: Clear Affordances (visible recovery options)",
        "- Article 8: Honest Performance (explain why recovery needed)",
        "",
        "Failure Types:",
    ]
    
    for failure_type in NavigationFailure:
        summary.append(f"  - {failure_type.value.replace('_', ' ').title()}")
        summary.append(f"    Immediate recovery: {failure_type.requires_immediate_recovery}")
        summary.append(f"    Allows continuation: {failure_type.allows_continuation}")
        summary.append(f"    Lost information: {failure_type.lost_information}")
        summary.append("")
    
    summary.append("Recovery Principles:")
    summary.append("1. No silent correction - all recovery is visible")
    summary.append("2. No guessing - only registered recovery paths")
    summary.append("3. No 'best effort' lies - declare lost capabilities")
    summary.append("4. Mandatory clarity - explain what happened")
    
    return "\n".join(summary)