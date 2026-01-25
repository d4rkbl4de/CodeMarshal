"""
api.py — Programmatic API for CodeMarshal.

ROLE: Expose the system to external programs without expanding capability.
PRINCIPLE: No silent power. Every call must feel deliberate.
"""

import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from bridge.commands import ExportRequest as CmdExportRequest
from bridge.commands import InvestigationRequest as CmdInvestigationRequest
from bridge.commands import ObservationRequest as CmdObservationRequest
from bridge.commands import QueryRequest as CmdQueryRequest
from bridge.commands import execute_export as export

# Allowed imports per constitutional constraints
from bridge.commands import execute_investigation as investigate
from bridge.commands import execute_observation as observe
from bridge.commands import execute_query as query
from bridge.results import ExportResult, InvestigateResult, ObserveResult, QueryResult
from core.runtime import ExecutionMode, Runtime, RuntimeConfiguration
from inquiry.session.context import QuestionType, SessionContext
from integrity.adapters.memory_monitor_adapter import IntegrityMemoryMonitorAdapter
from lens.navigation.context import create_initial_navigation_context
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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
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
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int | None = None
    error_code: APIErrorCode | None = None
    error_message: str | None = None
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        # Handle special types
        if data.get("error_code"):
            data["error_code"] = data["error_code"].value
        if data.get("timestamp"):
            data["timestamp"] = data["timestamp"].isoformat()
        return data

    def to_json(self, indent: int | None = None) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)


@dataclass(kw_only=True)
class InvestigateRequest(APIRequest):
    """Investigate API request schema."""

    path: str
    scope: str
    intent: str
    name: str | None = None
    initial_notes: str | None = None


@dataclass(kw_only=True)
class InvestigateResponse(APIResponse):
    """Investigate API response schema."""

    investigation_id: str | None = None
    path: str | None = None
    scope: str | None = None
    observation_count: int | None = None
    status: str | None = None


@dataclass(kw_only=True)
class ObserveRequest(APIRequest):
    """Observe API request schema."""

    path: str
    scope: str
    max_depth: int | None = None
    include_binary: bool = False
    follow_symlinks: bool = False


@dataclass(kw_only=True)
class ObserveResponse(APIResponse):
    """Observe API response schema."""

    snapshot_id: str | None = None
    path: str | None = None
    file_count: int | None = None
    module_count: int | None = None
    total_size_bytes: int | None = None
    limitations: list[str] = field(default_factory=list)


@dataclass(kw_only=True)
class QueryRequest(APIRequest):
    """Query API request schema."""

    investigation_id: str
    question: str
    question_type: str
    focus: str | None = None
    limit: int | None = None


