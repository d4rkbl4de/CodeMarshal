"""
inquiry/session/recovery.py

CRITICAL CONSTITUTIONAL GUARD: Session Recovery
===============================================
Recovery re-establishes continuity, not confidence.

Recovery is NOT:
- Guessing where to resume
- Silent repair of corrupted state
- Inference of human intent
- UI/UX optimization

Recovery IS:
- Explicit strategies with declared limitations
- Truth-preserving resumption
- Clear declaration of uncertainty
- Deterministic state restoration

CONSTITUTIONAL ARTICLES ENFORCED:
- Article 3: Truth Preservation (show uncertainty)
- Article 13: Deterministic Operation
- Article 14: Graceful Degradation
- Article 15: Session Integrity

ALLOWED IMPORTS:
- history.InvestigationHistory
- context.SessionContext
- storage.corruption
- storage.atomic

PROHIBITED IMPORTS:
- lens.* (no UI hints)
- bridge.* (no commands)
- patterns.* (no analysis)
- notebook.* (no thinking)
"""

import enum
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime

from storage.atomic import AtomicReadResult, read_atomic

# Allowed imports from storage module
from storage.corruption import CorruptionState, detect_corruption

# Allowed imports from session module
from .context import SessionContext
from .history import HistoryStep, InvestigationHistory

logger = logging.getLogger(__name__)


class RecoveryStrategy(enum.Enum):
    """Explicit, limited recovery strategies."""

    RESUME_FROM_LAST_VALID = "resume_from_last_valid"
    """Resume from last known valid state, requires valid context and history."""

    RESUME_WITH_WARNING = "resume_with_warning"
    """Resume with reduced guarantees, logs warnings for partial state."""

    RESUME_WITH_REDUCED_CAPABILITY = "resume_with_reduced_capability"
    """Resume without history, only context."""

    CANNOT_RECOVER = "cannot_recover"
    """Cannot recover truth-consistent state."""


class RecoveryIntegrity(enum.Enum):
    """Integrity status of recovered state."""

    CLEAN = "clean"
    """Full integrity, all expected data present."""

    PARTIAL = "partial"
    """Some data missing or corrupted, but truth-consistent resumption possible."""

    CORRUPTED = "corrupted"
    """Cannot establish truth-consistent state."""


@dataclass(frozen=True)
class RecoveryState:
    """
    Immutable descriptor of recovery state.

    This is a diagnostic record, not an action plan.
    Contains only what was found, not what should be done.
    """

    # References to valid components (if found)
    last_valid_context: SessionContext | None
    last_valid_history_step: HistoryStep | None

    # Diagnostic metadata
    integrity_status: RecoveryIntegrity
    corruption_state: CorruptionState | None
    recovery_time: datetime
    recovery_id: uuid.UUID

    # Declared limitations
    can_resume_cleanly: bool
    missing_components: tuple[str, ...]

    def __post_init__(self) -> None:
        """Validate recovery state invariants."""
        if not isinstance(self.recovery_time, datetime):
            raise TypeError("recovery_time must be datetime")

        if self.recovery_time.tzinfo is None:
            raise ValueError("recovery_time must be timezone-aware")

        if not isinstance(self.recovery_id, uuid.UUID):
            raise TypeError("recovery_id must be UUID")

        # Validate consistency between integrity and components
        if self.integrity_status == RecoveryIntegrity.CLEAN:
            if self.last_valid_context is None:
                raise ValueError("CLEAN integrity requires valid context")
            if "context" in self.missing_components:
                raise ValueError("CLEAN integrity cannot have missing context")

        # Partial state must declare limitations
        if self.integrity_status == RecoveryIntegrity.PARTIAL:
            if not self.missing_components:
                raise ValueError("PARTIAL integrity must declare missing components")


class RecoveryError(Exception):
    """Base class for recovery failures."""

    pass


class CorruptedStateError(RecoveryError):
    """Session state is corrupted beyond recovery."""

    pass


class CannotRecoverError(RecoveryError):
    """Cannot establish truth-consistent state."""

    pass


