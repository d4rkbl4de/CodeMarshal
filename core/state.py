"""
Investigation State Machine for CodeMarshal.

Constitutional Basis:
- Article 6: Linear Investigation
- Article 14: Graceful Degradation

Production Responsibility:
Define legal investigation phases and transitions.
This is not UI state. This is truth lifecycle state.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass
from enum import Enum, auto
from typing import ClassVar, List, Optional, Set, Tuple

from core.context import RuntimeContext


class InvestigationPhase(Enum):
    """Legal phases of a CodeMarshal investigation."""
    
    # Initialization
    BOOTSTRAPPED = auto()              # Core initialized, no actions yet
    ENFORCEMENT_ACTIVE = auto()        # Constitutional guards are active
    
    # Primary workflow
    OBSERVATION_COMPLETE = auto()      # All eyes have witnessed
    INQUIRY_ACTIVE = auto()            # Human questions being asked
    PATTERNS_CALCULATED = auto()       # Numeric patterns computed
    PRESENTATION_ACTIVE = auto()       # Lens showing truth
    
    # Terminal states
    TERMINATED_NORMAL = auto()         # Clean shutdown
    TERMINATED_VIOLATION = auto()      # Constitutional violation detected
    TERMINATED_ERROR = auto()          # System failure
    
    # Recovery states
    RECOVERY_NEEDED = auto()           # Can resume from here
    RESUME_IN_PROGRESS = auto()        # Restoring previous state
    
    def is_terminal(self) -> bool:
        """Return True if this phase ends the investigation."""
        return self in {
            InvestigationPhase.TERMINATED_NORMAL,
            InvestigationPhase.TERMINATED_VIOLATION,
            InvestigationPhase.TERMINATED_ERROR,
        }
    
    def is_recoverable(self) -> bool:
        """Return True if investigation can resume from this phase."""
        return self in {
            InvestigationPhase.OBSERVATION_COMPLETE,
            InvestigationPhase.INQUIRY_ACTIVE,
            InvestigationPhase.PATTERNS_CALCULATED,
            InvestigationPhase.PRESENTATION_ACTIVE,
            InvestigationPhase.RECOVERY_NEEDED,
        }


@dataclass(frozen=True)
class StateTransition:
    """Immutable record of a state change."""
    
    from_phase: InvestigationPhase
    to_phase: InvestigationPhase
    timestamp: datetime.datetime
    reason: Optional[str] = None
    
    def __str__(self) -> str:
        reason_str = f" ({self.reason})" if self.reason else ""
        return f"{self.from_phase.name} → {self.to_phase.name}{reason_str}"


class InvestigationState:
    """
    State machine for investigation lifecycle.
    
    Constitutional Guarantees:
    1. State transitions are explicit and validated
    2. Illegal transitions raise immediately
    3. State history is append-only
    4. Terminal states cannot be exited
    5. Linear investigation flow is enforced
    """
    
    # Legal transitions: (from, to)
    _LEGAL_TRANSITIONS: ClassVar[Set[Tuple[InvestigationPhase, InvestigationPhase]]] = {
        # Initialization path
        (InvestigationPhase.BOOTSTRAPPED, InvestigationPhase.ENFORCEMENT_ACTIVE),
        (InvestigationPhase.ENFORCEMENT_ACTIVE, InvestigationPhase.OBSERVATION_COMPLETE),
        
        # Primary linear investigation path
        (InvestigationPhase.OBSERVATION_COMPLETE, InvestigationPhase.INQUIRY_ACTIVE),
        (InvestigationPhase.INQUIRY_ACTIVE, InvestigationPhase.PATTERNS_CALCULATED),
        (InvestigationPhase.PATTERNS_CALCULATED, InvestigationPhase.PRESENTATION_ACTIVE),
        
        # Recovery path
        (InvestigationPhase.OBSERVATION_COMPLETE, InvestigationPhase.RECOVERY_NEEDED),
        (InvestigationPhase.INQUIRY_ACTIVE, InvestigationPhase.RECOVERY_NEEDED),
        (InvestigationPhase.PATTERNS_CALCULATED, InvestigationPhase.RECOVERY_NEEDED),
        (InvestigationPhase.PRESENTATION_ACTIVE, InvestigationPhase.RECOVERY_NEEDED),
        (InvestigationPhase.RECOVERY_NEEDED, InvestigationPhase.RESUME_IN_PROGRESS),
        (InvestigationPhase.RESUME_IN_PROGRESS, InvestigationPhase.OBSERVATION_COMPLETE),
        
        # Terminal transitions (from any state)
        (InvestigationPhase.BOOTSTRAPPED, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.ENFORCEMENT_ACTIVE, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.OBSERVATION_COMPLETE, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.INQUIRY_ACTIVE, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.PATTERNS_CALCULATED, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.PRESENTATION_ACTIVE, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.RECOVERY_NEEDED, InvestigationPhase.TERMINATED_NORMAL),
        (InvestigationPhase.RESUME_IN_PROGRESS, InvestigationPhase.TERMINATED_NORMAL),
        
        # Error/Violation transitions (from any state)
        (InvestigationPhase.BOOTSTRAPPED, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.ENFORCEMENT_ACTIVE, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.OBSERVATION_COMPLETE, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.INQUIRY_ACTIVE, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.PATTERNS_CALCULATED, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.PRESENTATION_ACTIVE, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.RECOVERY_NEEDED, InvestigationPhase.TERMINATED_VIOLATION),
        (InvestigationPhase.RESUME_IN_PROGRESS, InvestigationPhase.TERMINATED_VIOLATION),
        
        (InvestigationPhase.BOOTSTRAPPED, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.ENFORCEMENT_ACTIVE, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.OBSERVATION_COMPLETE, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.INQUIRY_ACTIVE, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.PATTERNS_CALCULATED, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.PRESENTATION_ACTIVE, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.RECOVERY_NEEDED, InvestigationPhase.TERMINATED_ERROR),
        (InvestigationPhase.RESUME_IN_PROGRESS, InvestigationPhase.TERMINATED_ERROR),
    }
    
    @classmethod
    def is_transition_legal(cls, from_phase: InvestigationPhase, to_phase: InvestigationPhase) -> bool:
        """Check if transition between phases is legal."""
        return (from_phase, to_phase) in cls._LEGAL_TRANSITIONS
    
    def __init__(self, context: RuntimeContext) -> None:
        """
        Initialize state machine with bootstrapped phase.
        
        Args:
            context: Runtime context for state management
        """
        self._context = context
        self._current_phase: InvestigationPhase = InvestigationPhase.BOOTSTRAPPED
        self._transition_history: List[StateTransition] = []
        
        # Note: No transition recorded for initial state since it's not a transition
    
    @property
    def current_phase(self) -> InvestigationPhase:
        """Get current investigation phase."""
        return self._current_phase
    
    @property
    def transition_history(self) -> Tuple[StateTransition, ...]:
        """Get immutable copy of transition history."""
        return tuple(self._transition_history)
    
    @property
    def is_terminal(self) -> bool:
        """Check if current state is terminal."""
        return self._current_phase.is_terminal()
    
    @property
    def is_recoverable(self) -> bool:
        """Check if current state supports recovery."""
        return self._current_phase.is_recoverable()
    
    def transition_to(self, to_phase: InvestigationPhase, reason: Optional[str] = None) -> None:
        """
        Transition to new phase with validation.
        
        Args:
            to_phase: Target phase
            reason: Human-readable reason for transition
            
        Raises:
            ValueError: If transition is illegal
            RuntimeError: If trying to exit terminal state
        """
        # Check if current state is terminal
        if self._current_phase.is_terminal():
            raise RuntimeError(
                f"Cannot transition from terminal state: {self._current_phase.name}"
            )
        
        # Validate transition
        if not self.is_transition_legal(self._current_phase, to_phase):
            raise ValueError(
                f"Illegal state transition: {self._current_phase.name} → {to_phase.name}\n"
                f"Reason: {reason or 'No reason provided'}"
            )
        
        # Record transition
        self._record_transition(to_phase, reason)
        self._current_phase = to_phase
    
    def force_transition(self, to_phase: InvestigationPhase, reason: str) -> None:
        """
        Force transition (for emergencies only).
        
        Constitutional Basis: Article 14 (Graceful Degradation)
        Use only when system cannot continue normally.
        
        Args:
            to_phase: Target phase (must be terminal)
            reason: Required explanation for emergency transition
            
        Raises:
            ValueError: If target phase is not terminal
        """
        if not to_phase.is_terminal():
            raise ValueError(
                "Force transitions must go to terminal states. "
                f"Attempted: {self._current_phase.name} → {to_phase.name}"
            )
        
        # Emergency transitions bypass normal validation
        emergency_transition = StateTransition(
            from_phase=self._current_phase,
            to_phase=to_phase,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            reason=f"FORCED: {reason}"
        )
        
        self._transition_history.append(emergency_transition)
        self._current_phase = to_phase
    
    def can_transition_to(self, to_phase: InvestigationPhase) -> bool:
        """
        Check if transition to target phase is currently legal.
        
        Args:
            to_phase: Target phase to check
            
        Returns:
            True if transition is currently allowed
        """
        if self._current_phase.is_terminal():
            return False
        
        return self.is_transition_legal(self._current_phase, to_phase)
    
    def get_available_transitions(self) -> Set[InvestigationPhase]:
        """
        Get set of phases that can be transitioned to from current phase.
        
        Returns:
            Set of legal next phases
        """
        if self._current_phase.is_terminal():
            return set()
        
        return {
            to_phase
            for (from_phase, to_phase) in self._LEGAL_TRANSITIONS
            if from_phase == self._current_phase
        }
    
    def get_history_since(self, timestamp: datetime.datetime) -> Tuple[StateTransition, ...]:
        """
        Get transitions since given timestamp.
        
        Args:
            timestamp: Filter transitions after this time
            
        Returns:
            Tuple of transitions after timestamp
        """
        return tuple(
            transition
            for transition in self._transition_history
            if transition.timestamp > timestamp
        )
    
    def _record_transition(self, to_phase: InvestigationPhase, reason: Optional[str]) -> None:
        """Record a transition in history."""
        transition = StateTransition(
            from_phase=self._current_phase,
            to_phase=to_phase,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            reason=reason
        )
        
        # Validate the transition (defensive programming)
        if not self.is_transition_legal(transition.from_phase, transition.to_phase):
            raise RuntimeError(
                f"Attempted to record illegal transition: {transition}"
            )
        
        self._transition_history.append(transition)
    
    def __repr__(self) -> str:
        """Machine-readable representation."""
        transitions = len(self._transition_history)
        return (
            f"InvestigationState("
            f"phase={self._current_phase.name}, "
            f"transitions={transitions}, "
            f"terminal={self.is_terminal})"
        )
    
    def __str__(self) -> str:
        """Human-readable representation."""
        transitions = len(self._transition_history)
        if transitions > 0:
            last_transition = self._transition_history[-1]
            time_since = datetime.datetime.now(datetime.timezone.utc) - last_transition.timestamp
            return (
                f"Current: {self._current_phase.name}\n"
                f"Last transition: {last_transition}\n"
                f"Time in state: {time_since.total_seconds():.1f}s\n"
                f"Total transitions: {transitions}"
            )
        return f"Current: {self._current_phase.name}"