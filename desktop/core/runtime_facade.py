"""Desktop runtime facade for direct bridge command integration."""

from __future__ import annotations

import csv
import io
import json
import threading
import uuid
from dataclasses import asdict, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bridge.commands import (
    ExportFormat,
    ExportRequest,
    ExportType,
    InvestigationRequest,
    InvestigationScope,
    InvestigationType,
    ObservationRequest,
    ObservationType,
    QueryRequest,
    QueryType,
    QuestionName,
    execute_export,
    execute_investigation,
    execute_observation,
    execute_pattern_list,
    execute_pattern_scan,
    execute_query,
)
from core.runtime import ExecutionMode, Runtime, RuntimeConfiguration
from inquiry.answers import (
    AnomalyDetector,
    ConnectionMapper,
    PurposeExtractor,
    StructureAnalyzer,
    ThinkingEngine,
)
from inquiry.interface import MinimalInquiryInterface
from inquiry.session.context import QuestionType, SessionContext
from lens.interface import MinimalLensInterface
from lens.navigation.context import (
    FocusType,
    NavigationContext,
    create_navigation_context,
)
from lens.navigation.workflow import WorkflowStage
from lens.views import ViewType
from observations.interface import MinimalObservationInterface
from storage.investigation_storage import InvestigationStorage

from .exceptions import OperationCancelledError