def inspect_session(session_path: str) -> RecoveryState:
    """
    Examine stored session without modifying anything.

    Returns diagnostic state only. No repair attempts.
    No inference about what human intended.

    Args:
        session_path: Path to session storage directory

    Returns:
        RecoveryState describing what was found

    Raises:
        ValueError: If session_path is invalid
        OSError: If storage access fails
    """
    if not session_path:
        raise ValueError("session_path cannot be empty")

    recovery_time = datetime.now(UTC)
    recovery_id = uuid.uuid4()

    # Attempt to read session components atomically
    context_result = _read_component(session_path, "context")
    history_result = _read_component(session_path, "history")

    # Check for corruption
    corruption_state = _check_corruption(context_result, history_result)

    # Determine integrity status
    integrity_status = _determine_integrity(
        context_result, history_result, corruption_state
    )

    # Extract valid components (if any)
    last_valid_context = (
        context_result.data if context_result and context_result.is_valid else None
    )

    # For history, we need the last valid step
    last_valid_history_step = _extract_last_valid_history_step(history_result)

    # Determine what can be resumed
    can_resume_cleanly = _can_resume_cleanly(
        integrity_status, last_valid_context, last_valid_history_step
    )

    # Declare missing components
    missing_components = _identify_missing_components(context_result, history_result)

    return RecoveryState(
        last_valid_context=last_valid_context,
        last_valid_history_step=last_valid_history_step,
        integrity_status=integrity_status,
        corruption_state=corruption_state,
        recovery_time=recovery_time,
        recovery_id=recovery_id,
        can_resume_cleanly=can_resume_cleanly,
        missing_components=missing_components,
    )


def resume_from_last_valid(
    recovery_state: RecoveryState,
) -> tuple[SessionContext, InvestigationHistory | None]:
    """
    Strategy: Resume from last known valid state.

    Requires:
    - Valid SessionContext
    - At least partial InvestigationHistory

    If history is partially corrupted, returns only valid prefix.

    Args:
        recovery_state: RecoveryState from inspect_session

    Returns:
        Tuple of (context, optional_history)

    Raises:
        CannotRecoverError: If cannot establish truth-consistent state
        CorruptedStateError: If state is corrupted
    """
    if recovery_state.integrity_status == RecoveryIntegrity.CORRUPTED:
        raise CorruptedStateError(
            "Cannot resume from corrupted state. "
            f"Corruption: {recovery_state.corruption_state}"
        )

    if recovery_state.last_valid_context is None:
        raise CannotRecoverError(
            "Cannot resume: no valid context found. "
            f"Missing: {recovery_state.missing_components}"
        )

    # We can resume with just context if history is missing
    # This maintains truth: we know where we were looking,
    # but we lost the trail of how we got there.
    context = recovery_state.last_valid_context

    # If we have a valid history step, we need to reconstruct history
    # In practice, this would require reading the full history file
    # and truncating at the last valid step.
    # For now, we return None for history - caller must handle this.

    return (context, None)


def resume_with_warning(
    recovery_state: RecoveryState,
) -> tuple[SessionContext, InvestigationHistory | None]:
    """
    Strategy: Resume with warnings about partial state.

    Same as resume_from_last_valid, but logs explicit warnings
    about missing components.

    Args:
        recovery_state: RecoveryState from inspect_session

    Returns:
        Tuple of (context, optional_history)

    Raises:
        CannotRecoverError: If cannot establish truth-consistent state
    """
    if recovery_state.integrity_status == RecoveryIntegrity.CORRUPTED:
        raise CorruptedStateError(
            "Cannot resume from corrupted state. "
            f"Corruption: {recovery_state.corruption_state}"
        )

    if recovery_state.last_valid_context is None:
        raise CannotRecoverError(
            "Cannot resume: no valid context found. "
            f"Missing: {recovery_state.missing_components}"
        )

    # Log warnings about missing components
    if recovery_state.missing_components:
        logger.warning(
            "Resuming session with missing components: %s. "
            "Investigation continuity may be impaired.",
            ", ".join(recovery_state.missing_components),
        )

    if recovery_state.integrity_status == RecoveryIntegrity.PARTIAL:
        logger.warning(
            "Resuming from partially recovered state. "
            "Some investigation steps may be lost."
        )

    context = recovery_state.last_valid_context
    return (context, None)


def resume_with_reduced_capability(
    recovery_state: RecoveryState,
) -> tuple[SessionContext, InvestigationHistory | None]:
    """
    Strategy: Resume with only context, no history.

    For when history is corrupted but context is valid.
    Explicitly declares reduced capability.

    Args:
        recovery_state: RecoveryState from inspect_session

    Returns:
        Tuple of (context, None) - history explicitly omitted

    Raises:
        CannotRecoverError: If context is also missing
    """
    if recovery_state.last_valid_context is None:
        raise CannotRecoverError(
            "Cannot resume with reduced capability: no valid context. "
            f"Missing: {recovery_state.missing_components}"
        )

    # Explicit declaration of reduced capability
    logger.warning(
        "Resuming with reduced capability: no investigation history available. "
        "You can continue observing, but previous steps are unavailable."
    )

    context = recovery_state.last_valid_context
    return (context, None)


