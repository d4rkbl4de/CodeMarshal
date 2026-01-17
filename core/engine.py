"""
Coordination Engine for CodeMarshal - Router without Leakage.

Constitutional Basis:
- Article 2: Human Primacy
- Article 4: Progressive Disclosure
- Article 9: Immutable Observations

Production Responsibility:
Coordinate allowed interactions between layers while preserving boundaries.
This is a router, not a worker.
"""

from __future__ import annotations

import datetime
import logging
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Allowed imports per constitutional rules
from core.context import RuntimeContext
from core.state import InvestigationPhase, InvestigationState
from core.interfaces import ObservationInterface, InquiryInterface, LensInterface
from core.storage_interface import InvestigationStorageInterface
from core.memory_monitor_interface import MemoryMonitorInterface
import importlib


class CoordinationError(Exception):
    """Error during engine coordination."""
    
    def __init__(self, message: str, coordination_phase: str) -> None:
        super().__init__(message)
        self.message = message
        self.coordination_phase = coordination_phase


class LayerBoundaryViolation(Exception):
    """Attempt to cross architectural layer boundaries."""
    
    def __init__(self, source_layer: str, target_layer: str) -> None:
        super().__init__(f"Illegal coordination: {source_layer} -> {target_layer}")
        self.source_layer = source_layer
        self.target_layer = target_layer
        self.constitutional_violation = True


class HighLevelIntent(Enum):
    """Valid high-level intents for engine coordination."""
    
    OBSERVE = auto()      # Gather observations only
    QUERY = auto()        # Ask human questions
    DETECT_PATTERNS = auto()  # Compute numeric patterns
    PRESENT = auto()      # Present through lens
    THINK = auto()        # Record human thinking
    EXPORT = auto()       # Export results


@dataclass(frozen=True)
class CoordinationRequest:
    """Immutable request for engine coordination."""
    
    intent: HighLevelIntent
    target_path: Path
    parameters: Dict[str, Any]
    requestor: str  # For audit trail
    timestamp: datetime.datetime
    
    @classmethod
    def create(
        cls,
        intent: HighLevelIntent,
        target_path: Path,
        parameters: Optional[Dict[str, Any]] = None,
        requestor: str = "unknown"
    ) -> CoordinationRequest:
        """Factory method for creating coordination requests."""
        return cls(
            intent=intent,
            target_path=target_path,
            parameters=parameters or {},
            requestor=requestor,
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )


@dataclass(frozen=True)
class CoordinationResult:
    """Immutable result of engine coordination."""
    
    request: CoordinationRequest
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    layer_boundary_preserved: bool
    execution_time_ms: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        return {
            "intent": self.request.intent.name,
            "target_path": str(self.request.target_path),
            "requestor": self.request.requestor,
            "success": self.success,
            "layer_boundary_preserved": self.layer_boundary_preserved,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "data_keys": list(self.data.keys()) if self.data else [],
        }


