"""
api.py — Programmatic API for CodeMarshal.

ROLE: Expose the system to external programs without expanding capability.
PRINCIPLE: No silent power. Every call must feel deliberate.
"""

import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
import inspect
import uuid

# Allowed imports per constitutional constraints
from bridge.commands import (
    execute_investigation as investigate,
    execute_observation as observe, 
    execute_query as query,
    execute_export as export,
    InvestigationRequest as CmdInvestigationRequest,
    ObservationRequest as CmdObservationRequest,
    QueryRequest as CmdQueryRequest,
    ExportRequest as CmdExportRequest
)

from bridge.results import (
    InvestigateResult,
    ObserveResult,
    QueryResult,
    ExportResult
)

from core.runtime import Runtime, RuntimeConfiguration, ExecutionMode
from inquiry.session.context import SessionContext, QuestionType
from integrity.adapters.memory_monitor_adapter import IntegrityMemoryMonitorAdapter
from storage.investigation_storage import InvestigationStorage

logger = logging.getLogger(__name__)


class APIErrorCode(Enum):
    """Explicit error codes for API responses."""
    VALIDATION_ERROR = "validation_error"
    PATH_NOT_FOUND = "path_not_found"
    INVESTIGATION_NOT_FOUND = "investigation_not_found"
    COMMAND_FAILED = "command_failed"
    CONFIRMATION_REQUIRED = "confirmation_required"
    LIMIT_EXCEEDED = "limit_exceeded"
    PERMISSION_DENIED = "permission_denied"
    INTERNAL_ERROR = "internal_error"


@dataclass(kw_only=True)
class APIRequest:
    """Base class for all API requests."""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Handle datetime serialization
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
        return data


@dataclass(kw_only=True)
class APIResponse:
    """Base class for all API responses."""
    success: bool
    request_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None
    error_code: Optional[APIErrorCode] = None
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Handle special types
        if data.get("error_code"):
            data["error_code"] = data["error_code"].value
        if data.get("timestamp"):
            data["timestamp"] = data["timestamp"].isoformat()
        return data
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass(kw_only=True)
class InvestigateRequest(APIRequest):
    """Investigate API request schema."""
    path: str
    scope: str
    intent: str
    name: Optional[str] = None
    initial_notes: Optional[str] = None


@dataclass(kw_only=True)
class InvestigateResponse(APIResponse):
    """Investigate API response schema."""
    investigation_id: Optional[str] = None
    path: Optional[str] = None
    scope: Optional[str] = None
    observation_count: Optional[int] = None
    status: Optional[str] = None


@dataclass(kw_only=True)
class ObserveRequest(APIRequest):
    """Observe API request schema."""
    path: str
    scope: str
    max_depth: Optional[int] = None
    include_binary: bool = False
    follow_symlinks: bool = False


@dataclass(kw_only=True)
class ObserveResponse(APIResponse):
    """Observe API response schema."""
    snapshot_id: Optional[str] = None
    path: Optional[str] = None
    file_count: Optional[int] = None
    module_count: Optional[int] = None
    total_size_bytes: Optional[int] = None
    limitations: List[str] = field(default_factory=list)


@dataclass(kw_only=True)
class QueryRequest(APIRequest):
    """Query API request schema."""
    investigation_id: str
    question: str
    question_type: str
    focus: Optional[str] = None
    limit: Optional[int] = None


@dataclass(kw_only=True)
class QueryResponse(APIResponse):
    """Query API response schema."""
    investigation_id: Optional[str] = None
    question: Optional[str] = None
    question_type: Optional[str] = None
    answer: Optional[str] = None
    uncertainties: List[str] = field(default_factory=list)
    anchors: List[str] = field(default_factory=list)
    patterns: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(kw_only=True)
class ExportRequest(APIRequest):
    """Export API request schema."""
    investigation_id: str
    format: str
    output_path: str
    include_notes: bool = False
    include_patterns: bool = False


@dataclass(kw_only=True)
class ExportResponse(APIResponse):
    """Export API response schema."""
    investigation_id: Optional[str] = None
    format: Optional[str] = None
    output_path: Optional[str] = None
    file_size_bytes: Optional[int] = None
    checksum: Optional[str] = None
    observation_count: Optional[int] = None
    pattern_count: Optional[int] = None
    note_count: Optional[int] = None


