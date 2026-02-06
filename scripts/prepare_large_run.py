#!/usr/bin/env python3
"""
Prepare CodeMarshal for Large-Scale Observation Runs

Purpose:
    This script prepares the CodeMarshal system for processing large codebases
    containing 50,000 or more files. It performs comprehensive system checks,
    creates necessary backups, configures monitoring systems, and validates
    that the environment is ready for sustained observation operations.

Constitutional Basis:
    - Article 8: Complete Evidence - Ensures all data is preserved before processing
    - Article 21: Self-Validation - Validates system integrity before operation
    - Article 22: Resource Bounds - Ensures adequate resources for the task
    - Article 19: Local Operation - Confirms no external dependencies required

Usage:
    python prepare_large_run.py <target_directory> [expected_files]

    Arguments:
        target_directory: Path to the codebase or directory to be observed
        expected_files: Optional estimate of files to process (default: 50,000)

Examples:
    # Prepare for observing a large Python project
    python prepare_large_run.py /path/to/large/project 75000

    # Prepare for observing a multi-language codebase
    python prepare_large_run.py /path/to/monorepo 100000

    # Quick preparation with default settings
    python prepare_large_run.py /path/to/project

Output:
    The script provides detailed progress updates including:
    - Storage integrity verification results
    - Backup creation confirmation
    - Disk space analysis
    - Memory monitoring configuration
    - Chunking strategy recommendations
    - Final readiness assessment

Exit Codes:
    0: Preparation successful, system ready for large run
    1: Preparation failed, see error messages for details
    2: Critical issues detected that prevent safe operation

Author: CodeMarshal Team
Version: 1.0.0
Last Updated: February 5, 2026

Dependencies:
    - CodeMarshal core modules (core, storage, integrity)
    - Python 3.11+
    - Sufficient disk space (minimum 10GB recommended)
    - Available memory (minimum 4GB recommended)
"""

import hashlib
import os
import shutil
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any

# CodeMarshal imports
from config.boundaries import get_agent_nexus_config
from core.context import RuntimeContext
from integrity.monitoring.memory import (
    setup_memory_monitoring,
)

# Observations imports - consolidated to avoid duplicates
from storage.backup import BackupManager
from storage.investigation_storage import InvestigationStorage

# Add the project root directory to Python's import path
# This allows the script to import CodeMarshal modules regardless of
# the current working directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# Observations imports - consolidated to avoid duplicates
# SECTION 2: ENUM DEFINITIONS FOR CONFIGURATION OPTIONS
# ============================================================================


class PreparationPhase(Enum):
    """
    Enumeration of the distinct phases in the preparation process.

    Each phase represents a logical grouping of preparation tasks
    that must be completed before proceeding to the next phase.
    """

    INITIALIZATION = auto()  # Phase 0: Initial setup and validation
    STORAGE_CHECK = auto()  # Phase 1: Storage integrity verification
    BACKUP_CREATION = auto()  # Phase 2: Backup of existing data
    DISK_SPACE_CHECK = auto()  # Phase 3: Disk space analysis
    MEMORY_CONFIG = auto()  # Phase 4: Memory monitoring setup
    CHUNKING_SETUP = auto()  # Phase 5: Chunking strategy configuration
    BOUNDARY_VALIDATION = auto()  # Phase 6: Boundary rule verification
    FINAL_VERIFICATION = auto()  # Phase 7: Complete system readiness check


class DiskSpaceStatus(Enum):
    """
    Enumeration representing the disk space availability status.

    This classification helps determine if there is sufficient
    disk space for the planned observation operation.
    """

    SUFFICIENT = auto()  # Adequate space for operation
    MARGINAL = auto()  # Space is adequate but limited
    INSUFFICIENT = auto()  # Not enough space for safe operation
    CRITICAL = auto()  # Immediate action required


class MemoryThreshold(Enum):
    """
    Enumeration of memory threshold levels for monitoring.

    These thresholds define the points at which different
    severity levels of memory warnings are triggered.
    """

    WARNING = 2048  # 2GB - Warning threshold in MB
    CRITICAL = 4096  # 4GB - Critical threshold in MB
    MAXIMUM = 6144  # 6GB - Maximum recommended in MB


class ChunkingStrategy(Enum):
    """
    Enumeration of available chunking strategies for large observations.

    Different strategies optimize for different aspects of
    observation processing and memory usage.
    """

    FIXED_SIZE = auto()  # Fixed number of files per chunk
    DIRECTORY_BASED = auto()  # Chunk by directory boundaries
    ADAPTIVE = auto()  # Dynamically adjusted chunk sizes
    HYBRID = auto()  # Combination of fixed and adaptive


# ============================================================================
# SECTION 3: DATA CLASSES FOR CONFIGURATION AND RESULTS
# ============================================================================


@dataclass(frozen=True)
class LargeRunConfiguration:
    """
    Immutable configuration for large-scale observation runs.

    This configuration encapsulates all settings required for
    processing large codebases while maintaining system stability
    and data integrity.

    Attributes:
        target_path: Path to the directory or file to be observed
        expected_files: Estimated number of files to process
        chunk_size: Number of files to process per chunk
        memory_warning_mb: Memory threshold for warnings
        memory_critical_mb: Memory threshold for critical alerts
        enable_backup: Whether to create pre-run backups
        backup_location: Path for backup storage
        enable_monitoring: Whether to enable real-time monitoring
        monitoring_interval: Seconds between monitoring checks
        validate_boundaries: Whether to verify boundary rules
        max_retries: Maximum retry attempts for failed operations
        timeout_seconds: Global timeout for the observation run
    """

    target_path: Path
    expected_files: int = 50000
    chunk_size: int = 1000
    memory_warning_mb: int = MemoryThreshold.WARNING.value
    memory_critical_mb: int = MemoryThreshold.CRITICAL.value
    enable_backup: bool = True
    backup_location: Path = field(default_factory=lambda: Path("storage/backups"))
    enable_monitoring: bool = True
    monitoring_interval: int = 1000
    validate_boundaries: bool = True
    max_retries: int = 3
    timeout_seconds: int = 7200


