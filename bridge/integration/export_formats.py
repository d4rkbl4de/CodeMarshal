"""
Export formats for truth preservation.

This module defines how truth leaves the system without mutation.
Every export format must be explicit about what it loses.
"""

import json
import textwrap
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from inquiry.notebook.entries import NoteEntry
from observations.record.anchors import Anchor
from observations.record.integrity import IntegrityRoot

# Allowed imports
from observations.record.snapshot import Snapshot


class ExportFormat(Enum):
    """Finite set of supported export formats."""

    JSON = "json"
    MARKDOWN = "markdown"
    PLAIN_TEXT = "plain_text"


@dataclass(frozen=True)
class ExportLimitations:
    """
    Explicit declaration of what this export format cannot preserve.

    Every export must include this as metadata.
    """

    format_type: ExportFormat
    context_loss: list[str]  # What is lost in translation
    structure_loss: list[str]  # What structural information is lost
    cannot_express: list[str]  # What cannot be expressed at all

    def to_dict(self) -> dict[str, Any]:
        return {
            "format_type": self.format_type.value,
            "context_loss": self.context_loss,
            "structure_loss": self.structure_loss,
            "cannot_express": self.cannot_express,
            "generated_at": datetime.now(UTC).isoformat(),
        }


class BaseExporter:
    """Base class for all exporters. Enforces limitation declaration."""

    def __init__(self, format_type: ExportFormat):
        self.format_type = format_type
        self.limitations = self._define_limitations()

    def _define_limitations(self) -> ExportLimitations:
        """Override in subclasses to declare format-specific limitations."""
        raise NotImplementedError("Every exporter must declare its limitations")

    def export(
        self,
        snapshot: Snapshot | None = None,
        anchors: list[Anchor] | None = None,
        notebook_entries: list[NoteEntry] | None = None,
        integrity_hashes: list[IntegrityRoot] | None = None,
    ) -> str:
        """Export truth in this format. Must include limitations metadata."""
        raise NotImplementedError("Export method must be implemented")

    def prepare_export(self) -> str:
        """Prepare export and return export ID."""
        # In real implementation, this would set up the export pipeline
        # For now, return a mock export ID
        import uuid

        return str(uuid.uuid4())

    def _create_metadata(
        self, snapshot_version: str | None = None, export_scope: str | None = None
    ) -> dict[str, Any]:
        """Create standard metadata header for all exports."""
        return {
            "codemarshal_version": "0.1.0",  # Should come from pyproject.toml in real impl
            "format": self.format_type.value,
            "exported_at": datetime.now(UTC).isoformat(),
            "snapshot_version": snapshot_version,
            "export_scope": export_scope,
            "limitations": self.limitations.to_dict(),
            "warning": "This export is a flattened representation. Context may be lost.",
            "source_system": "CodeMarshal Truth-Preserving Investigation",
            "constitutional_article": "Article 19: Backward Truth Compatibility",
        }