class CodeMarshalAPI:
    """
    API implementation with zero cleverness.
    
    CONSTRAINTS:
    - One endpoint per command
    - Explicit request schemas
    - Explicit refusal responses
    - No implicit chaining
    - No auto-resume behavior
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Set up structured logging for API calls."""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [request:%(request_id)s] %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def investigate(self, request: InvestigateRequest) -> InvestigateResponse:
        """
        Handle investigate API call.
        """
        start_time = datetime.now(timezone.utc)
        response = InvestigateResponse(
            success=False,
            request_id=request.request_id
        )
        
        try:
            # Validate request
            validation_errors = self._validate_investigate_request(request)
            if validation_errors:
                response.error_code = APIErrorCode.VALIDATION_ERROR
                response.error_message = f"Validation errors: {validation_errors}"
                self.logger.warning(f"Investigate validation failed: {validation_errors}")
                return response
            
            # Check path exists
            if not Path(request.path).exists():
                response.error_code = APIErrorCode.PATH_NOT_FOUND
                response.error_message = f"Path does not exist: {request.path}"
                self.logger.warning(f"Path not found: {request.path}")
                return response
            
            self.logger.info(f"Starting investigation: path={request.path}, scope={request.scope}")
            
            # Create command request from API request
            from pathlib import Path as PathLib
            from bridge.commands import InvestigationType, InvestigationScope
            
            cmd_request = CmdInvestigationRequest(
                type=InvestigationType.NEW,
                target_path=PathLib(request.path),
                scope=InvestigationScope(request.scope.lower()),
                parameters={
                    "intent": request.intent,
                    "name": request.name,
                    "initial_notes": request.initial_notes
                }
            )
            
            from lens.navigation.context import create_initial_navigation_context
            
            config = RuntimeConfiguration(
                investigation_root=PathLib(request.path),
                execution_mode=ExecutionMode.API,
                constitution_path=PathLib("Structure.md"),
                code_root=PathLib(request.path)
            )
            runtime = Runtime(config=config)
            nav_context = create_initial_navigation_context()
            existing_sessions = {} # Empty for NEW
            
            raw_result = investigate(
                request=cmd_request,
                runtime=runtime,
                nav_context=nav_context,
                existing_sessions=existing_sessions
            )
            
            command_result = InvestigateResult(**raw_result)
            
            # Handle command result
            if command_result.success:
                response.success = True
                response.investigation_id = command_result.investigation_id
                response.path = command_result.path
                response.scope = command_result.scope
                response.observation_count = command_result.observation_count
                response.status = command_result.status
                response.warnings = command_result.warnings
                self.logger.info(f"Investigation successful: id={command_result.investigation_id}")
            else:
                response.error_code = APIErrorCode.COMMAND_FAILED
                response.error_message = command_result.error_message
                self.logger.error(f"Investigation failed: {command_result.error_message}")
                
        except Exception as e:
            self.logger.exception(f"Investigate API error: {e}")
            response.error_code = APIErrorCode.INTERNAL_ERROR
            response.error_message = f"Internal error: {str(e)}"
        
        finally:
            response.duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        
        return response

    def observe(self, request: ObserveRequest) -> ObserveResponse:
        """
        Handle observe API call.
        """
        start_time = datetime.now(timezone.utc)
        response = ObserveResponse(
            success=False,
            request_id=request.request_id
        )
        
        try:
            from pathlib import Path as PathLib
            from bridge.commands import ObservationType
            
            # Map API scope/parameters to command request
            cmd_request = CmdObservationRequest(
                types={ObservationType.FILE_SIGHT}, # Default for API
                target_path=PathLib(request.path),
                session_id=request.request_id, # Simplified for API
                parameters={
                    "scope": request.scope,
                    "max_depth": request.max_depth,
                    "include_binary": request.include_binary,
                    "follow_symlinks": request.follow_symlinks
                }
            )
            
            from core.runtime import Runtime
            from core.engine import Engine
            from lens.navigation.context import create_initial_navigation_context
            from inquiry.session.context import SessionContext
            
            # Mock/default dependencies
            config = RuntimeConfiguration(
                investigation_root=PathLib(request.path).absolute(),
                execution_mode=ExecutionMode.API,
                constitution_path=PathLib("Structure.md").absolute(),
                code_root=PathLib(request.path).absolute()
            )
            runtime = Runtime(config=config)
            engine = Engine(
                runtime._context,
                runtime._state,
                storage=InvestigationStorage(),
                memory_monitor=IntegrityMemoryMonitorAdapter(),
            )
            nav_context = create_initial_navigation_context()
            session_context = SessionContext(
                snapshot_id=uuid.uuid4(),
                anchor_id="root",
                question_type=QuestionType.STRUCTURE
            )
            
            raw_result = observe(
                request=cmd_request,
                runtime=runtime,
                engine=engine,
                nav_context=nav_context,
                session_context=session_context
            )
            
            command_result = ObserveResult(**raw_result)
            
            if command_result.success:
                response.success = True
                response.snapshot_id = command_result.observation_id
                response.path = request.path
                # Map other fields from command result
                response.limitations = list(command_result.limitations.keys())
            else:
                response.error_code = APIErrorCode.COMMAND_FAILED
                response.error_message = command_result.error_message
                
        except Exception as e:
            self.logger.exception(f"Observe API error: {e}")
            response.error_code = APIErrorCode.INTERNAL_ERROR
            response.error_message = str(e)
            
        finally:
            response.duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
        return response

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Handle query API call.
        """
        start_time = datetime.now(timezone.utc)
        response = QueryResponse(
            success=False,
            request_id=request.request_id
        )
        
        try:
            cmd_request = CmdQueryRequest(
                investigation_id=request.investigation_id,
                question=request.question,
                question_type=request.question_type,
                parameters={
                    "focus": request.focus,
                    "limit": request.limit
                }
            )
            
            # Mock/default dependencies
            config = RuntimeConfiguration(
                investigation_root=PathLib(".").absolute(),
                execution_mode=ExecutionMode.API,
                constitution_path=PathLib("Structure.md").absolute(),
                code_root=PathLib(".").absolute()
            )
            runtime = Runtime(config=config)
            from core.engine import Engine
            engine = Engine(
                runtime._context,
                runtime._state,
                storage=InvestigationStorage(),
                memory_monitor=IntegrityMemoryMonitorAdapter(),
            )
            session_context = SessionContext(
                snapshot_id=uuid.uuid4(),
                anchor_id="root",
                question_type=QuestionType.STRUCTURE
            )
            nav_context = create_initial_navigation_context()
            
            raw_result = query(
                request=cmd_request,
                runtime=runtime,
                engine=engine,
                session_context=session_context,
                nav_context=nav_context
            )
            
            command_result = QueryResult(**raw_result)
            
            if command_result.success:
                response.success = True
                response.investigation_id = command_result.investigation_id
                response.question = command_result.question
                response.question_type = command_result.question_type
                response.answer = command_result.answer
                response.uncertainties = command_result.uncertainties
                response.anchors = command_result.anchors
                response.patterns = command_result.patterns
            else:
                response.error_code = APIErrorCode.COMMAND_FAILED
                response.error_message = command_result.error_message
                
        except Exception as e:
            self.logger.exception(f"Query API error: {e}")
            response.error_code = APIErrorCode.INTERNAL_ERROR
            response.error_message = str(e)
            
        finally:
            response.duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
        return response

    def export(self, request: ExportRequest) -> ExportResponse:
        """
        Handle export API call.
        """
        start_time = datetime.now(timezone.utc)
        response = ExportResponse(
            success=False,
            request_id=request.request_id
        )
        
        try:
            cmd_request = CmdExportRequest(
                investigation_id=request.investigation_id,
                format=request.format,
                output_path=request.output_path,
                parameters={
                    "include_notes": request.include_notes,
                    "include_patterns": request.include_patterns
                }
            )
            
            config = RuntimeConfiguration(
                investigation_root=PathLib(".").absolute(),
                execution_mode=ExecutionMode.API,
                constitution_path=PathLib("Structure.md").absolute(),
                code_root=PathLib(".").absolute()
            )
            runtime = Runtime(config=config)
            from core.engine import Engine
            engine = Engine(
                runtime._context,
                runtime._state,
                storage=InvestigationStorage(),
                memory_monitor=IntegrityMemoryMonitorAdapter(),
            )
            session_context = SessionContext(
                snapshot_id=uuid.uuid4(),
                anchor_id="root",
                question_type=QuestionType.STRUCTURE
            )
            
            raw_result = export(
                request=cmd_request,
                runtime=runtime,
                engine=engine,
                session_context=session_context
            )
            
            command_result = ExportResult(**raw_result)
            
            if command_result.success:
                response.success = True
                response.investigation_id = command_result.investigation_id
                response.format = command_result.format
                response.output_path = command_result.output_path
                response.file_size_bytes = command_result.file_size_bytes
                response.checksum = command_result.checksum
                response.observation_count = command_result.observation_count
                response.pattern_count = command_result.pattern_count
                response.note_count = command_result.note_count
            else:
                response.error_code = APIErrorCode.COMMAND_FAILED
                response.error_message = command_result.error_message
                
        except Exception as e:
            self.logger.exception(f"Export API error: {e}")
            response.error_code = APIErrorCode.INTERNAL_ERROR
            response.error_message = str(e)
            
        finally:
            response.duration_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            
        return response

    def _validate_investigate_request(self, request: InvestigateRequest) -> List[str]:
        """Validate an investigate request."""
        errors = []
        if not request.path:
            errors.append("Path is required")
        if not request.scope:
            errors.append("Scope is required")
        if not request.intent:
            errors.append("Intent is required")
        return errors

def create_http_server(api_instance: CodeMarshalAPI, host: str = "localhost", port: int = 8080):
    """
    Create a mock HTTP server for the API.
    In a real implementation, this would use Flask/FastAPI.
    """
    logger.info(f"Mock HTTP server starting at http://{host}:{port}")
    return None, host, port