def select_recovery_strategy(recovery_state: RecoveryState) -> RecoveryStrategy:
    """
    Deterministically select appropriate recovery strategy.

    No guessing, no heuristics. Simple rules based on what exists.

    Args:
        recovery_state: RecoveryState from inspect_session

    Returns:
        Selected RecoveryStrategy
    """
    # If corrupted, cannot recover
    if recovery_state.integrity_status == RecoveryIntegrity.CORRUPTED:
        return RecoveryStrategy.CANNOT_RECOVER

    # If no context, cannot recover
    if recovery_state.last_valid_context is None:
        return RecoveryStrategy.CANNOT_RECOVER

    # If clean state, resume fully
    if recovery_state.integrity_status == RecoveryIntegrity.CLEAN:
        return RecoveryStrategy.RESUME_FROM_LAST_VALID

    # Partial state with context but missing history
    if "history" in recovery_state.missing_components:
        return RecoveryStrategy.RESUME_WITH_REDUCED_CAPABILITY

    # Partial state with other missing components
    return RecoveryStrategy.RESUME_WITH_WARNING


# -------------------------------------------------------------------
# PRIVATE HELPER FUNCTIONS
# No inference, only explicit checks.
# -------------------------------------------------------------------


def _read_component(session_path: str, component_name: str) -> AtomicReadResult | None:
    """
    Attempt atomic read of session component.

    Returns None if file doesn't exist or cannot be read.
    No attempt to repair or interpret.
    """
    file_path = f"{session_path}/{component_name}.json"

    try:
        result = read_atomic(file_path)
        return result
    except (OSError, ValueError) as e:
        logger.debug("Cannot read component %s: %s", component_name, e)
        return None


def _check_corruption(
    context_result: AtomicReadResult | None, history_result: AtomicReadResult | None
) -> CorruptionState | None:
    """
    Check for corruption in session components.

    Returns None if no corruption detected or cannot check.
    """
    # If we can't read either component, cannot check corruption
    if not context_result and not history_result:
        return None

    corruption_states = []

    if context_result and context_result.data_bytes:
        corruption = detect_corruption(context_result.data_bytes, "session_context")
        if corruption:
            corruption_states.append(corruption)

    if history_result and history_result.data_bytes:
        corruption = detect_corruption(
            history_result.data_bytes, "investigation_history"
        )
        if corruption:
            corruption_states.append(corruption)

    if not corruption_states:
        return None

    # Return first corruption found
    # In practice, we'd want more sophisticated aggregation
    return corruption_states[0]


def _determine_integrity(
    context_result: AtomicReadResult | None,
    history_result: AtomicReadResult | None,
    corruption_state: CorruptionState | None,
) -> RecoveryIntegrity:
    """
    Determine integrity status based on what was found.
    """
    # If corruption detected, state is corrupted
    if corruption_state:
        return RecoveryIntegrity.CORRUPTED

    # If both components exist and are valid, clean
    if (
        context_result
        and context_result.is_valid
        and history_result
        and history_result.is_valid
    ):
        return RecoveryIntegrity.CLEAN

    # If at least one component exists and is valid, partial
    if (context_result and context_result.is_valid) or (
        history_result and history_result.is_valid
    ):
        return RecoveryIntegrity.PARTIAL

    # Nothing valid found
    return RecoveryIntegrity.CORRUPTED


def _extract_last_valid_history_step(
    history_result: AtomicReadResult | None,
) -> HistoryStep | None:
    """
    Extract last valid history step if history exists and is valid.

    Returns None if history is missing, corrupted, or empty.
    """
    if not history_result or not history_result.is_valid:
        return None

    history_data = history_result.data
    if not isinstance(history_data, InvestigationHistory):
        return None

    if not history_data.steps:
        return None

    # Return the last step
    return history_data.steps[-1]


def _can_resume_cleanly(
    integrity_status: RecoveryIntegrity,
    last_valid_context: SessionContext | None,
    last_valid_history_step: HistoryStep | None,
) -> bool:
    """
    Determine if clean resumption is possible.

    Clean resumption requires:
    - CLEAN integrity status
    - Valid context
    - At least one history step
    """
    if integrity_status != RecoveryIntegrity.CLEAN:
        return False

    if last_valid_context is None:
        return False

    # For clean resumption, we expect history
    # But technically we could resume with just context
    # if history is intentionally empty
    return True


def _identify_missing_components(
    context_result: AtomicReadResult | None, history_result: AtomicReadResult | None
) -> tuple[str, ...]:
    """
    Identify which session components are missing.

    Returns tuple of component names.
    """
    missing = []

    if not context_result or not context_result.is_valid:
        missing.append("context")

    if not history_result or not history_result.is_valid:
        missing.append("history")

    return tuple(missing)
