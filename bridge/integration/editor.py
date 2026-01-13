"""
Editor integration for truth preservation.

This module maps observations to editor locations without controlling editors.
Editors may show truth, not summon it.
"""

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Set
from enum import Enum
import textwrap

# Allowed imports
from observations.record.anchors import Anchor
from observations.record.snapshot import Snapshot
from inquiry.notebook.entries import NotebookEntry
from lens.indicators.errors import ErrorSeverity
from bridge.commands.export import ExportCommand  # read-only metadata


class EditorType(Enum):
    """Finite set of supported editor integrations."""
    VSCODE = "vscode"
    NEOVIM = "neovim"
    SUPPORTED_EDITORS = [VSCODE, NEOVIM]  # Explicit finite set


@dataclass(frozen=True)
class EditorLocation:
    """
    A stable reference to a location in an editor.
    
    This is a one-way mapping from anchor to editor location.
    The editor does not control this mapping.
    """
    path: Path
    line: Optional[int] = None
    column: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    
    def to_vscode_range(self) -> Dict[str, Any]:
        """Convert to VS Code range format."""
        if self.line is None:
            return {}
        
        range_dict = {
            "start": {
                "line": self.line - 1,  # VS Code uses 0-indexed lines
                "character": (self.column - 1) if self.column else 0
            }
        }
        
        if self.end_line:
            range_dict["end"] = {
                "line": self.end_line - 1,
                "character": (self.end_column - 1) if self.end_column else 0
            }
        else:
            # Single line range
            range_dict["end"] = range_dict["start"].copy()
        
        return range_dict
    
    def to_neovim_position(self) -> str:
        """Convert to Neovim position string."""
        if self.line is None:
            return str(self.path)
        
        if self.column:
            return f"{self.path}:{self.line}:{self.column}"
        return f"{self.path}:{self.line}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to generic dictionary format."""
        return {
            "path": str(self.path),
            "line": self.line,
            "column": self.column,
            "end_line": self.end_line,
            "end_column": self.end_column
        }


