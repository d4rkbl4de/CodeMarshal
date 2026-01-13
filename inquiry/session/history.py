"""
inquiry/session/history.py

CRITICAL CONSTITUTIONAL GUARD: Investigation History
===================================================
History is the audit trail of human curiosity, not a map.

History is NOT:
- Branching narratives
- Summarized conclusions
- Recommended paths
- Performance metrics

History IS:
- Append-only sequence of investigative steps
- Immutable record of exactly what was done
- Deterministic replay capability
- Truth-preserving audit trail

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 2: Human Primacy (records human actions)
- Article 6: Linear Investigation (append-only)
- Article 9: Immutable Observations (immutable steps)
- Article 13: Deterministic Operation (replayable)
- Article 15: Session Integrity (preserved across interruptions)

ALLOWED IMPORTS:
- context.SessionContext
- storage.atomic
- datetime, uuid, typing, dataclasses, pathlib

PROHIBITED IMPORTS:
- recovery.py (no recovery logic)
- lens.* (no UI concerns)
- patterns.* (no analysis)
- notebook.* (no thinking content)
"""

import enum
import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Union
from uuid import UUID, uuid4

# Allowed imports from session module
from .context import SessionContext

# Allowed imports from storage module
from storage.atomic import AtomicWriteResult, write_atomic, AtomicReadResult, read_atomic
from storage.corruption import CorruptionCheck, CorruptionState


class HistoryAction(enum.Enum):
    """Type of investigative action taken."""
    
    OBSERVE = "observe"
    """Observe a new path or anchor."""
    
    QUERY = "query"
    """Ask a question about what's being observed."""
    
    PATTERN = "pattern"
    """Request pattern detection."""
    
    NOTE = "note"
    """Add a human thought/note."""
    
    EXPORT = "export"
    """Export investigation state."""
    
    NAVIGATE = "navigate"
    """Navigate to a different view."""
    
    CHANGE_FOCUS = "change_focus"
    """Change investigation focus (question type)."""


