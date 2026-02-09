"""
Lifecycle Authority for CodeMarshal - Supreme Authority of Execution.

Constitutional Basis:
- Article 12: Local Operation
- Article 21: Self-Validation
- Article 13: Deterministic Operation
- Article 1: Observation Purity

Production Responsibility:
Nothing runs unless runtime permits it.
If runtime.py lies, CodeMarshal lies.
"""

from __future__ import annotations

import datetime
import hashlib
import logging
import os
import subprocess
import sys
import traceback
import uuid
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, NoReturn

# Allowed imports per constitutional rules
from core.context import RuntimeContext
from core.engine import Engine
from core.shutdown import TerminationReason, initialize_shutdown, shutdown
from core.state import InvestigationPhase, InvestigationState


class RuntimeInitializationError(Exception):
    """Critical failure during runtime initialization."""

    def __init__(self, message: str, phase: str) -> None:
        super().__init__(message)
        self.message = message
        self.phase = phase
        self.timestamp = datetime.datetime.now(datetime.UTC)

        # Mark as constitutional violation for shutdown
        self.constitutional_violation = True
        self.violation_type = "RUNTIME_INITIALIZATION_FAILURE"


class ConstitutionValidationError(Exception):
    """Constitutional validation failed."""

    def __init__(self, message: str, article: str) -> None:
        super().__init__(message)
        self.message = message
        self.article = article
        self.constitutional_violation = True
        self.violation_type = "CONSTITUTION_VIOLATION"


class ExecutionMode(Enum):
    """Valid execution modes for CodeMarshal."""

    CLI = auto()  # Command-line interface
    TUI = auto()  # Terminal user interface
    API = auto()  # Programmatic API
    EXPORT = auto()  # Export-only mode (no interactive features)

    @classmethod
    def from_string(cls, mode_str: str) -> ExecutionMode:
        """Convert string to execution mode."""
        mode_str_upper = mode_str.upper()
        if mode_str_upper not in cls.__members__:
            raise ValueError(f"Unknown execution mode: {mode_str}")
        return cls[mode_str_upper]


@dataclass(frozen=True)
class RuntimeConfiguration:
    """Immutable configuration for runtime initialization."""

    investigation_root: Path
    execution_mode: ExecutionMode
    constitution_path: Path
    code_root: Path
    session_id_override: str | None = None

    # Enforcement flags
    network_enabled: bool = False  # Article 12: Local Operation
    allow_mutation: bool = False  # Article 9: Immutable Observations
    allow_runtime_imports: bool = False  # Article 1: Observation Purity

    def validate(self) -> None:
        """Validate runtime configuration."""
        if not self.investigation_root.exists():
            raise RuntimeInitializationError(
                f"Investigation root does not exist: {self.investigation_root}",
                "configuration_validation",
            )

        if not self.investigation_root.is_dir():
            raise RuntimeInitializationError(
                f"Investigation root is not a directory: {self.investigation_root}",
                "configuration_validation",
            )

        if not self.constitution_path.exists():
            raise RuntimeInitializationError(
                f"Constitution file not found: {self.constitution_path}",
                "configuration_validation",
            )

        if not self.code_root.exists():
            raise RuntimeInitializationError(
                f"Code root does not exist: {self.code_root}",
                "configuration_validation",
            )