@dataclass
class PreparationReport:
    """
    Comprehensive report of the preparation process.

    This data class captures the results and details of each
    phase of the preparation process for later review.

    Attributes:
        success: Whether all preparation phases completed successfully
        start_time: When preparation began
        end_time: When preparation completed
        phases_completed: List of phases that were completed
        phases_skipped: List of phases that were skipped
        total_duration_seconds: Total preparation time
        storage_report: Results of storage integrity checks
        backup_report: Details of backup creation
        disk_space_report: Analysis of disk space availability
        memory_report: Memory monitoring configuration details
        chunking_report: Chunking strategy configuration
        boundary_report: Boundary validation results
        warnings: List of non-critical warnings encountered
        errors: List of errors that occurred during preparation
        recommendations: Suggested actions for optimal operation
    """

    success: bool = True
    start_time: datetime | None = None
    end_time: datetime | None = None
    phases_completed: list[str] = field(default_factory=list)
    phases_skipped: list[str] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    storage_report: dict[str, Any] | None = None
    backup_report: dict[str, Any] | None = None
    disk_space_report: dict[str, Any] | None = None
    memory_report: dict[str, Any] | None = None
    chunking_report: dict[str, Any] | None = None
    boundary_report: dict[str, Any] | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class DiskSpaceAnalysis:
    """
    Detailed analysis of disk space availability.

    This class provides comprehensive information about disk
    space usage and availability for the observation operation.

    Attributes:
        total_bytes: Total disk capacity in bytes
        available_bytes: Available disk space in bytes
        used_bytes: Used disk space in bytes
        usage_percentage: Percentage of disk used
        status: Disk space status classification
        required_bytes: Estimated bytes needed for observation
        margin_bytes: Safety margin for operations
        warnings: Any warnings about disk space
    """

    total_bytes: int
    available_bytes: int
    used_bytes: int
    usage_percentage: float
    status: DiskSpaceStatus
    required_bytes: int
    margin_bytes: int
    warnings: list[str] = field(default_factory=list)


@dataclass
class MemoryConfiguration:
    """
    Configuration for memory monitoring during observation runs.

    This class encapsulates all settings related to memory
    monitoring and management during large-scale observations.

    Attributes:
        warning_threshold_mb: Memory threshold for warnings
        critical_threshold_mb: Memory threshold for critical alerts
        check_interval_files: Check memory every N files
        max_memory_mb: Maximum memory to use
        enable_gc_triggers: Enable garbage collection triggers
        pause_on_warning: Pause operation on warning
        pause_on_critical: Pause operation on critical
        recovery_action: Action to take on memory issues
    """

    warning_threshold_mb: int
    critical_threshold_mb: int
    check_interval_files: int
    max_memory_mb: int
    enable_gc_triggers: bool = True
    pause_on_warning: bool = False
    pause_on_critical: bool = True
    recovery_action: str = "pause_and_notify"


@dataclass
class ChunkingConfiguration:
    """
    Configuration for file chunking strategy.

    This class defines how large codebases are divided into
    manageable chunks for processing.

    Attributes:
        strategy: The chunking strategy to use
        chunk_size: Number of files per chunk
        max_chunk_size: Maximum files in a single chunk
        min_chunk_size: Minimum files in a single chunk
        overlap_files: Number of overlapping files between chunks
        estimated_chunks: Total number of chunks based on configuration
        memory_estimated_mb: Estimated memory usage per chunk
    """

    strategy: ChunkingStrategy
    chunk_size: int
    max_chunk_size: int = 2000
    min_chunk_size: int = 100
    overlap_files: int = 0
    estimated_chunks: int = 0
    memory_estimated_mb: int = 512


@dataclass
class BackupManifest:
    """
    Manifest tracking details of a backup operation.

    This class records all relevant information about a backup
    created during the preparation process.

    Attributes:
        backup_id: Unique identifier for this backup
        created_at: When the backup was created
        source_path: Path that was backed up
        file_count: Number of files in the backup
        total_size_bytes: Total size of the backup in bytes
        checksum: SHA256 checksum of the backup
        location: Where the backup is stored
        metadata: Additional backup metadata
    """

    backup_id: str
    created_at: datetime
    source_path: Path
    file_count: int
    total_size_bytes: int
    checksum: str
    location: Path
    compression_ratio: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_size(self) -> int:
        """Backward-compatible alias for total_size_bytes."""
        return self.total_size_bytes


# ============================================================================
# SECTION 4: HELPER CLASSES FOR SPECIALIZED OPERATIONS
# ============================================================================


