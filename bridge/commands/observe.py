"""
bridge.commands.observe - Authorize observation collection

This command validates and delegates observation collection.
It creates immutable truth, making it the most sensitive command in the system.

Constitutional Context:
- Article 1: Observation Purity (only textually present)
- Article 3: Truth Preservation (never obscure or invent)
- Article 9: Immutable Observations (once recorded, never changed)
- Article 11: Declared Limitations (explicit blind spots)

Role: Gatekeeper for truth creation. Validates what can be seen, when.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Set, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
import time
from pathlib import Path

from .. import integrity_check
from lens.navigation.workflow import WorkflowStage
from lens.navigation.context import NavigationContext
from inquiry.session.context import SessionContext
from core.runtime import Runtime
from core.engine import Engine


class ObservationType(Enum):
    """Allowed ways of seeing. Extends only when new pure readers exist."""
    FILE_SIGHT = "file_sight"           # Files, directories, paths
    IMPORT_SIGHT = "import_sight"       # Static import statements
    EXPORT_SIGHT = "export_sight"       # Definitions, signatures
    BOUNDARY_SIGHT = "boundary_sight"   # Module boundaries
    ENCODING_SIGHT = "encoding_sight"   # File encoding & type detection


@dataclass(frozen=True)
class ObservationRequest:
    """Immutable observation request. Validated before truth creation."""
    types: Set[ObservationType]
    target_path: Path
    session_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self) -> None:
        """Validate structure on creation."""
        if not self.types:
            raise ValueError("types cannot be empty")
        
        for obs_type in self.types:
            if not isinstance(obs_type, ObservationType):
                raise TypeError(f"type must be ObservationType, got {type(obs_type)}")
        
        if not isinstance(self.target_path, Path):
            raise TypeError(f"target_path must be Path, got {type(self.target_path)}")
        
        if not self.target_path.exists():
            raise ValueError(f"target_path does not exist: {self.target_path}")
        
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        
        # Ensure immutability
        object.__setattr__(self, 'types', frozenset(self.types))
        object.__setattr__(self, 'parameters', dict(self.parameters))


class ObservationAuthorization:
    """
    Validates observation requests against constitutional rules and limitations.
    
    Rules enforced:
    1. Only allowed observation types (pure readers)
    2. Target path must be within allowed boundaries
    3. Must respect declared limitations of each observation type
    4. Cannot observe during prohibited stages
    5. Must acknowledge truth-preserving constraints
    """
    
    # Types that require special validation
    _SPECIALIZED_TYPES = {
        ObservationType.FILE_SIGHT: ["symlink_validation", "size_limits"],
        ObservationType.IMPORT_SIGHT: ["no_inference", "static_only"],
        ObservationType.EXPORT_SIGHT: ["signatures_only", "no_semantics"],
        ObservationType.BOUNDARY_SIGHT: ["structural_only", "no_intent"],
        ObservationType.ENCODING_SIGHT: ["binary_detection", "encoding_only"],
    }
    
    @classmethod
    def is_lawful(
        cls,
        request: ObservationRequest,
        nav_context: NavigationContext,
        session_context: SessionContext
    ) -> tuple[bool, Optional[str], Optional[Dict[str, List[str]]]]:
        """
        Check if observation request is lawful.
        
        Returns:
            (is_allowed, error_message_if_not, declared_limitations)
            
        declared_limitations maps observation_type -> list of limitations
        """
        # 1. Check investigation is active
        if not session_context.active:
            return False, "No active investigation", None
        
        # 2. Check current stage allows observation
        current_stage = nav_context.current_stage
        if current_stage != WorkflowStage.ORIENTATION:
            stage_name = current_stage.value
            return False, f"Observation only allowed in ORIENTATION stage, not {stage_name}", None
        
        # 3. Check target path is valid (no traversal attacks)
        path_error = cls._validate_target_path(request.target_path, session_context)
        if path_error:
            return False, path_error, None
        
        # 4. Collect declared limitations
        limitations = cls._collect_limitations(request.types)
        
        # 5. Check single-focus constraint
        if session_context.has_observations and not request.parameters.get("additional_view", False):
            return False, "Single-focus violation: must complete current observation first", limitations
        
        # 6. Check for overlapping/contradictory types
        conflict_error = cls._check_type_conflicts(request.types)
        if conflict_error:
            return False, conflict_error, limitations
        
        return True, None, limitations
    
    @classmethod
    def _validate_target_path(
        cls, 
        target_path: Path, 
        session_context: SessionContext
    ) -> Optional[str]:
        """Validate target path against filesystem and session constraints."""
        try:
            # Check for symlink traversal (input_validation role)
            if target_path.is_symlink():
                return "Symlink observation requires explicit symlink_validation parameter"
            
            # Check size limits
            if target_path.is_file():
                file_size = target_path.stat().st_size
                if file_size > session_context.max_file_size:
                    return f"File size {file_size} exceeds limit {session_context.max_file_size}"
            elif target_path.is_dir():
                # Directory size checking deferred to actual observation
                pass
            
            # Ensure path is within session boundaries
            if not session_context.is_path_accessible(target_path):
                return f"Path outside session boundaries: {target_path}"
            
        except (PermissionError, OSError) as e:
            return f"Path validation failed: {e}"
        
        return None
    
    @classmethod
    def _collect_limitations(
        cls, 
        types: Set[ObservationType]
    ) -> Dict[str, List[str]]:
        """Collect all declared limitations for the requested observation types."""
        limitations: Dict[str, List[str]] = {}
        
        # Common limitations that apply to all observations
        common_limitations = [
            "no_inference",
            "textual_only", 
            "immutable_once_recorded",
            "cannot_see_runtime_behavior",
            "cannot_see_dynamic_imports",
            "cannot_see_comments_as_code",
        ]
        
        for obs_type in types:
            type_name = obs_type.value
            limitations[type_name] = common_limitations.copy()
            
            # Add type-specific limitations
            if obs_type in cls._SPECIALIZED_TYPES:
                limitations[type_name].extend(cls._SPECIALIZED_TYPES[obs_type])
        
        return limitations
    
    @classmethod
    def _check_type_conflicts(
        cls, 
        types: Set[ObservationType]
    ) -> Optional[str]:
        """Check for contradictory observation requests."""
        type_set = set(types)
        
        # Import and export sight might conflict on certain file types
        if (ObservationType.IMPORT_SIGHT in type_set and 
            ObservationType.EXPORT_SIGHT in type_set):
            # This is actually valid, but we need to ensure they're processed separately
            # No conflict, just note they'll be sequential
            pass
        
        # Encoding sight with other types requires careful ordering
        if ObservationType.ENCODING_SIGHT in type_set and len(type_set) > 1:
            return "ENCODING_SIGHT must be requested alone or processed first"
        
        return None


@integrity_check
def execute_observation(
    request: ObservationRequest,
    runtime: Runtime,
    engine: Engine,
    nav_context: NavigationContext,
    session_context: SessionContext
) -> Dict[str, Any]:
    """
    Authorize and delegate observation collection.
    
    This is the only public entry point for creating observations.
    It validates, records intent, and delegates truth creation.
    
    Args:
        request: Validated observation request
        runtime: For session state management
        engine: For observation delegation
        nav_context: Current navigation state
        session_context: Current investigation context
    
    Returns:
        Dict with observation_id, limitations, and metadata
        
    Raises:
        ValueError: If observation is not lawful
        RuntimeError: If delegation fails
    """
    # 1. Constitutional compliance check
    is_allowed, error, limitations = ObservationAuthorization.is_lawful(
        request, nav_context, session_context
    )
    
    if not is_allowed:
        raise ValueError(f"Observation not authorized: {error}")
    
    # 2. Acknowledge limitations (Article 11)
    limitations_acknowledged = _acknowledge_limitations(limitations)
    if not limitations_acknowledged:
        raise ValueError("Observation limitations must be explicitly acknowledged")
    
    # 3. Record intent (not results)
    intent_record = {
        "observation_types": [t.value for t in request.types],
        "target_path": str(request.target_path),
        "session_id": request.session_id,
        "parameters": dict(request.parameters),
        "timestamp": request.timestamp,
        "limitations_acknowledged": limitations_acknowledged,
        "nav_stage": nav_context.current_stage.value,
    }
    
    # 4. Delegate to engine for actual observation collection
    try:
        # Convert set to list for serialization
        type_list = [t.value for t in request.types]
        
        observation_id = engine.submit_observation(
            observation_types=type_list,
            target_path=str(request.target_path),
            parameters=request.parameters,
            session_id=request.session_id,
            limitations=limitations,
        )
    except Exception as e:
        raise RuntimeError(f"Failed to delegate observation: {e}") from e
    
    # 5. Return reference only (not observations)
    return {
        "success": True,
        "observation_id": observation_id,
        "intent_record": intent_record,
        "status": "collecting",
        "limitations": limitations,
        "estimated_time": _estimate_observation_time(request),
        "truth_preservation_guarantee": True,
    }


def _acknowledge_limitations(limitations: Optional[Dict[str, List[str]]]) -> bool:
    """
    Simulate limitation acknowledgment.
    
    In practice, this would:
    1. Display limitations to user
    2. Require explicit acknowledgment
    3. Record the acknowledgment
    
    For now, returns True if limitations exist (acknowledged by checking).
    """
    if not limitations:
        return False
    
    # In real implementation:
    # 1. Show each limitation category with type-specific limitations
    # 2. Require user to check "I understand these limitations"
    # 3. Record acknowledgment with timestamp and user context
    
    # For command line, we might print them and require --acknowledge-limitations flag
    # For TUI, we'd show a modal with acknowledgment required
    
    return True  # Placeholder - assumes limitations were displayed and acknowledged


def _estimate_observation_time(request: ObservationRequest) -> str:
    """Provide honest performance estimate based on observation types."""
    # Simple heuristics - would be refined based on actual performance data
    type_count = len(request.types)
    
    if type_count == 1:
        return "fast"
    elif type_count <= 3:
        return "moderate"
    else:
        return "slow"  # Multiple observations should be sequential, not parallel


def _create_single_observation_request(
    obs_type: ObservationType,
    target_path: Path,
    session_id: str,
    **parameters: Any
) -> ObservationRequest:
    """Helper for creating single-type observation requests."""
    return ObservationRequest(
        types={obs_type},
        target_path=target_path,
        session_id=session_id,
        parameters=parameters,
    )


# Convenience functions for common observation patterns
def observe_file_structure(
    target_path: Path,
    session_id: str,
    include_hidden: bool = False
) -> ObservationRequest:
    """Request to see file and directory structure."""
    return _create_single_observation_request(
        ObservationType.FILE_SIGHT,
        target_path,
        session_id,
        include_hidden=include_hidden,
        recursive=True,
    )


def observe_imports(
    target_path: Path,
    session_id: str,
    follow_imports: bool = False
) -> ObservationRequest:
    """Request to see import statements."""
    return _create_single_observation_request(
        ObservationType.IMPORT_SIGHT,
        target_path,
        session_id,
        follow_imports=follow_imports,
        static_only=True,
    )


# Forbidden imports check (static analysis would catch these)
# DO NOT IMPORT FROM:
# - observations.*
# - storage.*
# - lens.views.*
# - lens.aesthetic.*
# - patterns.*

# These would be caught by constitutional test suite:
# test_no_direct_observation_collection()
# test_no_storage_access_in_commands()
# test_limitations_always_acknowledged()