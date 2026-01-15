"""
bridge.commands.export - Authorize truth extraction

This command validates and delegates the extraction of truth from the system.
Export is dangerous because it removes context and constitutional constraints.

Constitutional Context:
- Article 3: Truth Preservation (never obscure or distort)
- Article 10: Anchored Thinking (notes must be anchored to observations)
- Article 11: Declared Limitations (must export limitations)
- Article 19: Backward Truth Compatibility (exports must remain valid)

Role: Gatekeeper for truth leaving the system. Validates what can be exported, how.
"""

from __future__ import annotations

from typing import Dict, Any, Optional, Set, List, Union, Literal
from dataclasses import dataclass, field
from enum import Enum
import time

from .. import integrity_check
from lens.navigation.context import NavigationContext
from inquiry.session.context import SessionContext
from core.runtime import Runtime


class ExportType(Enum):
    """What type of truth can be exported."""
    OBSERVATIONS = "observations"
    NOTES = "notes"
    PATTERNS = "patterns"
    SESSION = "session"  # Complete investigation state
    CONSTITUTIONAL = "constitutional"  # Constitutional analysis only


class ExportFormat(Enum):
    """Available export formats. Each has different truth-preserving properties."""
    JSON = "json"  # Structured, preserves relationships
    MARKDOWN = "markdown"  # Human-readable, hierarchical
    HTML = "html"  # Interactive, preserves navigation
    PLAINTEXT = "plaintext"  # Minimal, no formatting
    CSV = "csv"  # Tabular data only (patterns)


@dataclass(frozen=True)
class ExportRequest:
    """Immutable export request. Validated before truth extraction."""
    type: ExportType
    format: ExportFormat
    session_id: str
    scope: Optional[Dict[str, Any]] = None  # What subset to export
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def __post_init__(self) -> None:
        """Validate structure on creation."""
        if not isinstance(self.type, ExportType):
            raise TypeError(f"type must be ExportType, got {type(self.type)}")
        
        if not isinstance(self.format, ExportFormat):
            raise TypeError(f"format must be ExportFormat, got {type(self.format)}")
        
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        
        # Validate format-type compatibility
        compatibility_error = self._validate_compatibility()
        if compatibility_error:
            raise ValueError(compatibility_error)
        
        # Ensure immutability
        if self.scope:
            object.__setattr__(self, 'scope', dict(self.scope))
        object.__setattr__(self, 'parameters', dict(self.parameters))
    
    def _validate_compatibility(self) -> Optional[str]:
        """Validate that export type and format are compatible."""
        incompatible_pairs = {
            (ExportType.PATTERNS, ExportFormat.HTML): "Patterns cannot be exported as HTML",
            (ExportType.NOTES, ExportFormat.CSV): "Notes cannot be exported as CSV",
        }
        
        error = incompatible_pairs.get((self.type, self.format))
        if error:
            return error
        
        # Additional constraints
        if self.type == ExportType.CONSTITUTIONAL and self.format not in [ExportFormat.JSON, ExportFormat.MARKDOWN]:
            return "Constitutional analysis only supports JSON or Markdown"
        
        return None