class RuntimeFacade:
    """High-level integration facade for desktop operations."""

    def __init__(self, storage_root: Path | str = Path("storage")) -> None:
        self._storage_root = Path(storage_root)
        self._storage_root.mkdir(parents=True, exist_ok=True)
        self._storage = InvestigationStorage(base_path=self._storage_root)

        self._runtime: Runtime | None = None
        self._session_context: SessionContext | None = None
        self._nav_context: NavigationContext | None = None

        self._current_path: Path | None = None
        self._current_investigation_id: str | None = None

        self._latest_observations: list[dict[str, Any]] = []
        self._latest_pattern_scan: dict[str, Any] | None = None

        self._lock = threading.RLock()

    @property
    def current_investigation_id(self) -> str | None:
        return self._current_investigation_id

    @property
    def current_path(self) -> Path | None:
        return self._current_path

    def _check_cancel(self, cancel_event: threading.Event | None) -> None:
        if cancel_event is not None and cancel_event.is_set():
            raise OperationCancelledError("Operation cancelled")

    def _emit_progress(
        self,
        callback: Any,
        current: int,
        total: int,
        message: str,
    ) -> None:
        if callable(callback):
            callback(current, total, message)

    def _get_constitution_path(self) -> Path:
        candidates = [
            Path("Structure.md"),
            Path("docs") / "Structure.md",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        raise FileNotFoundError("Constitution file not found (Structure.md)")

    def _create_session_context(self) -> SessionContext:
        return SessionContext(
            snapshot_id=uuid.uuid4(),
            anchor_id="root",
            question_type=QuestionType.STRUCTURE,
            context_id=uuid.uuid4(),
            active=True,
            has_observations=False,
            current_stage="orientation",
        )

    def _ensure_runtime(self, target_path: Path) -> Runtime:
        root = target_path if target_path.is_dir() else target_path.parent
        root = root.resolve()

        with self._lock:
            if self._runtime is not None and self._current_path == root:
                return self._runtime

            config = RuntimeConfiguration(
                investigation_root=root,
                execution_mode=ExecutionMode.API,
                constitution_path=self._get_constitution_path(),
                code_root=root,
            )
            runtime = Runtime(config=config)
            engine = runtime.engine

            status = engine.get_layer_interfaces_status()
            if not status.get("observations"):
                engine.register_observation_interface(
                    MinimalObservationInterface(runtime.context)
                )
            if not status.get("inquiry"):
                engine.register_inquiry_interface(MinimalInquiryInterface())
            if not status.get("lens"):
                engine.register_lens_interface(MinimalLensInterface())

            session_context = self._create_session_context()
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:desktop",
                current_view=ViewType.OVERVIEW,
            )

            self._runtime = runtime
            self._session_context = session_context
            self._nav_context = nav_context
            self._current_path = root

            return runtime

    def _set_stage(self, stage: WorkflowStage, focus_id: str) -> None:
        if self._session_context is None:
            self._session_context = self._create_session_context()
        self._session_context = replace(
            self._session_context,
            current_stage=stage.value,
        )
        self._nav_context = create_navigation_context(
            session_context=self._session_context,
            workflow_stage=stage,
            focus_type=FocusType.SYSTEM,
            focus_id=focus_id,
            current_view=ViewType.OVERVIEW,
        )

    def _ensure_active_context(self) -> None:
        if self._session_context is None:
            self._session_context = self._create_session_context()
        if self._nav_context is None:
            self._nav_context = create_navigation_context(
                session_context=self._session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:desktop",
                current_view=ViewType.OVERVIEW,
            )

    def resolve_session_id(self, session_id: str | None = None) -> str | None:
        if session_id and session_id != "latest":
            return session_id
        if self._current_investigation_id:
            return self._current_investigation_id
        sessions = self._storage.list_sessions(limit=1)
        if sessions:
            return str(sessions[0].get("session_id") or sessions[0].get("id"))
        return None

    def list_recent_investigations(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._storage.list_sessions(limit=limit)

    def load_session_metadata(self, session_id: str) -> dict[str, Any] | None:
        return self._storage.load_session_metadata(session_id)

    def _upsert_session_metadata(self, metadata: dict[str, Any]) -> str:
        metadata = dict(metadata)
        metadata.setdefault("id", metadata.get("session_id"))
        metadata.setdefault("session_id", metadata.get("id"))
        metadata.setdefault("created_at", datetime.now(UTC).isoformat())
        metadata["modified_at"] = datetime.now(UTC).isoformat()
        metadata.setdefault("path", str(self._current_path) if self._current_path else "")
        metadata.setdefault("scope", "codebase")
        metadata.setdefault("intent", "initial_scan")
        metadata.setdefault("state", "active")
        metadata.setdefault("observation_ids", [])
        metadata.setdefault("question_ids", [])
        metadata.setdefault("pattern_ids", [])
        metadata.setdefault("notes", [])
        metadata.setdefault("patterns", [])
        metadata.setdefault("file_count", 0)

        return self._storage.save_session(metadata)

    def _append_session_reference(self, session_id: str, field: str, value: str) -> None:
        session = self._storage.load_session_metadata(session_id)
        if not session:
            return
        items = list(session.get(field, []) or [])
        if value and value not in items:
            items.append(value)
            session[field] = items
            self._storage.save_session(session)

    def load_observations_for_session(self, session_id: str) -> list[dict[str, Any]]:
        session = self._storage.load_session_metadata(session_id)
        if not session:
            return []

        observations: list[dict[str, Any]] = []
        observation_ids = list(session.get("observation_ids", []) or [])
        observations_dir = self._storage_root / "observations"

        for obs_id in observation_ids:
            obs_file = observations_dir / f"{obs_id}.observation.json"
            if not obs_file.exists():
                continue
            try:
                payload = json.loads(obs_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            if isinstance(payload, dict) and isinstance(payload.get("data"), dict):
                data_payload = payload["data"]
                nested = data_payload.get("observations")
                if isinstance(nested, list) and nested:
                    observations.extend([n for n in nested if isinstance(n, dict)])
                else:
                    observations.append(
                        {
                            "type": "file_sight",
                            "result": data_payload,
                            "path": data_payload.get("path", ""),
                        }
                    )
            elif isinstance(payload, dict) and isinstance(
                payload.get("observations"), list
            ):
                observations.extend(
                    [n for n in payload["observations"] if isinstance(n, dict)]
                )
            elif isinstance(payload, dict):
                observations.append(payload)

        return observations

    def run_investigation(
        self,
        path: Path | str,
        scope: str,
        intent: str,
        name: str = "",
        notes: str = "",
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        target_path = Path(path).resolve()
        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 4, "Initializing runtime")

        runtime = self._ensure_runtime(target_path)
        self._ensure_active_context()

        scope_map = {
            "file": InvestigationScope.FILE,
            "module": InvestigationScope.MODULE,
            "package": InvestigationScope.PACKAGE,
            "project": InvestigationScope.CODEBASE,
            "codebase": InvestigationScope.CODEBASE,
        }
        selected_scope = scope_map.get(scope.lower(), InvestigationScope.CODEBASE)

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 2, 4, "Submitting investigation request")

        request = InvestigationRequest(
            type=InvestigationType.NEW,
            target_path=target_path,
            scope=selected_scope,
            parameters={
                "intent": intent,
                "name": name,
                "notes": notes,
            },
        )

        result = execute_investigation(
            request=request,
            runtime=runtime,
            nav_context=self._nav_context,
            existing_sessions={},
        )

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 3, 4, "Persisting session metadata")

        investigation_id = str(result.get("investigation_id"))
        self._current_investigation_id = investigation_id

        self._session_context = replace(
            self._session_context,
            has_observations=True,
            current_stage=WorkflowStage.THINKING.value,
        )
        self._set_stage(WorkflowStage.THINKING, "system:investigation")

        self._upsert_session_metadata(
            {
                "id": investigation_id,
                "name": name or target_path.name,
                "path": str(target_path),
                "scope": selected_scope.value,
                "intent": intent,
                "state": str(result.get("status", "completed")),
                "file_count": int(result.get("observation_count") or 0),
            }
        )

        self._emit_progress(progress_callback, 4, 4, "Investigation completed")
        return result

    def run_observation(
        self,
        path: Path | str,
        eye_types: list[str],
        session_id: str | None = None,
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        target_path = Path(path).resolve()
        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 4, "Preparing observation")

        runtime = self._ensure_runtime(target_path)
        self._ensure_active_context()
        self._set_stage(WorkflowStage.ORIENTATION, "system:observe")

        selected_types: set[ObservationType] = set()
        for eye in eye_types:
            normalized = eye.strip().lower()
            if not normalized.endswith("_sight"):
                normalized = f"{normalized}_sight"
            selected_types.add(ObservationType(normalized))

        if not selected_types:
            raise ValueError("At least one observation eye must be selected")

        active_session_id = session_id or self.resolve_session_id() or str(uuid.uuid4())
        self._current_investigation_id = active_session_id

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 2, 4, "Running observation")

        request = ObservationRequest(
            types=selected_types,
            target_path=target_path,
            session_id=active_session_id,
            parameters={
                "include_results": True,
                "additional_view": True,
            },
        )

        result = execute_observation(
            request=request,
            runtime=runtime,
            engine=runtime.engine,
            nav_context=self._nav_context,
            session_context=self._session_context,
        )

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 3, 4, "Updating session metadata")

        data_payload = result.get("data") or {}
        if isinstance(data_payload, dict):
            observations = data_payload.get("observations", [])
            if isinstance(observations, list):
                self._latest_observations = [
                    obs for obs in observations if isinstance(obs, dict)
                ]

        observation_id = str(result.get("observation_id") or "")

        self._session_context = replace(
            self._session_context,
            has_observations=True,
            current_stage=WorkflowStage.EXAMINATION.value,
        )

        self._upsert_session_metadata(
            {
                "id": active_session_id,
                "name": active_session_id,
                "path": str(target_path),
                "state": "observation_complete",
                "file_count": len(self._latest_observations),
            }
        )

        if observation_id and observation_id != "unknown":
            self._append_session_reference(active_session_id, "observation_ids", observation_id)

        self._emit_progress(progress_callback, 4, 4, "Observation completed")

        result["session_id"] = active_session_id
        result["observations_count"] = len(self._latest_observations)
        return result

    def _question_to_stage(self, question_type: str) -> WorkflowStage:
        mapping = {
            "structure": WorkflowStage.ORIENTATION,
            "purpose": WorkflowStage.EXAMINATION,
            "connections": WorkflowStage.CONNECTIONS,
            "anomalies": WorkflowStage.PATTERNS,
            "thinking": WorkflowStage.THINKING,
        }
        return mapping.get(question_type.lower(), WorkflowStage.EXAMINATION)

    def _question_name(self, question_type: str) -> QuestionName:
        mapping = {
            "structure": QuestionName.STRUCTURE,
            "purpose": QuestionName.PURPOSE,
            "connections": QuestionName.CONNECTIONS,
            "anomalies": QuestionName.ANOMALIES,
            "thinking": QuestionName.THINKING,
        }
        return mapping.get(question_type.lower(), QuestionName.STRUCTURE)

    def _analyzer_for_question(self, question_type: str) -> Any:
        mapping = {
            "structure": StructureAnalyzer,
            "purpose": PurposeExtractor,
            "connections": ConnectionMapper,
            "anomalies": AnomalyDetector,
            "thinking": ThinkingEngine,
        }
        return mapping.get(question_type.lower(), StructureAnalyzer)

    def run_query(
        self,
        question: str,
        question_type: str,
        focus: str | None = None,
        limit: int = 25,
        session_id: str | None = None,
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        active_session_id = self.resolve_session_id(session_id)
        if not active_session_id:
            raise ValueError("No investigation session available")
        self._current_investigation_id = active_session_id

        if self._current_path is None:
            metadata = self._storage.load_session_metadata(active_session_id)
            if metadata and metadata.get("path"):
                self._ensure_runtime(Path(str(metadata["path"])))
            else:
                raise ValueError("Unable to determine investigation path")

        self._ensure_active_context()
        stage = self._question_to_stage(question_type)
        self._set_stage(stage, "system:query")

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 3, "Authorizing query")

        params: dict[str, Any] = {
            "question": question,
            "focus": focus,
            "limit": max(int(limit), 1),
        }
        if question_type.lower() == "thinking":
            params.setdefault("anchor", focus or "root")

        request = QueryRequest(
            type=QueryType.QUESTION,
            name=self._question_name(question_type),
            session_id=active_session_id,
            parameters=params,
        )

        command_result = execute_query(
            request=request,
            runtime=self._runtime,
            engine=self._runtime.engine,
            nav_context=self._nav_context,
            session_context=self._session_context,
        )

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 2, 3, "Building answer from observations")

        observations = self.load_observations_for_session(active_session_id)
        analyzer_cls = self._analyzer_for_question(question_type)
        analyzer = analyzer_cls()
        answer = analyzer.analyze(observations, question)

        query_id = str(command_result.get("query_id") or f"query_{uuid.uuid4().hex[:8]}")
        self._append_session_reference(active_session_id, "question_ids", query_id)

        self._emit_progress(progress_callback, 3, 3, "Query completed")
        return {
            "query_id": query_id,
            "session_id": active_session_id,
            "question": question,
            "question_type": question_type,
            "answer": answer,
            "observations_used": len(observations),
        }

    def run_pattern_list(
        self,
        category: str | None = None,
        show_disabled: bool = False,
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 2, "Loading pattern library")

        list_result = execute_pattern_list(
            category=category,
            show_disabled=show_disabled,
            output_format="table",
        )

        self._emit_progress(progress_callback, 2, 2, "Pattern library ready")
        payload = asdict(list_result)
        payload["patterns"] = [asdict(pattern) for pattern in list_result.patterns]
        return payload

    def run_pattern_scan(
        self,
        path: Path | str,
        category: str | None = None,
        pattern_ids: list[str] | None = None,
        glob: str = "*",
        max_files: int = 10000,
        session_id: str | None = None,
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        target_path = Path(path).resolve()
        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 3, "Preparing pattern scan")

        scan_result = execute_pattern_scan(
            path=target_path,
            patterns=pattern_ids,
            category=category,
            glob=glob,
            output_format="table",
            max_files=max_files,
        )

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 2, 3, "Collecting scan results")

        payload = asdict(scan_result)
        self._latest_pattern_scan = payload

        active_session_id = self.resolve_session_id(session_id)
        if active_session_id:
            self._current_investigation_id = active_session_id
            pattern_ref = (
                f"pattern_scan_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
            )
            self._append_session_reference(active_session_id, "pattern_ids", pattern_ref)

        self._emit_progress(progress_callback, 3, 3, "Pattern scan completed")
        return payload

    def _export_format(self, name: str) -> ExportFormat:
        mapping = {
            "json": ExportFormat.JSON,
            "markdown": ExportFormat.MARKDOWN,
            "html": ExportFormat.HTML,
            "plain": ExportFormat.PLAINTEXT,
            "plaintext": ExportFormat.PLAINTEXT,
            "csv": ExportFormat.CSV,
            "jupyter": ExportFormat.JUPYTER,
            "pdf": ExportFormat.PDF,
            "svg": ExportFormat.SVG,
        }
        key = name.strip().lower()
        if key not in mapping:
            raise ValueError(f"Unsupported export format: {name}")
        return mapping[key]

    def _authorize_export(self, export_format: ExportFormat) -> dict[str, Any]:
        self._ensure_active_context()
        self._set_stage(WorkflowStage.THINKING, "system:export")

        auth_session_id = str(self._session_context.snapshot_id)
        request = ExportRequest(
            type=ExportType.SESSION,
            format=export_format,
            session_id=auth_session_id,
            parameters={"source": "desktop"},
        )

        return execute_export(
            request=request,
            runtime=self._runtime,
            session_context=self._session_context,
            nav_context=self._nav_context,
        )

    def _load_export_source(
        self,
        session_id: str,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        session_data = self._storage.load_session_metadata(session_id)
        if not session_data:
            raise ValueError(f"Session not found: {session_id}")
        observations = self.load_observations_for_session(session_id)
        return session_data, observations

    def _generate_export_content(
        self,
        format_name: str,
        session_data: dict[str, Any],
        observations: list[dict[str, Any]],
        include_notes: bool,
        include_patterns: bool,
    ) -> str | bytes:
        normalized = format_name.lower()

        if normalized == "json":
            payload = {
                "export_metadata": {
                    "version": "2.1.0",
                    "exported_at": datetime.now(UTC).isoformat(),
                    "format": "json",
                    "tool": "CodeMarshal",
                },
                "investigation": session_data,
                "observations": observations,
            }
            if include_notes:
                payload["notes"] = session_data.get("notes", [])
            if include_patterns:
                payload["patterns"] = session_data.get("patterns", [])
            return json.dumps(payload, indent=2, default=str)

        if normalized == "markdown":
            lines = [
                "# CodeMarshal Investigation Report",
                "",
                f"Exported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}",
                "",
                "## Investigation",
                f"- ID: {session_data.get('id', 'unknown')}",
                f"- Path: {session_data.get('path', 'unknown')}",
                f"- State: {session_data.get('state', 'unknown')}",
                "",
                "## Observations",
                f"Total observations: {len(observations)}",
            ]
            by_type: dict[str, int] = {}
            for obs in observations:
                obs_type = str(obs.get("type", "unknown"))
                by_type[obs_type] = by_type.get(obs_type, 0) + 1
            if by_type:
                lines.append("")
                lines.append("### By Type")
                for key, value in sorted(by_type.items()):
                    lines.append(f"- {key}: {value}")

            if include_notes:
                lines.append("")
                lines.append("## Notes")
                notes = session_data.get("notes", [])
                if notes:
                    for note in notes:
                        lines.append(f"- {note}")
                else:
                    lines.append("- No notes")

            if include_patterns:
                lines.append("")
                lines.append("## Patterns")
                patterns = session_data.get("patterns", [])
                if patterns:
                    for pattern in patterns:
                        lines.append(f"- {pattern}")
                else:
                    lines.append("- No patterns")

            return "\n".join(lines)

        if normalized == "html":
            summary = {
                "session_id": session_data.get("id", "unknown"),
                "path": session_data.get("path", "unknown"),
                "state": session_data.get("state", "unknown"),
                "observations": len(observations),
            }
            obs_html = "".join(
                f"<li>{str(obs.get('type', 'unknown'))}</li>" for obs in observations[:100]
            )
            return (
                "<!doctype html><html><head><meta charset='utf-8'><title>CodeMarshal Export</title>"
                "<style>body{font-family:Arial,sans-serif;margin:24px;}"
                "table{border-collapse:collapse;}td,th{border:1px solid #ddd;padding:8px;}</style></head><body>"
                "<h1>CodeMarshal Investigation Report</h1>"
                f"<p>Exported: {datetime.now(UTC).isoformat()}</p>"
                "<h2>Summary</h2>"
                "<table>"
                f"<tr><th>ID</th><td>{summary['session_id']}</td></tr>"
                f"<tr><th>Path</th><td>{summary['path']}</td></tr>"
                f"<tr><th>State</th><td>{summary['state']}</td></tr>"
                f"<tr><th>Observations</th><td>{summary['observations']}</td></tr>"
                "</table>"
                "<h2>Observation Types</h2>"
                f"<ul>{obs_html}</ul>"
                "</body></html>"
            )

        if normalized in {"plain", "plaintext"}:
            lines = [
                "CodeMarshal Investigation Export",
                "=" * 40,
                f"ID: {session_data.get('id', 'unknown')}",
                f"Path: {session_data.get('path', 'unknown')}",
                f"State: {session_data.get('state', 'unknown')}",
                f"Observations: {len(observations)}",
            ]
            return "\n".join(lines)

        if normalized == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["type", "file", "line", "module"])
            for obs in observations:
                obs_type = obs.get("type", "unknown")
                if obs_type == "import_sight":
                    statements = obs.get("statements", [])
                    for stmt in statements:
                        writer.writerow(
                            [
                                "import",
                                obs.get("file", ""),
                                stmt.get("line_number", ""),
                                stmt.get("module", ""),
                            ]
                        )
                else:
                    writer.writerow([obs_type, obs.get("file", ""), "", ""])
            return output.getvalue()

        if normalized == "jupyter":
            from bridge.integration.jupyter_exporter import JupyterExporter

            return JupyterExporter().export(
                session_data,
                observations,
                include_notes=include_notes,
                include_patterns=include_patterns,
            )

        if normalized == "svg":
            from bridge.integration.svg_exporter import SVGExporter

            return SVGExporter().export(
                session_data,
                observations,
                include_notes=include_notes,
                include_patterns=include_patterns,
            )

        if normalized == "pdf":
            from bridge.integration.pdf_exporter import PDFExporter

            return PDFExporter().export(
                session_data,
                observations,
                include_notes=include_notes,
                include_patterns=include_patterns,
            )

        raise ValueError(f"Unsupported export format: {format_name}")

    def preview_export(
        self,
        session_id: str,
        format_name: str,
        include_notes: bool,
        include_patterns: bool,
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 3, "Loading session data")

        resolved_session = self.resolve_session_id(session_id)
        if not resolved_session:
            raise ValueError("No session available for preview")
        self._current_investigation_id = resolved_session

        if self._current_path is None:
            metadata = self._storage.load_session_metadata(resolved_session)
            if metadata and metadata.get("path"):
                self._ensure_runtime(Path(str(metadata["path"])))

        export_format = self._export_format(format_name)
        self._authorize_export(export_format)

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 2, 3, "Generating preview")

        session_data, observations = self._load_export_source(resolved_session)
        content = self._generate_export_content(
            format_name,
            session_data,
            observations,
            include_notes,
            include_patterns,
        )

        if isinstance(content, bytes):
            preview = f"Binary export generated ({len(content)} bytes)."
        else:
            preview = content[:4000]
            if len(content) > 4000:
                preview += "\n\n[Preview truncated]"

        self._emit_progress(progress_callback, 3, 3, "Preview ready")
        return {
            "session_id": resolved_session,
            "format": format_name,
            "preview": preview,
            "observations_count": len(observations),
        }

    def run_export(
        self,
        session_id: str,
        format_name: str,
        output_path: Path | str,
        include_notes: bool,
        include_patterns: bool,
        include_evidence: bool,
        progress_callback: Any = None,
        cancel_event: threading.Event | None = None,
    ) -> dict[str, Any]:
        del include_evidence  # current exporters always include observed evidence context

        resolved_session = self.resolve_session_id(session_id)
        if not resolved_session:
            raise ValueError("No session available for export")
        self._current_investigation_id = resolved_session

        metadata = self._storage.load_session_metadata(resolved_session)
        if metadata and metadata.get("path"):
            self._ensure_runtime(Path(str(metadata["path"])))

        export_format = self._export_format(format_name)

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 1, 4, "Authorizing export")
        auth_result = self._authorize_export(export_format)

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 2, 4, "Loading export source")
        session_data, observations = self._load_export_source(resolved_session)

        self._check_cancel(cancel_event)
        self._emit_progress(progress_callback, 3, 4, "Rendering export content")
        content = self._generate_export_content(
            format_name,
            session_data,
            observations,
            include_notes,
            include_patterns,
        )

        output_file = Path(output_path).resolve()
        output_file.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            output_file.write_bytes(content)
        else:
            output_file.write_text(content, encoding="utf-8")

        self._emit_progress(progress_callback, 4, 4, "Export complete")
        return {
            "export_id": str(auth_result.get("export_id") or uuid.uuid4()),
            "session_id": resolved_session,
            "format": format_name,
            "path": str(output_file),
            "bytes": output_file.stat().st_size,
        }


