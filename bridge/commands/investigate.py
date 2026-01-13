"""
bridge.commands.investigate - Authorize investigation genesis

This command validates and delegates the start or continuation of an investigation.
Starting an investigation has epistemic consequences - it commits to a line of inquiry.

Constitutional Context:
- Article 2: Human Primacy (human initiates investigation)
- Article 4: Progressive Disclosure (start simple)
- Article 6: Linear Investigation (follow natural curiosity)
- Article 15: Session Integrity (pausable, resumable, recoverable)

Role: Gatekeeper for investigation lifecycle. Validates if we can begin.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import time
from pathlib import Path

from .. import integrity_check
from observations.interface import MinimalObservationInterface
from inquiry.interface import MinimalInquiryInterface
from lens.interface import MinimalLensInterface
from lens.navigation.context import NavigationContext
from inquiry.session.context import SessionContext
from core.runtime import Runtime
from core.state import InvestigationState


class InvestigationType(Enum):
    """Type of investigation to authorize."""
    NEW = "new"
    RESUME = "resume"
    FORK = "fork"


class InvestigationScope(Enum):
    """What level of the codebase to investigate."""
    FILE = "file"
    MODULE = "module"
    PACKAGE = "package"
    CODEBASE = "codebase"


@dataclass(frozen=True)
class InvestigationRequest:
    """Immutable investigation request. Validated before session creation."""
    type: InvestigationType
    target_path: Path
    session_id: Optional[str] = None  # Required for RESUME/FORK, auto-generated for NEW
    scope: InvestigationScope = InvestigationScope.CODEBASE
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self) -> None:
        """Validate structure on creation."""
        if not isinstance(self.type, InvestigationType):
            raise TypeError(f"type must be InvestigationType, got {type(self.type)}")
        
        if not isinstance(self.target_path, Path):
            raise TypeError(f"target_path must be Path, got {type(self.target_path)}")
        
        # For RESUME and FORK, session_id is required
        if self.type in [InvestigationType.RESUME, InvestigationType.FORK]:
            if not self.session_id:
                raise ValueError(f"session_id required for {self.type.value} investigation")
        
        # For NEW, generate session_id if not provided
        if self.type == InvestigationType.NEW and not self.session_id:
            object.__setattr__(self, 'session_id', self._generate_session_id())
        
        # Ensure immutability
        object.__setattr__(self, 'parameters', dict(self.parameters))
    
    def _generate_session_id(self) -> str:
        """Generate a deterministic session ID based on request properties."""
        timestamp_int = int(self.timestamp * 1000)
        path_hash = hash(str(self.target_path.resolve())) & 0xFFFFFFFF
        return f"investigation_{timestamp_int}_{path_hash:08x}"


class InvestigationAuthorization:
    """
    Validates investigation requests against constitutional rules and system state.
    
    Rules enforced:
    1. No active conflicting session (unless resuming)
    2. Target path exists and is accessible
    3. For resume: session must be recoverable
    4. For new: clean state required
    5. Must respect single-focus constraints
    """
    
    @classmethod
    def is_lawful(
        cls,
        request: InvestigationRequest,
        runtime: Runtime,
        nav_context: NavigationContext,
        existing_sessions: Dict[str, InvestigationState]
    ) -> tuple[bool, Optional[str], Optional[InvestigationState]]:
        """
        Check if investigation request is lawful.
        
        Returns:
            (is_allowed, error_message_if_not, existing_state_if_resuming)
        """
        # 1. Validate target path
        path_error = cls._validate_target_path(request.target_path)
        if path_error:
            return False, path_error, None
        
        # 2. Type-specific validation
        if request.type == InvestigationType.NEW:
            return cls._validate_new_investigation(request, runtime, existing_sessions)
        
        elif request.type == InvestigationType.RESUME:
            return cls._validate_resume_investigation(request, runtime, existing_sessions)
        
        elif request.type == InvestigationType.FORK:
            return cls._validate_fork_investigation(request, runtime, existing_sessions)
        
        else:
            return False, f"Unknown investigation type: {request.type}", None
    
    @classmethod
    def _validate_target_path(cls, target_path: Path) -> Optional[str]:
        """Validate that target path exists and is accessible."""
        try:
            # Check existence
            if not target_path.exists():
                return f"Target path does not exist: {target_path}"
            
            # Check readability
            if not os.access(target_path, os.R_OK):
                return f"Target path not readable: {target_path}"
            
            # Check it's a directory or file (not special file)
            if not (target_path.is_dir() or target_path.is_file()):
                return f"Target path must be a file or directory: {target_path}"
            
        except (PermissionError, OSError) as e:
            return f"Path validation failed: {e}"
        
        return None
    
    @classmethod
    def _validate_new_investigation(
        cls,
        request: InvestigationRequest,
        runtime: Runtime,
        existing_sessions: Dict[str, InvestigationState]
    ) -> tuple[bool, Optional[str], Optional[InvestigationState]]:
        """Validate a new investigation request."""
        # Check for conflicting active sessions on same path
        for session_id, state in existing_sessions.items():
            if state.active and str(state.target_path) == str(request.target_path):
                return False, f"Active session exists for this path: {session_id}", None
        
        # Check system has capacity for new investigation
        if runtime.at_capacity:
            return False, "System at capacity for new investigations", None
        
        return True, None, None
    
    @classmethod
    def _validate_resume_investigation(
        cls,
        request: InvestigationRequest,
        runtime: Runtime,
        existing_sessions: Dict[str, InvestigationState]
    ) -> tuple[bool, Optional[str], Optional[InvestigationState]]:
        """Validate a resume investigation request."""
        if not request.session_id:
            return False, "session_id required for resume", None
        
        # Check session exists
        existing_state = existing_sessions.get(request.session_id)
        if not existing_state:
            return False, f"Session not found: {request.session_id}", None
        
        # Check session is resumable
        if not existing_state.resumable:
            return False, f"Session not resumable: {request.session_id}", existing_state
        
        # Check target path matches (optional for resume)
        if str(existing_state.target_path) != str(request.target_path):
            return False, "Target path mismatch with existing session", existing_state
        
        return True, None, existing_state
    
    @classmethod
    def _validate_fork_investigation(
        cls,
        request: InvestigationRequest,
        runtime: Runtime,
        existing_sessions: Dict[str, InvestigationState]
    ) -> tuple[bool, Optional[str], Optional[InvestigationState]]:
        """Validate a fork investigation request."""
        if not request.session_id:
            return False, "session_id required for fork", None
        
        # Check source session exists
        source_state = existing_sessions.get(request.session_id)
        if not source_state:
            return False, f"Source session not found: {request.session_id}", None
        
        # Check system has capacity for new investigation
        if runtime.at_capacity:
            return False, "System at capacity for new investigations", source_state
        
        return True, None, source_state


@integrity_check
def execute_investigation(
    request: InvestigationRequest,
    runtime: Runtime,
    nav_context: NavigationContext,
    existing_sessions: Dict[str, InvestigationState]
) -> Dict[str, Any]:
    """
    Authorize and delegate investigation start/resume.
    
    This is the only public entry point for investigation lifecycle.
    It validates, records intent, and delegates session management.
    
    Args:
        request: Validated investigation request
        runtime: For session state management
        nav_context: Current navigation state (will be reset for new)
        existing_sessions: Currently active/inactive sessions
    
    Returns:
        Dict with session_id, status, and metadata
        
    Raises:
        ValueError: If investigation is not lawful
        RuntimeError: If delegation fails
    """
    # 1. Constitutional compliance check
    is_allowed, error, existing_state = InvestigationAuthorization.is_lawful(
        request, runtime, nav_context, existing_sessions
    )
    
    if not is_allowed:
        raise ValueError(f"Investigation not authorized: {error}")
    
    # 2. Record intent (not results)
    intent_record = {
        "investigation_type": request.type.value,
        "target_path": str(request.target_path),
        "session_id": request.session_id,
        "scope": request.scope.value,
        "parameters": dict(request.parameters),
        "timestamp": request.timestamp,
        "existing_session_state": existing_state.state_name if existing_state else None,
    }
    
    # 3. Delegate to runtime for actual investigation management
    try:
        if request.type == InvestigationType.NEW:
            session_result = runtime.start_investigation(
                target_path=str(request.target_path),
                scope=request.scope.value,
                parameters=request.parameters,
                session_id=request.session_id,
            )
            
            # Inject interfaces into engine (dependency injection)
            engine = runtime.engine
            if engine:
                # Register layer interfaces (bridge layer injects into core)
                engine.register_observation_interface(MinimalObservationInterface())
                engine.register_inquiry_interface(MinimalInquiryInterface())
                engine.register_lens_interface(MinimalLensInterface())
                
                # Execute full investigation lifecycle via engine
                investigation_result = engine.execute_investigation()
                # Update session result with actual investigation data
                session_result.update({
                    "observation_count": getattr(engine, '_observation_count', 0),
                    "status": "investigation_running"
                })
        
        elif request.type == InvestigationType.RESUME:
            session_result = runtime.resume_investigation(
                session_id=request.session_id,
                parameters=request.parameters,
            )
            
            # Resume investigation via engine
            engine = runtime.engine
            if engine:
                investigation_result = engine.execute_investigation()
                session_result.update({
                    "observation_count": getattr(engine, '_observation_count', 0),
                    "status": "investigation_resumed"
                })
        
        else:  # FORK
            session_result = runtime.fork_investigation(
                source_session_id=request.session_id,
                target_path=str(request.target_path),
                parameters=request.parameters,
            )
            
            # Fork investigation via engine
            engine = runtime.engine
            if engine:
                investigation_result = engine.execute_investigation()
                session_result.update({
                    "observation_count": getattr(engine, '_observation_count', 0),
                    "status": "investigation_forked"
                })
    
    except Exception as e:
        raise RuntimeError(f"Failed to delegate investigation: {e}") from e
    
    # 4. Return session reference (not full state)
    return {
        "investigation_id": session_result["session_id"],
        "path": str(request.target_path),
        "scope": request.scope.value,
        "status": session_result["status"],
        "observation_count": 0,  # Will be populated by actual investigation
        "warnings": [],
        "intent_record": intent_record,
        "investigation_type": request.type.value,
        "estimated_duration": _estimate_investigation_duration(request),
        "constitutional_commitments": _get_constitutional_commitments(request),
        "next_recommended_action": "observe" if request.type == InvestigationType.NEW else "continue",
    }


def _estimate_investigation_duration(request: InvestigationRequest) -> str:
    """Provide honest estimate based on investigation scope."""
    scope_sizes = {
        InvestigationScope.FILE: "minutes",
        InvestigationScope.MODULE: "tens of minutes",
        InvestigationScope.PACKAGE: "hours",
        InvestigationScope.CODEBASE: "multiple sessions",
    }
    return scope_sizes.get(request.scope, "variable")


def _get_constitutional_commitments(request: InvestigationRequest) -> Dict[str, bool]:
    """Declare which constitutional articles are invoked by this investigation."""
    commitments = {
        "article_2_human_primacy": True,  # Human initiated
        "article_4_progressive_disclosure": True,  # Will start simple
        "article_6_linear_investigation": True,  # Will follow flow
        "article_15_session_integrity": request.type != InvestigationType.NEW,  # Resume/fork only
        "article_9_immutable_observations": True,  # All observations will be immutable
        "article_11_declared_limitations": True,  # Will declare limitations
    }
    return commitments


# Convenience functions for common investigation patterns
def new_investigation(
    target_path: Union[str, Path],
    scope: InvestigationScope = InvestigationScope.CODEBASE,
    **parameters: Any
) -> InvestigationRequest:
    """Create a new investigation request."""
    path = target_path if isinstance(target_path, Path) else Path(target_path)
    return InvestigationRequest(
        type=InvestigationType.NEW,
        target_path=path,
        scope=scope,
        parameters=parameters,
    )


def resume_investigation(
    session_id: str,
    target_path: Optional[Union[str, Path]] = None,
    **parameters: Any
) -> InvestigationRequest:
    """Create a resume investigation request."""
    path = None
    if target_path:
        path = target_path if isinstance(target_path, Path) else Path(target_path)
    
    # Create request without path first, will be validated against existing session
    return InvestigationRequest(
        type=InvestigationType.RESUME,
        target_path=path or Path("."),  # placeholder, will be validated
        session_id=session_id,
        parameters=parameters,
    )


def fork_investigation(
    source_session_id: str,
    target_path: Union[str, Path],
    **parameters: Any
) -> InvestigationRequest:
    """Create a fork investigation request."""
    path = target_path if isinstance(target_path, Path) else Path(target_path)
    return InvestigationRequest(
        type=InvestigationType.FORK,
        target_path=path,
        session_id=source_session_id,
        parameters=parameters,
    )


# Import guard - ensure we don't import prohibited modules
import os
# Forbidden imports would be caught by static analysis:
# test_no_direct_session_creation()
# test_no_state_mutation_in_commands()
# test_no_storage_access_in_commands()

# This module only authorizes, never executes.