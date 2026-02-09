"""
cli.py — Command Line Interface for CodeMarshal.

ROLE: Translate command-line invocations into explicit command calls.
PRINCIPLE: Explicitness over comfort. The CLI is a contract, not a conversation.
"""

import argparse
import logging
import sys
import uuid
from pathlib import Path
from typing import Any

from bridge.commands import (
    ExportFormat,
    ExportRequest,
    ExportType,
    ObservationRequest,
    ObservationType,
)

# Only allowed imports per constitutional constraints
from bridge.commands import execute_investigation as investigate
from bridge.commands import execute_observation as observe
from bridge.commands.investigate import (
    InvestigationRequest,
    InvestigationScope,
    InvestigationType,
)
from core.engine import Engine
from core.runtime import ExecutionMode, Runtime, RuntimeConfiguration
from inquiry.session.context import QuestionType, SessionContext
from integrity.adapters.memory_monitor_adapter import create_memory_monitor_adapter
from lens.navigation.context import FocusType, create_navigation_context
from lens.navigation.workflow import WorkflowStage
from lens.views import ViewType
from storage.investigation_storage import InvestigationStorage

# Type aliases for clarity
PathStr = str
InvestigationID = str
Format = str

logger = logging.getLogger(__name__)


class CodeMarshalCLI:
    """
    CLI implementation with zero magic.

    CONSTRAINTS:
    - No defaults that imply intent
    - No helpful guessing
    - No chained commands
    - Immediate refusal on ambiguity
    """

    def __init__(self):
        self.parser = self._build_parser()

    def _build_parser(self) -> argparse.ArgumentParser:
        """Build explicit, non-magical argument parser."""
        parser = argparse.ArgumentParser(
            prog="codemarshal",
            description="CodeMarshal: Truth-preserving code investigation.",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
CONSTITUTIONAL RULES:
1. No inference - only what exists in source code
2. No guessing - explicit limitations shown
3. No magic - every action must be deliberate

EXAMPLES:
  codemarshal investigate /path/to/code --scope=project
  codemarshal observe /path/to/code --scope=module --intent=initial_scan
  codemarshal query investigation_id --question="what imports exist?"
  codemarshal export investigation_id --format=json --output=report.json
""",
        )

        # Global arguments
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging (verbose, not for normal use)",
        )

        parser.add_argument(
            "--config",
            type=Path,
            help="Path to configuration file (MUST be provided if used)",
        )

        parser.add_argument(
            "--version",
            action="store_true",
            help="Show version information and exit",
        )

        parser.add_argument(
            "--info",
            action="store_true",
            help="Show system diagnostics and exit",
        )

        # Subcommands
        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
            title="commands",
            description="Available commands (one required)",
        )

        # investigate command
        self._add_investigate_parser(subparsers)

        # observe command
        self._add_observe_parser(subparsers)

        # query command
        self._add_query_parser(subparsers)

        # export command
        self._add_export_parser(subparsers)

        # gui command
        self._add_gui_parser(subparsers)

        # tui command
        self._add_tui_parser(subparsers)

        # config command
        self._add_config_parser(subparsers)

        # backup command
        self._add_backup_parser(subparsers)

        # cleanup command
        self._add_cleanup_parser(subparsers)

        # repair command
        self._add_repair_parser(subparsers)

        # test command
        self._add_test_parser(subparsers)

        # search command
        self._add_search_parser(subparsers)

        # pattern command
        self._add_pattern_parser(subparsers)

        return parser

    def _add_investigate_parser(self, subparsers: Any) -> None:
        """Add investigate command parser with explicit arguments."""
        parser = subparsers.add_parser(
            "investigate",
            help="Start a new investigation",
            description="""
Start a new investigation of a codebase.
This collects observations, analyzes patterns, and creates investigation state.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # REQUIRED arguments
        parser.add_argument("path", type=Path, help="Path to investigate (MUST exist)")

        parser.add_argument(
            "--scope",
            required=True,
            choices=["file", "module", "package", "project"],
            help="Scope of investigation (MUST be specified)",
        )

        parser.add_argument(
            "--intent",
            required=True,
            choices=[
                "initial_scan",
                "constitutional_check",
                "dependency_analysis",
                "architecture_review",
            ],
            help="Intent of investigation (MUST be specified)",
        )

        # OPTIONAL arguments (but explicit)
        parser.add_argument(
            "--name", type=str, help="Investigation name (optional but recommended)"
        )

        parser.add_argument(
            "--notes", type=str, help="Initial notes (optional, can be added later)"
        )

        # Confirmation for large scopes
        parser.add_argument(
            "--confirm-large",
            action="store_true",
            help="Explicitly confirm if investigation scope is large",
        )

    def _add_observe_parser(self, subparsers: Any) -> None:
        """Add observe command parser with explicit arguments."""
        parser = subparsers.add_parser(
            "observe",
            help="Collect observations only",
            description="""
Collect observations without full investigation.
Pure data collection with no inference.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # REQUIRED arguments
        parser.add_argument("path", type=Path, help="Path to observe (MUST exist)")

        parser.add_argument(
            "--scope",
            required=True,
            choices=["file", "module", "package", "project"],
            help="Scope of observation (MUST be specified)",
        )

        # OPTIONAL but explicit
        parser.add_argument(
            "--depth",
            type=int,
            help="Maximum depth to traverse (if not specified, uses default)",
        )

        parser.add_argument(
            "--include-binary",
            action="store_true",
            help="Include binary files (normally excluded)",
        )

        parser.add_argument(
            "--follow-symlinks",
            action="store_true",
            help="Follow symbolic links (normally not followed)",
        )

        parser.add_argument(
            "--constitutional",
            action="store_true",
            help="Enable constitutional analysis (includes boundary, import, and export sight)",
        )

    def _add_query_parser(self, subparsers: Any) -> None:
        """Add query command parser with explicit arguments."""
        parser = subparsers.add_parser(
            "query",
            help="Query an investigation",
            description="""
Ask questions about an existing investigation.
Questions must be anchored to specific observations.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # REQUIRED arguments
        parser.add_argument(
            "investigation_id",
            type=str,
            help="Investigation ID to query (MUST be valid)",
        )

        parser.add_argument(
            "--question",
            required=True,
            type=str,
            help="Question to ask (MUST be specified)",
        )

        parser.add_argument(
            "--question-type",
            required=True,
            choices=["structure", "purpose", "connections", "anomalies", "thinking"],
            help="Type of question (MUST be specified)",
        )

        # OPTIONAL but explicit
        parser.add_argument(
            "--focus", type=str, help="Focus area within investigation (optional)"
        )

        parser.add_argument(
            "--limit", type=int, help="Maximum number of results (optional)"
        )

    def _add_export_parser(self, subparsers: Any) -> None:
        """Add export command parser with explicit arguments."""
        parser = subparsers.add_parser(
            "export",
            help="Export investigation",
            description="""
Export investigation to external format.
Export preserves truth without alteration.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # REQUIRED arguments
        parser.add_argument(
            "investigation_id",
            type=str,
            help="Investigation ID to export (MUST be valid)",
        )

        parser.add_argument(
            "--format",
            required=True,
            choices=["json", "markdown", "html", "plain", "csv"],
            help="Export format (MUST be specified)",
        )

        parser.add_argument(
            "--output", type=Path, required=True, help="Output path (MUST be specified)"
        )

        # Confirmation for overwrite
        parser.add_argument(
            "--confirm-overwrite",
            action="store_true",
            help="Explicitly confirm if output file exists",
        )

        # OPTIONAL but explicit
        parser.add_argument(
            "--include-notes",
            action="store_true",
            help="Include investigation notes (optional)",
        )

        parser.add_argument(
            "--include-patterns",
            action="store_true",
            help="Include pattern analysis (optional)",
        )

    def _add_tui_parser(self, subparsers: Any) -> None:
        """Add TUI command parser."""
        parser = subparsers.add_parser(
            "tui",
            help="Launch Text User Interface",
            description="""
Launch the CodeMarshal Text User Interface for interactive investigation.
The TUI provides a single-focus, truth-preserving investigation interface.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        # OPTIONAL arguments
        parser.add_argument(
            "--path",
            type=Path,
            default=Path(".").absolute(),
            help="Starting path for investigation (default: current directory)",
        )

    def _add_gui_parser(self, subparsers: Any) -> None:
        """Add GUI command parser."""
        parser = subparsers.add_parser(
            "gui",
            help="Launch Desktop GUI",
            description="""
Launch the CodeMarshal Desktop GUI for single-focus investigation.
The GUI is local-only and does not use network dependencies.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=Path(".").absolute(),
            help="Starting path for investigation (default: current directory)",
        )

    def _add_config_parser(self, subparsers: Any) -> None:
        """Add config command parser."""
        parser = subparsers.add_parser(
            "config",
            help="Configuration management",
            description="""
Manage CodeMarshal configuration.
Commands: show, edit, reset, validate
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        config_subparsers = parser.add_subparsers(
            dest="config_command",
            required=True,
            title="config commands",
        )

        # config show
        show_parser = config_subparsers.add_parser(
            "show", help="Show current configuration"
        )
        show_parser.add_argument("--path", type=Path, help="Path to config file")
        show_parser.add_argument(
            "--format", choices=["yaml", "json"], default="yaml", help="Output format"
        )
        show_parser.add_argument(
            "--secrets",
            action="store_true",
            help="Show sensitive values (masked by default)",
        )

        # config edit
        edit_parser = config_subparsers.add_parser("edit", help="Edit configuration")
        edit_parser.add_argument("--path", type=Path, help="Path to config file")
        edit_parser.add_argument("--editor", help="Editor to use")

        # config reset
        reset_parser = config_subparsers.add_parser("reset", help="Reset to defaults")
        reset_parser.add_argument("--path", type=Path, help="Path to config file")
        reset_parser.add_argument(
            "--confirm", action="store_true", help="Skip confirmation"
        )
        reset_parser.add_argument(
            "--no-backup", action="store_true", help="Don't create backup"
        )

        # config validate
        validate_parser = config_subparsers.add_parser(
            "validate", help="Validate configuration"
        )
        validate_parser.add_argument("--path", type=Path, help="Path to config file")
        validate_parser.add_argument(
            "--strict", action="store_true", help="Fail on warnings"
        )

    def _add_backup_parser(self, subparsers: Any) -> None:
        """Add backup command parser."""
        parser = subparsers.add_parser(
            "backup",
            help="Backup operations",
            description="""
Manage CodeMarshal backups.
Commands: create, list, restore, verify
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        backup_subparsers = parser.add_subparsers(
            dest="backup_command",
            required=True,
            title="backup commands",
        )

        # backup create
        create_parser = backup_subparsers.add_parser(
            "create", help="Create a new backup"
        )
        create_parser.add_argument(
            "--source", type=Path, required=True, help="Source directory to backup"
        )
        create_parser.add_argument(
            "--type",
            choices=["full", "incremental"],
            default="full",
            help="Type of backup",
        )
        create_parser.add_argument(
            "--parent",
            type=str,
            default=None,
            help="Parent backup ID for incremental backup",
        )
        create_parser.add_argument(
            "--compress", action="store_true", help="Compress backup"
        )

        # backup list
        list_parser = backup_subparsers.add_parser(
            "list", help="List available backups"
        )
        list_parser.add_argument(
            "--format", choices=["table", "json"], default="table", help="Output format"
        )

        # backup restore
        restore_parser = backup_subparsers.add_parser(
            "restore", help="Restore from backup"
        )
        restore_parser.add_argument("backup_id", type=str, help="Backup ID to restore")
        restore_parser.add_argument(
            "--target", type=Path, required=True, help="Target directory to restore to"
        )
        restore_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview restore without actually restoring",
        )

        # backup verify
        verify_parser = backup_subparsers.add_parser(
            "verify", help="Verify backup integrity"
        )
        verify_parser.add_argument("backup_id", type=str, help="Backup ID to verify")

    def _add_cleanup_parser(self, subparsers: Any) -> None:
        """Add cleanup command parser."""
        parser = subparsers.add_parser(
            "cleanup",
            help="Remove temporary files and cache",
            description="""
Remove temporary files, cache data, and build artifacts.
Use --dry-run to preview what would be cleaned.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--path",
            type=Path,
            default=Path("."),
            help="Directory to clean (default: current directory)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be cleaned without actually cleaning",
        )
        parser.add_argument("--all", action="store_true", help="Clean all categories")
        parser.add_argument(
            "--cache", action="store_true", help="Clean cache files only"
        )
        parser.add_argument("--temp", action="store_true", help="Clean temp files only")
        parser.add_argument(
            "--artifacts", action="store_true", help="Clean build artifacts only"
        )
        parser.add_argument("--logs", action="store_true", help="Clean log files only")
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )

    def _add_repair_parser(self, subparsers: Any) -> None:
        """Add repair command parser."""
        parser = subparsers.add_parser(
            "repair",
            help="Fix corrupted data and validate integrity",
            description="""
Fix corrupted data, validate integrity, and restore system state.
Creates a backup before repairing unless --validate-only is used.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--path",
            type=Path,
            default=Path("."),
            help="Directory to repair (default: current directory)",
        )
        parser.add_argument(
            "--no-backup",
            action="store_true",
            help="Skip creating backup before repair",
        )
        parser.add_argument(
            "--restore",
            type=Path,
            default=None,
            help="Restore from backup file instead of repairing",
        )
        parser.add_argument(
            "--validate-only", action="store_true", help="Only validate, don't repair"
        )
        parser.add_argument(
            "--no-storage", action="store_true", help="Skip storage repair"
        )
        parser.add_argument(
            "--no-investigations",
            action="store_true",
            help="Skip investigations repair",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Show detailed output"
        )

    def _add_test_parser(self, subparsers: Any) -> None:
        """Add test command parser."""
        parser = subparsers.add_parser(
            "test",
            help="Run test suite",
            description="""
Run CodeMarshal's test suite using pytest.
Supports coverage reporting, parallel execution, and various output formats.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "--path",
            type=Path,
            default=Path("tests"),
            help="Test directory or file (default: tests/)",
        )
        parser.add_argument(
            "--pattern",
            type=str,
            default="test_*.py",
            help="Test file pattern (default: test_*.py)",
        )
        parser.add_argument(
            "--coverage", action="store_true", help="Enable coverage reporting"
        )
        parser.add_argument(
            "--fail-fast", "-x", action="store_true", help="Stop on first failure"
        )
        parser.add_argument(
            "--verbose", "-v", action="store_true", help="Verbose output"
        )
        parser.add_argument("--quiet", "-q", action="store_true", help="Minimal output")
        parser.add_argument(
            "--markers",
            type=str,
            default=None,
            help="Only run tests with these markers (comma-separated)",
        )
        parser.add_argument(
            "--ignore",
            type=str,
            default=None,
            help="Ignore these test files (comma-separated)",
        )
        parser.add_argument(
            "--parallel", "-n", action="store_true", help="Run tests in parallel"
        )
        parser.add_argument(
            "--junit-xml",
            type=Path,
            default=None,
            help="Output JUnit XML report to this file",
        )
        parser.add_argument(
            "--html-report",
            type=Path,
            default=None,
            help="Output HTML coverage report to this directory",
        )
        parser.add_argument(
            "--show-locals",
            action="store_true",
            help="Show local variables in tracebacks",
        )
        parser.add_argument(
            "--tb-style",
            choices=["auto", "long", "short", "line", "native", "no"],
            default="short",
            help="Traceback style",
        )
        parser.add_argument(
            "--last-failed",
            "--lf",
            action="store_true",
            help="Run only previously failed tests",
        )
        parser.add_argument(
            "--no-header", action="store_true", help="Suppress header output"
        )

    def _add_search_parser(self, subparsers: Any) -> None:
        """Add search command parser."""
        parser = subparsers.add_parser(
            "search",
            help="Search codebase for text patterns",
            description="""
Search codebase for text patterns using ripgrep (if available) or Python regex.
Supports regex patterns, file filtering, and context display.
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "query",
            type=str,
            help="Search pattern (regex)",
        )
        parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=Path("."),
            help="Directory to search (default: current directory)",
        )
        parser.add_argument(
            "--case-insensitive",
            "-i",
            action="store_true",
            help="Case-insensitive search",
        )
        parser.add_argument(
            "--context",
            "-C",
            type=int,
            default=3,
            help="Lines of context around matches (default: 3)",
        )
        parser.add_argument(
            "--glob",
            "-g",
            type=str,
            default=None,
            help="File glob pattern (e.g., '*.py')",
        )
        parser.add_argument(
            "--type",
            "-t",
            type=str,
            default=None,
            help="File type filter (py, js, java, etc.)",
        )
        parser.add_argument(
            "--limit",
            "-m",
            type=int,
            default=100,
            help="Maximum results (default: 100)",
        )
        parser.add_argument(
            "--output",
            "-o",
            choices=["text", "json", "count"],
            default="text",
            help="Output format",
        )
        parser.add_argument(
            "--json-file",
            type=Path,
            default=None,
            help="Output JSON to file",
        )
        parser.add_argument(
            "--threads",
            type=int,
            default=4,
            help="Number of parallel threads (default: 4)",
        )
        parser.add_argument(
            "--exclude",
            "-e",
            type=str,
            default=None,
            help="Exclude pattern",
        )
        parser.add_argument(
            "--files-with-matches",
            "-l",
            action="store_true",
            help="Show only filenames with matches",
        )

    def _add_pattern_parser(self, subparsers: Any) -> None:
        """Add pattern command parser."""
        parser = subparsers.add_parser(
            "pattern",
            help="Pattern detection and management",
            description="""
Detect code patterns using built-in and custom pattern detectors.
Commands: list, scan, add
            """,
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        pattern_subparsers = parser.add_subparsers(
            dest="pattern_command",
            required=True,
            title="pattern commands",
        )

        # pattern list
        list_parser = pattern_subparsers.add_parser(
            "list", help="List available patterns"
        )
        list_parser.add_argument(
            "--category",
            "-c",
            type=str,
            choices=["security", "performance", "style"],
            default=None,
            help="Filter by category",
        )
        list_parser.add_argument(
            "--show-disabled", action="store_true", help="Include disabled patterns"
        )
        list_parser.add_argument(
            "--output",
            "-o",
            choices=["table", "json"],
            default="table",
            help="Output format",
        )

        # pattern scan
        scan_parser = pattern_subparsers.add_parser(
            "scan", help="Scan code for patterns"
        )
        scan_parser.add_argument(
            "path",
            type=Path,
            nargs="?",
            default=Path("."),
            help="Directory or file to scan",
        )
        scan_parser.add_argument(
            "--pattern",
            "-p",
            type=str,
            action="append",
            help="Specific pattern ID to run (can be used multiple times)",
        )
        scan_parser.add_argument(
            "--category",
            "-c",
            type=str,
            choices=["security", "performance", "style"],
            default=None,
            help="Run all patterns in category",
        )
        scan_parser.add_argument(
            "--glob", "-g", type=str, default="*", help="File glob pattern"
        )
        scan_parser.add_argument(
            "--output",
            "-o",
            choices=["table", "json"],
            default="table",
            help="Output format",
        )
        scan_parser.add_argument(
            "--max-files", type=int, default=10000, help="Maximum files to scan"
        )

        # pattern add
        add_parser = pattern_subparsers.add_parser("add", help="Add a custom pattern")
        add_parser.add_argument(
            "--id", type=str, required=True, help="Unique pattern identifier"
        )
        add_parser.add_argument(
            "--name", type=str, required=True, help="Human-readable name"
        )
        add_parser.add_argument(
            "--pattern", type=str, required=True, help="Regex pattern"
        )
        add_parser.add_argument(
            "--severity",
            type=str,
            choices=["critical", "warning", "info"],
            default="warning",
            help="Pattern severity",
        )
        add_parser.add_argument(
            "--description", type=str, default="", help="Pattern description"
        )
        add_parser.add_argument(
            "--message", type=str, default="", help="Message template"
        )
        add_parser.add_argument(
            "--tags",
            type=str,
            action="append",
            help="Tags (can be used multiple times)",
        )
        add_parser.add_argument(
            "--languages",
            type=str,
            action="append",
            help="Target languages (can be used multiple times)",
        )

    def run(self, args: list[str] | None = None) -> int:
        """
        Run the CLI with provided arguments.

        Args:
            args: Command line arguments (if None, uses sys.argv[1:])

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            parsed_args = self.parser.parse_args(args)
        except SystemExit:
            # argparse already printed help or error
            return 1

        # Handle version flag before requiring a command
        if parsed_args.version:
            return self._handle_version()

        # Handle info flag before requiring a command
        if parsed_args.info:
            return self._handle_info()

        # Set up logging
        self._setup_logging(parsed_args.debug)

        logger.debug(f"CLI invoked with: {parsed_args}")

        # Execute command
        try:
            if parsed_args.command == "investigate":
                return self._handle_investigate(parsed_args)
            elif parsed_args.command == "observe":
                return self._handle_observe(parsed_args)
            elif parsed_args.command == "query":
                return self._handle_query(parsed_args)
            elif parsed_args.command == "export":
                return self._handle_export(parsed_args)
            elif parsed_args.command == "gui":
                return self._handle_gui(parsed_args)
            elif parsed_args.command == "tui":
                return self._handle_tui(parsed_args)
            elif parsed_args.command == "config":
                return self._handle_config(parsed_args)
            elif parsed_args.command == "backup":
                return self._handle_backup(parsed_args)
            elif parsed_args.command == "cleanup":
                return self._handle_cleanup(parsed_args)
            elif parsed_args.command == "repair":
                return self._handle_repair(parsed_args)
            elif parsed_args.command == "test":
                return self._handle_test(parsed_args)
            elif parsed_args.command == "search":
                return self._handle_search(parsed_args)
            elif parsed_args.command == "pattern":
                return self._handle_pattern(parsed_args)
            else:
                # Should not happen due to argparse validation
                self._refuse(f"Unknown command: {parsed_args.command}")
                return 1

        except KeyboardInterrupt:
            print("\nInterrupted by user.", file=sys.stderr)
            return 130
        except Exception as e:
            logger.exception(f"Unexpected error in {parsed_args.command}")
            self._refuse(f"Internal error: {str(e)}")
            return 1

    def _handle_investigate(self, args: argparse.Namespace) -> int:
        """Handle investigate command with explicit validation."""
        # Validate path exists
        if not args.path.exists():
            self._refuse(f"Path does not exist: {args.path}")
            return 1

        # Validate scope appropriateness
        if args.scope == "project" and not self._looks_like_project(args.path):
            self._warn(
                f"Path {args.path} may not be a project. Use --scope=module or --scope=package if this is not a project root."
            )
            # Continue anyway - user may know what they're doing

        # Check for large scope without confirmation
        if args.scope in ["project", "package"] and not args.confirm_large:
            if self._estimate_size(args.path) > 1000:  # Rough estimate
                self._refuse(
                    f"Large investigation scope ({args.scope}) requires --confirm-large flag. "
                    f"Estimated files: {self._estimate_size(args.path)}"
                )
                return 1

        # Call command
        try:
            config = RuntimeConfiguration(
                investigation_root=args.path
                if hasattr(args, "path")
                and isinstance(args.path, Path)
                and args.path.is_dir()
                else Path(".").absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / "Structure.md",
                code_root=args.path
                if hasattr(args, "path")
                and isinstance(args.path, Path)
                and args.path.is_dir()
                else Path(".").absolute(),
            )
            runtime = Runtime(config=config)
            Engine(
                runtime._context,
                runtime._state,
                storage=InvestigationStorage(),
                memory_monitor=create_memory_monitor_adapter(runtime._context),
            )
            session_context = SessionContext(
                snapshot_id=uuid.uuid4(),
                anchor_id="root",
                question_type=QuestionType.STRUCTURE,
                context_id=uuid.uuid4(),
            )
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:welcome",
                current_view=ViewType.OVERVIEW,
            )

            # Convert string scope to enum
            scope_map = {
                "file": InvestigationScope.FILE,
                "module": InvestigationScope.MODULE,
                "package": InvestigationScope.PACKAGE,
                "project": InvestigationScope.CODEBASE,  # Map project to codebase
                "codebase": InvestigationScope.CODEBASE,
            }

            try:
                scope = scope_map[args.scope]
            except KeyError:
                raise ValueError(
                    f"'{args.scope}' is not a valid InvestigationScope"
                ) from None

            req = InvestigationRequest(
                type=InvestigationType.NEW,
                target_path=args.path,
                scope=scope,
                parameters={
                    "intent": args.intent,
                    "name": args.name,
                    "initial_notes": args.notes,
                },
            )

            raw_result = investigate(
                request=req,
                runtime=runtime,
                nav_context=nav_context,
                existing_sessions={},
            )

            # Wrap in result object for display logic
            from bridge.results import InvestigateResult

            # Map dictionary result to InvestigateResult fields
            # The start_investigation method returns {session_id, status, path}
            # InvestigateResult expects arguments matching its __init__ or fields

            # Handle potentially mismatched fields or extra fields
            clean_result = {
                "success": True,
                "investigation_id": raw_result.get("investigation_id", "unknown"),
                "status": raw_result.get("status", "unknown"),
                "path": raw_result.get("path", str(args.path)),
                "scope": str(scope.value),
                "observation_count": raw_result.get("observation_count", 0),
                # 'intent': raw_result.get('intent_record', {}).get('parameters', {}).get('intent', 'unknown')
            }

            result = InvestigateResult(**clean_result)

            # Add extra fields manually if needed for display
            if hasattr(result, "intent"):
                pass  # Already there if added to dataclass, otherwise we attach it
            else:
                # We can't attach to frozen dataclass, so we pass it separately or use a wrapper
                # For now, let's just rely on what InvestigateResult has
                pass

            if result.success:
                intent_val = (
                    raw_result.get("intent_record", {})
                    .get("parameters", {})
                    .get("intent", "unknown")
                )
                self._show_investigation_result(result, intent=intent_val)
                return 0
            else:
                self._refuse(f"Investigation failed: {result.error_message}")
                return 1

        except Exception as e:
            logger.exception("Investigate command failed")
            self._refuse(f"Investigate error: {str(e)}")
            return 1

    def _handle_observe(self, args: argparse.Namespace) -> int:
        """Handle observe command with explicit validation."""
        # Validate path exists
        if not args.path.exists():
            self._refuse(f"Path does not exist: {args.path}")
            return 1

        # Validate not following symlinks by default (security)
        if args.follow_symlinks:
            self._warn("Following symlinks may access files outside intended scope.")

        # Validate binary inclusion
        if args.include_binary:
            self._warn("Including binary files may produce large observations.")

        # Call command
        try:
            print("1. Creating config...", file=sys.stderr)
            config = RuntimeConfiguration(
                investigation_root=args.path
                if hasattr(args, "path")
                and isinstance(args.path, Path)
                and args.path.is_dir()
                else Path(".").absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / "Structure.md",
                code_root=args.path
                if hasattr(args, "path")
                and isinstance(args.path, Path)
                and args.path.is_dir()
                else Path(".").absolute(),
            )
            print("2. Initializing runtime...", file=sys.stderr)
            runtime = Runtime(config=config)
            print("3. Creating engine...", file=sys.stderr)
            engine = Engine(
                runtime._context,
                runtime._state,
                storage=InvestigationStorage(),
                memory_monitor=create_memory_monitor_adapter(runtime._context),
            )

            # Register interfaces
            from observations.interface import MinimalObservationInterface

            engine.register_observation_interface(
                MinimalObservationInterface(runtime._context)
            )

            print("4. Creating context...", file=sys.stderr)
            session_context = SessionContext(
                snapshot_id=uuid.uuid4(),
                anchor_id="root",
                question_type=QuestionType.STRUCTURE,
                context_id=uuid.uuid4(),
            )
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:welcome",
                current_view=ViewType.OVERVIEW,
            )

            # Determine observation types based on constitutional flag
            if hasattr(args, "constitutional") and args.constitutional:
                # Enable all sight types for constitutional analysis
                types = {
                    ObservationType.FILE_SIGHT,
                    ObservationType.IMPORT_SIGHT,
                    ObservationType.BOUNDARY_SIGHT,
                    ObservationType.EXPORT_SIGHT,
                }
                # Try to load boundary configuration
                boundary_config_path = None
                if hasattr(args, "config") and args.config:
                    boundary_config_path = args.config
                else:
                    # Try to find Agent Nexus config in project
                    from config.boundaries import find_config_file

                    boundary_config_path = find_config_file(
                        project_root=args.path.parent
                        if args.path.is_file()
                        else args.path
                    )

                if boundary_config_path:
                    print(
                        f"Using boundary configuration: {boundary_config_path}",
                        file=sys.stderr,
                    )
                else:
                    self._warn(
                        "Constitutional mode enabled but no boundary configuration found. Using default boundaries."
                    )
            else:
                # Default: only file sight
                types = {ObservationType.FILE_SIGHT}
                boundary_config_path = None

            req = ObservationRequest(
                types=types,
                target_path=args.path,
                session_id=str(
                    session_context.snapshot_id
                ),  # Use snapshot_id as session key
                parameters={
                    "scope": args.scope,
                    "max_depth": args.depth,
                    "include_binary": args.include_binary,
                    "follow_symlinks": args.follow_symlinks,
                    "constitutional": getattr(args, "constitutional", False),
                    "boundary_config_path": str(boundary_config_path)
                    if boundary_config_path
                    else None,
                },
            )

            print("5. Executing observation...", file=sys.stderr)
            raw_result = observe(
                request=req,
                runtime=runtime,
                engine=engine,
                nav_context=nav_context,
                session_context=session_context,
            )
            print("6. Result received.", file=sys.stderr)

            from bridge.results import ObserveResult

            # Create ObserveResult with proper mapping from raw_result
            result = ObserveResult(
                success=raw_result.get("success", True),
                observation_id=raw_result.get("observation_id", "unknown"),
                status=raw_result.get("status", "unknown"),
                estimated_time=raw_result.get("estimated_time", "unknown"),
                intent_record=raw_result.get("intent_record"),
                limitations=raw_result.get("limitations"),
                truth_preservation_guarantee=raw_result.get(
                    "truth_preservation_guarantee", False
                ),
                warnings=raw_result.get("warnings", []),
                error_message=raw_result.get("error_message"),
            )

            if result.success:
                self._show_observation_result(result)
                return 0
            else:
                self._refuse(f"Observation failed: {result.error_message}")
                return 1

        except Exception as e:
            logger.exception("Observe command failed")
            self._refuse(f"Observe error: {str(e)}")
            return 1

    def _handle_query(self, args: argparse.Namespace) -> int:
        """Handle query command with explicit validation."""
        # Validate question type matches question content
        if not self._question_matches_type(args.question, args.question_type):
            self._warn(
                f"Question type '{args.question_type}' may not match question content."
            )
            # Continue - user may know what they're doing

        # Call command
        try:
            # Load investigation data and observations
            storage = InvestigationStorage()

            # Load session data from storage
            session_data = self._load_session_data(storage, args.investigation_id)
            if not session_data:
                self._refuse(f"Investigation not found: {args.investigation_id}")
                return 1

            # Load observations for this session
            observations = self._load_observations(storage, session_data)

            # Generate answer based on question type
            answer = self._generate_answer(
                args.question, args.question_type, observations
            )

            from bridge.results import QueryResult

            # Create QueryResult with the generated answer
            result = QueryResult(
                success=True,
                investigation_id=args.investigation_id,
                question=args.question,
                question_type=args.question_type,
                answer=answer,
                error_message=None,
            )

            self._show_query_result(result)
            return 0

        except Exception as e:
            logger.exception("Query command failed")
            self._refuse(f"Query error: {str(e)}")
            return 1

    def _load_session_data(
        self, storage: InvestigationStorage, investigation_id: str
    ) -> dict | None:
        """Load session data from storage."""
        import json
        from pathlib import Path

        # Look for session file in storage/sessions/
        sessions_dir = Path("storage/sessions")
        if not sessions_dir.exists():
            return None

        # Try to find session file by investigation_id
        for session_file in sessions_dir.glob("*.session.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    # Check if this is the right session
                    if data.get("id") == investigation_id:
                        return data
                    # Also check by filename pattern (investigation_id format)
                    if investigation_id in str(session_file):
                        return data
            except Exception:
                continue

        # If not found, return the most recent session as fallback
        # (This handles cases where investigation_id isn't properly mapped)
        most_recent = None
        most_recent_time = 0

        for session_file in sessions_dir.glob("*.session.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                    # Get timestamp from created_at
                    created_at = data.get("created_at", "")
                    if created_at:
                        # Parse ISO timestamp to compare
                        try:
                            from datetime import datetime

                            dt = datetime.fromisoformat(
                                created_at.replace("Z", "+00:00")
                            )
                            timestamp = dt.timestamp()
                            if timestamp > most_recent_time:
                                most_recent_time = timestamp
                                most_recent = data
                        except Exception:
                            pass
            except Exception:
                continue

        if most_recent:
            self._warn(
                f"Investigation {investigation_id} not found, using most recent session"
            )
            return most_recent

        return None

    def _load_observations(
        self, storage: InvestigationStorage, session_data: dict
    ) -> list:
        """Load observations for a session."""
        import json
        from pathlib import Path

        observations = []
        observation_ids = session_data.get("observation_ids", [])

        observations_dir = Path("storage/observations")
        if not observations_dir.exists():
            return observations

        for obs_id in observation_ids:
            # Look for observation file (with .observation.json extension)
            obs_file = observations_dir / f"{obs_id}.observation.json"
            if obs_file.exists():
                try:
                    with open(obs_file) as f:
                        data = json.load(f)
                        # Extract the actual observation data from the nested structure
                        if "data" in data and isinstance(data["data"], dict):
                            obs_data = data["data"]
                            # Check if there are nested observations
                            if "observations" in obs_data and obs_data["observations"]:
                                for nested_obs in obs_data["observations"]:
                                    observations.append(nested_obs)
                            else:
                                # Add the main data as a file_sight observation
                                observations.append(
                                    {
                                        "type": "file_sight",
                                        "result": obs_data,
                                        "path": obs_data.get("path", ""),
                                    }
                                )
                        else:
                            observations.append(data)
                except Exception as e:
                    logger.warning(f"Failed to load observation {obs_id}: {e}")
                    continue

        return observations

    def _generate_answer(
        self, question: str, question_type: str, observations: list
    ) -> str:
        """Generate answer using appropriate analyzer."""
        from inquiry.answers import (
            AnomalyDetector,
            ConnectionMapper,
            PurposeExtractor,
            StructureAnalyzer,
            ThinkingEngine,
        )

        # Map question type to analyzer
        analyzers = {
            "structure": StructureAnalyzer,
            "connections": ConnectionMapper,
            "anomalies": AnomalyDetector,
            "purpose": PurposeExtractor,
            "thinking": ThinkingEngine,
        }

        analyzer_class = analyzers.get(question_type)
        if not analyzer_class:
            return f"Unknown question type: {question_type}"

        try:
            analyzer = analyzer_class()
            return analyzer.analyze(observations, question)
        except Exception as e:
            return f"Error generating answer: {str(e)}"

    def _handle_export(self, args: argparse.Namespace) -> int:
        """Handle export command with explicit validation."""
        # Validate output path
        if args.output.exists() and not args.confirm_overwrite:
            self._refuse(
                f"Output file exists: {args.output}. Use --confirm-overwrite to overwrite."
            )
            return 1

        # Validate output directory exists
        output_dir = args.output.parent
        if not output_dir.exists():
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                self._refuse(f"Cannot create output directory: {str(e)}")
                return 1

        # Call command
        try:
            config = RuntimeConfiguration(
                investigation_root=args.path
                if hasattr(args, "path")
                and isinstance(args.path, Path)
                and args.path.is_dir()
                else Path(".").absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / "Structure.md",
                code_root=args.path
                if hasattr(args, "path")
                and isinstance(args.path, Path)
                and args.path.is_dir()
                else Path(".").absolute(),
            )
            Runtime(config=config)
            if not str(args.investigation_id).startswith(
                "investigation_"
            ) or "_" not in str(args.investigation_id):
                self._refuse(
                    "Investigation ID must be in format: investigation_<timestamp>_<hash>"
                )
                return 1

            # Extract timestamp for session context
            try:
                parts = str(args.investigation_id).split("_")
                int(parts[1]) / 1000  # Convert back to seconds
                session_uuid = uuid.uuid4()  # Generate UUID for internal use
            except Exception:
                self._refuse("Invalid investigation ID format")
                return 1

            session_context = SessionContext(
                snapshot_id=session_uuid,
                anchor_id="root",
                question_type=QuestionType.STRUCTURE,
                context_id=uuid.uuid4(),
            )
            create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:export",
                current_view=ViewType.OVERVIEW,
            )

            format_map = {
                "json": ExportFormat.JSON,
                "markdown": ExportFormat.MARKDOWN,
                                        "html": ExportFormat.HTML,
                                        "plain": ExportFormat.PLAINTEXT,
                                        "csv": ExportFormat.CSV,            }
            export_format = format_map.get(str(args.format).lower())
            if not export_format:
                self._refuse(f"Unsupported export format: {args.format}")
                return 1

            ExportRequest(
                type=ExportType.SESSION,
                format=export_format,
                session_id=str(session_uuid),
                parameters={
                    "output_path": str(args.output),
                    "include_notes": args.include_notes,
                    "include_patterns": args.include_patterns,
                    "confirm_overwrite": args.confirm_overwrite,
                },
            )

            # Load investigation data for export
            storage = InvestigationStorage()
            session_data = self._load_session_data(storage, args.investigation_id)
            if not session_data:
                self._refuse(f"Investigation not found: {args.investigation_id}")
                return 1

            # Load observations for this session
            observations = self._load_observations(storage, session_data)

            # Generate export content
            export_content = self._generate_export_content(
                args.format,
                session_data,
                observations,
                args.include_notes,
                args.include_patterns,
            )

            # Write to file
            output_path = Path(args.output)
            try:
                output_path.write_text(export_content, encoding="utf-8")
            except Exception as e:
                self._refuse(f"Failed to write export file: {str(e)}")
                return 1

            # Verify file was created
            if not output_path.exists():
                self._refuse("Export file was not created")
                return 1

            from bridge.results import ExportResult

            # Create ExportResult
            result = ExportResult(
                success=True,
                export_id=str(uuid.uuid4()),
                format=args.format,
                path=str(output_path),
                error_message=None,
            )

            self._show_export_result(result)
            return 0

        except Exception as e:
            logger.exception("Export command failed")
            self._refuse(f"Export error: {str(e)}")
            return 1

    def _handle_gui(self, args: argparse.Namespace) -> int:
        """Handle GUI command."""
        try:
            from bridge.entry.gui import launch_gui

            if not args.path.exists():
                self._refuse(f"Path does not exist: {args.path}")
                return 1

            return launch_gui(args.path)

        except Exception as e:
            logger.exception("GUI command failed")
            self._refuse(f"GUI error: {str(e)}")
            return 1

    def _handle_tui(self, args: argparse.Namespace) -> int:
        """Handle TUI command."""
        try:
            # Import TUI here to avoid import issues if not available
            from bridge.entry.tui import TruthPreservingTUI

            # Validate path exists
            if not args.path.exists():
                self._refuse(f"Path does not exist: {args.path}")
                return 1

            # Create and launch TUI
            tui = TruthPreservingTUI()
            exit_code = tui.run(initial_path=args.path)
            return exit_code

        except ImportError as e:
            self._refuse(f"TUI not available: {str(e)}")
            return 1
        except Exception as e:
            logger.exception("TUI command failed")
            self._refuse(f"TUI error: {str(e)}")
            return 1

    def _handle_config(self, args: argparse.Namespace) -> int:
        """Handle config command."""
        from bridge.commands import (
            execute_config_edit,
            execute_config_reset,
            execute_config_show,
            execute_config_validate,
        )

        try:
            if args.config_command == "show":
                result = execute_config_show(
                    path=args.path, format=args.format, show_secrets=args.secrets
                )
                if result.success:
                    print(result.formatted_output)
                    return 0
                else:
                    self._refuse(f"Failed to show config: {result.error}")
                    return 1

            elif args.config_command == "edit":
                result = execute_config_edit(path=args.path, editor=args.editor)
                if result.success:
                    print(f"Configuration edited successfully")
                    if result.backup_path:
                        print(f"  Backup created: {result.backup_path}")
                    return 0
                else:
                    self._refuse(f"Failed to edit config: {result.error}")
                    return 1

            elif args.config_command == "reset":
                if not args.confirm:
                    confirm = input("Reset configuration to defaults? [y/N]: ")
                    if confirm.lower() != "y":
                        print("Cancelled.")
                        return 0

                result = execute_config_reset(
                    path=args.path,
                    confirm=args.confirm,
                    create_backup=not args.no_backup,
                )
                if result.success:
                    print(f"Configuration reset to defaults")
                    if result.backup_path:
                        print(f"  Backup created: {result.backup_path}")
                    return 0
                else:
                    self._refuse(f"Failed to reset config: {result.error}")
                    return 1

            elif args.config_command == "validate":
                result = execute_config_validate(path=args.path, strict=args.strict)
                if result.success:
                    if result.warnings:
                        print("Configuration valid (with warnings):")
                        for warning in result.warnings:
                            print(f"  ! {warning}")
                    else:
                        print("Configuration is valid")
                    print(f"  Rules defined: {result.rule_count}")
                    return 0
                else:
                    print("Configuration validation failed:")
                    for error in result.errors:
                        print(f"  X {error}")
                    return 1

            else:
                self._refuse(f"Unknown config command: {args.config_command}")
                return 1

        except Exception as e:
            logger.exception("Config command failed")
            self._refuse(f"Config error: {str(e)}")
            return 1

    def _handle_backup(self, args: argparse.Namespace) -> int:
        """Handle backup command."""
        from bridge.commands import (
            execute_backup_create,
            execute_backup_list,
            execute_backup_restore,
            execute_backup_verify,
        )

        try:
            if args.backup_command == "create":
                result = execute_backup_create(
                    source_path=args.source,
                    backup_type=args.type,
                    parent_backup_id=args.parent,
                    compress=args.compress,
                )
                if result.success:
                    print(f"Backup created: {result.backup_id}")
                    print(f"  Files: {result.file_count}")
                    print(f"  Size: {result.size_mb} MB")
                    return 0
                else:
                    self._refuse(f"Failed to create backup: {result.error}")
                    return 1

            elif args.backup_command == "list":
                result = execute_backup_list(output_format=args.format)
                if result.success:
                    if result.count == 0:
                        print("No backups found")
                    else:
                        print(
                            f"\n{'Backup ID':<30} {'Files':<10} {'Size (MB)':<12} {'Created':<25}"
                        )
                        print("=" * 77)
                        for backup in result.backups:
                            created = (
                                backup["created_at"][:19]
                                if len(backup["created_at"]) > 19
                                else backup["created_at"]
                            )
                            print(
                                f"{backup['backup_id']:<30} {backup['file_count']:<10} {backup['total_size_mb']:<12} {created:<25}"
                            )
                        print(f"\nTotal: {result.count} backup(s)")
                    return 0
                else:
                    self._refuse(f"Failed to list backups: {result.error}")
                    return 1

            elif args.backup_command == "restore":
                result = execute_backup_restore(
                    backup_id=args.backup_id,
                    target_path=args.target,
                    dry_run=args.dry_run,
                )
                if result.success:
                    print(result.message)
                    return 0
                else:
                    self._refuse(f"Failed to restore backup: {result.error}")
                    return 1

            elif args.backup_command == "verify":
                result = execute_backup_verify(backup_id=args.backup_id)
                if result.success:
                    if result.valid:
                        print(f"Backup {args.backup_id} is valid")
                        print(f"  Expected files: {result.expected_files}")
                        print(f"  Actual files: {result.actual_files}")
                        return 0
                    else:
                        self._refuse(
                            f"Backup {args.backup_id} is invalid: {result.message}"
                        )
                        return 1
                else:
                    self._refuse(f"Failed to verify backup: {result.error}")
                    return 1

            else:
                self._refuse(f"Unknown backup command: {args.backup_command}")
                return 1

        except Exception as e:
            logger.exception("Backup command failed")
            self._refuse(f"Backup error: {str(e)}")
            return 1

    def _handle_cleanup(self, args: argparse.Namespace) -> int:
        """Handle cleanup command."""
        from bridge.commands import execute_cleanup

        try:
            result = execute_cleanup(
                path=args.path,
                dry_run=args.dry_run,
                clean_all=args.all,
                clean_cache=args.cache,
                clean_temp=args.temp,
                clean_artifacts=args.artifacts,
                clean_logs=args.logs,
                verbose=args.verbose,
            )
            if result.success:
                if result.dry_run:
                    return 0
                print(f"Cleanup completed")
                print(f"  Removed: {result.removed_count} items")
                print(f"  Freed: {result.freed_space_mb:.2f} MB")
                if result.errors:
                    print(f"  Errors: {len(result.errors)}")
                    for error in result.errors[:5]:  # Show first 5 errors
                        print(f"    - {error}")
                return 0
            else:
                self._refuse(f"Cleanup failed: {result.message}")
                return 1

        except Exception as e:
            logger.exception("Cleanup command failed")
            self._refuse(f"Cleanup error: {str(e)}")
            return 1

    def _handle_repair(self, args: argparse.Namespace) -> int:
        """Handle repair command."""
        from bridge.commands import execute_repair

        try:
            result = execute_repair(
                path=args.path,
                create_backup=not args.no_backup,
                restore_from=args.restore,
                validate_only=args.validate_only,
                repair_storage=not args.no_storage,
                repair_investigations=not args.no_investigations,
                verbose=args.verbose,
            )
            if result.success:
                if args.validate_only:
                    print("Validation completed")
                else:
                    print(f"Repair completed")
                    print(f"  Fixed: {result.fixed_items} items")

                if result.errors:
                    print(f"  Errors: {len(result.errors)}")
                    for error in result.errors[:5]:
                        print(f"    - {error}")
                return 0
            else:
                self._refuse(f"Repair failed: {result.message}")
                return 1

        except Exception as e:
            logger.exception("Repair command failed")
            self._refuse(f"Repair error: {str(e)}")
            return 1

    def _handle_test(self, args: argparse.Namespace) -> int:
        """Handle test command."""
        from bridge.commands import execute_test

        try:
            # Parse markers
            markers = None
            if args.markers:
                markers = [m.strip() for m in args.markers.split(",")]

            # Parse ignore list
            ignore = None
            if args.ignore:
                ignore = [i.strip() for i in args.ignore.split(",")]

            result = execute_test(
                path=args.path,
                pattern=args.pattern,
                coverage=args.coverage,
                fail_fast=args.fail_fast,
                verbose=args.verbose,
                quiet=args.quiet,
                markers=markers,
                ignore=ignore,
                parallel=args.parallel,
                junit_xml=args.junit_xml,
                html_report=args.html_report,
                show_locals=args.show_locals,
                tb_style=args.tb_style,
                last_failed=args.last_failed,
                no_header=args.no_header,
            )

            # Print output
            if result.output:
                print(result.output)

            # Print summary
            print(f"\n{'=' * 60}")
            print(f"Tests: {result.tests_run} | ", end="")
            print(f"Passed: {result.tests_passed} | ", end="")
            print(f"Failed: {result.tests_failed} | ", end="")
            print(f"Skipped: {result.tests_skipped}")

            if result.coverage_percent is not None:
                print(f"Coverage: {result.coverage_percent:.1f}%")

            print(f"{'=' * 60}")

            if result.success:
                return 0
            else:
                return result.exit_code if result.exit_code else 1

        except Exception as e:
            logger.exception("Test command failed")
            self._refuse(f"Test error: {str(e)}")
            return 1

    def _handle_search(self, args: argparse.Namespace) -> int:
        """Handle search command."""
        from bridge.commands import execute_search

        try:
            result = execute_search(
                query=args.query,
                path=args.path,
                case_insensitive=args.case_insensitive,
                context=args.context,
                glob=args.glob,
                file_type=args.type,
                limit=args.limit,
                output_format=args.output,
                json_file=args.json_file,
                threads=args.threads,
                exclude_pattern=args.exclude,
                files_with_matches=args.files_with_matches,
            )

            if result.success:
                return 0
            else:
                self._refuse(f"Search failed: {result.error}")
                return 1

        except Exception as e:
            logger.exception("Search command failed")
            self._refuse(f"Search error: {str(e)}")
            return 1

    def _handle_pattern(self, args: argparse.Namespace) -> int:
        """Handle pattern command."""
        from bridge.commands import (
            execute_pattern_add,
            execute_pattern_list,
            execute_pattern_scan,
        )

        try:
            if args.pattern_command == "list":
                result = execute_pattern_list(
                    category=args.category,
                    show_disabled=args.show_disabled,
                    output_format=args.output,
                )
                if result.success:
                    print(f"\nAvailable Patterns ({result.total_count} total):")
                    print("=" * 80)
                    print(f"{'ID':<30} {'Name':<30} {'Severity':<10}")
                    print("-" * 80)
                    for pattern in result.patterns:
                        print(
                            f"{pattern.id:<30} {pattern.name:<30} {pattern.severity:<10}"
                        )
                    return 0
                else:
                    self._refuse(f"Failed to list patterns: {result.error}")
                    return 1

            elif args.pattern_command == "scan":
                result = execute_pattern_scan(
                    path=args.path,
                    patterns=args.pattern,
                    category=args.category,
                    glob=args.glob,
                    output_format=args.output,
                    max_files=args.max_files,
                )
                if result.success:
                    print(f"\nPattern Scan Results")
                    print("=" * 80)
                    print(f"Patterns scanned: {result.patterns_scanned}")
                    print(f"Files scanned: {result.files_scanned}")
                    print(f"Matches found: {result.matches_found}")
                    print(f"Scan time: {result.scan_time_ms:.2f}ms")

                    if result.matches:
                        print("\nMatches:")
                        print("-" * 80)
                        for match in result.matches:
                            severity_color = {
                                "critical": "\033[91m",
                                "warning": "\033[93m",
                                "info": "\033[94m",
                            }.get(match["severity"], "")
                            reset_color = "\033[0m"
                            print(
                                f"{severity_color}[{match['severity'].upper()}]{reset_color} {match['file']}:{match['line']}"
                            )
                            print(f"  {match['message']}")
                            print(f"  > {match['matched']}")
                            print()

                    return 0 if result.matches_found == 0 else 1
                else:
                    self._refuse(f"Scan failed: {result.error}")
                    return 1

            elif args.pattern_command == "add":
                result = execute_pattern_add(
                    pattern_id=args.id,
                    name=args.name,
                    pattern=args.pattern,
                    severity=args.severity,
                    description=args.description,
                    message=args.message,
                    tags=args.tags,
                    languages=args.languages,
                )
                if result.success:
                    print(f"✓ Pattern '{result.pattern_id}' added successfully")
                    return 0
                else:
                    self._refuse(f"Failed to add pattern: {result.error}")
                    return 1

            else:
                self._refuse(f"Unknown pattern command: {args.pattern_command}")
                return 1

        except Exception as e:
            logger.exception("Pattern command failed")
            self._refuse(f"Pattern error: {str(e)}")
            return 1

    def _handle_version(self) -> int:
        """Handle --version flag."""
        import platform

        try:
            from importlib.metadata import version

            codemarshal_version = version("codemarshal")
        except ImportError:
            codemarshal_version = "1.0.0"
        except Exception:
            codemarshal_version = "unknown"

        print(f"CodeMarshal v{codemarshal_version}")
        print(f"Python: {platform.python_version()}")
        print(f"Platform: {platform.platform()}")

        return 0

    def _handle_info(self) -> int:
        """Handle --info flag."""
        import platform

        try:
            from importlib.metadata import version, requires

            codemarshal_version = version("codemarshal")
        except ImportError:
            codemarshal_version = "1.0.0"
        except Exception:
            codemarshal_version = "unknown"

        print("CodeMarshal System Information")
        print("=" * 40)
        print(f"\nVersion: v{codemarshal_version}")
        print(f"Python: {platform.python_version()}")
        print(f"Platform: {platform.platform()}")

        # Configuration info
        print("\nConfiguration:")
        try:
            # Try to get default config path
            config_path = Path.home() / ".config" / "codemarshal" / "config.yaml"
            print(f"  Config Path: {config_path}")
            if config_path.exists():
                print("  Config Status: Exists")
            else:
                print("  Config Status: Not found (will use defaults)")
        except Exception as e:
            print(f"  Config Error: {e}")

        # Storage info
        print("\nStorage:")
        try:
            storage_dir = Path("storage")
            if storage_dir.exists():
                session_count = len(list(storage_dir.glob("sessions/*.session.json")))
                obs_count = len(
                    list(storage_dir.glob("observations/*.observation.json"))
                )
                print(f"  Sessions: {session_count}")
                print(f"  Observations: {obs_count}")
            else:
                print("  Storage directory not initialized")
        except Exception as e:
            print(f"  Storage Error: {e}")

        print("\n" + "=" * 40)
        return 0

    def _generate_export_content(
        self,
        format_type: str,
        session_data: dict,
        observations: list,
        include_notes: bool = False,
        include_patterns: bool = False,
    ) -> str:
        """Generate export content in the specified format."""

        if format_type.lower() == "json":
            return self._generate_json_export(
                session_data, observations, include_notes, include_patterns
            )
        elif format_type.lower() == "markdown":
            return self._generate_markdown_export(
                session_data, observations, include_notes, include_patterns
            )
        elif format_type.lower() == "html":
            return self._generate_html_export(
                session_data, observations, include_notes, include_patterns
            )
        elif format_type.lower() in ["plain", "plaintext"]:
            return self._generate_plaintext_export(
                session_data, observations, include_notes, include_patterns
            )
        else:
            raise ValueError(f"Unsupported export format: {format_type}")

    def _generate_json_export(
        self,
        session_data: dict,
        observations: list,
        include_notes: bool,
        include_patterns: bool,
    ) -> str:
        """Generate JSON export."""
        import json
        from datetime import datetime

        export_data = {
            "export_metadata": {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "format": "json",
                "tool": "CodeMarshal",
            },
            "investigation": session_data,
            "observations": observations,
        }

        if include_notes:
            export_data["notes"] = session_data.get("notes", [])

        if include_patterns:
            export_data["patterns"] = session_data.get("patterns", [])

        return json.dumps(export_data, indent=2, default=str)

    def _generate_markdown_export(
        self,
        session_data: dict,
        observations: list,
        include_notes: bool,
        include_patterns: bool,
    ) -> str:
        """Generate Markdown export."""
        from datetime import datetime

        lines = [
            "# CodeMarshal Investigation Report",
            "",
            f"**Exported:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "**Format:** Markdown",
            "",
            "---",
            "",
            "## Investigation Metadata",
            "",
            f"- **ID:** {session_data.get('id', 'Unknown')}",
            f"- **Path:** {session_data.get('path', 'Unknown')}",
            f"- **State:** {session_data.get('state', 'Unknown')}",
            f"- **Created:** {session_data.get('created_at', 'Unknown')}",
            "",
            "---",
            "",
        ]

        # Add observations summary
        lines.extend(
            [
                "## Observations Summary",
                "",
                f"Total Observations: {len(observations)}",
                "",
            ]
        )

        # Group observations by type
        obs_by_type = {}
        for obs in observations:
            obs_type = obs.get("type", "unknown")
            if obs_type not in obs_by_type:
                obs_by_type[obs_type] = []
            obs_by_type[obs_type].append(obs)

        for obs_type, obs_list in obs_by_type.items():
            lines.extend(
                [
                    f"### {obs_type.title()}",
                    "",
                    f"Count: {len(obs_list)}",
                    "",
                ]
            )

        if include_notes and session_data.get("notes"):
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Notes",
                    "",
                ]
            )
            for note in session_data["notes"]:
                lines.append(f"- {note}")

        if include_patterns and session_data.get("patterns"):
            lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Patterns",
                    "",
                ]
            )
            for pattern in session_data["patterns"]:
                lines.append(f"- {pattern}")

        lines.extend(
            [
                "",
                "---",
                "",
                "*Generated by CodeMarshal - Truth-Preserving Investigation*",
            ]
        )

        return "\n".join(lines)

    def _generate_html_export(
        self,
        session_data: dict,
        observations: list,
        include_notes: bool,
        include_patterns: bool,
    ) -> str:
        """Generate HTML export."""
        from datetime import datetime

        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CodeMarshal Investigation Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007acc; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        h3 {{ color: #666; }}
        .metadata {{ background: #f9f9f9; padding: 15px; border-left: 4px solid #007acc; margin: 20px 0; }}
        .observation {{ background: #fff; border: 1px solid #ddd; padding: 10px; margin: 10px 0; border-radius: 4px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 0.9em; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>CodeMarshal Investigation Report</h1>
        <div class="metadata">
            <p><strong>Exported:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
            <p><strong>Format:</strong> HTML</p>
            <p><strong>Investigation ID:</strong> {session_data.get("id", "Unknown")}</p>
        </div>
        <h2>Investigation Details</h2>
        <table>
            <tr><th>Property</th><th>Value</th></tr>
            <tr><td>ID</td><td>{session_data.get("id", "Unknown")}</td></tr>
            <tr><td>Path</td><td>{session_data.get("path", "Unknown")}</td></tr>
            <tr><td>State</td><td>{session_data.get("state", "Unknown")}</td></tr>
            <tr><td>Created</td><td>{session_data.get("created_at", "Unknown")}</td></tr>
        </table>
        <h2>Observations</h2>
        <p>Total Observations: {len(observations)}</p>
"""

        # Group observations by type
        obs_by_type = {}
        for obs in observations:
            obs_type = obs.get("type", "unknown")
            if obs_type not in obs_by_type:
                obs_by_type[obs_type] = []
            obs_by_type[obs_type].append(obs)

        for obs_type, obs_list in obs_by_type.items():
            html += f"""
        <h3>{obs_type.title()}</h3>
        <p>Count: {len(obs_list)}</p>
"""

        if include_notes and session_data.get("notes"):
            html += """
        <h2>Notes</h2>
        <ul>
"""
            for note in session_data["notes"]:
                html += f"            <li>{note}</li>\n"
            html += "        </ul>\n"

        if include_patterns and session_data.get("patterns"):
            html += """
        <h2>Patterns</h2>
        <ul>
"""
            for pattern in session_data["patterns"]:
                html += f"            <li>{pattern}</li>\n"
            html += "        </ul>\n"

        html += """
        <div class="footer">
            <p>Generated by CodeMarshal - Truth-Preserving Investigation</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def _generate_plaintext_export(
        self,
        session_data: dict,
        observations: list,
        include_notes: bool,
        include_patterns: bool,
    ) -> str:
        """Generate Plain text export."""
        from datetime import datetime

        lines = [
            "=" * 70,
            "CODEMARSHAL INVESTIGATION REPORT",
            "=" * 70,
            "",
            f"Exported: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "Format: Plain Text",
            "",
            "-" * 70,
            "INVESTIGATION DETAILS",
            "-" * 70,
            "",
            f"ID:       {session_data.get('id', 'Unknown')}",
            f"Path:     {session_data.get('path', 'Unknown')}",
            f"State:    {session_data.get('state', 'Unknown')}",
            f"Created:  {session_data.get('created_at', 'Unknown')}",
            "",
            "-" * 70,
            "OBSERVATIONS SUMMARY",
            "-" * 70,
            "",
            f"Total Observations: {len(observations)}",
            "",
        ]

        # Group observations by type
        obs_by_type = {}
        for obs in observations:
            obs_type = obs.get("type", "unknown")
            if obs_type not in obs_by_type:
                obs_by_type[obs_type] = []
            obs_by_type[obs_type].append(obs)

        for obs_type, obs_list in obs_by_type.items():
            lines.extend(
                [
                    f"{obs_type.title()}:",
                    f"  Count: {len(obs_list)}",
                    "",
                ]
            )

        if include_notes and session_data.get("notes"):
            lines.extend(
                [
                    "-" * 70,
                    "NOTES",
                    "-" * 70,
                    "",
                ]
            )
            for note in session_data["notes"]:
                lines.append(f"- {note}")
            lines.append("")

        if include_patterns and session_data.get("patterns"):
            lines.extend(
                [
                    "-" * 70,
                    "PATTERNS",
                    "-" * 70,
                    "",
                ]
            )
            for pattern in session_data["patterns"]:
                lines.append(f"- {pattern}")
            lines.append("")

        lines.extend(
            [
                "=" * 70,
                "Generated by CodeMarshal - Truth-Preserving Investigation",
                "=" * 70,
            ]
        )

        return "\n".join(lines)

    # Validation helpers
    def _looks_like_project(self, path: Path) -> bool:
        """Check if path looks like a project root."""
        project_indicators = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            ".git",
            "README.md",
            "src",
        ]

        for indicator in project_indicators:
            if (path / indicator).exists():
                return True
        return False

    def _estimate_size(self, path: Path) -> int:
        """Estimate number of files in path (quick check)."""
        try:
            if path.is_file():
                return 1

            count = 0
            for _ in path.rglob("*.py"):
                count += 1
                if count > 1000:  # Early exit for large projects
                    break
            return count
        except Exception:
            return 0

    def _question_matches_type(self, question: str, question_type: str) -> bool:
        """Check if question seems to match declared type."""
        question_lower = question.lower()

        type_keywords = {
            "structure": ["what", "structure", "contains", "files", "modules"],
            "purpose": ["what does", "purpose", "function", "does this"],
            "connections": ["how", "connect", "depend", "import", "export"],
            "anomalies": ["unusual", "strange", "anomal", "odd", "weird"],
            "thinking": ["think", "opinion", "believe", "suspicious", "concern"],
        }

        keywords = type_keywords.get(question_type, [])
        for keyword in keywords:
            if keyword in question_lower:
                return True
        return False

    def _safe_print(self, text: str) -> None:
        """Print text safely, handling encoding errors by replacing characters."""
        try:
            print(text)
        except UnicodeEncodeError:
            # Fallback: encode to ascii with replacement, then decode
            encoding = sys.stdout.encoding or "utf-8"
            print(text.encode(encoding, errors="replace").decode(encoding))

    # Output methods
    def _show_investigation_result(
        self, result: Any, intent: str | None = None
    ) -> None:
        """Show investigation result clearly."""
        self._safe_print("\nINVESTIGATION STARTED")
        self._safe_print("=" * 80)
        self._safe_print(f"ID:          {result.investigation_id}")
        self._safe_print(f"Path:        {result.path}")
        self._safe_print(f"Scope:       {result.scope}")

        # Optional fields
        if intent:
            self._safe_print(f"Intent:      {intent}")

        self._safe_print(f"Status:      {result.status}")

        warnings = getattr(result, "warnings", None) or []
        if warnings:
            self._safe_print("\nWARNINGS:")
            for warning in warnings:
                self._safe_print(f"  ⚠️  {warning}")

        self._safe_print("\nNext steps:")
        self._safe_print(
            f"  codemarshal query {result.investigation_id} --question='...'"
        )
        self._safe_print(
            f"  codemarshal export {result.investigation_id} --format=markdown --output=report.md"
        )
        self._safe_print("=" * 80)

    def _show_observation_result(self, result: Any) -> None:
        """Show observation result in explicit format."""
        self._safe_print("OBSERVATION COLLECTED")
        self._safe_print("=" * 80)
        self._safe_print(f"Observation ID: {result.observation_id}")
        self._safe_print(f"Status:         {result.status}")
        self._safe_print(f"Estimated Time: {result.estimated_time}")

        if result.intent_record:
            self._safe_print(
                f"Target Path:    {result.intent_record.get('target_path', 'N/A')}"
            )
            self._safe_print(
                f"Session ID:     {result.intent_record.get('session_id', 'N/A')}"
            )
            self._safe_print(
                f"Types:          {', '.join(result.intent_record.get('observation_types', []))}"
            )

        if result.limitations:
            self._safe_print("\nLIMITATIONS:")
            for obs_type, limits in result.limitations.items():
                self._safe_print(f"  {obs_type}:")
                for limit in limits:
                    self._safe_print(f"    ⚠️  {limit}")

        self._safe_print("\nObservation includes:")
        self._safe_print("  ✅ Pure facts only (no inferences)")
        self._safe_print("  ✅ Immutable once recorded")
        self._safe_print("  ✅ Truth-preserving guarantee")

        if result.truth_preservation_guarantee:
            self._safe_print("\n✓ Truth preservation guaranteed")
        self._safe_print("=" * 80)

    def _show_query_result(self, result: Any) -> None:
        """Show query result in explicit format."""
        self._safe_print("\nQUERY RESULT")
        self._safe_print("=" * 80)
        self._safe_print(f"Question:    {result.question}")
        self._safe_print(f"Type:        {result.question_type}")
        self._safe_print(f"Investigation:{result.investigation_id}")

        # Optional timestamp if available
        if hasattr(result, "timestamp"):
            self._safe_print(f"Timestamp:   {result.timestamp}")

        if result.answer:
            self._safe_print("\nAnswer:")
            self._safe_print(result.answer)

        if result.uncertainties:
            self._safe_print("\nUNCERTAINTIES:")
            for uncertainty in result.uncertainties:
                self._safe_print(f"  ⚠️  {uncertainty}")

        if result.anchors:
            self._safe_print("\nANCHORS (linked to observations):")
            for anchor in result.anchors[:5]:  # Limit display
                self._safe_print(f"  • {anchor}")
            if len(result.anchors) > 5:
                self._safe_print(f"  ... and {len(result.anchors) - 5} more")

        patterns = getattr(result, "patterns", [])
        if patterns:
            self._safe_print("\nPatterns detected:")
            for pattern in patterns:
                self._safe_print(f"  • {pattern}")

        self._safe_print("=" * 80)

    def _show_export_result(self, result: Any) -> None:
        """Show export result in explicit format."""
        self._safe_print("EXPORT COMPLETE")
        self._safe_print("=" * 80)
        self._safe_print(f"Export ID:      {getattr(result, 'export_id', 'unknown')}")
        self._safe_print(f"Format:         {getattr(result, 'format', 'unknown')}")
        self._safe_print(f"Output:         {getattr(result, 'path', 'unknown')}")
        if getattr(result, "error_message", None):
            self._safe_print(f"Error:          {result.error_message}")

        self._safe_print("=" * 80)

    def _setup_logging(self, debug: bool) -> None:
        """Set up logging based on debug flag."""
        level = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    def _refuse(self, message: str) -> None:
        """Show refusal message clearly."""
        try:
            print(f"❌ REFUSED: {message}", file=sys.stderr)
        except UnicodeEncodeError:
            encoding = sys.stderr.encoding or "utf-8"
            print(
                f"❌ REFUSED: {message}".encode(encoding, errors="replace").decode(
                    encoding
                ),
                file=sys.stderr,
            )

    def _warn(self, message: str) -> None:
        """Show warning message clearly."""
        try:
            print(f"⚠️  WARNING: {message}", file=sys.stderr)
        except UnicodeEncodeError:
            encoding = sys.stderr.encoding or "utf-8"
            print(
                f"⚠️  WARNING: {message}".encode(encoding, errors="replace").decode(
                    encoding
                ),
                file=sys.stderr,
            )

    def _map_question_type_to_workflow_stage(self, question_type: str) -> WorkflowStage:
        """
        Map question type to appropriate workflow stage.

        This allows CLI queries to bypass rigid stage progression while
        maintaining constitutional compliance.
        """
        question_to_stage = {
            "structure": WorkflowStage.ORIENTATION,
            "purpose": WorkflowStage.EXAMINATION,
            "connections": WorkflowStage.CONNECTIONS,
            "anomalies": WorkflowStage.PATTERNS,
            "thinking": WorkflowStage.THINKING,
        }

        return question_to_stage.get(question_type, WorkflowStage.ORIENTATION)


def main() -> None:
    """Main entry point for CLI."""
    cli = CodeMarshalCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
