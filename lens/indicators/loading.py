"""
loading.py — Time Without Illusion

Defines how ongoing work is signaled without implying speed, progress, or success.

Strict Rules:
- No progress percentages
- No completion estimates  
- No animated implication of momentum
- Only semantic intent: "Something is happening", "Nothing is happening", "We are stuck"
"""

from enum import Enum, auto
from typing import Optional, ClassVar, Dict, Any, Callable
from dataclasses import dataclass, field
import time
from datetime import datetime, timezone

# Import from allowed modules only
from lens.aesthetic.palette import SemanticColor as Color
from lens.aesthetic.typography import Glyph
from lens.philosophy.clarity import RequirementLevel


class LoadingState(Enum):
    """
    Finite set of loading states.
    
    Each state represents a semantic condition, not progress or prediction.
    States are mutually exclusive and collectively exhaustive.
    """
    IDLE = auto()               # System is ready, nothing happening
    WORKING = auto()            # System is actively processing
    BLOCKED = auto()            # System is stuck (non-recoverable waiting)
    WAITING_ON_INPUT = auto()   # System paused for human input
    
    # --- String representations (for logging/export only) ---
    def __str__(self) -> str:
        return {
            LoadingState.IDLE: "ready",
            LoadingState.WORKING: "working",
            LoadingState.BLOCKED: "blocked",
            LoadingState.WAITING_ON_INPUT: "waiting for input",
        }[self]
    
    @property
    def description(self) -> str:
        """Human-readable description of the semantic state."""
        return {
            LoadingState.IDLE: "System is idle",
            LoadingState.WORKING: "System is working",
            LoadingState.BLOCKED: "System is blocked",
            LoadingState.WAITING_ON_INPUT: "Waiting for user input",
        }[self]