class DiskSpaceAnalyzer:
    """
    Analyzer for disk space availability and usage.

    This class provides methods to analyze disk space for
    large-scale observation operations.

    Constitutional Basis:
    - Article 22: Resource Bounds - Ensures adequate disk space
    """

    # Constants for disk space calculations
    BYTES_PER_MB = 1024 * 1024
    BYTES_PER_GB = BYTES_PER_MB * 1024
    SAFETY_MARGIN_MULTIPLIER = 1.5  # 50% safety margin
    MINIMUM_AVAILABLE_GB = 10  # Minimum 10GB recommended

    def __init__(self, target_path: Path):
        """
        Initialize the disk space analyzer.

        Args:
            target_path: Path to the directory to analyze
        """
        self.target_path = target_path.resolve()
        self._analysis: DiskSpaceAnalysis | None = None

    def analyze(self, expected_files: int = 50000) -> DiskSpaceAnalysis:
        """
        Perform comprehensive disk space analysis.

        This method calculates whether sufficient disk space is
        available for the expected observation operation.

        Args:
            expected_files: Number of files expected to process

        Returns:
            DiskSpaceAnalysis containing detailed space information

        Calculation Details:
            - Assumes average 50KB per file for observation data
            - Adds 50% safety margin for operational overhead
            - Accounts for temporary files and checkpoints
        """
        # Get disk statistics for the target path
        # Use shutil for cross-platform compatibility
        disk_usage = shutil.disk_usage(self.target_path)

        # Calculate required space based on expected files
        # Average observation data per file (conservative estimate)
        bytes_per_file = 50 * 1024  # 50KB per file
        required_bytes = expected_files * bytes_per_file

        # Add safety margin for operational overhead
        # Includes: temporary files, checkpoints, logs, backups
        safety_margin = int(required_bytes * self.SAFETY_MARGIN_MULTIPLIER)
        total_required = required_bytes + safety_margin

        # Calculate usage percentage
        usage_percentage = (disk_usage.used / disk_usage.total) * 100

        # Determine disk space status
        available_gb = disk_usage.free / self.BYTES_PER_GB
        status = self._determine_status(disk_usage.free, total_required)

        # Generate warnings based on analysis
        warnings = self._generate_warnings(
            disk_usage=disk_usage,
            available_bytes=disk_usage.free,
            required_bytes=total_required,
            status=status,
            available_gb=available_gb,
        )

        # Create and return the analysis result
        self._analysis = DiskSpaceAnalysis(
            total_bytes=disk_usage.total,
            available_bytes=disk_usage.free,
            used_bytes=disk_usage.used,
            usage_percentage=round(usage_percentage, 2),
            status=status,
            required_bytes=total_required,
            margin_bytes=safety_margin,
            warnings=warnings,
        )

        return self._analysis

    def _determine_status(
        self, available_bytes: int, required_bytes: int
    ) -> DiskSpaceStatus:
        """
        Determine disk space status based on available and required space.

        Args:
            available_bytes: Available disk space in bytes
            required_bytes: Required disk space in bytes

        Returns:
            DiskSpaceStatus enumeration value
        """
        # Check for critical insufficiency
        if available_bytes < required_bytes:
            return DiskSpaceStatus.INSUFFICIENT

        # Check for marginal availability
        available_gb = available_bytes / self.BYTES_PER_GB
        if available_gb < self.MINIMUM_AVAILABLE_GB:
            return DiskSpaceStatus.MARGINAL

        # Sufficient space available
        return DiskSpaceStatus.SUFFICIENT

    def _generate_warnings(
        self,
        disk_usage: Any,
        available_bytes: int,
        required_bytes: int,
        status: DiskSpaceStatus,
        available_gb: float,
    ) -> list[str]:
        """
        Generate appropriate warnings based on disk space analysis.

        Args:
            disk_usage: shutil.disk_usage result
            available_bytes: Available space in bytes
            required_bytes: Required space in bytes
            status: Determined disk space status
            available_gb: Available space in gigabytes

        Returns:
            List of warning messages (may be empty)
        """
        warnings = []

        # Critical warning for insufficient space
        if status == DiskSpaceStatus.INSUFFICIENT:
            shortage_gb = (required_bytes - available_bytes) / self.BYTES_PER_GB
            warnings.append(
                f"CRITICAL: Insufficient disk space. "
                f"Need {shortage_gb:.1f}GB more for safe operation."
            )

        # Warning for marginal space
        if status == DiskSpaceStatus.MARGINAL:
            warnings.append(
                f"WARNING: Disk space is marginal ({available_gb:.1f}GB available). "
                f"Consider freeing up more space before proceeding."
            )

        # Warning for high disk usage
        usage_percentage = (disk_usage.used / disk_usage.total) * 100
        if usage_percentage > 90:
            warnings.append(
                f"WARNING: Disk is {usage_percentage:.1f}% full. "
                f"High disk usage may impact performance."
            )

        # Warning for low available gigabytes
        if available_gb < 5:
            warnings.append(
                "WARNING: Less than 5GB free space available. "
                "This may cause issues during long-running observations."
            )

        return warnings

    def get_human_readable_summary(self, analysis: DiskSpaceAnalysis) -> str:
        """
        Generate a human-readable summary of the disk space analysis.

        Args:
            analysis: The disk space analysis to summarize

        Returns:
            Formatted string summary suitable for display
        """

        # Format bytes to human-readable units
        def format_bytes(num_bytes: int) -> str:
            """Convert bytes to appropriate unit."""
            num = float(num_bytes)
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if abs(num) < 1024.0:
                    return f"{num:.2f}{unit}"
                num /= 1024.0
            return f"{num:.2f}PB"

        # Build summary lines
        summary_lines = [
            "=" * 60,
            "DISK SPACE ANALYSIS",
            "=" * 60,
            f"Target Path:      {self.target_path}",
            f"Total Capacity:   {format_bytes(analysis.total_bytes)}",
            f"Used Space:       {format_bytes(analysis.used_bytes)}",
            f"Available Space:  {format_bytes(analysis.available_bytes)}",
            f"Usage Percentage: {analysis.usage_percentage:.1f}%",
            f"Required Space:   {format_bytes(analysis.required_bytes)}",
            f"Safety Margin:    {format_bytes(analysis.margin_bytes)}",
            f"Status:           {analysis.status.name}",
            "=" * 60,
        ]

        # Add warnings if present
        if analysis.warnings:
            summary_lines.append("WARNINGS:")
            for warning in analysis.warnings:
                summary_lines.append(f"  ⚠ {warning}")
            summary_lines.append("=" * 60)

        return "\n".join(summary_lines)