class JSONExporter(BaseExporter):
    """JSON export format. Preserves structure but loses some semantic context."""

    def __init__(self):
        super().__init__(ExportFormat.JSON)

    def _define_limitations(self) -> ExportLimitations:
        return ExportLimitations(
            format_type=ExportFormat.JSON,
            context_loss=[
                "Hierarchical observation relationships become flat lists",
                "Temporal investigation sequence is lost (only final state remains)",
                "Progressive disclosure context is flattened",
            ],
            structure_loss=[
                "Visual grouping and spatial relationships are lost",
                "Color-coded severity indicators become plain text",
                "Interactive navigation paths are removed",
            ],
            cannot_express=[
                "Live investigation state (paused, in-progress)",
                "Uncertainty visualizations (⚠️ symbols lose their meaning)",
                "User interface affordances (what can be done next)",
            ],
        )

    def export(
        self,
        snapshot: Snapshot | None = None,
        anchors: list[Anchor] | None = None,
        notebook_entries: list[NoteEntry] | None = None,
        integrity_hashes: list[IntegrityRoot] | None = None,
    ) -> str:
        """Export as JSON with explicit structure preservation."""

        metadata = self._create_metadata(
            snapshot_version=snapshot.version if snapshot else None,
            export_scope="full" if snapshot else "partial",
        )

        # Build export structure
        export_data: dict[str, Any] = {
            "metadata": metadata,
            "limitations_declaration": self.limitations.to_dict(),
        }

        # Add observations if provided
        if snapshot:
            export_data["observations"] = self._serialize_snapshot(snapshot)

        # Add anchors if provided
        if anchors:
            export_data["anchors"] = [
                self._serialize_anchor(anchor) for anchor in anchors
            ]

        # Add notebook entries if provided
        if notebook_entries:
            export_data["notebook"] = [
                self._serialize_notebook_entry(entry) for entry in notebook_entries
            ]

        # Add integrity information if provided
        if integrity_hashes:
            export_data["integrity"] = [
                self._serialize_integrity_root(root_obj)
                for root_obj in integrity_hashes
            ]

        # Export with readable formatting and sorted keys for determinism
        return json.dumps(
            export_data, indent=2, sort_keys=True, default=self._json_serializer
        )

    def _serialize_snapshot(self, snapshot: Snapshot) -> dict[str, Any]:
        """Convert snapshot to JSON-serializable format."""
        # In real implementation, Snapshot would have a to_dict() method
        # This is a placeholder for the structure
        return {
            "id": snapshot.id,
            "version": snapshot.version,
            "created_at": snapshot.created_at.isoformat()
            if hasattr(snapshot, "created_at")
            else None,
            "observation_count": getattr(snapshot, "observation_count", 0),
            "path": str(snapshot.path) if hasattr(snapshot, "path") else None,
            "note": "Snapshot serialization preserves observation facts but loses investigation context",
        }

    def _serialize_anchor(self, anchor: Anchor) -> dict[str, Any]:
        """Convert anchor to JSON-serializable format."""
        return {
            "type": anchor.type,
            "location": str(anchor.location),
            "identifier": anchor.identifier,
            "context": anchor.context if hasattr(anchor, "context") else None,
        }

    def _serialize_notebook_entry(self, entry: NoteEntry) -> dict[str, Any]:
        """Convert notebook entry to JSON-serializable format."""
        return {
            "id": getattr(entry, "id", "unknown"),
            "created_at": getattr(entry, "created_at", None).isoformat()
            if getattr(entry, "created_at", None)
            else None,
            "anchor_id": getattr(entry, "anchor_id", None),
            "content": getattr(entry, "content", ""),
            "tags": getattr(entry, "tags", []),
        }

    def _serialize_integrity_root(
        self, integrity_root: IntegrityRoot
    ) -> dict[str, Any]:
        """Convert integrity root to JSON-serializable format."""
        return integrity_root.to_dict()

    def _json_serializer(self, obj: Any) -> Any:
        """Custom JSON serializer for non-standard types."""
        if isinstance(obj, Path):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class MarkdownExporter(BaseExporter):
    """Markdown export format. Human-readable but loses machine structure."""

    def __init__(self):
        super().__init__(ExportFormat.MARKDOWN)

    def _define_limitations(self) -> ExportLimitations:
        return ExportLimitations(
            format_type=ExportFormat.MARKDOWN,
            context_loss=[
                "Machine-readable structure is replaced with human-oriented formatting",
                "Exact data types and constraints are not preserved",
                "Programmatic validation rules are lost",
            ],
            structure_loss=[
                "Type hierarchies become flat bullet lists",
                "Complex relationships become simple cross-references",
                "Metadata becomes inline text",
            ],
            cannot_express=[
                "Interactive elements (cannot click through)",
                "Real-time validation feedback",
                "Dynamic content loading",
            ],
        )

    def export(
        self,
        snapshot: Snapshot | None = None,
        anchors: list[Anchor] | None = None,
        notebook_entries: list[NoteEntry] | None = None,
        integrity_hashes: list[IntegrityRoot] | None = None,
    ) -> str:
        """Export as Markdown with clear section organization."""

        lines: list[str] = []

        # Header
        lines.append("# CodeMarshal Investigation Export")
        lines.append(f"*Format: {self.format_type.value}*")
        lines.append(
            f"*Exported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}*"
        )
        lines.append("")

        # Limitations Warning
        lines.append("## ⚠️ Export Limitations")
        lines.append("")
        lines.append("**This is a flattened representation of truth.**")
        lines.append("")
        lines.append("### Context Loss")
        for loss in self.limitations.context_loss:
            lines.append(f"- {loss}")
        lines.append("")
        lines.append("### Structure Loss")
        for loss in self.limitations.structure_loss:
            lines.append(f"- {loss}")
        lines.append("")
        lines.append("### Cannot Express")
        for cannot_express in self.limitations.cannot_express:
            lines.append(f"- {cannot_express}")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Snapshot Information
        if snapshot:
            lines.append("## 📸 Snapshot")
            lines.append("")
            lines.append(f"- **ID**: `{snapshot.id}`")
            lines.append(f"- **Version**: `{snapshot.version}`")
            if hasattr(snapshot, "created_at"):
                lines.append(
                    f"- **Created**: {snapshot.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            if hasattr(snapshot, "path"):
                lines.append(f"- **Path**: `{snapshot.path}`")
            if hasattr(snapshot, "observation_count"):
                lines.append(f"- **Observations**: {snapshot.observation_count}")
            lines.append("")

        # Anchors
        if anchors:
            lines.append("## 🔗 Anchors")
            lines.append("")
            for i, anchor in enumerate(anchors, 1):
                lines.append(f"### Anchor {i}: {anchor.type}")
                lines.append(f"- **Location**: `{anchor.location}`")
                lines.append(f"- **Identifier**: `{anchor.identifier}`")
                if hasattr(anchor, "context") and anchor.context:
                    lines.append(f"- **Context**: {anchor.context}")
                lines.append("")

        # Notebook Entries
        if notebook_entries:
            lines.append("## 📓 Investigation Notes")
            lines.append("")
            lines.append("*Notes are anchored to observations and preserve thinking.*")
            lines.append("")

            for entry in notebook_entries:
                lines.append(
                    f"### Note: {getattr(entry, 'created_at', None).strftime('%Y-%m-%d %H:%M') if getattr(entry, 'created_at', None) else 'Unknown'}"
                )
                lines.append(f"**Anchor**: `{getattr(entry, 'anchor_id', None)}`")
                lines.append("")
                # Preserve newlines in content
                for line in getattr(entry, "content", "").split("\n"):
                    if line.strip():
                        lines.append(f"{line}")
                    else:
                        lines.append("")
                lines.append("")
                if getattr(entry, "tags", None):
                    lines.append(
                        f"**Tags**: {', '.join(f'`{tag}`' for tag in getattr(entry, 'tags', []))}"
                    )
                    lines.append("")
                lines.append("---")
                lines.append("")

        # Integrity Information
        if integrity_hashes:
            lines.append("## 🔒 Integrity Verification")
            lines.append("")
            lines.append("Use these hashes to verify export integrity:")
            lines.append("")
            for hash_obj in integrity_hashes:
                lines.append("### Snapshot Integrity Root")
                lines.append(
                    f"- **Algorithm**: {hash_obj.algorithm.value if hasattr(hash_obj.algorithm, 'value') else hash_obj.algorithm}"
                )
                lines.append(f"- **Root Hash**: `{hash_obj.root_hash}`")
                lines.append(f"- **Metadata Hash**: `{hash_obj.metadata_hash}`")
                lines.append(f"- **Payload Hash**: `{hash_obj.payload_hash}`")
                if getattr(hash_obj, "anchors_hash", None):
                    lines.append(f"- **Anchors Hash**: `{hash_obj.anchors_hash}`")
                lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append(
            "*Export generated by CodeMarshal Truth-Preserving Investigation System*"
        )
        lines.append("*Constitutional Article 19: Backward Truth Compatibility*")

        return "\n".join(lines)


class PlainTextExporter(BaseExporter):
    """Plain text export format. Maximum compatibility, minimum structure."""

    def __init__(self):
        super().__init__(ExportFormat.PLAIN_TEXT)

    def _define_limitations(self) -> ExportLimitations:
        return ExportLimitations(
            format_type=ExportFormat.PLAIN_TEXT,
            context_loss=[
                "All formatting and structure is removed",
                "Hierarchical relationships become linear text",
                "Visual emphasis and grouping are lost",
            ],
            structure_loss=[
                "No headings, lists, or sections in machine-readable form",
                "Metadata becomes inline commentary",
                "Cross-references become plain text mentions",
            ],
            cannot_express=[
                "Rich text formatting",
                "Interactive elements",
                "Embedded metadata",
            ],
        )

    def export(
        self,
        snapshot: Snapshot | None = None,
        anchors: list[Anchor] | None = None,
        notebook_entries: list[NoteEntry] | None = None,
        integrity_hashes: list[IntegrityRoot] | None = None,
    ) -> str:
        """Export as plain text with minimal formatting."""

        lines: list[str] = []

        # Header with explicit limitation warning
        lines.append("=" * 70)
        lines.append("CODEMARSHAL INVESTIGATION EXPORT - PLAIN TEXT FORMAT")
        lines.append("=" * 70)
        lines.append("")
        lines.append("WARNING: This export format has significant limitations.")
        lines.append("All formatting, structure, and metadata are flattened to text.")
        lines.append("Use only for human reading, not programmatic analysis.")
        lines.append("")
        lines.append(f"Exported: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("Format: Plain Text (maximum compatibility, minimum structure)")
        lines.append("")
        lines.append("-" * 70)
        lines.append("")

        # Snapshot Information
        if snapshot:
            lines.append("SNAPSHOT")
            lines.append("")
            lines.append(f"  ID: {snapshot.id}")
            lines.append(f"  Version: {snapshot.version}")
            if hasattr(snapshot, "created_at"):
                lines.append(
                    f"  Created: {snapshot.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            if hasattr(snapshot, "path"):
                lines.append(f"  Path: {snapshot.path}")
            if hasattr(snapshot, "observation_count"):
                lines.append(f"  Observations: {snapshot.observation_count}")
            lines.append("")
            lines.append("-" * 50)
            lines.append("")

        # Anchors
        if anchors:
            lines.append("ANCHORS (Stable Reference Points)")
            lines.append("")
            for anchor in anchors:
                lines.append(f"  Type: {anchor.type}")
                lines.append(f"  Location: {anchor.location}")
                lines.append(f"  Identifier: {anchor.identifier}")
                if hasattr(anchor, "context") and anchor.context:
                    lines.append(f"  Context: {anchor.context}")
                lines.append("")
            lines.append("-" * 50)
            lines.append("")

        # Notebook Entries
        if notebook_entries:
            lines.append("INVESTIGATION NOTES")
            lines.append("")
            lines.append("  Notes preserve human thinking anchored to observations.")
            lines.append("")

            for entry in notebook_entries:
                lines.append(
                    f"  Note from {entry.created_at.strftime('%Y-%m-%d %H:%M')}"
                )
                lines.append(f"  Anchor: {entry.anchor_id}")
                lines.append("")
                # Indent and wrap content
                wrapped = textwrap.fill(
                    entry.content, width=65, initial_indent="  ", subsequent_indent="  "
                )
                lines.append(wrapped)
                lines.append("")
                if hasattr(entry, "tags") and entry.tags:
                    lines.append(f"  Tags: {', '.join(entry.tags)}")
                    lines.append("")
                lines.append("  ---")
                lines.append("")

            lines.append("-" * 50)
            lines.append("")

        # Integrity Information
        if integrity_hashes:
            lines.append("INTEGRITY VERIFICATION")
            lines.append("")
            lines.append("  Use these values to verify export integrity:")
            lines.append("")
            for hash_obj in integrity_hashes:
                lines.append("  Snapshot Integrity Root")
                lines.append(
                    f"  Algorithm: {hash_obj.algorithm.value if hasattr(hash_obj.algorithm, 'value') else hash_obj.algorithm}"
                )
                lines.append(f"  Root Hash: {hash_obj.root_hash}")
                lines.append(f"  Metadata Hash: {hash_obj.metadata_hash}")
                lines.append(f"  Payload Hash: {hash_obj.payload_hash}")
                if getattr(hash_obj, "anchors_hash", None):
                    lines.append(f"  Anchors Hash: {hash_obj.anchors_hash}")
                lines.append("")

        # Footer
        lines.append("=" * 70)
        lines.append("End of CodeMarshal Export")
        lines.append("Truth preserved, context flattened.")
        lines.append("Constitutional Article 19: Backward Truth Compatibility")
        lines.append("=" * 70)

        return "\n".join(lines)


# Registry of available exporters
_EXPORTER_REGISTRY: dict[ExportFormat, BaseExporter] = {
    ExportFormat.JSON: JSONExporter(),
    ExportFormat.MARKDOWN: MarkdownExporter(),
    ExportFormat.PLAIN_TEXT: PlainTextExporter(),
}


def get_exporter(format_type: ExportFormat | str) -> BaseExporter:
    """
    Get exporter for the specified format.

    Args:
        format_type: Either an ExportFormat enum or string value

    Returns:
        BaseExporter instance

    Raises:
        ValueError: If format is not supported
    """
    if isinstance(format_type, str):
        try:
            format_type = ExportFormat(format_type.lower())
        except ValueError:
            raise ValueError(
                f"Unsupported export format: {format_type}. "
                f"Supported formats: {[f.value for f in ExportFormat]}"
            ) from None

    if format_type not in _EXPORTER_REGISTRY:
        raise ValueError(
            f"Exporter not registered for format: {format_type}. "
            f"Available: {list(_EXPORTER_REGISTRY.keys())}"
        )

    return _EXPORTER_REGISTRY[format_type]


def list_supported_formats() -> list[dict[str, Any]]:
    """List all supported export formats with their limitations."""
    return [
        {
            "format": exporter.format_type.value,
            "description": _get_format_description(exporter.format_type),
            "limitations": exporter.limitations.to_dict(),
        }
        for exporter in _EXPORTER_REGISTRY.values()
    ]


def _get_format_description(format_type: ExportFormat) -> str:
    """Get human-readable description of format."""
    descriptions = {
        ExportFormat.JSON: "Structured data, machine-readable, preserves some hierarchy",
        ExportFormat.MARKDOWN: "Human-readable documentation, preserves some formatting",
        ExportFormat.PLAIN_TEXT: "Maximum compatibility, minimum structure, human-readable",
    }
    return descriptions.get(format_type, "No description available")