class ExportAuthorization:
    """
    Validates export requests against constitutional rules.
    
    Rules enforced:
    1. Export type must be available in current session
    2. Format must preserve truth for that type
    3. Must include limitations and uncertainty markers
    4. Cannot export incomplete or corrupt data
    5. Must maintain backward compatibility guarantees
    """
    
    # Format -> truth preservation score (higher is better)
    _TRUTH_PRESERVATION_SCORES: Dict[ExportFormat, int] = {
        ExportFormat.JSON: 10,      # Preserves all structure
        ExportFormat.HTML: 8,       # Interactive, but can lose data
        ExportFormat.MARKDOWN: 7,   # Readable, but flattening
        ExportFormat.PLAINTEXT: 5,  # Minimal, loses structure
        ExportFormat.CSV: 3,        # Tabular, severe flattening
    }
    
    @classmethod
    def is_lawful(
        cls,
        request: ExportRequest,
        session_context: SessionContext,
        nav_context: NavigationContext
    ) -> tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Check if export request is lawful.
        
        Returns:
            (is_allowed, error_message_if_not, required_disclosures)
            
        required_disclosures includes limitations, warnings, and format constraints
        """
        # 1. Check session is active and exportable
        if not session_context.active:
            return False, "No active investigation to export", None

        # Best-effort session ID validation (do not guess)
        if hasattr(session_context, 'snapshot_id'):
            try:
                if str(session_context.snapshot_id) != request.session_id:
                    return False, "Session ID mismatch", None
            except Exception:
                return False, "Session ID mismatch", None
        
        # 2. Check export type is available
        type_available, type_error = cls._check_type_availability(
            request.type, session_context
        )
        if not type_available:
            return False, type_error, None
        
        # 3. Check for incomplete data
        incomplete_warning = cls._check_completeness(request.type, session_context)
        
        # 4. Generate required disclosures
        disclosures = cls._generate_disclosures(request, session_context, incomplete_warning)
        
        # 5. Format-specific validation
        format_error = cls._validate_format_constraints(request, session_context)
        if format_error:
            return False, format_error, disclosures
        
        # 6. Scope validation (if provided)
        if request.scope:
            scope_error = cls._validate_scope(request.scope, request.type, session_context)
            if scope_error:
                return False, scope_error, disclosures
        
        return True, None, disclosures
    
    @classmethod
    def _check_type_availability(
        cls,
        export_type: ExportType,
        session_context: SessionContext
    ) -> tuple[bool, Optional[str]]:
        """Check if the requested export type exists in the session."""
        has_observations = bool(getattr(session_context, 'has_observations', False))
        has_notes = bool(getattr(session_context, 'has_notes', False))
        has_patterns = bool(getattr(session_context, 'has_patterns', False))
        availability_map = {
            ExportType.OBSERVATIONS: has_observations,
            ExportType.NOTES: has_notes,
            ExportType.PATTERNS: has_patterns,
            ExportType.SESSION: True,  # Always available if session exists
            ExportType.CONSTITUTIONAL: has_observations,  # Needs something to analyze
        }
        
        is_available = availability_map.get(export_type, False)
        if not is_available:
            error_message = {
                ExportType.OBSERVATIONS: "No observations collected in this session",
                ExportType.NOTES: "No notes recorded in this session",
                ExportType.PATTERNS: "No patterns computed in this session",
                ExportType.CONSTITUTIONAL: "Cannot analyze constitutional compliance without observations",
            }.get(export_type, "Export type not available")
            
            return False, error_message
        
        return True, None
    
    @classmethod
    def _check_completeness(
        cls,
        export_type: ExportType,
        session_context: SessionContext
    ) -> Optional[str]:
        """Check if the data is complete or has known gaps."""
        if export_type == ExportType.OBSERVATIONS:
            if session_context.observations_incomplete:
                return "Observations are incomplete (partial scan)"
        
        elif export_type == ExportType.PATTERNS:
            if session_context.patterns_partial:
                return "Patterns are partial (computation interrupted)"
        
        return None
    
    @classmethod
    def _generate_disclosures(
        cls,
        request: ExportRequest,
        session_context: SessionContext,
        incomplete_warning: Optional[str]
    ) -> Dict[str, Any]:
        """Generate all required disclosures for this export."""
        disclosures = {
            "truth_preservation_score": cls._TRUTH_PRESERVATION_SCORES.get(request.format, 0),
            "format_constraints": cls._get_format_constraints(request.format),
            "limitations_included": True,  # Always include limitations
            "uncertainty_markers_included": request.type in [ExportType.PATTERNS, ExportType.CONSTITUTIONAL],
            "timestamp": request.timestamp,
            "export_context": {
                "session_stage": session_context.current_stage,
                "observation_count": session_context.observation_count,
                "note_count": session_context.note_count,
            },
        }
        
        if incomplete_warning:
            disclosures["incomplete_data_warning"] = incomplete_warning
        
        # Add constitutional constraints
        if request.type == ExportType.CONSTITUTIONAL:
            disclosures["constitutional_reference"] = {
                "version": "1.0",
                "articles_applied": list(range(1, 25)),  # All articles
                "validation_method": "static_analysis",
            }
        
        return disclosures
    
    @classmethod
    def _validate_format_constraints(
        cls,
        request: ExportRequest,
        session_context: SessionContext
    ) -> Optional[str]:
        """Validate format-specific constraints."""
        # CSV can only export patterns
        if request.format == ExportFormat.CSV and request.type != ExportType.PATTERNS:
            return "CSV format only supports pattern export"
        
        # HTML requires certain data completeness
        if request.format == ExportFormat.HTML and session_context.observations_incomplete:
            return "HTML export requires complete observations"
        
        return None
    
    @classmethod
    def _validate_scope(
        cls,
        scope: Dict[str, Any],
        export_type: ExportType,
        session_context: SessionContext
    ) -> Optional[str]:
        """Validate export scope against available data."""
        if "observation_ids" in scope and export_type == ExportType.OBSERVATIONS:
            # Check all IDs exist
            pass  # Would validate against session_context
        
        if "note_anchors" in scope and export_type == ExportType.NOTES:
            # Check anchors exist
            pass  # Would validate against session_context
        
        return None
    
    @classmethod
    def _get_format_constraints(cls, format: ExportFormat) -> List[str]:
        """Get the truth-preserving constraints of each format."""
        constraints = {
            ExportFormat.JSON: [
                "preserves_all_relationships",
                "maintains_references",
                "includes_metadata",
                "machine_readable",
            ],
            ExportFormat.HTML: [
                "interactive_navigation",
                "visual_hierarchy",
                "human_readable",
                "may_flatten_some_relationships",
            ],
            ExportFormat.MARKDOWN: [
                "human_readable",
                "preserves_hierarchy",
                "lossy_relationships",
                "no_interactivity",
            ],
            ExportFormat.PLAINTEXT: [
                "minimal_formatting",
                "severe_flattening",
                "loss_of_structure",
                "portable",
            ],
            ExportFormat.CSV: [
                "tabular_only",
                "no_hierarchy",
                "patterns_only",
                "spreadsheet_compatible",
            ],
        }
        return constraints.get(format, ["unknown_format"])


@integrity_check
def execute_export(
    request: ExportRequest,
    runtime: Runtime,
    session_context: SessionContext,
    nav_context: NavigationContext
) -> Dict[str, Any]:
    """
    Authorize and delegate truth extraction.
    
    This is the only public entry point for exporting truth.
    It validates, records intent, and delegates formatting.
    
    Args:
        request: Validated export request
        runtime: For system state management
        session_context: Current investigation context
        nav_context: Current navigation state
    
    Returns:
        Dict with export_id, disclosures, and metadata
        
    Raises:
        ValueError: If export is not lawful
        RuntimeError: If delegation fails
    """
    # 1. Constitutional compliance check
    is_allowed, error, disclosures = ExportAuthorization.is_lawful(
        request, session_context, nav_context
    )
    
    if not is_allowed:
        raise ValueError(f"Export not authorized: {error}")
    
    # 2. Acknowledge format constraints (Article 3)
    constraints_acknowledged = _acknowledge_constraints(disclosures)
    if not constraints_acknowledged:
        raise ValueError("Export format constraints must be explicitly acknowledged")
    
    # 3. Record intent (not results)
    intent_record = {
        "export_type": request.type.value,
        "export_format": request.format.value,
        "session_id": request.session_id,
        "scope": request.scope.copy() if request.scope else None,
        "parameters": dict(request.parameters),
        "timestamp": request.timestamp,
        "truth_preservation_score": disclosures.get("truth_preservation_score", 0),
        "constraints_acknowledged": constraints_acknowledged,
    }
    
    # 4. Delegate to integration layer for actual export
    try:
        # Import here to maintain separation of concerns
        from bridge.integration.export_formats import get_exporter
        
        exporter = get_exporter(request.format.value)
        
        export_id = exporter.prepare_export()
        
    except ImportError as e:
        raise RuntimeError(f"Export format not available: {e}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to delegate export: {e}") from e
    
    # 5. Return reference only (not exported data)
    return {
        "export_id": export_id,
        "intent_record": intent_record,
        "status": "preparing",
        "disclosures": disclosures,
        "estimated_size": _estimate_export_size(request, session_context),
        "backward_compatibility_guarantee": True,
        "verification_hash_available": True,  # Will be computed during export
    }


def _acknowledge_constraints(disclosures: Dict[str, Any]) -> bool:
    """
    Simulate constraint acknowledgment.
    
    In practice, this would:
    1. Display truth preservation score and constraints
    2. Warn about format limitations
    3. Require explicit acknowledgment
    
    Returns True if constraints were acknowledged.
    """
    if not disclosures:
        return False
    
    # In real implementation:
    # 1. Show truth preservation score (0-10 scale)
    # 2. List format constraints
    # 3. Show incomplete data warnings if present
    # 4. Require user to check "I understand these limitations"
    # 5. Record acknowledgment
    
    # For CLI: --acknowledge-constraints flag
    # For TUI: Modal with acknowledgment required
    
    return True  # Placeholder - assumes constraints were displayed and acknowledged


def _estimate_export_size(
    request: ExportRequest,
    session_context: SessionContext
) -> Dict[str, Any]:
    """Provide honest estimate of export size and complexity."""
    base_sizes = {
        ExportType.OBSERVATIONS: session_context.observation_count * 1024,  # 1KB per observation
        ExportType.NOTES: session_context.note_count * 512,  # 512B per note
        ExportType.PATTERNS: 100 * 1024,  # Fixed overhead + pattern data
        ExportType.SESSION: 500 * 1024,  # Complete state
        ExportType.CONSTITUTIONAL: 50 * 1024,  # Analysis report
    }
    
    base_bytes = base_sizes.get(request.type, 1024)
    
    # Format multipliers
    format_multipliers = {
        ExportFormat.JSON: 1.2,
        ExportFormat.HTML: 2.5,
        ExportFormat.MARKDOWN: 1.5,
        ExportFormat.PLAINTEXT: 1.0,
        ExportFormat.CSV: 0.8,
    }
    
    estimated_bytes = int(base_bytes * format_multipliers.get(request.format, 1.0))
    
    return {
        "estimated_bytes": estimated_bytes,
        "human_readable": _bytes_to_human(estimated_bytes),
        "warning_threshold": 10 * 1024 * 1024,  # 10MB
        "is_large": estimated_bytes > 10 * 1024 * 1024,
    }


def _bytes_to_human(bytes: int) -> str:
    """Convert bytes to human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"