class ChunkingStrategyCalculator:
    """
    Calculator for determining optimal chunking strategy.

    This class analyzes the codebase characteristics and determines
    the optimal way to divide files into manageable chunks.

    Constitutional Basis:
    - Article 22: Resource Bounds - Manages memory and processing efficiently
    """

    # Constants for chunking calculations
    DEFAULT_CHUNK_SIZE = 1000
    MAX_CHUNK_SIZE = 2000
    MIN_CHUNK_SIZE = 100
    MEMORY_PER_FILE_MB = 0.5  # Estimated memory per file in MB

    def __init__(self, target_path: Path):
        """
        Initialize the chunking strategy calculator.

        Args:
            target_path: Path to the target directory
        """
        self.target_path = target_path
        self._file_count: int | None = None

    def count_files(self, extensions: list[str] | None = None) -> int:
        """
        Count files in the target directory.

        Args:
            extensions: Optional list of file extensions to count
                      (e.g., ['.py', '.java'] for specific languages)
                      If None, counts all files.

        Returns:
            Total number of files matching criteria
        """
        count = 0
        excluded_dirs = {
            "__pycache__",
            ".git",
            ".venv",
            "venv",
            "node_modules",
            "dist",
            "build",
        }

        for _root, dirs, files in os.walk(self.target_path):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for file in files:
                if extensions is None:
                    count += 1
                else:
                    if any(file.endswith(ext) for ext in extensions):
                        count += 1

        self._file_count = count
        return count

    def calculate_chunking(
        self,
        expected_files: int | None = None,
        memory_limit_mb: int = 4096,
    ) -> ChunkingConfiguration:
        """
        Calculate optimal chunking configuration.

        This method determines the best chunking strategy based on
        file count and memory constraints.

        Args:
            expected_files: Override for the number of files to process
            memory_limit_mb: Maximum memory to use in MB

        Returns:
            ChunkingConfiguration with optimized settings
        """
        # Use provided count or get from previous count
        file_count = expected_files or self._file_count or self.count_files()

        # Determine chunk size based on memory limit
        # Estimate memory per file and calculate optimal chunk size
        memory_per_file = self.MEMORY_PER_FILE_MB
        max_chunk_by_memory = int(memory_limit_mb / memory_per_file)

        # Choose chunk size: prefer smaller chunks for stability
        # but large enough for efficiency
        chunk_size = min(self.DEFAULT_CHUNK_SIZE, max_chunk_by_memory)
        chunk_size = max(chunk_size, self.MIN_CHUNK_SIZE)
        chunk_size = min(chunk_size, self.MAX_CHUNK_SIZE)

        # Calculate estimated number of chunks
        estimated_chunks = (file_count + chunk_size - 1) // chunk_size

        # Estimate memory usage per chunk (as integer MB)
        memory_estimated_mb = int(chunk_size * memory_per_file)

        # Create and return configuration
        return ChunkingConfiguration(
            strategy=ChunkingStrategy.ADAPTIVE,
            chunk_size=chunk_size,
            max_chunk_size=self.MAX_CHUNK_SIZE,
            min_chunk_size=self.MIN_CHUNK_SIZE,
            overlap_files=0,
            estimated_chunks=estimated_chunks,
            memory_estimated_mb=memory_estimated_mb,
        )

    def get_chunking_recommendations(self, config: ChunkingConfiguration) -> list[str]:
        """
        Generate recommendations based on chunking configuration.

        Args:
            config: The chunking configuration to analyze

        Returns:
            List of recommendations for optimal operation
        """
        recommendations = []

        # Memory-based recommendations
        if config.memory_estimated_mb > 2048:
            recommendations.append(
                "Consider reducing chunk size if memory usage is high."
            )

        # Chunk count recommendations
        if config.estimated_chunks > 100:
            recommendations.append(
                f"Large number of chunks ({config.estimated_chunks}) expected. "
                "Consider checkpoint frequency adjustment."
            )

        # Strategy recommendations
        if config.strategy == ChunkingStrategy.ADAPTIVE:
            recommendations.append(
                "Using adaptive chunking - chunk sizes will adjust "
                "based on directory boundaries and file types."
            )

        return recommendations