class Runtime:
    """
    Supreme authority of execution for CodeMarshal.

    Constitutional Guarantees:
    1. No partial execution - either fully initialized or not at all
    2. No degraded mode without explicit explanation
    3. Tier 1 violations cause immediate halt
    4. Deterministic behavior across runs
    5. Complete separation of concerns
    """

    def __init__(self, config: RuntimeConfiguration) -> None:
        """
        Initialize runtime with validation but don't start execution.

        Args:
            config: Validated runtime configuration

        Raises:
            RuntimeInitializationError: If any initialization step fails
            ConstitutionValidationError: If constitutional validation fails
        """
        self._config = config
        self._logger = self._create_logger()

        # Initialize in order
        try:
            self._logger.info("Initializing CodeMarshal Runtime...")

            # Phase 1: Constitution Validation
            self._validate_constitution()

            # Phase 2: Create Runtime Context (immutable)
            self._context = self._create_runtime_context()

            # Phase 3: Initialize Shutdown System
            initialize_shutdown(self._context)

            # Phase 4: Activate Runtime Prohibitions
            self._activate_prohibitions()

            # Phase 5: Verify Constitutional Integrity
            self._verify_integrity()

            # Phase 6: Initialize State Machine
            self._state = InvestigationState(self._context)

            # Phase 7: Create Engine
            self._engine = Engine(self._context, self._state)

            # Phase 7.5: Register Layer Interfaces
            self._register_layer_interfaces()

            # Phase 8: Mark as initialized
            self._initialized = True
            self._execution_started = False

            self._logger.info(
                f"Runtime initialized successfully (mode={self._config.execution_mode.name})"
            )

        except Exception as e:
            # Convert any exception during initialization to RuntimeInitializationError
            if not isinstance(
                e, (RuntimeInitializationError, ConstitutionValidationError)
            ):
                error_msg = f"Runtime initialization failed: {e}"
                self._logger.critical(error_msg, exc_info=True)
                raise RuntimeInitializationError(error_msg, "initialization") from e
            raise

    def start_investigation(
        self,
        target_path: Path,
        session_id: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Start a new investigation session.

        This delegates to the engine to perform the actual work.
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")

        self._execution_started = True

        # Delegate to engine
        return self._engine.start_investigation(
            target_path=target_path, session_id=session_id, parameters=parameters or {}
        )

    def _create_logger(self) -> logging.Logger:
        """Create isolated runtime logger."""
        logger = logging.getLogger("codemarshal.runtime")

        if not logger.handlers:
            # Set up basic console logging for runtime initialization
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s [RUNTIME] %(levelname)s: %(message)s",
                    datefmt="%H:%M:%S",
                )
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

        return logger

    def _validate_constitution(self) -> None:
        """Validate constitutional rules are present and accessible."""
        self._logger.debug("Validating constitution...")

        try:
            # Read constitution file
            with open(self._config.constitution_path, encoding="utf-8") as f:
                constitution_text = f.read()

            # Basic validation - ensure it contains core articles
            required_articles = [
                "Article 1: Observation Purity",
                "Article 2: Human Primacy",
                "Article 3: Truth Preservation",
                "Article 4: Progressive Disclosure",
            ]

            missing_articles = []
            for article in required_articles:
                if article not in constitution_text:
                    missing_articles.append(article)

            if missing_articles:
                raise ConstitutionValidationError(
                    f"Constitution missing required articles: {missing_articles}",
                    "TIER 1",
                )

            self._logger.debug("Constitution validation passed")

        except OSError as e:
            raise RuntimeInitializationError(
                f"Failed to read constitution file: {e}", "constitution_validation"
            ) from e

    def _create_runtime_context(self) -> RuntimeContext:
        """Create immutable runtime context."""
        self._logger.debug("Creating runtime context...")

        try:
            # Calculate constitution hash
            constitution_hash = self._calculate_file_hash(
                self._config.constitution_path
            )

            # Calculate code version hash (hash of code root)
            code_version_hash = self._calculate_code_version_hash(
                self._config.code_root
            )

            # Generate session ID
            session_id = self._generate_session_id()

            # Get current timestamp
            start_timestamp = datetime.datetime.now(datetime.UTC)

            # Create context
            from core.context import RuntimeContext

            context = RuntimeContext(
                investigation_root=self._config.investigation_root.resolve(),
                constitution_hash=constitution_hash,
                code_version_hash=code_version_hash,
                execution_mode=self._config.execution_mode.name,
                network_enabled=self._config.network_enabled,
                mutation_allowed=self._config.allow_mutation,
                runtime_imports_allowed=self._config.allow_runtime_imports,
                session_id=session_id,
                start_timestamp=start_timestamp,
            )

            self._logger.debug(f"Runtime context created (session={session_id})")
            return context

        except Exception as e:
            raise RuntimeInitializationError(
                f"Failed to create runtime context: {e}", "context_creation"
            ) from e

    def _calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256 = hashlib.sha256()

        try:
            with open(filepath, "rb") as f:
                # Read in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
        except OSError as e:
            raise RuntimeInitializationError(
                f"Failed to calculate file hash for {filepath}: {e}", "hash_calculation"
            ) from e

        return sha256.hexdigest()

    def _calculate_code_version_hash(self, code_root: Path) -> str:
        git_dir = code_root / ".git"
        if git_dir.exists() and git_dir.is_dir():
            try:
                return self._calculate_git_hash(code_root)
            except Exception:
                return self._calculate_lightweight_code_hash(code_root)
        return self._calculate_lightweight_code_hash(code_root)

    def _calculate_git_hash(self, repo_root: Path) -> str:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            stderr=subprocess.DEVNULL,
            text=True,
        )
        sha256 = hashlib.sha256()
        sha256.update(head.encode("utf-8"))
        sha256.update(status.encode("utf-8"))
        return sha256.hexdigest()

    def _calculate_lightweight_code_hash(self, code_root: Path) -> str:
        """Calculate a deterministic hash of relevant code/config files.

        This avoids a full repository scan, which can be extremely slow on Windows.
        The goal is version tracking for the runtime context, not content addressing
        of every artifact under the root.
        """
        sha256 = hashlib.sha256()

        allow_suffixes = {".py", ".md", ".toml", ".txt"}
        # Keep the pruning list conservative (performance win without changing behavior).
        skip_dir_names = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "dist",
            "build",
        }

        unique: dict[str, Path] = {}

        for root, dirs, files in os.walk(code_root):
            dirs[:] = [
                d for d in dirs if d not in skip_dir_names and not d.startswith(".")
            ]

            root_path = Path(root)
            for name in files:
                p = root_path / name
                if p.suffix not in allow_suffixes:
                    continue
                try:
                    rel = str(p.relative_to(code_root))
                except Exception:
                    continue
                unique[rel] = p

        for rel_path in sorted(unique.keys()):
            filepath = unique[rel_path]
            try:
                stat = filepath.stat()
            except (FileNotFoundError, PermissionError):
                continue
            sha256.update(rel_path.encode("utf-8"))
            sha256.update(str(stat.st_size).encode("utf-8"))
            sha256.update(str(int(stat.st_mtime)).encode("utf-8"))

        return sha256.hexdigest()

    def _calculate_directory_hash(self, directory: Path) -> str:
        """
        Calculate deterministic hash of directory structure and file contents.

        Constitutional Basis: Article 13 (Deterministic Operation)
        """
        sha256 = hashlib.sha256()

        # Sort files for deterministic hashing
        files = []
        for f in directory.rglob("*"):
            if not f.is_file():
                continue

            # Skip pycache and hidden files
            parts = f.parts
            if any(p == "__pycache__" or p.startswith(".") for p in parts):
                continue

            files.append(f)

        files.sort(key=lambda x: str(x.relative_to(directory)))

        for filepath in files:
            try:
                # Add relative path to hash
                rel_path = str(filepath.relative_to(directory))
                sha256.update(rel_path.encode("utf-8"))

                # Add file size
                stat = filepath.stat()
                sha256.update(str(stat.st_size).encode("utf-8"))

                # Add modification time (for versioning)
                mtime = int(stat.st_mtime)
                sha256.update(str(mtime).encode("utf-8"))
            except (FileNotFoundError, PermissionError):
                # Skip files that disappear or are inaccessible
                continue

        return sha256.hexdigest()

    def _generate_session_id(self) -> str:
        """Generate deterministic session ID based on configuration."""
        import uuid

        if self._config.session_id_override:
            return self._config.session_id_override

        # Create deterministic UUID from configuration
        base_string = (
            f"{self._config.investigation_root}"
            f"{self._config.execution_mode.name}"
        )

        namespace = uuid.uuid5(uuid.NAMESPACE_DNS, "codemarshal.internal")
        return str(uuid.uuid5(namespace, base_string))

    def _register_layer_interfaces(self) -> None:
        """Register layer interfaces with the engine (dependency injection)."""
        self._logger.debug("Registering layer interfaces via dependency injection...")

        # Interfaces must be injected from bridge layer
        # Core layer does NOT import from higher layers (Article 9)
        pass

    def _activate_prohibitions(self) -> None:
        """
        Activate runtime prohibitions per constitutional rules.

        Note: Prohibition enforcement is handled at the integrity layer.
        Core layer only records the configuration. This preserves
        architectural layering (Article 9: Immutable Observations).
        """
        self._logger.debug("Activating runtime prohibitions...")

        # Core layer only validates configuration, doesn't enforce prohibitions
        # Enforcement happens at integrity layer via dependency injection
        # This preserves architectural purity: core doesn't depend on integrity

        if not self._config.network_enabled:
            self._logger.debug("Network access disabled per configuration")

        if not self._config.allow_runtime_imports:
            self._logger.debug("Runtime imports disabled per configuration")

        if not self._config.allow_mutation:
            self._logger.debug("Observation mutation disabled per configuration")

        self._logger.debug("Runtime prohibition configuration recorded")

    def _verify_integrity(self) -> None:
        """
        Verify constitutional integrity before execution.

        Note: Full integrity validation is handled at the integrity layer.
        Core layer performs basic self-checks only. This preserves
        architectural layering (Article 9: Immutable Observations).
        """
        self._logger.debug("Verifying constitutional integrity...")

        try:
            # Core layer performs basic self-validation only
            # Full integrity checks are done at integrity layer via dependency injection

            # Basic validation: ensure context is valid
            if not self._context:
                raise ConstitutionValidationError(
                    "Runtime context is invalid", "TIER_1"
                )

            # Basic validation: ensure configuration matches context
            if self._context.network_enabled != self._config.network_enabled:
                raise ConstitutionValidationError(
                    "Context network_enabled mismatch with configuration", "TIER_1"
                )

            if self._context.mutation_allowed != self._config.allow_mutation:
                raise ConstitutionValidationError(
                    "Context mutation_allowed mismatch with configuration", "TIER_1"
                )

            self._logger.debug("Basic constitutional integrity verified")

        except Exception as e:
            if isinstance(e, ConstitutionValidationError):
                raise
            raise RuntimeInitializationError(
                f"Integrity verification failed: {e}", "integrity_verification"
            ) from e

    def execute(self) -> None:
        """
        Execute the full investigation lifecycle.

        Constitutional Guarantee: Linear investigation enforced.
        No partial execution - either completes fully or fails completely.
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")

        if self._execution_started:
            raise RuntimeError("Runtime execution already started")

        self._execution_started = True

        try:
            self._logger.info("Starting investigation execution...")

            # Step 1: Transition to ENFORCEMENT_ACTIVE
            self._state.transition_to(
                InvestigationPhase.ENFORCEMENT_ACTIVE,
                reason="Runtime execution started",
            )

            # Step 2: Execute investigation via engine
            self._engine.execute_investigation()

            # Step 3: Check final state
            if self._state.current_phase.is_terminal():
                exit_code = (
                    0
                    if self._state.current_phase == InvestigationPhase.TERMINATED_NORMAL
                    else 1
                )
                self._logger.info(
                    f"Investigation completed with terminal state: {self._state.current_phase.name}"
                )
            else:
                # This should never happen - engine should always reach terminal state
                self._logger.error(
                    f"Investigation ended in non-terminal state: {self._state.current_phase.name}"
                )
                self._state.force_transition(
                    InvestigationPhase.TERMINATED_ERROR,
                    reason="Engine returned without reaching terminal state",
                )
                exit_code = 1

            # Step 4: Normal shutdown
            shutdown(reason=TerminationReason.NORMAL_COMPLETION, exit_code=exit_code)

        except Exception as e:
            # Convert any execution exception to proper shutdown
            self._handle_execution_error(e)

    def execute_observation_only(self) -> dict[str, Any]:
        """
        Execute only the observation phase and return results.

        For use by witness command-line interface.
        Constitutional Basis: Article 4 (Progressive Disclosure)
        """
        if not self._initialized:
            raise RuntimeError("Runtime not initialized")

        if self._execution_started:
            raise RuntimeError("Runtime execution already started")

        self._execution_started = True

        try:
            self._logger.info("Starting observation-only execution...")

            # Transition to ENFORCEMENT_ACTIVE
            self._state.transition_to(
                InvestigationPhase.ENFORCEMENT_ACTIVE,
                reason="Observation-only execution started",
            )

            # Execute observation phase via engine
            observations = self._engine.execute_observations_only()

            # Transition to OBSERVATION_COMPLETE
            self._state.transition_to(
                InvestigationPhase.OBSERVATION_COMPLETE,
                reason="Observations collected successfully",
            )

            self._logger.info(
                f"Observation phase completed: {len(observations)} observations"
            )

            # Return observations
            return {
                "observations": observations,
                "session_id": str(self._context.session_id),
                "constitution_hash": self._context.constitution_hash,
                "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            }

        except Exception as e:
            self._handle_execution_error(e)

    def _handle_execution_error(self, error: Exception) -> NoReturn:
        """Handle execution error and initiate proper shutdown."""
        self._logger.critical(f"Execution error: {error}", exc_info=True)

        # Determine termination reason
        if isinstance(error, ConstitutionValidationError):
            reason = TerminationReason.CONSTITUTIONAL_VIOLATION
            exit_code = 2
        else:
            reason = TerminationReason.SYSTEM_ERROR
            exit_code = 1

        # Get error info for shutdown
        error_info = (error, traceback.format_exc())

        # Force state to terminal if needed
        if not self._state.current_phase.is_terminal():
            try:
                terminal_phase = (
                    InvestigationPhase.TERMINATED_VIOLATION
                    if reason == TerminationReason.CONSTITUTIONAL_VIOLATION
                    else InvestigationPhase.TERMINATED_ERROR
                )
                self._state.force_transition(
                    terminal_phase, reason=f"Execution error: {error}"
                )
            except Exception as state_error:
                self._logger.error(f"Failed to transition state: {state_error}")

        # Initiate shutdown
        shutdown(reason, exit_code, error_info)

    @property
    def context(self) -> RuntimeContext:
        """Get runtime context (read-only)."""
        return self._context

    @property
    def state(self) -> InvestigationState:
        """Get investigation state (read-only)."""
        return self._state

    @property
    def engine(self) -> Engine:
        """Get engine instance (read-only)."""
        return self._engine

    def resume_investigation(
        self, session_id: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Resume an existing investigation session."""
        self._logger.info(f"Resuming investigation: {session_id}")

        # In a real implementation, this would:
        # 1. Load existing session state
        # 2. Validate session can be resumed
        # 3. Update with new parameters
        # For now, return a mock session result

        return {
            "session_id": session_id,
            "status": "resumed",
            "resumed_at": datetime.now(datetime.UTC).isoformat(),
        }

    def fork_investigation(
        self, source_session_id: str, target_path: str, parameters: dict[str, Any]
    ) -> dict[str, Any]:
        """Fork an existing investigation session."""
        self._logger.info(
            f"Forking investigation: {source_session_id} -> {target_path}"
        )

        # In a real implementation, this would:
        # 1. Copy source session state
        # 2. Create new session with copied state
        # 3. Initialize tracking for fork
        # For now, return a mock session result

        return {
            "session_id": str(uuid.uuid4()),
            "status": "forked",
            "source_session_id": source_session_id,
            "target_path": target_path,
            "forked_at": datetime.now(datetime.UTC).isoformat(),
        }

    @property
    def at_capacity(self) -> bool:
        """Check if system is at capacity for new investigations."""
        # Simple capacity check - limit concurrent investigations
        # In a real implementation, this might check:
        # - Memory usage
        # - Active session count
        # - System resources
        # For now, always return False (no capacity limits)
        return False

    def __repr__(self) -> str:
        """Machine-readable representation."""
        status = "INITIALIZED" if self._initialized else "UNINITIALIZED"
        started = "STARTED" if self._execution_started else "NOT_STARTED"
        return f"Runtime(status={status}, execution={started}, mode={self._config.execution_mode.name})"


