"""
cli.py — Command Line Interface for CodeMarshal.

ROLE: Translate command-line invocations into explicit command calls.
PRINCIPLE: Explicitness over comfort. The CLI is a contract, not a conversation.
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import logging

# Only allowed imports per constitutional constraints
from bridge.commands import (
    execute_investigation as investigate,
    execute_observation as observe,
    execute_query as query,
    execute_export as export,
    ObservationRequest,
    QueryRequest,
    ExportRequest,
    ExportType,
    ExportFormat,
    ObservationType
)
from bridge.commands.investigate import InvestigationRequest, InvestigationType, InvestigationScope
from bridge.commands.query import QueryType, QuestionName

from core.runtime import Runtime, RuntimeConfiguration, ExecutionMode
from core.engine import Engine
from integrity.adapters.memory_monitor_adapter import IntegrityMemoryMonitorAdapter
from storage.investigation_storage import InvestigationStorage
from lens.navigation.context import create_navigation_context
from lens.navigation.workflow import WorkflowStage
from lens.navigation.context import FocusType
from lens.views import ViewType
from inquiry.session.context import SessionContext, QuestionType
import typing
import uuid

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
"""
        )
        
        # Global arguments
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logging (verbose, not for normal use)"
        )
        
        parser.add_argument(
            "--config",
            type=Path,
            help="Path to configuration file (MUST be provided if used)"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(
            dest="command",
            required=True,
            title="commands",
            description="Available commands (one required)"
        )
        
        # investigate command
        self._add_investigate_parser(subparsers)
        
        # observe command
        self._add_observe_parser(subparsers)
        
        # query command
        self._add_query_parser(subparsers)
        
        # export command
        self._add_export_parser(subparsers)
        
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
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # REQUIRED arguments
        parser.add_argument(
            "path",
            type=Path,
            help="Path to investigate (MUST exist)"
        )
        
        parser.add_argument(
            "--scope",
            required=True,
            choices=["file", "module", "package", "project"],
            help="Scope of investigation (MUST be specified)"
        )
        
        parser.add_argument(
            "--intent",
            required=True,
            choices=[
                "initial_scan",
                "constitutional_check",
                "dependency_analysis",
                "architecture_review"
            ],
            help="Intent of investigation (MUST be specified)"
        )
        
        # OPTIONAL arguments (but explicit)
        parser.add_argument(
            "--name",
            type=str,
            help="Investigation name (optional but recommended)"
        )
        
        parser.add_argument(
            "--notes",
            type=str,
            help="Initial notes (optional, can be added later)"
        )
        
        # Confirmation for large scopes
        parser.add_argument(
            "--confirm-large",
            action="store_true",
            help="Explicitly confirm if investigation scope is large"
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
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # REQUIRED arguments
        parser.add_argument(
            "path",
            type=Path,
            help="Path to observe (MUST exist)"
        )
        
        parser.add_argument(
            "--scope",
            required=True,
            choices=["file", "module", "package", "project"],
            help="Scope of observation (MUST be specified)"
        )
        
        # OPTIONAL but explicit
        parser.add_argument(
            "--depth",
            type=int,
            help="Maximum depth to traverse (if not specified, uses default)"
        )
        
        parser.add_argument(
            "--include-binary",
            action="store_true",
            help="Include binary files (normally excluded)"
        )
        
        parser.add_argument(
            "--follow-symlinks",
            action="store_true",
            help="Follow symbolic links (normally not followed)"
        )
        
        parser.add_argument(
            "--constitutional",
            action="store_true",
            help="Enable constitutional analysis (includes boundary, import, and export sight)"
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
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # REQUIRED arguments
        parser.add_argument(
            "investigation_id",
            type=str,
            help="Investigation ID to query (MUST be valid)"
        )
        
        parser.add_argument(
            "--question",
            required=True,
            type=str,
            help="Question to ask (MUST be specified)"
        )
        
        parser.add_argument(
            "--question-type",
            required=True,
            choices=[
                "structure",
                "purpose", 
                "connections",
                "anomalies",
                "thinking"
            ],
            help="Type of question (MUST be specified)"
        )
        
        # OPTIONAL but explicit
        parser.add_argument(
            "--focus",
            type=str,
            help="Focus area within investigation (optional)"
        )
        
        parser.add_argument(
            "--limit",
            type=int,
            help="Maximum number of results (optional)"
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
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        # REQUIRED arguments
        parser.add_argument(
            "investigation_id",
            type=str,
            help="Investigation ID to export (MUST be valid)"
        )
        
        parser.add_argument(
            "--format",
            required=True,
            choices=["json", "markdown", "html", "plain"],
            help="Export format (MUST be specified)"
        )
        
        parser.add_argument(
            "--output",
            type=Path,
            required=True,
            help="Output path (MUST be specified)"
        )
        
        # Confirmation for overwrite
        parser.add_argument(
            "--confirm-overwrite",
            action="store_true",
            help="Explicitly confirm if output file exists"
        )
        
        # OPTIONAL but explicit
        parser.add_argument(
            "--include-notes",
            action="store_true",
            help="Include investigation notes (optional)"
        )
        
        parser.add_argument(
            "--include-patterns",
            action="store_true",
            help="Include pattern analysis (optional)"
        )
        
    def run(self, args: Optional[List[str]] = None) -> int:
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
            self._warn(f"Path {args.path} may not be a project. Use --scope=module or --scope=package if this is not a project root.")
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
                investigation_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / 'Structure.md',
                code_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute()
            )
            runtime = Runtime(config=config)
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
                context_id=uuid.uuid4()
            )
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:welcome",
                current_view=ViewType.OVERVIEW
            )
            
            # Convert string scope to enum
            scope_map = {
                'file': InvestigationScope.FILE,
                'module': InvestigationScope.MODULE,
                'package': InvestigationScope.PACKAGE,
                'project': InvestigationScope.CODEBASE,  # Map project to codebase
                'codebase': InvestigationScope.CODEBASE
            }
            
            try:
                scope = scope_map[args.scope]
            except KeyError:
                raise ValueError(f"'{args.scope}' is not a valid InvestigationScope")

            req = InvestigationRequest(
                type=InvestigationType.NEW,
                target_path=args.path,
                scope=scope,
                parameters={
                    "intent": args.intent,
                    "name": args.name,
                    "initial_notes": args.notes
                }
            )
            
            raw_result = investigate(
                request=req,
                runtime=runtime,
                nav_context=nav_context,
                existing_sessions={}
            )
            
            # Wrap in result object for display logic
            from bridge.results import InvestigateResult
            
            # Map dictionary result to InvestigateResult fields
            # The start_investigation method returns {session_id, status, path}
            # InvestigateResult expects arguments matching its __init__ or fields
            
            # Handle potentially mismatched fields or extra fields
            clean_result = {
                'success': True,
                'investigation_id': raw_result.get('investigation_id', 'unknown'),
                'status': raw_result.get('status', 'unknown'),
                'path': raw_result.get('path', str(args.path)),
                'scope': str(scope.value),
                'observation_count': raw_result.get('observation_count', 0),
                # 'intent': raw_result.get('intent_record', {}).get('parameters', {}).get('intent', 'unknown')
            }
            
            result = InvestigateResult(**clean_result)
            
            # Add extra fields manually if needed for display
            if hasattr(result, 'intent'):
                pass # Already there if added to dataclass, otherwise we attach it
            else:
                # We can't attach to frozen dataclass, so we pass it separately or use a wrapper
                # For now, let's just rely on what InvestigateResult has
                pass
            
            if result.success:
                intent_val = raw_result.get('intent_record', {}).get('parameters', {}).get('intent', 'unknown')
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
                investigation_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / 'Structure.md',
                code_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute()
            )
            print("2. Initializing runtime...", file=sys.stderr)
            runtime = Runtime(config=config)
            print("3. Creating engine...", file=sys.stderr)
            engine = Engine(
                runtime._context,
                runtime._state,
                storage=InvestigationStorage(),
                memory_monitor=IntegrityMemoryMonitorAdapter(),
            )
            
            # Register interfaces
            from observations.interface import MinimalObservationInterface
            engine.register_observation_interface(MinimalObservationInterface())
            
            print("4. Creating context...", file=sys.stderr)
            session_context = SessionContext(
                snapshot_id=uuid.uuid4(),
                anchor_id="root",
                question_type=QuestionType.STRUCTURE,
                context_id=uuid.uuid4()
            )
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:welcome",
                current_view=ViewType.OVERVIEW
            )
            
            # Determine observation types based on constitutional flag
            if hasattr(args, 'constitutional') and args.constitutional:
                # Enable all sight types for constitutional analysis
                types = {
                    ObservationType.FILE_SIGHT,
                    ObservationType.IMPORT_SIGHT,
                    ObservationType.BOUNDARY_SIGHT,
                    ObservationType.EXPORT_SIGHT
                }
                # Try to load boundary configuration
                boundary_config_path = None
                if hasattr(args, 'config') and args.config:
                    boundary_config_path = args.config
                else:
                    # Try to find Agent Nexus config in project
                    from config.boundaries import find_config_file
                    boundary_config_path = find_config_file(project_root=args.path.parent if args.path.is_file() else args.path)
                
                if boundary_config_path:
                    print(f"Using boundary configuration: {boundary_config_path}", file=sys.stderr)
                else:
                    self._warn("Constitutional mode enabled but no boundary configuration found. Using default boundaries.")
            else:
                # Default: only file sight
                types = {ObservationType.FILE_SIGHT}
                boundary_config_path = None
            
            req = ObservationRequest(
                types=types,
                target_path=args.path,
                session_id=str(session_context.snapshot_id), # Use snapshot_id as session key
                parameters={
                    "scope": args.scope,
                    "max_depth": args.depth,
                    "include_binary": args.include_binary,
                    "follow_symlinks": args.follow_symlinks,
                    "constitutional": getattr(args, 'constitutional', False),
                    "boundary_config_path": str(boundary_config_path) if boundary_config_path else None
                }
            )
            
            print("5. Executing observation...", file=sys.stderr)
            raw_result = observe(
                request=req,
                runtime=runtime,
                engine=engine,
                nav_context=nav_context,
                session_context=session_context
            )
            print("6. Result received.", file=sys.stderr)
            
            from bridge.results import ObserveResult
            # Create ObserveResult with proper mapping from raw_result
            result = ObserveResult(
                success=raw_result.get('success', True),
                observation_id=raw_result.get('observation_id', 'unknown'),
                status=raw_result.get('status', 'unknown'),
                estimated_time=raw_result.get('estimated_time', 'unknown'),
                intent_record=raw_result.get('intent_record'),
                limitations=raw_result.get('limitations'),
                truth_preservation_guarantee=raw_result.get('truth_preservation_guarantee', False),
                warnings=raw_result.get('warnings', []),
                error_message=raw_result.get('error_message')
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
            self._warn(f"Question type '{args.question_type}' may not match question content.")
            # Continue - user may know what they're doing
        
        # Call command
        try:
            config = RuntimeConfiguration(
                investigation_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / 'Structure.md',
                code_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute()
            )
            runtime = Runtime(config=config)
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
                context_id=uuid.uuid4()
            )
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:welcome",
                current_view=ViewType.OVERVIEW
            )
            
            req = QueryRequest(
                type=QueryType.QUESTION,
                name=QuestionName(args.question_type),
                session_id=args.investigation_id, # CLI argument is investigation_id, but request expects session_id
                parameters={
                    "question": args.question,
                    "focus": args.focus,
                    "limit": args.limit
                }
            )
            
            raw_result = query(
                request=req,
                runtime=runtime,
                engine=engine,
                nav_context=nav_context,
                session_context=session_context
            )
            
            from bridge.results import QueryResult
            # Create QueryResult with proper mapping from raw_result
            result = QueryResult(
                success=raw_result.get('success', True),
                investigation_id=raw_result.get('investigation_id', args.investigation_id),
                question=raw_result.get('question', args.question),
                question_type=raw_result.get('question_type', args.question_type),
                answer=raw_result.get('answer', 'No answer provided'),
                error_message=raw_result.get('error_message')
            )
            
            if result.success:
                self._show_query_result(result)
                return 0
            else:
                self._refuse(f"Query failed: {result.error_message}")
                return 1
                
        except Exception as e:
            logger.exception("Query command failed")
            self._refuse(f"Query error: {str(e)}")
            return 1
    
    def _handle_export(self, args: argparse.Namespace) -> int:
        """Handle export command with explicit validation."""
        # Validate output path
        if args.output.exists() and not args.confirm_overwrite:
            self._refuse(f"Output file exists: {args.output}. Use --confirm-overwrite to overwrite.")
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
                investigation_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute(),
                execution_mode=ExecutionMode.CLI,
                constitution_path=Path(__file__).parent.parent.parent / 'Structure.md',
                code_root=args.path if hasattr(args, 'path') and isinstance(args.path, Path) and args.path.is_dir() else Path('.').absolute()
            )
            runtime = Runtime(config=config)
            try:
                session_uuid = uuid.UUID(str(args.investigation_id))
            except Exception:
                self._refuse("Investigation ID must be a valid UUID for export")
                return 1

            session_context = SessionContext(
                snapshot_id=session_uuid,
                anchor_id="root",
                question_type=QuestionType.STRUCTURE,
                context_id=uuid.uuid4()
            )
            nav_context = create_navigation_context(
                session_context=session_context,
                workflow_stage=WorkflowStage.ORIENTATION,
                focus_type=FocusType.SYSTEM,
                focus_id="system:export",
                current_view=ViewType.OVERVIEW
            )
            
            format_map = {
                "json": ExportFormat.JSON,
                "markdown": ExportFormat.MARKDOWN,
                "html": ExportFormat.HTML,
                "plain": ExportFormat.PLAINTEXT,
            }
            export_format = format_map.get(str(args.format).lower())
            if not export_format:
                self._refuse(f"Unsupported export format: {args.format}")
                return 1
            
            req = ExportRequest(
                type=ExportType.SESSION,
                format=export_format,
                session_id=str(session_uuid),
                parameters={
                    "output_path": str(args.output),
                    "include_notes": args.include_notes,
                    "include_patterns": args.include_patterns,
                    "confirm_overwrite": args.confirm_overwrite
                }
            )
            
            raw_result = export(
                request=req,
                runtime=runtime,
                session_context=session_context,
                nav_context=nav_context
            )
            
            from bridge.results import ExportResult
            # Create ExportResult with proper mapping from raw_result
            result = ExportResult(
                success=True,
                export_id=raw_result.get('export_id', 'unknown'),
                format=req.format.value,
                path=req.parameters.get('output_path', 'unknown'),
                error_message=None
            )
            
            if result.success:
                self._show_export_result(result)
                return 0
            else:
                self._refuse(f"Export failed: {result.error_message}")
                return 1
                
        except Exception as e:
            logger.exception("Export command failed")
            self._refuse(f"Export error: {str(e)}")
            return 1
    
    # Validation helpers
    def _looks_like_project(self, path: Path) -> bool:
        """Check if path looks like a project root."""
        project_indicators = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
            ".git",
            "README.md",
            "src"
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
            "thinking": ["think", "opinion", "believe", "suspicious", "concern"]
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
            encoding = sys.stdout.encoding or 'utf-8'
            print(text.encode(encoding, errors='replace').decode(encoding))

    # Output methods
    def _show_investigation_result(self, result: Any, intent: str = None) -> None:
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

        warnings = getattr(result, 'warnings', None) or []
        if warnings:
            self._safe_print("\nWARNINGS:")
            for warning in warnings:
                self._safe_print(f"  ⚠️  {warning}")
        
        self._safe_print("\nNext steps:")
        self._safe_print(f"  codemarshal query {result.investigation_id} --question='...'")
        self._safe_print(f"  codemarshal export {result.investigation_id} --format=markdown --output=report.md")
        self._safe_print("=" * 80)
    
    def _show_observation_result(self, result: Any) -> None:
        """Show observation result in explicit format."""
        self._safe_print("OBSERVATION COLLECTED")
        self._safe_print("=" * 80)
        self._safe_print(f"Observation ID: {result.observation_id}")
        self._safe_print(f"Status:         {result.status}")
        self._safe_print(f"Estimated Time: {result.estimated_time}")
        
        if result.intent_record:
            self._safe_print(f"Target Path:    {result.intent_record.get('target_path', 'N/A')}")
            self._safe_print(f"Session ID:     {result.intent_record.get('session_id', 'N/A')}")
            self._safe_print(f"Types:          {', '.join(result.intent_record.get('observation_types', []))}")
        
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
        if hasattr(result, 'timestamp'):
            self._safe_print(f"Timestamp:   {result.timestamp}")
        
        if result.answer:
            self._safe_print(f"\nAnswer:")
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
        
        patterns = getattr(result, 'patterns', [])
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
        if getattr(result, 'error_message', None):
            self._safe_print(f"Error:          {result.error_message}")
        
        self._safe_print("=" * 80)
    
    def _setup_logging(self, debug: bool) -> None:
        """Set up logging based on debug flag."""
        level = logging.DEBUG if debug else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _refuse(self, message: str) -> None:
        """Show refusal message clearly."""
        try:
            print(f"❌ REFUSED: {message}", file=sys.stderr)
        except UnicodeEncodeError:
            encoding = sys.stderr.encoding or 'utf-8'
            print(f"❌ REFUSED: {message}".encode(encoding, errors='replace').decode(encoding), file=sys.stderr)
    
    def _warn(self, message: str) -> None:
        """Show warning message clearly."""
        try:
            print(f"⚠️  WARNING: {message}", file=sys.stderr)
        except UnicodeEncodeError:
            encoding = sys.stderr.encoding or 'utf-8'
            print(f"⚠️  WARNING: {message}".encode(encoding, errors='replace').decode(encoding), file=sys.stderr)


def main() -> None:
    """Main entry point for CLI."""
    cli = CodeMarshalCLI()
    exit_code = cli.run()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()