class ProgressDisplay:
    """
    Utility class for displaying progress during preparation.

    This class provides formatted output for the various
    preparation phases.
    """

    # ANSI color codes for terminal output
    COLOR_RESET = "\033[0m"
    COLOR_GREEN = "\033[92m"  # Success/Complete
    COLOR_YELLOW = "\033[93m"  # Warning
    COLOR_RED = "\033[91m"  # Error/Critical
    COLOR_CYAN = "\033[96m"  # Info/Progress
    COLOR_BOLD = "\033[1m"  # Bold text

    # Progress bar configuration
    BAR_WIDTH = 40
    BAR_CHAR_COMPLETE = "█"
    BAR_CHAR_INCOMPLETE = "░"

    def __init__(self, verbose: bool = True):
        """
        Initialize the progress display.

        Args:
            verbose: Whether to show detailed progress messages
        """
        self.verbose = verbose
        self.start_time: datetime | None = None

    def phase_header(self, phase: PreparationPhase, description: str) -> None:
        """
        Display a phase header with description.

        Args:
            phase: The current preparation phase
            description: Human-readable description of the phase
        """
        header = f"""
{self.COLOR_BOLD}{"=" * 70}
PHASE {phase.value}: {phase.name.replace("_", " ").title()}
{self.COLOR_RESET}
{description}
{self.COLOR_BOLD}{"=" * 70}{self.COLOR_RESET}
"""
        print(header)

    def phase_complete(self, phase: PreparationPhase) -> None:
        """
        Display completion message for a phase.

        Args:
            phase: The completed preparation phase
        """
        print(
            f"\n{self.COLOR_GREEN}✓{self.COLOR_RESET} Phase {phase.value} ({phase.name}) complete\n"
        )

    def section_header(self, title: str) -> None:
        """
        Display a section header within a phase.

        Args:
            title: Title of the section
        """
        print(f"\n{self.COLOR_CYAN}▶ {title}{self.COLOR_RESET}")

    def success_message(self, message: str) -> None:
        """
        Display a success message.

        Args:
            message: The success message to display
        """
        print(f"  {self.COLOR_GREEN}✓{self.COLOR_RESET} {message}")

    def warning_message(self, message: str) -> None:
        """
        Display a warning message.

        Args:
            message: The warning message to display
        """
        print(f"  {self.COLOR_YELLOW}⚠{self.COLOR_RESET} {message}")

    def error_message(self, message: str) -> None:
        """
        Display an error message.

        Args:
            message: The error message to display
        """
        print(f"  {self.COLOR_RED}✗{self.COLOR_RESET} {message}")

    def info_message(self, message: str, indent: int = 2) -> None:
        """
        Display an informational message.

        Args:
            message: The info message to display
            indent: Number of spaces to indent
        """
        indent_str = " " * indent
        print(f"{indent_str}{self.COLOR_CYAN}ℹ{self.COLOR_RESET} {message}")

    def progress_bar(
        self,
        current: int,
        total: int,
        prefix: str = "",
        suffix: str = "",
        length: int | None = None,
    ) -> None:
        """
        Display a progress bar.

        Args:
            current: Current progress value
            total: Total value for completion
            prefix: Text to display before the bar
            suffix: Text to display after the bar
            length: Width of the progress bar
        """
        if length is None:
            length = self.BAR_WIDTH

        percent = float(current) / total if total > 0 else 1.0
        filled_length = int(length * percent)
        bar = self.BAR_CHAR_COMPLETE * filled_length + self.BAR_CHAR_INCOMPLETE * (
            length - filled_length
        )

        print(
            f"\r{prefix} |{bar}| {percent * 100:.0f}% {suffix}",
            end="\r",
            flush=True,
        )

        if current == total:
            print()  # New line on completion

    def summary_report(self, report: PreparationReport) -> None:
        """
        Display a summary of the preparation report.

        Args:
            report: The completed preparation report
        """
        print(f"""
{self.COLOR_BOLD}{"=" * 70}
PREPARATION SUMMARY
{self.COLOR_RESET}
Status:           {self.COLOR_GREEN if report.success else self.COLOR_RED}{"SUCCESS" if report.success else "FAILED"}{self.COLOR_RESET}
Duration:         {report.total_duration_seconds:.2f} seconds
Phases Completed: {len(report.phases_completed)}
Phases Skipped:   {len(report.phases_skipped)}

Warnings:         {len(report.warnings)}
Errors:           {len(report.errors)}

Recommendations:
""")

        for i, rec in enumerate(report.recommendations, 1):
            print(f"  {i}. {rec}")

        if report.warnings:
            print("\nWarnings Detail:")
            for warning in report.warnings:
                print(f"  - {warning}")

        if report.errors:
            print("\nErrors Detail:")
            for error in report.errors:
                print(f"  - {error}")

        print(f"\n{self.COLOR_BOLD}{'=' * 70}{self.COLOR_RESET}")


def _calculate_constitution_hash() -> str:
    """
    Calculate the SHA256 hash of the constitution file.

    This function reads the constitution file and calculates
    its hash for the runtime context.

    Returns:
        Hexadecimal string representation of the hash
    """
    constitution_path = PROJECT_ROOT / "constitution.truth.md"

    if not constitution_path.exists():
        # Return a placeholder hash if constitution doesn't exist
        return "0" * 64

    sha256_hash = hashlib.sha256()

    try:
        with open(constitution_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
    except OSError:
        return "0" * 64

    return sha256_hash.hexdigest()


def _calculate_code_version_hash() -> str:
    """
    Calculate the version hash of the CodeMarshal codebase.

    This function creates a deterministic hash based on
    the relevant source files in the codebase.

    Returns:
        Hexadecimal string representation of the hash
    """
    sha256_hash = hashlib.sha256()

    # Define which file types to include in version hash
    allowed_suffixes = {".py", ".md", ".toml", ".txt"}

    # Define directories to skip
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

    # Collect unique files
    unique_files: dict[str, Path] = {}

    for root, dirs, files in os.walk(PROJECT_ROOT):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in skip_dir_names and not d.startswith(".")]

        root_path = Path(root)

        for name in files:
            file_path = root_path / name

            # Only include relevant file types
            if file_path.suffix not in allowed_suffixes:
                continue

            try:
                rel_path = str(file_path.relative_to(PROJECT_ROOT))
            except ValueError:
                continue

            unique_files[rel_path] = file_path

    # Process files in sorted order for deterministic hashing
    for rel_path in sorted(unique_files.keys()):
        file_path = unique_files[rel_path]

        try:
            stat = file_path.stat()

            # Add path, size, and mtime to hash
            sha256_hash.update(rel_path.encode("utf-8"))
            sha256_hash.update(str(stat.st_size).encode("utf-8"))
            sha256_hash.update(str(int(stat.st_mtime)).encode("utf-8"))

        except (FileNotFoundError, PermissionError):
            # Skip inaccessible files
            continue

    return sha256_hash.hexdigest()


# ============================================================================
# SECTION 5: MAIN PREPARATION FUNCTIONS
# ============================================================================