@dataclass(frozen=True)
class LoadingIndicator:
    """
    Immutable representation of a loading indicator.
    
    Frozen to prevent mutation during display. A new indicator must be created
    for state changes.
    """
    
    # --- Core State (Required) ---
    state: LoadingState
    
    # --- Optional Context (Not for Progress) ---
    context: Optional[str] = None
    """Optional context about what is being worked on, NOT progress."""
    
    start_time: Optional[float] = None
    """When this state began. For duration calculation only, never for ETA."""
    
    # --- Display Properties (via aesthetic module) ---
    display_color: Color = field(init=False)
    display_glyph: Glyph = field(init=False)
    
    # --- State-to-Display Mapping ---
    # Defined as class variables to ensure consistency
    _COLOR_MAP: ClassVar[Dict[LoadingState, Color]] = {
        LoadingState.IDLE: Color.NEUTRAL,
        LoadingState.WORKING: Color.ACTIVE,
        LoadingState.BLOCKED: Color.WARNING,
        LoadingState.WAITING_ON_INPUT: Color.ATTENTION,
    }
    
    _GLYPH_MAP: ClassVar[Dict[LoadingState, Glyph]] = {
        LoadingState.IDLE: Glyph.CHECK,
        LoadingState.WORKING: Glyph.SPINNER,
        LoadingState.BLOCKED: Glyph.WARNING,
        LoadingState.WAITING_ON_INPUT: Glyph.PAUSE,
    }
    
    def __post_init__(self) -> None:
        """Set display properties based on state after initialization."""
        # Use object.__setattr__ for frozen dataclass
        object.__setattr__(self, 'display_color', self._COLOR_MAP[self.state])
        object.__setattr__(self, 'display_glyph', self._GLYPH_MAP[self.state])
    
    # --- Properties (No Progress Calculations) ---
    
    @property
    def has_elapsed_time(self) -> bool:
        """Whether we can calculate elapsed time (truthful, not predictive)."""
        return self.start_time is not None
    
    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Current elapsed time in seconds. Never used for prediction."""
        if self.start_time is None:
            return None
        return time.time() - self.start_time
    
    @property
    def requires_action(self) -> RequirementLevel:
        """What level of human attention is required by this state."""
        mapping = {
            LoadingState.IDLE: RequirementLevel.NONE,
            LoadingState.WORKING: RequirementLevel.INFORMATIONAL,
            LoadingState.BLOCKED: RequirementLevel.ATTENTION,
            LoadingState.WAITING_ON_INPUT: RequirementLevel.ACTION,
        }
        return mapping[self.state]
    
    # --- Factory Methods ---
    
    @classmethod
    def create_idle(cls, context: Optional[str] = None) -> 'LoadingIndicator':
        """Create an idle indicator."""
        return cls(state=LoadingState.IDLE, context=context)
    
    @classmethod
    def create_working(
        cls, 
        context: Optional[str] = None,
        with_timer: bool = False
    ) -> 'LoadingIndicator':
        """Create a working indicator."""
        start_time = time.time() if with_timer else None
        return cls(
            state=LoadingState.WORKING, 
            context=context,
            start_time=start_time
        )
    
    @classmethod
    def create_blocked(
        cls, 
        context: Optional[str] = None,
        with_timer: bool = True  # Blocked states should always track time
    ) -> 'LoadingIndicator':
        """Create a blocked indicator."""
        start_time = time.time() if with_timer else None
        return cls(
            state=LoadingState.BLOCKED,
            context=context,
            start_time=start_time
        )
    
    @classmethod
    def create_waiting_for_input(
        cls, 
        context: Optional[str] = None
    ) -> 'LoadingIndicator':
        """Create a waiting-for-input indicator."""
        return cls(
            state=LoadingState.WAITING_ON_INPUT,
            context=context
        )
    
    # --- Serialization ---
    
    def to_dict(self) -> Dict[str, Any]:
        """Export state for logging or persistence."""
        return {
            'state': self.state.name,
            'state_description': self.description,
            'context': self.context,
            'start_time': self.start_time,
            'elapsed_seconds': self.elapsed_seconds,
            'requires_action': self.requires_action.name,
            'display_color': self.display_color.name,
            'display_glyph': self.display_glyph.name,
        }


# --- Validation Functions ---

def validate_no_progress_implication(indicator: LoadingIndicator) -> bool:
    """
    Ensure indicator doesn't imply progress, speed, or success.
    
    Returns True if indicator complies with truth-preserving rules.
    """
    # Rule: No progress percentages
    # (Implicitly enforced by data structure - no percentage field)
    
    # Rule: No completion estimates
    # (Implicitly enforced by data structure - no completion field)
    
    # Rule: No optimistic language in context
    if indicator.context:
        forbidden_terms = [
            'almost', 'nearly', 'soon', 'shortly',
            'quick', 'fast', 'speedy', 'brief',
            'progress', 'complete', 'finish', 'done'
        ]
        context_lower = indicator.context.lower()
        if any(term in context_lower for term in forbidden_terms):
            return False
    
    # Rule: Blocked states must have timers
    if indicator.state == LoadingState.BLOCKED and not indicator.has_elapsed_time:
        return False
    
    return True


def should_interrupt_for_attention(indicator: LoadingIndicator) -> bool:
    """
    Determine if this loading state requires interrupting the user.
    
    Used by the interface to decide when to break user flow.
    """
    return indicator.requires_action in [
        RequirementLevel.ATTENTION,
        RequirementLevel.ACTION,
        RequirementLevel.CRITICAL
    ]


# --- Performance Monitoring ---

@dataclass(frozen=True)
class PerformanceMonitor:
    """
    Tracks computation time for operations without making predictions.
    
    Provides honest timing information for Article 8 compliance.
    """
    
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    
    @property
    def is_complete(self) -> bool:
        """Whether operation has finished."""
        return self.end_time is not None
    
    @property
    def elapsed_seconds(self) -> Optional[float]:
        """Current elapsed time if running, total time if complete."""
        current_time = self.end_time if self.end_time is not None else time.time()
        return current_time - self.start_time
    
    @property
    def human_readable_duration(self) -> str:
        """Human-readable duration without optimistic language."""
        if not self.is_complete:
            return f"Running for {self._format_duration(self.elapsed_seconds)}"
        return f"Completed in {self._format_duration(self.elapsed_seconds)}"
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable terms."""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        elif seconds < 60:
            return f"{seconds:.1f}s"
        else:
            minutes = int(seconds // 60)
            remaining = seconds % 60
            return f"{minutes}m {remaining:.0f}s"
    
    def complete(self) -> 'PerformanceMonitor':
        """Mark operation as complete."""
        if self.end_time is not None:
            raise ValueError("Operation already completed")
        return PerformanceMonitor(
            operation_name=self.operation_name,
            start_time=self.start_time,
            end_time=time.time()
        )


def monitor_performance(operation_name: str) -> Callable:
    """
    Decorator to monitor performance of functions.
    
    Usage:
        @monitor_performance("file_observation")
        def observe_files(path):
            # ... observation logic
            return result
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            monitor = PerformanceMonitor(operation_name=operation_name, start_time=time.time())
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor = monitor.complete()
                # Log performance honestly
                print(f"[PERFORMANCE] {operation_name}: {monitor.human_readable_duration}")
        return wrapper
    return decorator


# --- Global Defaults ---

DEFAULT_INDICATOR = LoadingIndicator.create_idle()
"""Default indicator when system is first initialized."""

STATE_TRANSITIONS = {
    # From state -> allowed next states
    LoadingState.IDLE: {LoadingState.WORKING, LoadingState.WAITING_ON_INPUT},
    LoadingState.WORKING: {LoadingState.IDLE, LoadingState.BLOCKED},
    LoadingState.BLOCKED: {LoadingState.WORKING, LoadingState.IDLE},
    LoadingState.WAITING_ON_INPUT: {LoadingState.WORKING, LoadingState.IDLE},
}
"""Allowed state transitions to prevent nonsensical sequences."""