@dataclass(frozen=True)
class HistoryStep:
    """
    Immutable record of one investigative step.
    
    Contains only references, never payloads.
    This ensures steps remain lightweight and truth-preserving.
    """
    
    # Unique identifier for this step
    step_id: UUID
    
    # When this step was recorded
    timestamp: datetime
    
    # What the investigator was looking at
    context: SessionContext
    
    # What action was taken
    action: HistoryAction
    
    # References to outputs (IDs only, no content)
    output_references: Tuple[str, ...] = field(default_factory=tuple)
    
    # Optional metadata (never essential content)
    metadata: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    
    def __post_init__(self) -> None:
        """Validate HistoryStep invariants."""
        if not isinstance(self.step_id, UUID):
            raise TypeError("step_id must be UUID")
        
        if not isinstance(self.timestamp, datetime):
            raise TypeError("timestamp must be datetime")
        
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        
        if not isinstance(self.context, SessionContext):
            raise TypeError("context must be SessionContext")
        
        if not isinstance(self.action, HistoryAction):
            raise TypeError("action must be HistoryAction")
        
        # Validate output references are strings
        for ref in self.output_references:
            if not isinstance(ref, str):
                raise TypeError("output_references must be strings")
        
        # Validate metadata is pairs of strings
        for key, value in self.metadata:
            if not isinstance(key, str) or not isinstance(value, str):
                raise TypeError("metadata must be Tuple[Tuple[str, str], ...]")
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "step_id": str(self.step_id),
            "timestamp": self.timestamp.isoformat(),
            "context": asdict(self.context),
            "action": self.action.value,
            "output_references": list(self.output_references),
            "metadata": [
                {"key": key, "value": value}
                for key, value in self.metadata
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryStep":
        """Deserialize from dictionary."""
        # Reconstruct context
        context_data = data["context"]
        context = SessionContext(
            snapshot_id=UUID(context_data["snapshot_id"]),
            anchor_id=context_data["anchor_id"],
            question_type=context_data["question_type"],
            created_at=datetime.fromisoformat(context_data["created_at"])
        )
        
        return cls(
            step_id=UUID(data["step_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            context=context,
            action=HistoryAction(data["action"]),
            output_references=tuple(data["output_references"]),
            metadata=tuple(
                (item["key"], item["value"])
                for item in data["metadata"]
            )
        )
    
    def compute_integrity_hash(self) -> str:
        """
        Compute deterministic hash for integrity verification.
        
        Hash includes all fields except step_id and timestamp.
        This allows detecting if step content was modified.
        """
        hash_input = json.dumps(
            {
                "context": asdict(self.context),
                "action": self.action.value,
                "output_references": sorted(self.output_references),
                "metadata": sorted(
                    [f"{key}:{value}" for key, value in self.metadata]
                )
            },
            sort_keys=True
        )
        return hashlib.sha256(hash_input.encode()).hexdigest()


@dataclass
class InvestigationHistory:
    """
    Append-only container for investigation steps.
    
    Steps are never modified, reordered, or deleted.
    If a step is "wrong," it stays wrong. That's truth.
    """
    
    # Immutable identifier for this history
    history_id: UUID = field(default_factory=uuid4)
    
    # When this history was created
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Append-only list of steps
    steps: List[HistoryStep] = field(default_factory=list)
    
    # Last modification time (updated on each append)
    modified_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self) -> None:
        """Validate InvestigationHistory invariants."""
        if not isinstance(self.history_id, UUID):
            raise TypeError("history_id must be UUID")
        
        if not isinstance(self.created_at, datetime):
            raise TypeError("created_at must be datetime")
        
        if self.created_at.tzinfo is None:
            raise ValueError("created_at must be timezone-aware")
        
        if not isinstance(self.modified_at, datetime):
            raise TypeError("modified_at must be datetime")
        
        if self.modified_at.tzinfo is None:
            raise ValueError("modified_at must be timezone-aware")
    
    def append_step(self, step: HistoryStep) -> None:
        """
        Add a new step to the history.
        
        This is the ONLY mutation method allowed.
        Steps cannot be removed or modified after addition.
        
        Args:
            step: HistoryStep to append
            
        Raises:
            ValueError: If step validation fails
        """
        # Ensure step is not None
        if step is None:
            raise ValueError("Cannot append None step")
        
        # Ensure step is a HistoryStep
        if not isinstance(step, HistoryStep):
            raise TypeError("step must be HistoryStep")
        
        # Ensure timestamps are monotonic (not strictly required but good practice)
        if self.steps and step.timestamp < self.steps[-1].timestamp:
            logger = logging.getLogger(__name__)
            logger.warning(
                "Step timestamp %s is earlier than previous step %s",
                step.timestamp,
                self.steps[-1].timestamp
            )
        
        # Append step
        self.steps.append(step)
        
        # Update modification time
        object.__setattr__(self, 'modified_at', datetime.now(timezone.utc))
    
    def get_step(self, step_id: UUID) -> Optional[HistoryStep]:
        """
        Retrieve a step by ID.
        
        Returns None if step not found.
        """
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None
    
    def get_steps_by_action(self, action: HistoryAction) -> List[HistoryStep]:
        """
        Retrieve all steps of a specific action type.
        
        Returns empty list if none found.
        """
        return [step for step in self.steps if step.action == action]
    
    def get_last_step(self) -> Optional[HistoryStep]:
        """Get most recent step, if any."""
        if not self.steps:
            return None
        return self.steps[-1]
    
    def get_step_count(self) -> int:
        """Get total number of steps."""
        return len(self.steps)
    
    def is_empty(self) -> bool:
        """Check if history has no steps."""
        return len(self.steps) == 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for storage."""
        return {
            "history_id": str(self.history_id),
            "created_at": self.created_at.isoformat(),
            "steps": [step.to_dict() for step in self.steps],
            "modified_at": self.modified_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "InvestigationHistory":
        """Deserialize from dictionary."""
        steps = [
            HistoryStep.from_dict(step_data)
            for step_data in data["steps"]
        ]
        
        return cls(
            history_id=UUID(data["history_id"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            steps=steps,
            modified_at=datetime.fromisoformat(data["modified_at"])
        )
    
    def compute_integrity_hashes(self) -> Dict[str, str]:
        """
        Compute integrity hashes for all steps.
        
        Returns mapping from step_id to hash.
        """
        return {
            str(step.step_id): step.compute_integrity_hash()
            for step in self.steps
        }
    
    def verify_integrity(self) -> CorruptionCheck:
        """
        Verify integrity of all steps.
        
        Returns CorruptionCheck with any issues found.
        """
        issues: List[str] = []
        
        # Check for duplicate step IDs
        step_ids = set()
        for step in self.steps:
            if step.step_id in step_ids:
                issues.append(f"Duplicate step_id: {step.step_id}")
            step_ids.add(step.step_id)
        
        # Check temporal consistency (warnings only, not errors)
        for i in range(1, len(self.steps)):
            if self.steps[i].timestamp < self.steps[i-1].timestamp:
                issues.append(
                    f"Step {self.steps[i].step_id} timestamp ({self.steps[i].timestamp}) "
                    f"is earlier than previous step ({self.steps[i-1].timestamp})"
                )
        
        if issues:
            return CorruptionCheck(
                is_corrupt=True,
                corruption_type="history_integrity",
                issues=issues,
                severity="medium"
            )
        else:
            return CorruptionCheck(
                is_corrupt=False,
                corruption_type="history_integrity",
                issues=[],
                severity="none"
            )


class HistoryStorage:
    """
    Handles persistence of InvestigationHistory.
    
    Uses atomic writes to ensure history is never partially written.
    """
    
    def __init__(self, storage_path: Path) -> None:
        """
        Initialize history storage.
        
        Args:
            storage_path: Directory where history files are stored
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    def save_history(self, history: InvestigationHistory) -> AtomicWriteResult:
        """
        Save investigation history atomically.
        
        Args:
            history: InvestigationHistory to save
            
        Returns:
            AtomicWriteResult indicating success or failure
        """
        history_file = self.storage_path / "history.json"
        
        # Serialize history
        history_data = history.to_dict()
        data_bytes = json.dumps(history_data, indent=2).encode()
        
        # Write atomically
        return write_atomic(str(history_file), data_bytes)
    
    def load_history(self) -> Tuple[Optional[InvestigationHistory], Optional[CorruptionState]]:
        """
        Load investigation history if it exists.
        
        Returns:
            Tuple of (history, corruption_state)
            history may be None if file doesn't exist or cannot be loaded
        """
        history_file = self.storage_path / "history.json"
        
        if not history_file.exists():
            return None, None
        
        # Read atomically
        read_result = read_atomic(str(history_file))
        
        if not read_result or not read_result.is_valid:
            # Corrupted read
            corruption = CorruptionState(
                file_path=str(history_file),
                corruption_type="read_failure",
                detected_at=datetime.now(timezone.utc),
                severity="high"
            )
            return None, corruption
        
        try:
            # Parse JSON
            data = json.loads(read_result.data_bytes.decode())
            
            # Convert to InvestigationHistory
            history = InvestigationHistory.from_dict(data)
            
            # Verify integrity
            integrity_check = history.verify_integrity()
            if integrity_check.is_corrupt:
                corruption = CorruptionState(
                    file_path=str(history_file),
                    corruption_type=integrity_check.corruption_type,
                    detected_at=datetime.now(timezone.utc),
                    severity=integrity_check.severity,
                    details="; ".join(integrity_check.issues)
                )
                return history, corruption
            
            return history, None
            
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
            # Corrupted content
            corruption = CorruptionState(
                file_path=str(history_file),
                corruption_type="parse_failure",
                detected_at=datetime.now(timezone.utc),
                severity="high",
                details=str(e)
            )
            return None, corruption
    
    def create_new_history(self) -> InvestigationHistory:
        """
        Create a new empty investigation history.
        """
        return InvestigationHistory()


class HistoryBuilder:
    """
    Helper for constructing history steps.
    
    Ensures proper construction of HistoryStep objects.
    """
    
    @staticmethod
    def create_step(
        context: SessionContext,
        action: HistoryAction,
        output_references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> HistoryStep:
        """
        Create a new history step.
        
        Args:
            context: Current session context
            action: Type of action taken
            output_references: Optional list of output IDs
            metadata: Optional metadata dictionary
            
        Returns:
            New HistoryStep
        """
        # Convert output_references
        if output_references is None:
            output_refs_tuple: Tuple[str, ...] = ()
        else:
            output_refs_tuple = tuple(output_references)
        
        # Convert metadata
        if metadata is None:
            metadata_tuple: Tuple[Tuple[str, str], ...] = ()
        else:
            metadata_tuple = tuple(metadata.items())
        
        return HistoryStep(
            step_id=uuid4(),
            timestamp=datetime.now(timezone.utc),
            context=context,
            action=action,
            output_references=output_refs_tuple,
            metadata=metadata_tuple
        )
    
    @staticmethod
    def create_step_from_previous(
        previous_step: HistoryStep,
        new_context: SessionContext,
        action: HistoryAction,
        output_references: Optional[List[str]] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> HistoryStep:
        """
        Create a step that follows a previous step.
        
        This ensures temporal ordering by checking that
        the new step's timestamp is after the previous step's.
        
        Args:
            previous_step: Previous step in history
            new_context: New session context
            action: Type of action taken
            output_references: Optional list of output IDs
            metadata: Optional metadata dictionary
            
        Returns:
            New HistoryStep with timestamp after previous step
        """
        # Ensure we don't create a step with timestamp before previous
        now = datetime.now(timezone.utc)
        if now <= previous_step.timestamp:
            # Add 1 microsecond to ensure ordering
            now = previous_step.timestamp.replace(
                microsecond=previous_step.timestamp.microsecond + 1
            )
        
        return HistoryStep(
            step_id=uuid4(),
            timestamp=now,
            context=new_context,
            action=action,
            output_references=tuple(output_references) if output_references else (),
            metadata=tuple(metadata.items()) if metadata else ()
        )


# -------------------------------------------------------------------
# CONSTITUTIONAL ENFORCEMENT
# -------------------------------------------------------------------

def validate_history_invariants(history: InvestigationHistory) -> List[str]:
    """
    Validate constitutional invariants for history.
    
    Returns list of violations, empty if all invariants satisfied.
    """
    violations = []
    
    # Article 6: Linear Investigation (append-only)
    # Check that steps are temporally ordered
    for i in range(1, len(history.steps)):
        if history.steps[i].timestamp < history.steps[i - 1].timestamp:
            violations.append(
                f"Article 6 violation: Step {i} timestamp ({history.steps[i].timestamp}) "
                f"is before step {i-1} ({history.steps[i-1].timestamp})"
            )
    
    # Article 9: Immutable Observations
    # Check that steps are immutable (we can't fully check this at runtime,
    # but we can verify they're all HistoryStep instances)
    for i, step in enumerate(history.steps):
        if not isinstance(step, HistoryStep):
            violations.append(
                f"Article 9 violation: Step {i} is not immutable HistoryStep"
            )
    
    # Article 13: Deterministic Operation
    # Verify that all steps have required fields
    for i, step in enumerate(history.steps):
        if not hasattr(step, 'compute_integrity_hash'):
            violations.append(
                f"Article 13 violation: Step {i} missing integrity hash method"
            )
    
    return violations