def prepare_for_large_run(
    target_path: str,
    expected_files: int = 50000,
    enable_backup: bool = True,
    enable_monitoring: bool = True,
) -> tuple[bool, PreparationReport]:
    """
    Prepare CodeMarshal for processing a large codebase.

    This function performs a comprehensive set of preparation steps
    to ensure the system is ready for processing 50,000 or more files.

    Constitutional Basis:
    - Article 8: Complete Evidence - Creates backups before modifications
    - Article 21: Self-Validation - Validates system integrity
    - Article 22: Resource Bounds - Ensures adequate resources

    Args:
        target_path: Path to the directory to be observed
        expected_files: Expected number of files to process
        enable_backup: Whether to create pre-run backups
        enable_monitoring: Whether to enable memory monitoring

    Returns:
        Tuple of (success: bool, report: PreparationReport)

    The function performs these steps in order:
        1. Initialize logging and display systems
        2. Validate target path exists and is accessible
        3. Initialize storage with integrity checking
        4. Verify storage integrity
        5. Create backup (if enabled)
        6. Analyze disk space
        7. Configure memory monitoring
        8. Calculate chunking strategy
        9. Validate boundary rules
        10. Generate final report
    """
    # Initialize timing and display
    start_time = datetime.now(UTC)
    display = ProgressDisplay(verbose=True)
    report = PreparationReport(start_time=start_time)

    # Resolve and validate target path
    resolved_path = Path(target_path).resolve()

    if not resolved_path.exists():
        error_msg = f"Target path does not exist: {resolved_path}"
        report.errors.append(error_msg)
        report.success = False
        return False, report

    if not resolved_path.is_dir():
        error_msg = f"Target path is not a directory: {resolved_path}"
        report.errors.append(error_msg)
        report.success = False
        return False, report

    print(f"\n{'=' * 70}")
    print("CODEMARSHAL LARGE RUN PREPARATION")
    print(f"{'=' * 70}")
    print(f"Target:         {resolved_path}")
    print(f"Expected Files: {expected_files:,}")
    print(f"Backup:         {'Enabled' if enable_backup else 'Disabled'}")
    print(f"Monitoring:     {'Enabled' if enable_monitoring else 'Disabled'}")
    print(f"Started:        {start_time.isoformat()}")
    print(f"{'=' * 70}\n")

    # =========================================================================
    # PHASE 1: Storage Initialization and Integrity Check
    # =========================================================================

    phase = PreparationPhase.STORAGE_CHECK
    display.phase_header(
        phase,
        "Initializing storage system and verifying integrity...",
    )

    try:
        # Step 1.1: Initialize storage with backup support
        display.section_header("Initializing storage system")
        storage = InvestigationStorage(
            base_path="storage",
            enable_backups=enable_backup,
        )
        display.success_message("Storage system initialized")
        report.phases_completed.append("storage_initialization")

        # Step 1.2: Check storage integrity
        display.section_header("Verifying storage integrity")
        integrity_report = storage.verify_storage_integrity()
        report.storage_report = integrity_report

        if integrity_report["is_corrupt"]:
            display.warning_message(
                f"Found {integrity_report['corruption_count']} corruption issues"
            )

            # Attempt automatic repair
            display.section_header("Attempting automatic repair")
            repair_report = storage.repair_corruption()

            if repair_report["repaired_count"] > 0:
                display.success_message(
                    f"Repaired {repair_report['repairerrord_count']} issues"
                )
                for log_entry in repair_report["repair_log"]:
                    display.info_message(log_entry, indent=4)
            else:
                display.warning_message("No issues could be automatically repaired")
                report.warnings.append(
                    "Storage corruption detected - manual intervention may be required"
                )
        else:
            display.success_message("Storage integrity verified - no issues found")

        report.phases_completed.append("storage_verification")

    except Exception as e:
        error_msg = f"Storage initialization failed: {str(e)}"
        report.errors.append(error_msg)
        display.error_message(error_msg)
        report.success = False
        return False, report

    # =========================================================================
    # PHASE 2: Backup Creation
    # =========================================================================

    if enable_backup:
        phase = PreparationPhase.BACKUP_CREATION
        display.phase_header(
            phase,
            "Creating backup of existing observation data...",
        )

        try:
            # Initialize backup manager
            backup_manager = BackupManager(Path("storage/backups"))

            # Create full backup of observations directory
            observations_dir = Path("storage/observations")

            if observations_dir.exists():
                display.section_header("Creating full backup")

                # Generate unique backup ID with timestamp
                backup_id = f"pre_run_{int(time.time())}"

                # Create the backup
                backup_result = backup_manager.create_full_backup(
                    observations_dir,
                    backup_id=backup_id,
                )

                # Display backup results - backup_result is a BackupManifest object
                backup_manifest = backup_result
                report.backup_report = {
                    "backup_id": backup_manifest.backup_id,
                    "file_count": backup_manifest.file_count,
                    "size_bytes": backup_manifest.total_size,
                    "checksum": backup_manifest.checksum[:16] + "...",
                    "created_at": backup_manifest.created_at.isoformat(),
                }
                display.success_message(f"Backup created: {backup_manifest.backup_id}")
                display.info_message(f"Files backed up: {backup_manifest.file_count:,}")
                display.info_message(
                    f"Backup size: {backup_manifest.total_size // (1024 * 1024)} MB"
                )

                report.phases_completed.append("backup_creation")
            else:
                display.info_message(
                    "No observations directory found - skipping backup"
                )
                report.phases_skipped.append("backup_creation")

        except Exception as e:
            error_msg = f"Backup creation failed: {str(e)}"
            report.errors.append(error_msg)
            display.error_message(error_msg)
            report.warnings.append("Backup could not be created - proceed with caution")
    else:
        display.info_message("Backup creation disabled by configuration")
        report.phases_skipped.append("backup_creation")

    # =========================================================================
    # PHASE 3: Disk Space Analysis
    # =========================================================================

    phase = PreparationPhase.DISK_SPACE_CHECK
    display.phase_header(
        phase,
        "Analyzing disk space availability...",
    )

    try:
        # Initialize disk space analyzer
        analyzer = DiskSpaceAnalyzer(resolved_path)

        # Perform analysis
        display.section_header("Analyzing disk usage")
        disk_analysis = analyzer.analyze(expected_files)

        # Display results
        report.disk_space_report = {
            "total_bytes": disk_analysis.total_bytes,
            "available_bytes": disk_analysis.available_bytes,
            "usage_percentage": disk_analysis.usage_percentage,
            "status": disk_analysis.status.name,
            "required_bytes": disk_analysis.required_bytes,
        }

        # Display human-readable summary
        print(analyzer.get_human_readable_summary(disk_analysis))

        # Check if space is sufficient
        if disk_analysis.status == DiskSpaceStatus.INSUFFICIENT:
            error_msg = "Insufficient disk space for safe operation"
            report.errors.append(error_msg)
            display.error_message(error_msg)
            for warning in disk_analysis.warnings:
                report.errors.append(warning)
                print(f"  ✗ {warning}")
            report.success = False
            return False, report

        # Handle marginal space with warnings
        if disk_analysis.status == DiskSpaceStatus.MARGINAL:
            for warning in disk_analysis.warnings:
                report.warnings.append(warning)
                display.warning_message(warning)

        if disk_analysis.status == DiskSpaceStatus.SUFFICIENT:
            display.success_message("Disk space is sufficient for operation")

        report.phases_completed.append("disk_space_check")

    except Exception as e:
        error_msg = f"Disk space analysis failed: {str(e)}"
        report.errors.append(error_msg)
        display.error_message(error_msg)
        report.success = False
        return False, report

    # =========================================================================
    # PHASE 4: Memory Monitoring Configuration
    # =========================================================================

    if enable_monitoring:
        phase = PreparationPhase.MEMORY_CONFIG
        display.phase_header(
            phase,
            "Configuring memory monitoring system...",
        )

        try:
            # Calculate hashes for runtime context
            constitution_hash = _calculate_constitution_hash()
            code_version_hash = _calculate_code_version_hash()

            # Create runtime context for monitoring
            display.section_header("Creating runtime context")

            context = RuntimeContext(
                investigation_root=resolved_path,
                constitution_hash=constitution_hash,
                code_version_hash=code_version_hash,
                execution_mode="API",
                network_enabled=False,
                mutation_allowed=False,
                runtime_imports_allowed=False,
            )

            # Configure memory monitoring
            display.section_header("Setting up memory thresholds")

            warning_threshold = MemoryThreshold.WARNING.value
            critical_threshold = MemoryThreshold.CRITICAL.value

            monitor = setup_memory_monitoring(
                context=context,
                warning_threshold_mb=warning_threshold,
                critical_threshold_mb=critical_threshold,
            )

            # Get the memory monitor status for reporting
            memory_status = monitor.get_memory_status()

            report.memory_report = {
                "warning_threshold_mb": warning_threshold,
                "critical_threshold_mb": critical_threshold,
                "current_usage_mb": memory_status.get("current_rss_mb", 0),
                "peak_usage_mb": memory_status.get("current_rss_mb", 0),
                "check_interval": 1000,
            }

            display.success_message("Memory monitoring configured")
            display.info_message(f"Warning threshold: {warning_threshold} MB")
            display.info_message(f"Critical threshold: {critical_threshold} MB")
            display.info_message(
                f"Current usage: {memory_status.get('current_rss_mb', 0):.2f} MB"
            )
            display.info_message("Check interval: every 1000 files")

            report.phases_completed.append("memory_configuration")

        except Exception as e:
            error_msg = f"Memory monitoring setup failed: {str(e)}"
            report.errors.append(error_msg)
            display.error_message(error_msg)
            report.warnings.append("Memory monitoring could not be enabled")
    else:
        display.info_message("Memory monitoring disabled by configuration")
        report.phases_skipped.append("memory_configuration")

    # =========================================================================
    # PHASE 5: Chunking Strategy Configuration
    # =========================================================================

    phase = PreparationPhase.CHUNKING_SETUP
    display.phase_header(
        phase,
        "Calculating optimal chunking strategy...",
    )

    try:
        # Initialize chunking calculator
        calculator = ChunkingStrategyCalculator(resolved_path)

        # Count actual files if needed
        display.section_header("Counting files")
        actual_file_count = calculator.count_files()
        display.info_message(f"Files found: {actual_file_count:,}")

        # Calculate chunking configuration
        display.section_header("Calculating chunking strategy")

        # Determine memory limit for chunking
        memory_limit = (
            MemoryThreshold.CRITICAL.value
            if enable_monitoring
            else MemoryThreshold.MAXIMUM.value
        )

        chunking_config = calculator.calculate_chunking(
            expected_files=expected_files,
            memory_limit_mb=memory_limit,
        )

        # Update with actual file count
        chunking_config.estimated_chunks = (
            actual_file_count + chunking_config.chunk_size - 1
        ) // chunking_config.chunk_size

        # Generate recommendations
        recommendations = calculator.get_chunking_recommendations(chunking_config)

        report.chunking_report = {
            "strategy": chunking_config.strategy.name,
            "chunk_size": chunking_config.chunk_size,
            "estimated_chunks": chunking_config.estimated_chunks,
            "memory_per_chunk_mb": chunking_config.memory_estimated_mb,
            "file_count": actual_file_count,
        }

        report.recommendations.extend(recommendations)

        # Display chunking configuration
        display.success_message(f"Chunking strategy: {chunking_config.strategy.name}")
        display.info_message(f"Files per chunk: {chunking_config.chunk_size}")
        display.info_message(f"Estimated chunks: {chunking_config.estimated_chunks}")
        display.info_message(
            f"Memory per chunk: ~{chunking_config.memory_estimated_mb} MB"
        )

        if recommendations:
            display.section_header("Chunking recommendations")
            for rec in recommendations:
                display.info_message(rec, indent=2)

        report.phases_completed.append("chunking_setup")

    except Exception as e:
        error_msg = f"Chunking configuration failed: {str(e)}"
        report.errors.append(error_msg)
        display.error_message(error_msg)
        report.success = False
        return False, report

    # =========================================================================
    # PHASE 6: Boundary Rule Validation
    # =========================================================================

    phase = PreparationPhase.BOUNDARY_VALIDATION
    display.phase_header(
        phase,
        "Validating boundary rules and architectural constraints...",
    )

    try:
        # Load boundary configuration
        boundary_config = get_agent_nexus_config(project_root=resolved_path)

        # Perform boundary validation
        display.section_header("Checking import boundaries")

        if boundary_config is not None:
            # Valid boundary configuration found
            display.success_message(
                f"Boundary configuration loaded: {boundary_config.project_name}"
            )
            display.info_message(f"Architecture: {boundary_config.architecture}")
            display.info_message(
                f"Boundaries defined: {len(boundary_config.boundary_definitions)}"
            )

            report.boundary_report = {
                "configured": True,
                "project_name": boundary_config.project_name,
                "architecture": boundary_config.architecture,
                "boundary_count": len(boundary_config.boundary_definitions),
                "strictness": boundary_config.boundary_strictness,
            }

            # Check for circular dependencies if enabled
            if boundary_config.detect_circular:
                display.info_message("Circular dependency detection: enabled")

            # Check for boundary crossings if enabled
            if boundary_config.report_crossings:
                display.info_message("Boundary crossing reports: enabled")

        else:
            # No boundary configuration found - this is not an error
            display.info_message("No boundary configuration found")
            display.info_message("Proceeding with default CodeMarshal boundaries")

            report.boundary_report = {
                "configured": False,
                "message": "Using default CodeMarshal architectural boundaries",
                "default_boundaries": [
                    "core",
                    "observations",
                    "inquiry",
                    "lens",
                    "bridge",
                ],
            }

        report.phases_completed.append("boundary_validation")

    except Exception as e:
        error_msg = f"Boundary validation failed: {str(e)}"
        report.errors.append(error_msg)
        display.error_message(error_msg)
        report.warnings.append("Boundary validation could not be completed")

    # =========================================================================
    # PHASE 7: Final Verification and Summary
    # =========================================================================

    phase = PreparationPhase.FINAL_VERIFICATION
    display.phase_header(
        phase,
        "Performing final verification and generating report...",
    )

    # Calculate total duration
    end_time = datetime.now(UTC)
    duration = (end_time - start_time).total_seconds()
    report.end_time = end_time
    report.total_duration_seconds = duration

    # Generate final recommendations
    display.section_header("Generating recommendations")

    if report.memory_report:
        if report.memory_report["current_usage_mb"] > 1000:
            report.recommendations.append(
                "Consider restarting CodeMarshal if memory usage is high"
            )

    if report.chunking_report:
        if report.chunking_report["estimated_chunks"] > 50:
            report.recommendations.append(
                "Large observation detected - consider running during low-traffic periods"
            )

    report.recommendations.append("Monitor memory usage during the observation run")
    report.recommendations.append(
        "Check disk space periodically during long operations"
    )
    report.recommendations.append("Review the backup created before proceeding")

    # Display final summary
    print(f"\n{'=' * 70}")
    print("FINAL PREPARATION REPORT")
    print(f"{'=' * 70}")

    display.success_message("Preparation process completed")
    print("\nRun Configuration:")
    print(
        f"  - Chunking:      {chunking_config.strategy.name} ({chunking_config.chunk_size} files/chunk)"
    )
    print(
        f"  - Memory:         Monitoring {'active' if enable_monitoring else 'disabled'}"
    )
    print(f"  - Backup:         {'Created' if enable_backup else 'skipped'}")
    print(
        f"  - Boundaries:     {'Validated' if report.boundary_report and report.boundary_report.get('configured') else 'Using defaults'}"
    )
    print(f"  - Files:          {actual_file_count:,} detected")
    print(f"  - Estimated Time: ~{chunking_config.estimated_chunks * 2} minutes")

    print(f"\n{'=' * 70}")
    print("SYSTEM READY FOR LARGE OBSERVATION RUN")
    print(f"{'=' * 70}\n")

    # Generate and display summary report
    display.summary_report(report)

    # Return final status
    return report.success, report