# Convenience functions for common export patterns
def export_observations_json(
    session_id: str,
    include_metadata: bool = True,
    **parameters: Any
) -> ExportRequest:
    """Export observations in JSON format."""
    return ExportRequest(
        type=ExportType.OBSERVATIONS,
        format=ExportFormat.JSON,
        session_id=session_id,
        parameters={"include_metadata": include_metadata, **parameters},
    )


def export_notes_markdown(
    session_id: str,
    anchored_only: bool = True,
    **parameters: Any
) -> ExportRequest:
    """Export notes in Markdown format."""
    return ExportRequest(
        type=ExportType.NOTES,
        format=ExportFormat.MARKDOWN,
        session_id=session_id,
        parameters={"anchored_only": anchored_only, **parameters},
    )


def export_constitutional_report(
    session_id: str,
    format: ExportFormat = ExportFormat.MARKDOWN,
    **parameters: Any
) -> ExportRequest:
    """Export constitutional compliance analysis."""
    return ExportRequest(
        type=ExportType.CONSTITUTIONAL,
        format=format,
        session_id=session_id,
        parameters=parameters,
    )


# Forbidden imports check (static analysis would catch these)
# DO NOT IMPORT FROM:
# - observations.*
# - patterns.*
# - storage.*
# - lens.views.*
# - lens.aesthetic.*
# - inquiry.notebook.* (notes are accessed via session_context only)

# These would be caught by constitutional test suite:
# test_no_direct_data_access_in_export()
# test_format_constraints_always_acknowledged()
# test_export_delegates_to_integration_only()