@dataclass(kw_only=True)
class QueryResponse(APIResponse):
    """Query API response schema."""

    investigation_id: str | None = None
    question: str | None = None
    question_type: str | None = None
    answer: str | None = None
    uncertainties: list[str] = field(default_factory=list)
    anchors: list[str] = field(default_factory=list)
    patterns: list[dict[str, Any]] = field(default_factory=list)


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

    investigation_id: str | None = None
    format: str | None = None
    output_path: str | None = None
    file_size_bytes: int | None = None
    checksum: str | None = None
    observation_count: int | None = None
    pattern_count: int | None = None
    note_count: int | None = None


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
            "%(asctime)s - %(name)s - %(levelname)s - [request:%(request_id)s] %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def investigate(self, request: InvestigateRequest) -> InvestigateResponse:
        """
        Handle investigate API call.
        """
        start_time = datetime.now(UTC)
        response = InvestigateResponse(success=False, request_id=request.request_id)

        try:
            # Validate request
            validation_errors = self._validate_investigate_request(request)
            if validation_errors:
                response.error_code = APIErrorCode.VALIDATION_ERROR
                response.error_message = f"Validation errors: {validation_errors}"
                self.logger.warning(
                    f"Investigate validation failed: {validation_errors}"
                )
                return response

            # Check path exists
            if not Path(request.path).exists():
                response.error_code = APIErrorCode.PATH_NOT_FOUND
                response.error_message = f"Path does not exist: {request.path}"
                self.logger.warning(f"Path not found: {request.path}")
                return response

            self.logger.info(
                f"Starting investigation: path={request.path}, scope={request.scope}"
            )

            # Create command request from API request
            from bridge.commands import InvestigationScope, InvestigationType

            cmd_request = CmdInvestigationRequest(
                type=InvestigationType.NEW,
                target_path=Path(request.path),
                scope=InvestigationScope(request.scope.lower()),
                parameters={
                    "intent": request.intent,
                    "name": request.name,
                    "initial_notes": request.initial_notes,
                },
            )

            config = RuntimeConfiguration(
                investigation_root=Path(request.path),
                execution_mode=ExecutionMode.API,
                constitution_path=Path("Structure.md"),
                code_root=Path(request.path),
            )
            runtime = Runtime(config=config)
            nav_context = create_initial_navigation_context()
            existing_sessions = {}  # Empty for NEW

            raw_result = investigate(
                request=cmd_request,
                runtime=runtime,
                nav_context=nav_context,
                existing_sessions=existing_sessions,
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
                self.logger.info(
                    f"Investigation successful: id={command_result.investigation_id}"
                )
            else:
                response.error_code = APIErrorCode.COMMAND_FAILED
                response.error_message = command_result.error_message
                self.logger.error(
                    f"Investigation failed: {command_result.error_message}"
                )

        except Exception as e:
            self.logger.exception(f"Investigate API error: {e}")
            response.error_code = APIErrorCode.INTERNAL_ERROR
            response.error_message = f"Internal error: {str(e)}"

        finally:
            response.duration_ms = int(
                (datetime.now(UTC) - start_time).total_seconds() * 1000
            )

        return response

    def observe(self, request: ObserveRequest) -> ObserveResponse:
        """
        Handle observe API call.
        """
        start_time = datetime.now(UTC)
        response = ObserveResponse(success=False, request_id=request.request_id)

        try:
            from bridge.commands import ObservationType

            # Map API scope/parameters to command request
            cmd_request = CmdObservationRequest(
                types={ObservationType.FILE_SIGHT},  # Default for API
                target_path=Path(request.path),
                session_id=request.request_id,  # Simplified for API
                parameters={
                    "scope": request.scope,
                    "max_depth": request.max_depth,
                    "include_binary": request.include_binary,
                    "follow_symlinks": request.follow_symlinks,
                },
            )

            from core.engine import Engine
            from core.runtime import Runtime
            from inquiry.session.context import SessionContext
            from lens.navigation.context import create_initial_navigation_context

            # Mock/default dependencies
            config = RuntimeConfiguration(
                investigation_root=Path(request.path).absolute(),
                execution_mode=ExecutionMode.API,
                constitution_path=Path("Structure.md").absolute(),
                code_root=Path(request.path).absolute(),
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
                question_type=QuestionType.STRUCTURE,
            )

            raw_result = observe(
                request=cmd_request,
                runtime=runtime,
                engine=engine,
                nav_context=nav_context,
                session_context=session_context,
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
            response.duration_ms = int(
                (datetime.now(UTC) - start_time).total_seconds() * 1000
            )

        return response

    def query(self, request: QueryRequest) -> QueryResponse:
        """
        Handle query API call.
        """
        start_time = datetime.now(UTC)
        response = QueryResponse(success=False, request_id=request.request_id)

        try:
            cmd_request = CmdQueryRequest(
                investigation_id=request.investigation_id,
                question=request.question,
                question_type=request.question_type,
                parameters={"focus": request.focus, "limit": request.limit},
            )

            # Mock/default dependencies
            config = RuntimeConfiguration(
                investigation_root=Path(".").absolute(),
                execution_mode=ExecutionMode.API,
                constitution_path=Path("Structure.md").absolute(),
                code_root=Path(".").absolute(),
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
                question_type=QuestionType.STRUCTURE,
            )
            nav_context = create_initial_navigation_context()

            raw_result = query(
                request=cmd_request,
                runtime=runtime,
                engine=engine,
                session_context=session_context,
                nav_context=nav_context,
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
            response.duration_ms = int(
                (datetime.now(UTC) - start_time).total_seconds() * 1000
            )

        return response

    def export(self, request: ExportRequest) -> ExportResponse:
        """
        Handle export API call.
        """
        start_time = datetime.now(UTC)
        response = ExportResponse(success=False, request_id=request.request_id)

        try:
            cmd_request = CmdExportRequest(
                investigation_id=request.investigation_id,
                format=request.format,
                output_path=request.output_path,
                parameters={
                    "include_notes": request.include_notes,
                    "include_patterns": request.include_patterns,
                },
            )

            config = RuntimeConfiguration(
                investigation_root=Path(".").absolute(),
                execution_mode=ExecutionMode.API,
                constitution_path=Path("Structure.md").absolute(),
                code_root=Path(".").absolute(),
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
                question_type=QuestionType.STRUCTURE,
            )

            raw_result = export(
                request=cmd_request,
                runtime=runtime,
                engine=engine,
                session_context=session_context,
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
            response.duration_ms = int(
                (datetime.now(UTC) - start_time).total_seconds() * 1000
            )

        return response

    def _validate_investigate_request(self, request: InvestigateRequest) -> list[str]:
        """Validate an investigate request."""
        errors = []
        if not request.path:
            errors.append("Path is required")
        if not request.scope:
            errors.append("Scope is required")
        if not request.intent:
            errors.append("Intent is required")
        return errors


def create_http_server(
    api_instance: CodeMarshalAPI, host: str = "localhost", port: int = 8080
):
    """
    Create a mock HTTP server for the API.
    In a real implementation, this would use Flask/FastAPI.
    """
    logger.info(f"Mock HTTP server starting at http://{host}:{port}")
    return None, host, port