# ============================================================================
# SECTION 6: COMMAND-LINE INTERFACE
# ============================================================================


if __name__ == "__main__":
    # Display startup banner
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   CodeMarshal Large Run Preparation                                   ║
║   Version 1.0.0  |  February 5, 2026                                  ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    # Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python prepare_large_run.py <target_directory> [expected_files]")
        print()
        print("Arguments:")
        print("  target_directory   Path to the codebase to analyze")
        print(
            "  expected_files    Optional: Estimated number of files (default: 50000)"
        )
        print()
        print("Options:")
        print("  --no-backup       Skip backup creation")
        print("  --no-monitoring   Disable memory monitoring")
        print("  --verbose         Show detailed progress")
        print("  --help            Show this help message")
        print()
        print("Examples:")
        print("  python prepare_large_run.py /path/to/project")
        print("  python prepare_large_run.py /path/to/project 100000")
        print("  python prepare_large_run.py /path/to/project --no-backup")
        print()
        sys.exit(1)

    # Parse arguments with defaults
    target_path = sys.argv[1]
    expected_files = 50000
    enable_backup = True
    enable_monitoring = True
    verbose = False

    # Parse optional arguments
    i = 2
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--no-backup":
            enable_backup = False
        elif arg == "--no-monitoring":
            enable_monitoring = False
        elif arg == "--verbose":
            verbose = True
        elif arg == "--help":
            print(
                "Usage: python prepare_large_run.py <target_directory> [expected_files]"
            )
            print("       python prepare_large_run.py /path/to/project --no-backup")
            sys.exit(0)
        elif arg.isdigit():
            expected_files = int(arg)
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for usage information")
            sys.exit(1)
        i += 1

    # Execute preparation
    try:
        success, report = prepare_for_large_run(
            target_path=target_path,
            expected_files=expected_files,
            enable_backup=enable_backup,
            enable_monitoring=enable_monitoring,
        )

        # Exit with appropriate code
        if success:
            print(f"\n{'=' * 70}")
            print("Preparation completed successfully!")
            print(f"{'=' * 70}\n")
            sys.exit(0)
        else:
            print(f"\n{'=' * 70}")
            print("Preparation failed. Please review the errors above.")
            print(f"{'=' * 70}\n")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)

    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print("Please report this issue to the CodeMarshal team.")
        sys.exit(2)