@dataclass(frozen=True)
class EditorAnnotation:
    """
    An annotation that can be shown in an editor without controlling it.
    
    This is side-channel information only. The editor may choose to show it.
    """
    location: EditorLocation
    message: str
    severity: ErrorSeverity
    source: str = "CodeMarshal"
    anchor_id: Optional[str] = None
    
    # Explicit non-features
    actions: List[str] = field(default_factory=lambda: [])  # No actions allowed
    is_fixable: bool = False  # Cannot suggest fixes
    is_autofix: bool = False  # Cannot auto-fix
    
    def to_vscode_diagnostic(self) -> Dict[str, Any]:
        """Convert to VS Code Diagnostic format."""
        return {
            "range": self.location.to_vscode_range(),
            "message": self.message,
            "severity": self._vscode_severity(),
            "source": self.source
        }
    
    def to_neovim_quickfix(self) -> Dict[str, Any]:
        """Convert to Neovim quickfix format."""
        return {
            "filename": str(self.location.path),
            "lnum": self.location.line or 0,
            "col": self.location.column or 0,
            "text": f"[{self.source}] {self.message}",
            "type": self._neovim_severity_char()
        }
    
    def _vscode_severity(self) -> int:
        """Map to VS Code DiagnosticSeverity."""
        mapping = {
            ErrorSeverity.ERROR: 1,      # Error
            ErrorSeverity.WARNING: 2,    # Warning
            ErrorSeverity.INFO: 3,       # Information
            ErrorSeverity.HINT: 4        # Hint
        }
        return mapping.get(self.severity, 2)
    
    def _neovim_severity_char(self) -> str:
        """Map to Neovim quickfix severity character."""
        mapping = {
            ErrorSeverity.ERROR: "E",
            ErrorSeverity.WARNING: "W",
            ErrorSeverity.INFO: "I",
            ErrorSeverity.HINT: "N"  # Note
        }
        return mapping.get(self.severity, "W")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to generic dictionary format."""
        return {
            "location": self.location.to_dict(),
            "message": self.message,
            "severity": self.severity.value,
            "source": self.source,
            "anchor_id": self.anchor_id,
            "disclaimer": "This is a read-only annotation. No actions available."
        }


class EditorIntegration:
    """
    Maps observations to editor locations without editor control.
    
    Key principles:
    1. Read-only: Only shows what exists, never modifies
    2. No control: Does not navigate, open files, or trigger commands
    3. No inference: Only maps existing anchors and notes
    4. No background processes: One-time generation only
    """
    
    def __init__(self, editor_type: EditorType):
        if editor_type not in EditorType.SUPPORTED_EDITORS:
            raise ValueError(
                f"Unsupported editor type: {editor_type}. "
                f"Supported: {[e.value for e in EditorType.SUPPORTED_EDITORS]}"
            )
        self.editor_type = editor_type
        self.generated_at = datetime.now(timezone.utc)
    
    def map_anchors_to_locations(
        self,
        anchors: List[Anchor]
    ) -> List[EditorLocation]:
        """
        Map anchors to editor locations without editor control.
        
        This is a pure mapping function. It does not:
        - Open files
        - Navigate to locations
        - Create editor sessions
        """
        locations: List[EditorLocation] = []
        
        for anchor in anchors:
            # Extract location information from anchor
            # In real implementation, Anchor would have location parsing
            location = self._parse_anchor_location(anchor)
            if location:
                locations.append(location)
        
        return locations
    
    def create_annotations_from_notes(
        self,
        notes: List[NotebookEntry],
        anchor_mapping: Dict[str, EditorLocation]
    ) -> List[EditorAnnotation]:
        """
        Create editor annotations from notebook entries.
        
        Notes become side-channel annotations that editors may show.
        No control over when or how they are shown.
        """
        annotations: List[EditorAnnotation] = []
        
        for note in notes:
            # Get location for this note's anchor
            location = anchor_mapping.get(note.anchor_id)
            if not location:
                continue
            
            # Create annotation
            annotation = EditorAnnotation(
                location=location,
                message=self._format_note_message(note),
                severity=ErrorSeverity.INFO,  # Notes are informational
                anchor_id=note.anchor_id
            )
            annotations.append(annotation)
        
        return annotations
    
    def generate_configuration(
        self,
        locations: List[EditorLocation],
        annotations: List[EditorAnnotation]
    ) -> Dict[str, Any]:
        """
        Generate editor configuration for viewing truth.
        
        This configuration:
        - Shows where observations exist
        - Shows annotations from notes
        - Does not enable any editor control
        
        The editor may ignore this configuration.
        """
        metadata = {
            "generated_by": "CodeMarshal",
            "generated_at": self.generated_at.isoformat(),
            "editor_type": self.editor_type.value,
            "warning": "This configuration is read-only. It shows truth but cannot control the editor.",
            "constitutional_article": "Article 12: Local Operation"
        }
        
        if self.editor_type == EditorType.VSCODE:
            return self._generate_vscode_config(locations, annotations, metadata)
        elif self.editor_type == EditorType.NEOVIM:
            return self._generate_neovim_config(locations, annotations, metadata)
        else:
            # Generic fallback
            return self._generate_generic_config(locations, annotations, metadata)
    
    def export_configuration(
        self,
        config: Dict[str, Any],
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Export configuration to a file.
        
        The file can be loaded by the editor (or ignored).
        No guarantee that the editor will use it.
        """
        if output_path is None:
            timestamp = self.generated_at.strftime("%Y%m%d_%H%M%S")
            filename = f"codemarshal_{self.editor_type.value}_config_{timestamp}.json"
            output_path = Path.cwd() / filename
        
        # Write configuration
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, default=str)
        
        # Generate README explaining limitations
        self._generate_readme(output_path.parent)
        
        return output_path
    
    def _parse_anchor_location(self, anchor: Anchor) -> Optional[EditorLocation]:
        """
        Parse anchor to extract editor location.
        
        In real implementation, Anchor would have proper location parsing.
        This is a placeholder showing the intent.
        """
        # Example: Anchor might have location in format "path/to/file.py:10:5"
        # For now, return a minimal location
        if hasattr(anchor, 'location_str'):
            # Parse location string
            parts = str(anchor.location_str).split(':')
            if len(parts) >= 1:
                path = Path(parts[0])
                line = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
                column = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
                return EditorLocation(path=path, line=line, column=column)
        
        # Fallback: anchor has file path only
        if hasattr(anchor, 'file_path'):
            return EditorLocation(path=Path(anchor.file_path))
        
        return None
    
    def _format_note_message(self, note: NotebookEntry) -> str:
        """Format note content for editor display."""
        # Truncate if too long
        content = note.content
        if len(content) > 200:
            content = content[:197] + "..."
        
        # Add timestamp
        timestamp = note.created_at.strftime("%Y-%m-%d %H:%M")
        return f"[{timestamp}] {content}"
    
    def _generate_vscode_config(
        self,
        locations: List[EditorLocation],
        annotations: List[EditorAnnotation],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate VS Code specific configuration."""
        config = {
            "version": "0.1.0",
            "metadata": metadata,
            "tasks": [
                {
                    "label": "CodeMarshal: View Observations",
                    "type": "shell",
                    "command": "echo",
                    "args": ["Open the CodeMarshal configuration file to see observation locations"],
                    "problemMatcher": []
                }
            ],
            "settings": {
                "codemarshal.enabled": True,
                "codemarshal.readOnly": True,
                "codemarshal.annotationSource": "codemarshal_annotations.json",
                "codemarshal.warning": "This extension only shows observations. It cannot analyze or modify code."
            },
            "observations": {
                "locations": [loc.to_dict() for loc in locations],
                "count": len(locations),
                "note": "These are observation locations only. No navigation control provided."
            }
        }
        
        # Add annotations if any
        if annotations:
            config["annotations"] = {
                "diagnostics": [ann.to_vscode_diagnostic() for ann in annotations],
                "source": "CodeMarshal Notebook",
                "warning": "Annotations are informational only. No quick fixes available."
            }
        
        return config
    
    def _generate_neovim_config(
        self,
        locations: List[EditorLocation],
        annotations: List[EditorAnnotation],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate Neovim specific configuration."""
        config = {
            "metadata": metadata,
            "vimscript": [
                '" CodeMarshal Neovim Configuration - READ ONLY',
                '" This file shows observation locations but does not control Neovim',
                '',
                '" Load observation locations into quickfix list (optional)',
                '" command! -nargs=0 CodeMarshalLoadObs call codemarshal#LoadObservations()',
                '',
                '" View annotations (if any)',
                '" command! -nargs=0 CodeMarshalShowNotes call codemarshal#ShowAnnotations()',
                '',
                '" DISCLAIMER: This plugin only displays existing observations.',
                '" It cannot analyze code, run commands, or modify files.'
            ],
            "lua_config": [
                '-- CodeMarshal Lua configuration',
                'local codemarshal = {}',
                '',
                'function codemarshal.load_locations(locations)',
                '  -- Convert locations to quickfix format',
                '  local qf_items = {}',
                '  for _, loc in ipairs(locations) do',
                '    table.insert(qf_items, {',
                '      filename = loc.path,',
                '      lnum = loc.line or 1,',
                '      text = "CodeMarshal observation point"',
                '    })',
                '  end',
                '  vim.fn.setqflist(qf_items, "r")',
                '  print("Loaded " .. #qf_items .. " observation locations")',
                'end',
                '',
                'function codemarshal.show_annotations(annotations)',
                '  -- Display annotations in location list',
                '  local loc_items = {}',
                '  for _, ann in ipairs(annotations) do',
                '    table.insert(loc_items, {',
                '      filename = ann.location.path,',
                '      lnum = ann.location.line or 1,',
                '      col = ann.location.column or 1,',
                '      text = ann.message',
                '    })',
                '  end',
                '  vim.fn.setloclist(0, loc_items, "r")',
                '  vim.cmd("lopen")',
                'end',
                '',
                'return codemarshal'
            ],
            "observations": {
                "locations": [loc.to_neovim_position() for loc in locations],
                "quickfix_format": [loc.to_dict() for loc in locations],
                "note": "Use :copen to view quickfix list. No automatic navigation."
            }
        }
        
        # Add annotations if any
        if annotations:
            config["annotations"] = {
                "quickfix_items": [ann.to_neovim_quickfix() for ann in annotations],
                "note": "Annotations are from notebook entries. No actions attached."
            }
        
        return config
    
    def _generate_generic_config(
        self,
        locations: List[EditorLocation],
        annotations: List[EditorAnnotation],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate generic editor configuration."""
        config = {
            "metadata": metadata,
            "observations": {
                "locations": [loc.to_dict() for loc in locations],
                "count": len(locations),
                "formats": {
                    "path_only": [str(loc.path) for loc in locations],
                    "with_lines": [loc.to_neovim_position() for loc in locations if loc.line]
                }
            },
            "annotations": {
                "notes": [ann.to_dict() for ann in annotations],
                "count": len(annotations),
                "severity_breakdown": self._count_severities(annotations)
            },
            "usage": {
                "1": "This file contains observation locations from CodeMarshal.",
                "2": "It is read-only and does not control your editor.",
                "3": "You can manually navigate to these locations if desired.",
                "4": "Annotations are informational notes only.",
                "5": "No commands, actions, or automatic behavior is provided."
            }
        }
        
        return config
    
    def _count_severities(self, annotations: List[EditorAnnotation]) -> Dict[str, int]:
        """Count annotation severities."""
        counts: Dict[str, int] = {}
        for ann in annotations:
            severity = ann.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts
    
    def _generate_readme(self, directory: Path) -> None:
        """Generate README explaining editor integration limitations."""
        readme_path = directory / "README_editor_integration.md"
        
        content = textwrap.dedent("""
        # CodeMarshal Editor Integration
        
        ## What This Is
        
        This configuration file contains **observation locations** and **annotations** from CodeMarshal.
        
        ## What This Does **NOT** Do
        
        1. **Does NOT control your editor**
        2. **Does NOT open files automatically**
        3. **Does NOT navigate to locations**
        4. **Does NOT run commands**
        5. **Does NOT modify code**
        6. **Does NOT analyze or interpret code**
        7. **Does NOT create background processes**
        8. **Does NOT connect to network**
        
        ## Constitutional Constraints
        
        This integration follows CodeMarshal's Constitutional Article 12: **Local Operation**.
        
        > "All analysis works without network connectivity. No cloud dependencies for core functionality. Truth should not depend on external services."
        
        ## How To Use (Manually)
        
        1. **View observations**: Manually open the files listed in the configuration
        2. **See annotations**: Check the annotations section for notes
        3. **No automation**: Everything is manual by design
        
        ## Mental Model
        
        The editor is a **window**, not a **handle**.
        
        - Window: Shows what exists
        - Handle: Controls what happens
        
        CodeMarshal only provides things to look at, not things to click.
        
        ## Supported Editors
        
        - VS Code: Configuration for showing diagnostics
        - Neovim: Quickfix/location list configuration
        - Any editor: Generic JSON format
        
        ## Truth Preservation
        
        This configuration contains only:
        - Locations where observations were made
        - Annotations from human notes
        - No inferences, guesses, or interpretations
        
        When you look at these locations in your editor, you see the **actual code**, not CodeMarshal's interpretation of it.
        
        ---
        
        *Generated by CodeMarshal - A truth-preserving investigation environment*
        """)
        
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(content)


# Factory function for easy access
def create_editor_integration(
    editor_type: Union[EditorType, str]
) -> EditorIntegration:
    """
    Create editor integration for specified editor.
    
    Args:
        editor_type: Either EditorType enum or string value
        
    Returns:
        EditorIntegration instance
        
    Raises:
        ValueError: If editor type is not supported
    """
    if isinstance(editor_type, str):
        try:
            editor_type = EditorType(editor_type.lower())
        except ValueError:
            raise ValueError(
                f"Unsupported editor: {editor_type}. "
                f"Supported: {[e.value for e in EditorType.SUPPORTED_EDITORS]}"
            )
    
    return EditorIntegration(editor_type)


def list_supported_editors() -> List[Dict[str, Any]]:
    """List all supported editors with their capabilities."""
    return [
        {
            "editor": EditorType.VSCODE.value,
            "capabilities": [
                "Show observation locations as file paths",
                "Display annotations as diagnostics",
                "No navigation control",
                "No file modification"
            ],
            "limitations": [
                "Cannot open files automatically",
                "Cannot run CodeMarshal commands",
                "No background watching",
                "Read-only annotations only"
            ]
        },
        {
            "editor": EditorType.NEOVIM.value,
            "capabilities": [
                "Load observation locations into quickfix",
                "Show annotations in location list",
                "No automatic behavior",
                "Manual navigation only"
            ],
            "limitations": [
                "No plugin auto-installation",
                "No command execution",
                "No file system watching",
                "Configuration must be manually loaded"
            ]
        }
    ]