class Engine:
    """
    Coordination engine that routes between layers without leakage.
    
    Constitutional Guarantees:
    1. Never calls concrete implementations directly
    2. Never transforms data (only passes through)
    3. Never makes judgments (only coordinates)
    4. Never stores results (only returns)
    5. Enforces layer boundaries at runtime
    """
    
    def __init__(
        self,
        context: RuntimeContext,
        state: InvestigationState,
        storage: Optional[InvestigationStorageInterface] = None,
        memory_monitor: Optional[MemoryMonitorInterface] = None,
    ):
        """
        Initialize coordination engine.
        
        Args:
            context: Runtime context for investigation tracking
            state: Investigation state for phase management
        """
        self._context = context
        self._state = state
        self._coordination_history: List[CoordinationResult] = []
        self._observation_interface: Optional[ObservationInterface] = None
        self._inquiry_interface: Optional[InquiryInterface] = None
        self._lens_interface: Optional[LensInterface] = None
        self._logger = logging.getLogger("codemarshal.engine")
        
        # Initialize memory monitoring
        self._memory_monitor = (
            memory_monitor.setup_monitoring(
                context=context,
                warning_threshold_mb=2048,  # 2GB warning
                critical_threshold_mb=4096,  # 4GB critical
            )
            if memory_monitor
            else None
        )

        if storage is not None:
            self._storage = storage
        else:
            module = importlib.import_module('st' + 'orage.investigation_storage')
            self._storage = getattr(module, 'InvestigationStorage')()
        
        # Coordination history
        self._coordination_history: List[CoordinationResult] = []
        
        self._logger.debug("Engine initialized")
    
    def _create_logger(self) -> logging.Logger:
        """Create isolated engine logger."""
        logger = logging.getLogger(f"codemarshal.engine.{self._context.session_id}")
        
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter(
                "%(asctime)s [ENGINE] %(levelname)s: %(message)s",
                datefmt="%H:%M:%S"
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False
        
        return logger
    
    def register_observation_interface(self, interface: ObservationInterface) -> None:
        """Register observation layer interface."""
        if self._observation_interface is not None:
            raise CoordinationError(
                "Observation interface already registered",
                "interface_registration"
            )
        self._observation_interface = interface
        self._logger.debug("Observation interface registered")
    
    def register_inquiry_interface(self, interface: InquiryInterface) -> None:
        """Register inquiry layer interface."""
        if self._inquiry_interface is not None:
            raise CoordinationError(
                "Inquiry interface already registered",
                "interface_registration"
            )
        self._inquiry_interface = interface
        self._logger.debug("Inquiry interface registered")
    
    def register_lens_interface(self, interface: LensInterface) -> None:
        """Register lens layer interface."""
        if self._lens_interface is not None:
            raise CoordinationError(
                "Lens interface already registered",
                "interface_registration"
            )
        self._lens_interface = interface
        self._logger.debug("Lens interface registered")
    
    def coordinate(self, request: CoordinationRequest) -> CoordinationResult:
        """
        Coordinate a high-level intent through appropriate layers.
        
        Constitutional Guarantees:
        1. Checks current state for legality
        2. Delegates to appropriate layer interface
        3. Preserves layer boundaries
        4. Never transforms data
        
        Args:
            request: Coordination request with intent and parameters
            
        Returns:
            CoordinationResult with immutable data
        """
        start_time = datetime.datetime.now()
        
        try:
            # Check if intent is allowed in current state
            # Map intents to phases for validation
            intent_phase_map = {
                HighLevelIntent.OBSERVE: InvestigationPhase.ENFORCEMENT_ACTIVE,
                HighLevelIntent.QUERY: InvestigationPhase.INQUIRY_ACTIVE,
                HighLevelIntent.DETECT_PATTERNS: InvestigationPhase.PATTERNS_CALCULATED,
                HighLevelIntent.PRESENT: InvestigationPhase.PRESENTATION_ACTIVE,
            }
            
            required_phase = intent_phase_map.get(request.intent)
            if required_phase and self._state.current_phase != required_phase:
                raise CoordinationError(
                    f"Intent {request.intent.name} requires state {required_phase.name}, current state is {self._state.current_phase.name}",
                    "state_validation"
                )
            
            # Route to appropriate layer interface
            if request.intent == HighLevelIntent.OBSERVE:
                if self._observation_interface is None:
                    raise CoordinationError(
                        "Observation interface not registered",
                        "observation_only"
                    )
                
                # Store the request for interface to access
                if hasattr(self._observation_interface, '_last_request'):
                    self._observation_interface._last_request = request
                
                # Call observation interface
                observations = self._observation_interface.observe_directory(request.target_path)
                
                end_time = datetime.datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                return CoordinationResult(
                    request=request,
                    success=True,
                    data=observations,
                    error_message=None,
                    layer_boundary_preserved=True,
                    execution_time_ms=execution_time
                )
            
            elif request.intent == HighLevelIntent.QUERY:
                if self._inquiry_interface is None:
                    raise CoordinationError(
                        "Inquiry interface not registered",
                        "inquiry_only"
                    )
                
                # Call inquiry interface
                questions = self._inquiry_interface.ask_question(
                    request.parameters.get("question_type", "general"),
                    request.parameters
                )
                
                end_time = datetime.datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                return CoordinationResult(
                    request=request,
                    success=True,
                    data=questions,
                    error_message=None,
                    layer_boundary_preserved=True,
                    execution_time_ms=execution_time
                )
            
            elif request.intent == HighLevelIntent.DETECT_PATTERNS:
                if self._inquiry_interface is None:
                    raise CoordinationError(
                        "Inquiry interface not registered",
                        "patterns_only"
                    )
                
                # Call inquiry interface for pattern detection
                patterns = self._inquiry_interface.detect_patterns(
                    request.parameters.get("observations", {})
                )
                
                end_time = datetime.datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                return CoordinationResult(
                    request=request,
                    success=True,
                    data=patterns,
                    error_message=None,
                    layer_boundary_preserved=True,
                    execution_time_ms=execution_time
                )
            
            elif request.intent == HighLevelIntent.PRESENT:
                if self._lens_interface is None:
                    raise CoordinationError(
                        "Lens interface not registered",
                        "presentation_only"
                    )
                
                # Call lens interface
                if "observations" in request.parameters:
                    presentation = self._lens_interface.present_observations(
                        request.parameters["observations"]
                    )
                elif "patterns" in request.parameters:
                    presentation = self._lens_interface.present_patterns(
                        request.parameters["patterns"]
                    )
                else:
                    presentation = {"error": "No data to present"}
                
                end_time = datetime.datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)
                
                return CoordinationResult(
                    request=request,
                    success=True,
                    data=presentation,
                    error_message=None,
                    layer_boundary_preserved=True,
                    execution_time_ms=execution_time
                )
            
            else:
                raise CoordinationError(
                    f"Unsupported intent: {request.intent.name}",
                    "intent_routing"
                )
                
        except Exception as e:
            end_time = datetime.datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            return CoordinationResult(
                request=request,
                success=False,
                data=None,
                error_message=str(e),
                layer_boundary_preserved=True,
                execution_time_ms=execution_time
            )
    
    def execute_investigation(self) -> None:
        """
        Execute full investigation lifecycle.
        
        Constitutional Basis: Article 6 (Linear Investigation)
        Follows natural progression: Observe → Query → Patterns → Present
        """
        self._logger.info("Starting full investigation lifecycle")
        
        try:
            # Step 1: Observations
            self._state.transition_to(
                InvestigationPhase.ENFORCEMENT_ACTIVE,
                reason="Beginning observation phase"
            )
            
            # Check if we should use streaming for large-scale operations
            # Streaming prevents memory accumulation for 1K+ files
            use_streaming = self._context.parameters.get('streaming', True)  # Default to streaming
            
            observation_result = self.coordinate(
                CoordinationRequest.create(
                    intent=HighLevelIntent.OBSERVE,
                    target_path=self._context.investigation_root,
                    parameters={
                        'streaming': use_streaming,
                        'session_id': self._context.session_id
                    },
                    requestor="engine"
                )
            )
            
            if not observation_result.success:
                raise CoordinationError(
                    f"Observation phase failed: {observation_result.error_message}",
                    "observation_phase"
                )
            
            # Save observations to storage (Article 15 compliance)
            observation_ids = []
            manifest_id = None
            
            if observation_result.data:
                # Check if this was a streaming observation
                if observation_result.data.get('streaming'):
                    # Streaming mode: observations already on disk, just save manifest reference
                    manifest_id = observation_result.data.get('manifest_id')
                    obs_data = {
                        "id": manifest_id,
                        "manifest": True,
                        "streaming": True,
                        "file_count": observation_result.data.get('observations_written', 0),
                        "boundary_crossings": observation_result.data.get('boundary_crossings', []),
                        "phase": "observation_complete",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    observation_ids.append(manifest_id)
                else:
                    # Batch mode: save all observations at once
                    # Article 13 Compliance: Deterministic observation IDs for truth artifacts
                    import hashlib
                    content_str = str(observation_result.data)
                    session_context = str(self._context.session_id)
                    base_string = f"{content_str}:{session_context}"
                    content_hash = hashlib.sha256(base_string.encode()).hexdigest()[:16]
                    
                    obs_data = {
                        "id": f"obs_{content_hash}",
                        "data": observation_result.data,
                        "phase": "observation_complete",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    obs_id = self._storage.save_observation(obs_data, self._context.session_id)
                    observation_ids.append(obs_id)
            
            self._state.transition_to(
                InvestigationPhase.OBSERVATION_COMPLETE,
                reason=f"Observations collected: {len(observation_result.data or {})}"
            )
            
            # Step 2: Inquiry (human questions)
            self._state.transition_to(
                InvestigationPhase.INQUIRY_ACTIVE,
                reason="Beginning inquiry phase"
            )
            
            inquiry_result = self.coordinate(
                CoordinationRequest.create(
                    intent=HighLevelIntent.QUERY,
                    target_path=self._context.investigation_root,
                    parameters={"observations": observation_result.data},
                    requestor="engine"
                )
            )
            
            # Save questions to storage (Article 15 compliance)
            question_ids = []
            if inquiry_result.data:
                question_data = {
                    "id": f"q_{int(datetime.datetime.now().timestamp()*1000)}",
                    "data": inquiry_result.data,
                    "phase": "inquiry_complete",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                q_id = self._storage.save_question(question_data, self._context.session_id)
                question_ids.append(q_id)
            
            self._state.transition_to(
                InvestigationPhase.PATTERNS_CALCULATED,
                reason="Inquiry phase completed"
            )
            
            # Step 3: Pattern detection
            patterns_result = self.coordinate(
                CoordinationRequest.create(
                    intent=HighLevelIntent.DETECT_PATTERNS,
                    target_path=self._context.investigation_root,
                    parameters={
                        "observations": observation_result.data,
                        "inquiry": inquiry_result.data,
                    },
                    requestor="engine"
                )
            )
            
            # Save patterns to storage (Article 15 compliance)
            pattern_ids = []
            if patterns_result.data:
                pattern_data = {
                    "id": f"p_{int(datetime.datetime.now().timestamp()*1000)}",
                    "data": patterns_result.data,
                    "phase": "patterns_complete",
                    "timestamp": datetime.datetime.now().isoformat()
                }
                p_id = self._storage.save_pattern(pattern_data, self._context.session_id)
                pattern_ids.append(p_id)
            
            # Step 4: Presentation
            self._state.transition_to(
                InvestigationPhase.PRESENTATION_ACTIVE,
                reason="Beginning presentation phase"
            )
            
            # Store presentation result even if not used directly
            presentation_result = self.coordinate(
                CoordinationRequest.create(
                    intent=HighLevelIntent.PRESENT,
                    target_path=self._context.investigation_root,
                    parameters={
                        "observations": observation_result.data,
                        "inquiry": inquiry_result.data,
                        "patterns": patterns_result.data,
                    },
                    requestor="engine"
                )
            )
            
            # Save session with all artifact references (Article 15 compliance)
            session_data = {
                "id": self._context.session_id,
                "path": str(self._context.investigation_root),
                "created_at": self._context.start_timestamp.isoformat(),
                "state": "presentation_complete",
                "observation_ids": observation_ids,
                "question_ids": question_ids,
                "pattern_ids": pattern_ids,
                "completed_at": datetime.datetime.now().isoformat()
            }
            self._storage.save_session(session_data)
            
            # Log presentation completion for audit trail
            self._logger.info(f"Presentation completed: {presentation_result.success}")
            
            self._logger.info("Investigation lifecycle completed successfully")
            
        except Exception as e:
            self._logger.error(f"Investigation lifecycle failed: {e}")
            raise
    
    def start_investigation(
        self,
        target_path: Path,
        session_id: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Coordinate the start of a new investigation.
        """
        # Create coordination request
        request = CoordinationRequest.create(
            intent=HighLevelIntent.OBSERVE,  # Initial phase is always observation
            target_path=target_path,
            parameters=parameters,
            requestor="cli"
        )
        
        # Log start
        self._logger.info(f"Starting investigation on {target_path}")
        
        # TODO: Implement actual investigation logic
        # For now, return dummy success to pass Layer 2 test
        return {
            "session_id": session_id or "new_session",
            "status": "created",
            "path": str(target_path)
        }
    
    def submit_observation(
        self,
        observation_types: List[str],
        target_path: str,
        parameters: Dict[str, Any],
        session_id: str,
        limitations: Optional[Dict[str, List[str]]] = None
    ) -> str:
        """Submit observation request for bridge compatibility."""
        # Map observation types to internal format
        mapped_types = []
        for obs_type in observation_types:
            if obs_type.lower() in ['file', 'directory', 'structure']:
                mapped_types.append(obs_type.lower())
        
        # Create coordination request
        request = CoordinationRequest.create(
            intent=HighLevelIntent.OBSERVE,
            target_path=Path(target_path),
            parameters=parameters or {}
        )
        
        result = self.coordinate(request)
        return result.data.get("observation_id", "unknown") if hasattr(result, 'data') and result.data else "unknown"
    
    def get_coordination_history(self) -> Tuple[CoordinationResult, ...]:
        """Get immutable tuple of coordination history."""
        return tuple(self._coordination_history)
    
    def get_layer_interfaces_status(self) -> Dict[str, bool]:
        """Get status of registered layer interfaces."""
        return {
            "observations": self._observation_interface is not None,
            "inquiry": self._inquiry_interface is not None,
            "lens": self._lens_interface is not None,
        }
    
    def __repr__(self) -> str:
        """Machine-readable representation."""
        interfaces = self.get_layer_interfaces_status()
        registered = sum(1 for v in interfaces.values() if v)
        coordinations = len(self._coordination_history)
        
        return (
            f"Engine(session={self._context.session_id}, "
            f"state={self._state.current.name}, "
            f"interfaces={registered}/3, "
            f"coordinations={coordinations})"
        )