# Public API for creating and running runtime
def create_runtime(
    investigation_root: Path,
    execution_mode: str = "CLI",
    constitution_path: Path | None = None,
    code_root: Path | None = None,
    **kwargs,
) -> Runtime:
    """
    Create and initialize a runtime instance.

    Constitutional Basis: Article 12 (Local Operation)
    All paths must be local filesystem paths.

    Args:
        investigation_root: Path to investigate
        execution_mode: One of "CLI", "TUI", "API", "EXPORT"
        constitution_path: Optional path to constitution file
        code_root: Optional path to CodeMarshal source code
        **kwargs: Additional configuration options

    Returns:
        Initialized Runtime instance

    Raises:
        RuntimeInitializationError: If initialization fails
        ConstitutionValidationError: If constitutional validation fails
    """
    # Set default paths if not provided
    if constitution_path is None:
        # Look for constitution in code root or current directory
        potential_paths = [
            Path(__file__).parent.parent / "constitution.truth.md",
            Path.cwd() / "constitution.truth.md",
        ]

        for path in potential_paths:
            if path.exists():
                constitution_path = path
                break

        if constitution_path is None:
            raise RuntimeInitializationError(
                "Constitution file not found and no path provided", "path_resolution"
            )

    if code_root is None:
        # Default to parent of runtime.py
        code_root = Path(__file__).parent.parent

    # Create configuration
    config = RuntimeConfiguration(
        investigation_root=investigation_root,
        execution_mode=ExecutionMode.from_string(execution_mode),
        constitution_path=constitution_path,
        code_root=code_root,
        **kwargs,
    )

    # Validate configuration
    config.validate()

    # Create and return runtime
    return Runtime(config)


def execute_witness_command(investigation_path: Path) -> dict[str, Any]:
    """
    Execute the witness command-line interface.

    Constitutional Basis: Article 1 (Observation Purity)
    Outputs only what is textually present in source code.

    Args:
        investigation_path: Path to investigate

    Returns:
        Dictionary containing observations and metadata

    Raises:
        SystemExit: If execution fails (via shutdown)
    """
    try:
        # Create runtime for CLI mode
        runtime = create_runtime(
            investigation_root=investigation_path,
            execution_mode="CLI",
            network_enabled=False,
            allow_mutation=False,
            allow_runtime_imports=False,
        )

        # Execute observation-only mode
        return runtime.execute_observation_only()

    except (RuntimeInitializationError, ConstitutionValidationError) as e:
        # These are initialization errors, not execution errors
        print(f"Initialization failed: {e}", file=sys.stderr)

        if isinstance(e, ConstitutionValidationError):
            shutdown(
                TerminationReason.CONSTITUTIONAL_VIOLATION,
                exit_code=2,
                error_info=(e, traceback.format_exc()),
            )
        else:
            shutdown(
                TerminationReason.SYSTEM_ERROR,
                exit_code=1,
                error_info=(e, traceback.format_exc()),
            )
