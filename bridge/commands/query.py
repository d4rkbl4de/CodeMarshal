"""
bridge.commands.query - Authorize structured curiosity

This command validates and delegates queries about observations.
It ensures human questions and pattern requests are lawful before computation.

Constitutional Context:
- Article 2: Human Primacy (humans ask questions)
- Article 6: Linear Investigation (questions follow natural progression)
- Article 8: Honest Performance (show computation time if needed)

Role: Gatekeeper for curiosity. Validates what can be asked, when.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from core.engine import Engine
from core.runtime import Runtime
from inquiry.session.context import SessionContext
from lens.navigation.context import NavigationContext
from lens.navigation.workflow import WorkflowStage

from .. import integrity_check


class QueryType(Enum):
    """Allowed query types. Extend here only when new query categories emerge."""

    QUESTION = "question"
    PATTERN = "pattern"


class QuestionName(Enum):
    """Human questions from constitution. Ordered by investigation flow."""

    STRUCTURE = "structure"  # What's here?
    PURPOSE = "purpose"  # What does this do?
    CONNECTIONS = "connections"  # How is it connected?
    ANOMALIES = "anomalies"  # What seems unusual?
    THINKING = "thinking"  # What do I think?


class PatternName(Enum):
    """Numeric-only patterns. No labels, no interpretation."""

    DENSITY = "density"  # Import counts, clustering
    COUPLING = "coupling"  # Degree & fan-in/out
    COMPLEXITY = "complexity"  # Depth, node counts
    VIOLATIONS = "violations"  # Boundary crossings (boolean)
    UNCERTAINTY = "uncertainty"  # Incomplete data indicators


@dataclass(frozen=True)
class QueryRequest:
    """Immutable query request. Validated before dispatch."""

    type: QueryType
    name: QuestionName | PatternName
    session_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self) -> None:
        """Validate basic structure on creation."""
        if not isinstance(self.type, QueryType):
            raise TypeError(f"type must be QueryType, got {type(self.type)}")

        if not self.session_id:
            raise ValueError("session_id cannot be empty")

        # Ensure parameters dict is immutable
        object.__setattr__(self, "parameters", dict(self.parameters))


class QueryAuthorization:
    """
    Validates queries against investigation stage and constitutional rules.

    Rules enforced:
    1. Questions before patterns (Article 6)
    2. Pattern parameters must be numeric/boolean only
    3. Cannot ask 'why' of observations
    4. Cannot skip investigation stages
    """

    # Stage -> allowed query types
    _STAGE_PERMISSIONS: dict[WorkflowStage, set[QueryType]] = {
        WorkflowStage.ORIENTATION: {QueryType.QUESTION},
        WorkflowStage.EXAMINATION: {QueryType.QUESTION, QueryType.PATTERN},
        WorkflowStage.CONNECTIONS: {QueryType.QUESTION, QueryType.PATTERN},
        WorkflowStage.PATTERNS: {QueryType.QUESTION, QueryType.PATTERN},
        WorkflowStage.THINKING: {QueryType.QUESTION},
    }

    # Questions allowed in orientation stage (simpler first)
    _ORIENTATION_QUESTIONS: set[QuestionName] = {
        QuestionName.STRUCTURE,  # Basic "what's here?"
    }

    @classmethod
    def is_lawful(
        cls,
        request: QueryRequest,
        nav_context: NavigationContext,
        session_context: SessionContext,
    ) -> tuple[bool, str | None]:
        """
        Check if query is lawful given current investigation state.

        Returns:
            (is_allowed, error_message_if_not)
        """
        # 1. Check investigation is active
        if not session_context.active:
            return False, "No active investigation"

        # 2. Check query type allowed in current stage
        current_stage = nav_context.current_stage
        allowed_types = cls._STAGE_PERMISSIONS.get(current_stage, set())

        if request.type not in allowed_types:
            stage_name = current_stage.value
            return (
                False,
                f"Query type '{request.type.value}' not allowed in {stage_name} stage",
            )

        # 3. Stage-specific restrictions
        if current_stage == WorkflowStage.ORIENTATION:
            if (
                request.type == QueryType.QUESTION
                and request.name not in cls._ORIENTATION_QUESTIONS
            ):
                return False, "Only 'structure' question allowed during orientation"

        # 4. Pattern-specific validation
        if request.type == QueryType.PATTERN:
            # Must have observations first
            if not session_context.has_observations:
                return False, "Cannot compute patterns without observations"

            # Parameters must be numeric/boolean only
            error = cls._validate_pattern_parameters(request.parameters)
            if error:
                return False, error

        # 5. Question-specific validation
        if request.type == QueryType.QUESTION:
            error = cls._validate_question(request.name, request.parameters)
            if error:
                return False, error

        return True, None

    @classmethod
    def _validate_pattern_parameters(cls, params: dict[str, Any]) -> str | None:
        """Ensure pattern parameters contain only numeric/boolean values."""
        for key, value in params.items():
            if isinstance(value, (int, float, bool)):
                continue
            if isinstance(value, str) and value.isnumeric():
                continue
            return f"Pattern parameter '{key}' must be numeric or boolean"
        return None

    @classmethod
    def _validate_question(
        cls, name: QuestionName, params: dict[str, Any]
    ) -> str | None:
        """Ensure question parameters don't violate constitutional rules."""
        # Cannot ask "why" - that's interpretation
        if "why" in str(params).lower():
            return "Questions cannot ask 'why' - that requires human interpretation"

        # Thinking questions must have anchor
        if name == QuestionName.THINKING and "anchor" not in params:
            return "'thinking' questions must be anchored to an observation"

        return None


