"""
Concrete implementation of ObservationInterface for engine coordination.
"""

import datetime
from dataclasses import asdict, is_dataclass
from pathlib import Path, PurePath
from typing import Any

import yaml

from core.context import RuntimeContext
from core.engine import CoordinationRequest, CoordinationResult, ObservationInterface

# Memory monitoring integration
from integrity.monitoring.memory import get_memory_monitor

from .boundary_checker import BoundaryViolationChecker, create_agent_nexus_boundaries

# Import actual eye implementations
from .eyes import get_eye
from .eyes.boundary_sight import BoundaryDefinition, BoundarySight
from .eyes.go_sight import GoSight
from .eyes.java_sight import JavaSight
from .eyes.javascript_sight import JavaScriptSight
from .eyes.language_detector import LanguageDetector


# ...
def _coerce_for_json(value: Any) -> Any:
    """Convert payloads to JSON-compatible structures."""
    if isinstance(value, (Path, PurePath)):
        return str(value)
    if is_dataclass(value):
        return _coerce_for_json(asdict(value))
    if isinstance(value, dict):
        return {k: _coerce_for_json(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_coerce_for_json(v) for v in value]
    if hasattr(value, "__dict__"):
        return _coerce_for_json(value.__dict__)
    return value


class MinimalObservationInterface(ObservationInterface):
    """Minimal implementation of ObservationInterface to enable engine execution."""

    def __init__(self, context: RuntimeContext):
        """Initialize the observation interface."""
        self._context = context
        self._last_request = None
        # Initialize boundary checker with Agent Nexus boundaries
        self._boundary_checker = BoundaryViolationChecker(
            create_agent_nexus_boundaries()
        )
        self._language_detector = LanguageDetector()
        self._supported_extensions = self._language_detector.supported_extensions()

    def get_limitations(self) -> dict[str, Any]:
        """Get declared limitations of observation methods."""
        return {
            "file_sight": {
                "description": "File structure observation",
                "deterministic": True,
                "side_effect_free": True,
            },
            "import_sight": {
                "description": "Import statement detection",
                "deterministic": True,
                "side_effect_free": True,
            },
            "export_sight": {
                "description": "Public definition detection",
                "deterministic": True,
                "side_effect_free": True,
            },
            "javascript_sight": {
                "description": "JavaScript/TypeScript import/export detection",
                "deterministic": True,
                "side_effect_free": True,
            },
            "java_sight": {
                "description": "Java import/class detection",
                "deterministic": True,
                "side_effect_free": True,
            },
            "go_sight": {
                "description": "Go import/package detection",
                "deterministic": True,
                "side_effect_free": True,
            },
            "boundary_sight": {
                "description": "Architectural boundary violation detection",
                "deterministic": True,
                "side_effect_free": True,
            },
        }

    def coordinate(self, request: CoordinationRequest) -> CoordinationResult:
        """Handle observation coordination requests."""
        start_time = datetime.datetime.now()

        try:
            # Extract observation types from request parameters
            observation_types = request.parameters.get(
                "observation_types", ["file_sight"]
            )
            streaming = request.parameters.get("streaming", False)
            session_id = request.parameters.get("session_id", "default")

            # Store request for observe_directory to access
            self._last_request = request

            # If target is a directory and streaming is requested, use streaming mode
            target_path = Path(request.target_path)
            if target_path.is_dir() and streaming:
                data = self.observe_directory(
                    target_path, streaming=True, session_id=session_id
                )

                end_time = datetime.datetime.now()
                execution_time = int((end_time - start_time).total_seconds() * 1000)

                return CoordinationResult(
                    request=request,
                    success=True,
                    data=data,
                    error_message=None,
                    layer_boundary_preserved=True,
                    execution_time_ms=execution_time,
                )

            # Original batch mode for single files or small operations
            # Use actual eye implementations
            observations = []
            boundary_crossings = []
            target_path = Path(request.target_path)

            for obs_type in observation_types:
                try:
                    if obs_type in {"import_sight", "export_sight"}:
                        if target_path.is_dir():
                            code_files = self._iter_code_files(target_path)
                            self._observe_import_export_files(
                                code_files,
                                obs_type,
                                observations,
                                boundary_crossings=boundary_crossings,
                                check_boundaries=False,
                            )
                        else:
                            self._observe_import_export_file(
                                target_path,
                                obs_type,
                                observations,
                                boundary_crossings=boundary_crossings,
                                check_boundaries=False,
                            )
                        continue

                    # Get appropriate eye
                    eye = get_eye(obs_type)
                    if eye:
                        # For boundary_sight, load Agent Nexus configuration
                        if obs_type == "boundary_sight":
                            # Try to load Agent Nexus configuration
                            config_path = Path("config/agent_nexus.yaml")
                            if config_path.exists():
                                with open(config_path) as f:
                                    config = yaml.safe_load(f)

                                # Create boundary definitions from config
                                boundary_defs = []
                                for boundary in config.get("boundaries", []):
                                    # Convert string boundary type to enum
                                    boundary_type_str = boundary.get("type", "package")
                                    from .eyes.boundary_sight import BoundaryType

                                    boundary_type_map = {
                                        "layer": BoundaryType.LAYER,
                                        "package": BoundaryType.PACKAGE,
                                        "module": BoundaryType.MODULE,
                                        "external": BoundaryType.EXTERNAL,
                                        "custom": BoundaryType.CUSTOM,
                                    }

                                    boundary_defs.append(
                                        BoundaryDefinition(
                                            name=boundary.get("name"),
                                            boundary_type=boundary_type_map.get(
                                                boundary_type_str, BoundaryType.PACKAGE
                                            ),
                                            pattern=boundary.get("pattern"),
                                            description=boundary.get("description", ""),
                                            allowed_targets=tuple(
                                                boundary.get("allowed_targets", [])
                                            ),
                                            prohibited=boundary.get("prohibited", True),
                                        )
                                    )

                                # Create BoundarySight with definitions and project root
                                eye = BoundarySight(
                                    boundary_definitions=boundary_defs,
                                    project_root=target_path
                                    if target_path.is_dir()
                                    else target_path.parent,
                                )

                        # Use eye to observe
                        result = eye.observe(target_path)

                        # Extract the actual observation data
                        if hasattr(result, "raw_payload") and result.raw_payload:
                            # For ImportSight and BoundarySight, data is in raw_payload
                            if hasattr(result.raw_payload, "statements"):
                                # ImportSight
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "statements": [
                                            stmt.__dict__
                                            for stmt in result.raw_payload.statements
                                        ],
                                    }
                                )
                            elif hasattr(result.raw_payload, "crossings"):
                                # BoundarySight
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "crossings": [
                                            cross.__dict__
                                            for cross in result.raw_payload.crossings
                                        ],
                                    }
                                )
                                # Also collect boundary crossings separately
                                for cross in result.raw_payload.crossings:
                                    boundary_crossings.append(
                                        {
                                            "source": cross.source_module,
                                            "target": cross.target_module,
                                            "file": str(cross.source_module) + ".py",
                                            "line": cross.line_number,
                                            "violation": "cross_lobe_import",
                                        }
                                    )
                            elif hasattr(result.raw_payload, "modules"):
                                # FileSight and others
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "result": result.raw_payload.__dict__,
                                    }
                                )
                            else:
                                # Preserve other payload types (e.g., DirectoryTree)
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "result": _coerce_for_json(result.raw_payload),
                                    }
                                )
                        else:
                            # Fallback for other observation types
                            observations.append(
                                {
                                    "type": obs_type,
                                    "result": result.__dict__
                                    if hasattr(result, "__dict__")
                                    else str(result),
                                }
                            )
                except Exception as e:
                    # Log error but continue with other observations
                    observations.append({"type": obs_type, "error": str(e)})

            data = {
                "observations": observations,
                "boundary_crossings": boundary_crossings,
                "summary": f"Observation of {request.target_path} completed",
            }

            end_time = datetime.datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)

            return CoordinationResult(
                request=request,
                success=True,
                data=data,
                error_message=None,
                layer_boundary_preserved=True,
                execution_time_ms=execution_time,
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
                execution_time_ms=execution_time,
            )

    def observe_directory(
        self,
        directory_path: Path,
        streaming: bool = False,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Observe a directory with all configured observation types.

        Args:
            directory_path: Directory to observe
            streaming: If True, write observations incrementally (for large-scale)
            session_id: Session ID for streaming mode
        """
        # Get memory monitor
        memory_monitor = get_memory_monitor(self._context)

        # Start memory tracking for this operation
        memory_monitor.start_operation("observe", "scanning")

        # Check if constitutional flag is set

        # Get observation types from context or use defaults
        observation_types = ["file_sight"]  # Default

        # Try to determine if constitutional analysis is requested
        # This is a workaround since observe_directory doesn't get parameters
        if hasattr(self, "_last_request"):
            observation_types = self._last_request.parameters.get(
                "observation_types", ["file_sight"]
            )
            self._last_request.parameters.get("constitutional", False)

        # Use streaming for large-scale operations or when memory is tight
        if streaming or memory_monitor.should_chunk():
            return self._observe_directory_streaming(
                directory_path,
                observation_types,
                session_id or "default",
                memory_monitor,
            )

        # Original batch mode (for small directories)
        # Count files for memory tracking
        file_count = 0

        # Use actual eye implementations
        observations = []
        boundary_crossings = []

        for obs_type in observation_types:
            try:
                if obs_type in {"import_sight", "export_sight"}:
                    code_files = self._iter_code_files(directory_path)
                    self._observe_import_export_files(
                        code_files,
                        obs_type,
                        observations,
                        boundary_crossings=boundary_crossings,
                        check_boundaries=(obs_type == "import_sight"),
                        memory_monitor=memory_monitor,
                    )
                    file_count += len(code_files)
                    continue

                # Get appropriate eye
                eye = get_eye(obs_type)
                if eye:
                    # For boundary_sight, load Agent Nexus configuration
                    if obs_type == "boundary_sight":
                        # Try to load Agent Nexus configuration
                        config_path = Path("config/agent_nexus.yaml")
                        if config_path.exists():
                            with open(config_path) as f:
                                config = yaml.safe_load(f)

                            # Create boundary definitions from config
                            boundary_defs = []
                            for boundary in config.get("boundaries", []):
                                # Convert string boundary type to enum
                                boundary_type_str = boundary.get("type", "package")
                                from .eyes.boundary_sight import BoundaryType

                                boundary_type_map = {
                                    "layer": BoundaryType.LAYER,
                                    "package": BoundaryType.PACKAGE,
                                    "module": BoundaryType.MODULE,
                                    "external": BoundaryType.EXTERNAL,
                                    "custom": BoundaryType.CUSTOM,
                                }

                                boundary_defs.append(
                                    BoundaryDefinition(
                                        name=boundary.get("name"),
                                        boundary_type=boundary_type_map.get(
                                            boundary_type_str, BoundaryType.PACKAGE
                                        ),
                                        pattern=boundary.get("pattern"),
                                        description=boundary.get("description", ""),
                                        allowed_targets=tuple(
                                            boundary.get("allowed_targets", [])
                                        ),
                                        prohibited=boundary.get("prohibited", True),
                                    )
                                )

                            # Create BoundarySight with definitions and project root
                            eye = BoundarySight(
                                boundary_definitions=boundary_defs,
                                project_root=directory_path,
                            )

                    # Check if we should use chunking
                    if memory_monitor.should_chunk():
                        # For large directories, process in chunks
                        self._observe_chunked(
                            eye,
                            directory_path,
                            obs_type,
                            observations,
                            boundary_crossings,
                            memory_monitor,
                        )
                    else:
                        # Normal observation
                        result = eye.observe(directory_path)

                        # Extract the actual observation data
                        if hasattr(result, "raw_payload") and result.raw_payload:
                            # For ImportSight and BoundarySight, data is in raw_payload
                            if hasattr(result.raw_payload, "statements"):
                                # ImportSight - check boundary violations
                                statements = result.raw_payload.statements
                                violations = []

                                # Check each import statement for boundary violations
                                for stmt in statements:
                                    stmt_dict = {
                                        "type": "import"
                                        if not hasattr(stmt, "names")
                                        else "from_import",
                                        "module": stmt.module
                                        if hasattr(stmt, "module")
                                        else None,
                                        "names": list(stmt.names)
                                        if hasattr(stmt, "names")
                                        else [],
                                        "line": stmt.line
                                        if hasattr(stmt, "line")
                                        else None,
                                    }
                                    stmt_violations = (
                                        self._boundary_checker.check_import_statement(
                                            directory_path / f"{stmt.module}.py"
                                            if hasattr(stmt, "module") and stmt.module
                                            else directory_path,
                                            stmt_dict,
                                        )
                                    )
                                    violations.extend(stmt_violations)

                                observations.append(
                                    {
                                        "type": obs_type,
                                        "statements": [
                                            stmt.__dict__ for stmt in statements
                                        ],
                                        "boundary_violations": [
                                            v.__dict__ for v in violations
                                        ],
                                    }
                                )

                                # Add violations to boundary_crossings
                                for violation in violations:
                                    boundary_crossings.append(
                                        {
                                            "source": violation.source,
                                            "target": violation.target,
                                            "file": violation.source,
                                            "line": violation.line_number,
                                            "violation": f"boundary_{violation.type}",
                                            "rule": violation.rule,
                                            "source_boundary": violation.source_boundary,
                                            "target_boundary": violation.target_boundary,
                                        }
                                    )

                                file_count += len(statements)
                            elif hasattr(result.raw_payload, "crossings"):
                                # BoundarySight
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "crossings": [
                                            cross.__dict__
                                            for cross in result.raw_payload.crossings
                                        ],
                                    }
                                )
                                # Also collect boundary crossings separately
                                for cross in result.raw_payload.crossings:
                                    boundary_crossings.append(
                                        {
                                            "source": cross.source_module,
                                            "target": cross.target_module,
                                            "file": str(cross.source_module) + ".py",
                                            "line": cross.line_number,
                                            "violation": "cross_lobe_import",
                                        }
                                    )
                            elif hasattr(result.raw_payload, "modules"):
                                # FileSight and others
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "result": result.raw_payload.__dict__,
                                    }
                                )
                                file_count += len(result.raw_payload.modules)
                            else:
                                # Preserve other payload types (e.g., DirectoryTree)
                                observations.append(
                                    {
                                        "type": obs_type,
                                        "result": _coerce_for_json(result.raw_payload),
                                    }
                                )
                        else:
                            # Fallback for other observation types
                            observations.append(
                                {
                                    "type": obs_type,
                                    "result": result.__dict__
                                    if hasattr(result, "__dict__")
                                    else str(result),
                                }
                            )

                    # Track files processed for memory monitoring
                    memory_monitor.track_files(file_count)

            except Exception as e:
                # Log error but continue with other observations
                observations.append({"type": obs_type, "error": str(e)})

        # Get memory status for reporting
        memory_status = memory_monitor.get_memory_status()

        # Return observation data with memory info
        return {
            "path": str(directory_path),
            "file_count": len(self._iter_code_files(directory_path)),
            "directory_count": len(
                [d for d in directory_path.rglob("*") if d.is_dir()]
            ),
            "total_items": len(list(directory_path.rglob("*"))),
            "observations": observations,
            "boundary_crossings": boundary_crossings,
            "memory_usage": memory_status,
            "status": "observed",
        }

    def _iter_code_files(self, directory_path: Path) -> list[Path]:
        """Return deterministic list of supported code files."""
        exts = self._supported_extensions or {".py"}
        files = [
            path
            for path in directory_path.rglob("*")
            if path.is_file() and path.suffix.lower() in exts
        ]
        files.sort(key=lambda p: str(p).lower())
        return files

    def _language_for_file(self, file_path: Path) -> str:
        """Determine language by extension with fallback to detector."""
        ext = file_path.suffix.lower()
        for language, signature in self._language_detector.LANGUAGE_SIGNATURES.items():
            if ext in signature.get("extensions", []):
                return language
        detection = self._language_detector.detect_language_for_path(file_path)
        return detection.primary

    def _get_language_specific_eye(self, obs_type: str, language: str):
        """Select appropriate eye for a language-aware observation."""
        if obs_type not in {"import_sight", "export_sight"}:
            return get_eye(obs_type)

        if language == "python":
            return get_eye(obs_type)
        if language in {"javascript", "typescript"}:
            return get_eye("javascript_sight") or JavaScriptSight()
        if language == "java":
            return get_eye("java_sight") or JavaSight()
        if language == "go":
            return get_eye("go_sight") or GoSight()

        return None

    def _extract_import_statements(self, raw_payload: Any) -> tuple:
        if not raw_payload:
            return ()
        if hasattr(raw_payload, "statements"):
            return raw_payload.statements
        if hasattr(raw_payload, "imports"):
            return raw_payload.imports
        return ()

    def _serialize_import_statement(self, statement: Any) -> dict[str, Any]:
        if isinstance(statement, dict):
            data = dict(statement)
        elif hasattr(statement, "__dict__"):
            data = dict(statement.__dict__)
        else:
            data = {"value": str(statement)}

        data = _coerce_for_json(data)
        names = data.get("names")
        if isinstance(names, (tuple, set)):
            data["names"] = list(names)
        elif names is None:
            data["names"] = []
        return data

    def _extract_exports(self, raw_payload: Any) -> list[dict[str, Any]]:
        entries = []
        if raw_payload:
            if hasattr(raw_payload, "public_definitions"):
                entries = list(raw_payload.public_definitions)
            elif hasattr(raw_payload, "definitions"):
                entries = list(raw_payload.definitions)
            elif hasattr(raw_payload, "exports"):
                entries = list(raw_payload.exports)
            elif hasattr(raw_payload, "classes"):
                entries = list(raw_payload.classes)

        exports: list[dict[str, Any]] = []
        seen: set[str] = set()
        for entry in entries:
            name = None
            if isinstance(entry, str):
                name = entry
            elif isinstance(entry, dict):
                name = entry.get("name")
            elif hasattr(entry, "name"):
                name = getattr(entry, "name")
            if not name or name in seen:
                continue
            seen.add(name)
            exports.append({"name": name})
        return exports

    def _build_boundary_statements(self, statements: tuple) -> list[dict[str, Any]]:
        boundary_statements: list[dict[str, Any]] = []
        for stmt in statements:
            if isinstance(stmt, dict):
                module = stmt.get("module")
                names = stmt.get("names", [])
                import_type = stmt.get("import_type") or stmt.get("type")
                line_number = stmt.get("line") or stmt.get("line_number")
            else:
                module = getattr(stmt, "module", None)
                names = getattr(stmt, "names", ())
                import_type = getattr(stmt, "import_type", None)
                line_number = getattr(stmt, "line_number", None)

            if import_type == "from":
                stmt_type = "from_import"
            else:
                stmt_type = "import"

            boundary_statements.append(
                {
                    "type": stmt_type,
                    "module": module,
                    "names": list(names) if isinstance(names, (tuple, list, set)) else [],
                    "line": line_number,
                }
            )
        return boundary_statements

    def _observe_import_export_file(
        self,
        file_path: Path,
        obs_type: str,
        observations: list[dict[str, Any]],
        boundary_crossings: list[dict[str, Any]] | None = None,
        check_boundaries: bool = False,
    ) -> None:
        language = self._language_for_file(file_path)
        eye = self._get_language_specific_eye(obs_type, language)
        if not eye:
            return

        result = eye.observe(file_path)
        raw_payload = getattr(result, "raw_payload", None)

        if obs_type == "import_sight":
            statements = self._extract_import_statements(raw_payload)
            statements_list = [self._serialize_import_statement(s) for s in statements]
            observation = {
                "type": "import_sight",
                "file": str(file_path),
                "language": language,
                "statements": statements_list,
            }

            if check_boundaries and language == "python":
                boundary_statements = self._build_boundary_statements(statements)
                violations = self._boundary_checker.check_file_imports(
                    file_path, boundary_statements
                )
                if violations:
                    observation["boundary_violations"] = [
                        v.__dict__ for v in violations
                    ]
                    if boundary_crossings is not None:
                        for violation in violations:
                            boundary_crossings.append(
                                {
                                    "source": violation.source,
                                    "target": violation.target,
                                    "file": violation.source,
                                    "line": violation.line_number,
                                    "violation": f"boundary_{violation.type}",
                                    "rule": violation.rule,
                                    "source_boundary": violation.source_boundary,
                                    "target_boundary": violation.target_boundary,
                                }
                            )

            observations.append(observation)
        else:
            exports = self._extract_exports(raw_payload)
            observations.append(
                {
                    "type": "export_sight",
                    "file": str(file_path),
                    "language": language,
                    "result": {"exports": exports},
                }
            )

    def _observe_import_export_files(
        self,
        files: list[Path],
        obs_type: str,
        observations: list[dict[str, Any]],
        boundary_crossings: list[dict[str, Any]] | None = None,
        check_boundaries: bool = False,
        memory_monitor: Any | None = None,
    ) -> None:
        for idx, file_path in enumerate(files, start=1):
            try:
                self._observe_import_export_file(
                    file_path,
                    obs_type,
                    observations,
                    boundary_crossings=boundary_crossings,
                    check_boundaries=check_boundaries,
                )
            except Exception as exc:
                observations.append({"type": obs_type, "error": str(exc)})

            if memory_monitor and idx % 100 == 0:
                memory_monitor.track_files(100)

    def _observe_chunked(
        self,
        eye,
        directory_path: Path,
        obs_type: str,
        observations: list[dict],
        boundary_crossings: list[dict],
        memory_monitor,
    ) -> None:
        """Observe directory in chunks to manage memory usage."""
        chunk_size = 1000  # Process 1000 files at a time
        files_processed = 0

        # Get all supported code files
        all_files = self._iter_code_files(directory_path)

        for i in range(0, len(all_files), chunk_size):
            chunk_files = all_files[i : i + chunk_size]

            # Process chunk
            for file_path in chunk_files:
                try:
                    result = eye.observe(file_path)

                    # Extract data similar to main method
                    if hasattr(result, "raw_payload") and result.raw_payload:
                        if hasattr(result.raw_payload, "statements"):
                            observations.append(
                                {
                                    "type": obs_type,
                                    "statements": [
                                        stmt.__dict__
                                        for stmt in result.raw_payload.statements
                                    ],
                                }
                            )
                        elif hasattr(result.raw_payload, "crossings"):
                            observations.append(
                                {
                                    "type": obs_type,
                                    "crossings": [
                                        cross.__dict__
                                        for cross in result.raw_payload.crossings
                                    ],
                                }
                            )
                            for cross in result.raw_payload.crossings:
                                boundary_crossings.append(
                                    {
                                        "source": cross.source_module,
                                        "target": cross.target_module,
                                        "file": str(cross.source_module) + ".py",
                                        "line": cross.line_number,
                                        "violation": "cross_lobe_import",
                                    }
                                )
                        elif hasattr(result.raw_payload, "modules"):
                            observations.append(
                                {
                                    "type": obs_type,
                                    "result": result.raw_payload.__dict__,
                                }
                            )
                        else:
                            observations.append(
                                {
                                    "type": obs_type,
                                    "result": _coerce_for_json(result.raw_payload),
                                }
                            )

                    files_processed += 1

                    # Track memory every 100 files in chunk mode
                    if files_processed % 100 == 0:
                        memory_monitor.track_files(100)

                except Exception as e:
                    observations.append(
                        {
                            "type": obs_type,
                            "error": f"Error processing {file_path}: {str(e)}",
                        }
                    )

            # Force garbage collection after each chunk
            import gc

            gc.collect()

            # Check memory status
            memory_status = memory_monitor.get_memory_status()
            if memory_status["emergency_save_triggered"]:
                print(
                    "⚠️ Emergency save triggered during chunked observation", flush=True
                )
                break

    def _observe_directory_streaming(
        self,
        directory_path: Path,
        observation_types: list[str],
        session_id: str,
        memory_monitor,
    ) -> dict[str, Any]:
        """
        Observe directory with streaming writes to prevent memory accumulation.

        Constitutional Guarantees:
        - Article 8: Honest performance (reports progress in real-time)
        - Article 9: Immutable observations (each written atomically)
        - Article 13: Deterministic (processes files in sorted order)
        - Article 15: Checkpoints (each file write is a checkpoint)
        """
        from storage.investigation_storage import InvestigationStorage

        # Get storage instance
        storage = InvestigationStorage()

        # Create streaming observation writer
        with storage.create_streaming_observation(session_id) as stream:
            # Check for resume capability
            if stream.can_resume_from(session_id):
                resume_info = stream.resume_from(session_id)
                print(
                    f"[RESUME] Restoring from previous session: {resume_info['files_already_processed']} files already processed",
                    flush=True,
                )
            else:
                print("[STREAM] Starting fresh observation session", flush=True)

            # Get all supported code files in deterministic order (Article 13)
            all_files = self._iter_code_files(directory_path)

            # Skip already processed files if resuming
            start_index = 0
            if hasattr(stream, "files_processed") and stream.files_processed > 0:
                start_index = stream.files_processed
                if start_index >= len(all_files):
                    print(
                        f"[COMPLETE] All {len(all_files)} files were already processed",
                        flush=True,
                    )
                else:
                    print(
                        f"[RESUME] Continuing from file {start_index + 1} of {len(all_files)}",
                        flush=True,
                    )

            print(
                f"[STREAM] Observation: {len(all_files) - start_index} remaining files to process",
                flush=True,
            )

            for idx in range(start_index, len(all_files)):
                file_path = all_files[idx]
                file_observations = []

                for obs_type in observation_types:
                    try:
                        if obs_type in {"import_sight", "export_sight"}:
                            self._observe_import_export_file(
                                file_path,
                                obs_type,
                                file_observations,
                                boundary_crossings=None,
                                check_boundaries=False,
                            )
                            continue

                        # Get appropriate eye
                        eye = self._get_configured_eye(obs_type, directory_path)

                        if eye:
                            result = eye.observe(file_path)

                            # Extract observation data
                            if hasattr(result, "raw_payload") and result.raw_payload:
                                if hasattr(result.raw_payload, "statements"):
                                    # ImportSight
                                    file_observations.append(
                                        {
                                            "type": obs_type,
                                            "statements": [
                                                stmt.__dict__
                                                for stmt in result.raw_payload.statements
                                            ],
                                        }
                                    )
                                elif hasattr(result.raw_payload, "crossings"):
                                    # BoundarySight
                                    file_observations.append(
                                        {
                                            "type": obs_type,
                                            "crossings": [
                                                cross.__dict__
                                                for cross in result.raw_payload.crossings
                                            ],
                                        }
                                    )
                                elif hasattr(result.raw_payload, "modules"):
                                    # FileSight
                                    file_observations.append(
                                        {
                                            "type": obs_type,
                                            "result": result.raw_payload.__dict__,
                                        }
                                    )
                                else:
                                    file_observations.append(
                                        {
                                            "type": obs_type,
                                            "result": _coerce_for_json(
                                                result.raw_payload
                                            ),
                                        }
                                    )
                            else:
                                file_observations.append(
                                    {
                                        "type": obs_type,
                                        "result": result.__dict__
                                        if hasattr(result, "__dict__")
                                        else str(result),
                                    }
                                )
                    except Exception as e:
                        file_observations.append({"type": obs_type, "error": str(e)})

                # Write this file's observations atomically (Article 9 + 15)
                stream.write_file_observation(str(file_path), file_observations)

                # Track memory every 100 files
                if (idx + 1) % 100 == 0:
                    memory_monitor.track_files(100)
                    progress = stream.get_progress()

                    # Honest progress reporting (Article 8)
                    print(
                        f"[PROGRESS] {idx + 1}/{len(all_files)} files, "
                        f"{progress.get('observations_written', 0)} observations written, "
                        f"{memory_monitor.get_memory_status()['current_rss_mb']:.1f}MB",
                        flush=True,
                    )

                    # Check for memory warnings
                    if memory_monitor.should_chunk():
                        print(
                            "[WARNING] Memory pressure detected, continuing with streaming...",
                            flush=True,
                        )

            # Get final progress
            final_progress = stream.get_progress()
            memory_status = memory_monitor.get_memory_status()

            print(
                f"[COMPLETE] Streaming finished: {final_progress['files_processed']} files, "
                f"{final_progress['observations_written']} observations, "
                f"{final_progress['boundary_crossings']} boundary crossings",
                flush=True,
            )

            # Return summary (not the actual observations - they're on disk)
            return {
                "path": str(directory_path),
                "file_count": len(all_files),
                "observations_written": final_progress["observations_written"],
                "boundary_crossings": stream.boundary_crossings,  # Small list for summary
                "memory_usage": memory_status,
                "streaming": True,
                "manifest_id": stream.manifest_id,
                "status": "observed",
            }

    def _get_configured_eye(self, obs_type: str, directory_path: Path):
        """Get configured eye instance for observation type."""
        eye = get_eye(obs_type)

        # Configure boundary_sight with Agent Nexus rules
        if obs_type == "boundary_sight" and eye:
            config_path = Path("config/agent_nexus.yaml")
            if config_path.exists():
                with open(config_path) as f:
                    config = yaml.safe_load(f)

                # Create boundary definitions from config
                boundary_defs = []
                for boundary in config.get("boundaries", []):
                    boundary_type_str = boundary.get("type", "package")
                    from .eyes.boundary_sight import BoundaryType

                    boundary_type_map = {
                        "layer": BoundaryType.LAYER,
                        "package": BoundaryType.PACKAGE,
                        "module": BoundaryType.MODULE,
                        "external": BoundaryType.EXTERNAL,
                        "custom": BoundaryType.CUSTOM,
                    }

                    boundary_defs.append(
                        BoundaryDefinition(
                            name=boundary.get("name"),
                            boundary_type=boundary_type_map.get(
                                boundary_type_str, BoundaryType.PACKAGE
                            ),
                            pattern=boundary.get("pattern"),
                            description=boundary.get("description", ""),
                            allowed_targets=tuple(boundary.get("allowed_targets", [])),
                            prohibited=boundary.get("prohibited", True),
                        )
                    )

                # Return configured BoundarySight
                return BoundarySight(
                    boundary_definitions=boundary_defs, project_root=directory_path
                )

        return eye
