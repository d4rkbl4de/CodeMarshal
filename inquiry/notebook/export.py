"""
export.py - Safely export human thinking for reporting or sharing.

Export formats: Markdown, JSON, plain text.
Includes only note content, anchor references, tags, and timeline info.
Never includes raw observations or summarizes evidence.
"""

import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from .entries import NoteEntry
from .timeline import Timeline


class Exporter:
    """
    Safely exports notebook content without exposing observations.

    Rules:
    - Never include raw observations
    - Never summarize or interpret evidence
    - Export only human thinking and metadata
    """

    @staticmethod
    def export_markdown(
        notes: NoteEntry | list[NoteEntry],
        tags: dict[UUID, list[str]] | None = None,
        timeline: Timeline | None = None,
        title: str | None = None,
    ) -> str:
        """
        Export notes in Markdown format.

        Args:
            notes: Single note or list of notes
            tags: Optional mapping of note IDs to tags
            timeline: Optional timeline for chronological context
            title: Optional title for the export

        Returns:
            Markdown-formatted string

        Raises:
            TypeError: If notes not NoteEntry or list of NoteEntry
        """
        notes_list = _validate_and_normalize_notes(notes)

        output_lines: list[str] = []

        # Title
        if title:
            output_lines.append(f"# {title}\n")

        # Metadata header
        export_time = datetime.now().isoformat()
        output_lines.append(f"*Export generated: {export_time}*\n")
        output_lines.append(f"*Number of notes: {len(notes_list)}*\n")
        output_lines.append("---\n")

        # Export each note
        for i, note in enumerate(notes_list, 1):
            output_lines.append(f"## Note {i}: {note.id}\n")
            output_lines.append(f"**Author:** {note.author_id}\n")
            output_lines.append(f"**Session:** {note.session_id}\n")
            output_lines.append(f"**Created:** {note.created_at.isoformat()}\n")
            output_lines.append(f"**Updated:** {note.updated_at.isoformat()}\n")

            # Anchors (only references, not content)
            if note.anchors:
                anchor_ids = [_get_anchor_reference(a) for a in note.anchors]
                output_lines.append(f"**Anchors:** {', '.join(anchor_ids)}\n")

            # Tags
            if tags and note.id in tags:
                tag_list = tags[note.id]
                if tag_list:
                    output_lines.append(f"**Tags:** {', '.join(tag_list)}\n")

            # Timeline history if available
            if timeline:
                history = timeline.get_note_history(note.id)
                if history:
                    output_lines.append("### Edit History\n")
                    for hist_time, action, _old_content in history:
                        time_str = hist_time.isoformat()
                        if action == "created":
                            output_lines.append(f"- {time_str}: Created\n")
                        elif action == "updated":
                            # Show only that it was edited, not the old content
                            output_lines.append(f"- {time_str}: Edited\n")

            # Content
            output_lines.append("### Content\n")
            output_lines.append(f"{note.content}\n")
            output_lines.append("---\n")

        return "\n".join(output_lines)

    @staticmethod
    def export_json(
        notes: NoteEntry | list[NoteEntry],
        tags: dict[UUID, list[str]] | None = None,
        timeline: Timeline | None = None,
    ) -> str:
        """
        Export notes in JSON format.

        Args:
            notes: Single note or list of notes
            tags: Optional mapping of note IDs to tags
            timeline: Optional timeline for chronological context

        Returns:
            JSON-formatted string

        Raises:
            TypeError: If notes not NoteEntry or list of NoteEntry
        """
        notes_list = _validate_and_normalize_notes(notes)

        export_data = {
            "export_type": "notebook_export",
            "export_version": "1.0",
            "export_timestamp": datetime.now().isoformat(),
            "note_count": len(notes_list),
            "notes": [],
        }

        for note in notes_list:
            note_data = {
                "id": str(note.id),
                "author_id": note.author_id,
                "session_id": note.session_id,
                "created_at": note.created_at.isoformat(),
                "updated_at": note.updated_at.isoformat(),
                "content": note.content,
                "anchors": [_get_anchor_reference(a) for a in note.anchors],
            }

            # Add tags if available
            if tags and note.id in tags:
                note_data["tags"] = tags[note.id]

            # Add edit history if timeline available
            if timeline:
                history = timeline.get_note_history(note.id)
                if history:
                    note_data["edit_history"] = [
                        {
                            "timestamp": h_time.isoformat(),
                            "action": action,
                            # Don't include old content to avoid data duplication
                            "has_previous_content": old_content is not None,
                        }
                        for h_time, action, old_content in history
                    ]

            export_data["notes"].append(note_data)

        return json.dumps(export_data, indent=2, ensure_ascii=False)

    @staticmethod
    def export_text(
        notes: NoteEntry | list[NoteEntry],
        tags: dict[UUID, list[str]] | None = None,
        timeline: Timeline | None = None,
        include_metadata: bool = True,
    ) -> str:
        """
        Export notes in plain text format.

        Args:
            notes: Single note or list of notes
            tags: Optional mapping of note IDs to tags
            timeline: Optional timeline for chronological context
            include_metadata: Whether to include metadata headers

        Returns:
            Plain text string

        Raises:
            TypeError: If notes not NoteEntry or list of NoteEntry
        """
        notes_list = _validate_and_normalize_notes(notes)

        output_lines: list[str] = []

        if include_metadata:
            output_lines.append(f"Notebook Export - {datetime.now().isoformat()}")
            output_lines.append(f"Total notes: {len(notes_list)}")
            output_lines.append("=" * 60)

        for i, note in enumerate(notes_list, 1):
            if include_metadata:
                output_lines.append(f"\nNOTE {i}")
                output_lines.append("-" * 40)
                output_lines.append(f"ID: {note.id}")
                output_lines.append(f"Author: {note.author_id}")
                output_lines.append(f"Session: {note.session_id}")
                output_lines.append(f"Created: {note.created_at.isoformat()}")
                output_lines.append(f"Updated: {note.updated_at.isoformat()}")

                if note.anchors:
                    anchor_refs = [_get_anchor_reference(a) for a in note.anchors]
                    output_lines.append(f"Anchors: {', '.join(anchor_refs)}")

                if tags and note.id in tags:
                    tag_list = tags[note.id]
                    if tag_list:
                        output_lines.append(f"Tags: {', '.join(tag_list)}")

                if timeline:
                    history = timeline.get_note_history(note.id)
                    if history:
                        output_lines.append(
                            f"Edits: {len([h for h in history if h[1] == 'updated'])}"
                        )

                output_lines.append("")

            output_lines.append(note.content)
            output_lines.append("")

        return "\n".join(output_lines)

    @staticmethod
    def export_to_file(
        notes: NoteEntry | list[NoteEntry],
        output_path: str | Path,
        format_type: str = "markdown",
        tags: dict[UUID, list[str]] | None = None,
        timeline: Timeline | None = None,
        **kwargs,
    ) -> Path:
        """
        Export notes to a file.

        Args:
            notes: Single note or list of notes
            output_path: Path to write export to
            format_type: One of "markdown", "json", "text"
            tags: Optional mapping of note IDs to tags
            timeline: Optional timeline for chronological context
            **kwargs: Additional format-specific options

        Returns:
            Path to the created file

        Raises:
            ValueError: If format_type is invalid
            OSError: If file cannot be written
        """
        format_type = format_type.lower()

        if format_type == "markdown":
            content = Exporter.export_markdown(notes, tags, timeline, **kwargs)
        elif format_type == "json":
            content = Exporter.export_json(notes, tags, timeline)
        elif format_type == "text":
            content = Exporter.export_text(notes, tags, timeline, **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            output_path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise OSError(f"Failed to write export to {output_path}: {e}") from e

        return output_path


def _validate_and_normalize_notes(
    notes: NoteEntry | list[NoteEntry],
) -> list[NoteEntry]:
    """Validate notes input and return as list."""
    if isinstance(notes, NoteEntry):
        return [notes]
    elif isinstance(notes, list):
        if not all(isinstance(n, NoteEntry) for n in notes):
            raise TypeError("All items in list must be NoteEntry instances")
        return notes
    else:
        raise TypeError(
            f"Expected NoteEntry or list of NoteEntry, got {type(notes).__name__}"
        )


def _get_anchor_reference(anchor) -> str:
    """
    Get a safe string reference for an anchor.

    Returns:
        String identifier for the anchor without exposing observation content
    """
    # Try to get an ID attribute
    anchor_id = getattr(anchor, "id", None)
    if anchor_id:
        return str(anchor_id)

    # Try to get a type name
    anchor_type = getattr(anchor, "__class__", None)
    if anchor_type:
        return anchor_type.__name__

    # Fallback to object ID (not content)
    return f"anchor_{id(anchor)}"
