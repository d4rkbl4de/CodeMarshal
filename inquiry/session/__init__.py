"""
inquiry/session/__init__.py

CRITICAL BOUNDARY ENFORCEMENT: Session Subsystem Public Interface
=================================================================
This file defines the public surface of inquiry.session.
Nothing else.

CONSTITUTIONAL GUARD:
- Article 2: Human Primacy (session tracks human investigation)
- Article 6: Linear Investigation (history preserves sequence)
- Article 15: Session Integrity (recovery maintains continuity)

BOUNDARY RULES:
- NO computation in this file
- NO default instantiation
- NO imports from outside inquiry.session
- NO logic - only re-exports

This file exists solely to:
1. Define what other modules can import from inquiry.session
2. Prevent accidental coupling between modules
3. Enforce architectural boundaries
4. Provide clear public API documentation

VIOLATIONS ARE ARCHITECTURAL BREACHES:
- Adding computation here pollutes the boundary
- Importing non-session modules creates hidden dependencies
- Default values create unexpected side effects
"""

# -------------------------------------------------------------------
# CORE SESSION TYPES
# Immutable data structures that define investigation state
# -------------------------------------------------------------------
from .context import (
    SessionContext,
    QuestionType,
    create_context,
    create_initial_context,
    validate_context_references,
    get_context_age,
    is_context_stale,
)

from .history import (
    InvestigationHistory,
    HistoryStep,
    HistoryAction,
    HistoryStorage,
    HistoryBuilder,
    validate_history_invariants,
)

from .recovery import (
    RecoveryState,
    RecoveryStrategy,
    RecoveryIntegrity,
    inspect_session,
    resume_from_last_valid,
    resume_with_warning,
    resume_with_reduced_capability,
    select_recovery_strategy,
    RecoveryError,
    CorruptedStateError,
    CannotRecoverError,
)

# -------------------------------------------------------------------
# PUBLIC API EXPORTS
# These are the ONLY symbols available to other modules
# -------------------------------------------------------------------
__all__ = [
    # Context types and enums
    "SessionContext",
    "QuestionType",
    
    # Context factory functions
    "create_context",
    "create_initial_context",
    "validate_context_references",
    "get_context_age",
    "is_context_stale",
    
    # History types and enums
    "InvestigationHistory",
    "HistoryStep",
    "HistoryAction",
    
    # History management
    "HistoryStorage",
    "HistoryBuilder",
    "validate_history_invariants",
    
    # Recovery types and enums
    "RecoveryState",
    "RecoveryStrategy",
    "RecoveryIntegrity",
    
    # Recovery operations
    "inspect_session",
    "resume_from_last_valid",
    "resume_with_warning",
    "resume_with_reduced_capability",
    "select_recovery_strategy",
    
    # Recovery errors
    "RecoveryError",
    "CorruptedStateError",
    "CannotRecoverError",
]

# Boundary validation removed for constitutional compliance


# -------------------------------------------------------------------
# DOCUMENTATION STRINGS
# These provide guidance to developers using this module
# -------------------------------------------------------------------
__doc__ = """
SESSION SUBSYSTEM - Investigation Continuity Preserver
======================================================

PURPOSE:
Preserve the minimal state required to maintain continuity of human
investigation across time, interruptions, and system failures.

CONSTITUTIONAL RULES:
1. Session tracks WHERE the investigator is looking (context)
2. Session records HOW they got there (history)  
3. Session enables recovery WHEN interrupted (recovery)
4. Session contains NO observations, thoughts, or UI logic

KEY CONCEPTS:
- SessionContext: Immutable pointer to current focus (bookmark)
- InvestigationHistory: Append-only audit trail of steps (flight recorder)
- RecoveryState: Diagnostic assessment of session integrity (health check)

USAGE PATTERNS:

1. Starting a new investigation:
    ```python
    from inquiry.session import create_initial_context
    
    context = create_initial_context("/path/to/storage")
    history = InvestigationHistory()
    ```

2. Recording a step:
    ```python
    from inquiry.session import HistoryBuilder, HistoryAction
    
    step = HistoryBuilder.create_step(
        context=current_context,
        action=HistoryAction.OBSERVE,
        output_references=["obs_123"],
        metadata={"path": "/some/code"}
    )
    history.append_step(step)
    ```

3. Changing focus:
    ```python
    new_context = current_context.with_question_type(QuestionType.CONNECTIONS)
    ```

4. Recovering from interruption:
    ```python
    from inquiry.session import inspect_session, select_recovery_strategy
    
    state = inspect_session("/path/to/session")
    strategy = select_recovery_strategy(state)
    
    if strategy == RecoveryStrategy.CANNOT_RECOVER:
        # Start fresh
    else:
        context, history = resume_from_last_valid(state)
    ```

ARCHITECTURAL BOUNDARIES:
- MAY import from: observations.record.* (read-only), storage.*, Python stdlib
- MAY NOT import from: observations.eyes.*, inquiry.patterns.*, 
                     inquiry.notebook.*, lens.*, bridge.*
                     
This preserves the constitutional separation:
- Observations record WHAT exists
- Session records WHERE you're looking and HOW you got there
- Everything else is built on top of this foundation
"""

# -------------------------------------------------------------------
# VERSION INFORMATION
# -------------------------------------------------------------------
__version__ = "1.0.0"
__author__ = "CodeMarshal Core Team"
__license__ = "Constitutional License - See constitution.truth.md"