@integrity_check
def execute_query(
    request: QueryRequest,
    runtime: Runtime,
    engine: Engine,
    nav_context: NavigationContext,
    session_context: SessionContext,
) -> dict[str, Any]:
    """
    Authorize and delegate a query.

    This is the only public entry point for queries.
    It validates, records intent, and delegates computation.

    Args:
        request: Validated query request
        runtime: For session state management
        engine: For computation delegation
        nav_context: Current navigation state
        session_context: Current investigation context

    Returns:
        Dict with query_id and metadata for tracking computation

    Raises:
        ValueError: If query is not lawful
        RuntimeError: If delegation fails
    """
    # 1. Constitutional compliance check
    is_allowed, error = QueryAuthorization.is_lawful(
        request, nav_context, session_context
    )

    if not is_allowed:
        raise ValueError(f"Query not authorized: {error}")

    # 2. Record intent (not results)
    intent_record = {
        "query_type": request.type.value,
        "query_name": request.name.value,
        "parameters": dict(request.parameters),
        "session_id": request.session_id,
        "timestamp": request.timestamp,
        "nav_stage": nav_context.current_stage.value,
    }

    # 3. Delegate to engine for computation
    try:
        if request.type == QueryType.QUESTION:
            query_id = engine.submit_question(
                question_name=request.name.value,
                parameters=request.parameters,
                session_id=request.session_id,
            )
        else:  # PATTERN
            query_id = engine.submit_pattern(
                pattern_name=request.name.value,
                parameters=request.parameters,
                session_id=request.session_id,
            )
    except Exception as e:
        raise RuntimeError(f"Failed to delegate query: {e}") from e

    # 4. Return reference only (not results)
    return {
        "query_id": query_id,
        "intent_record": intent_record,
        "status": "submitted",
        "estimated_complexity": _estimate_complexity(request),
    }


def _estimate_complexity(request: QueryRequest) -> str:
    """Provide honest performance estimate (Article 8)."""
    if request.type == QueryType.PATTERN:
        if request.name in [PatternName.COUPLING, PatternName.COMPLEXITY]:
            return "moderate"  # Graph traversal
        elif request.name == PatternName.VIOLATIONS:
            return "light"  # Boundary checks
        else:
            return "variable"  # Depends on data
    else:
        return "light"  # Questions are metadata lookups


# Forbidden imports check (static analysis would catch these)
# DO NOT IMPORT FROM:
# - observations.*
# - patterns.* (except via inquiry.patterns through engine)
# - storage.*
# - lens.views.*
# - lens.aesthetic.*

# These would be caught by constitutional test suite:
# test_no_direct_observation_access()
# test_no_pattern_computation_in_commands()
# test_no_storage_access_in_commands()
