"""
notebook - Human thinking space for CodeMarshal investigations.

Public interface for the notebook subsystem.
Exposes classes/functions for managing notes, tags, timelines, exports, and enforcement.
Prevents direct access to internal helpers.
"""

from uuid import UUID

from .constraints import (
    AnchorValidationError,
    ConstraintsValidator,
    ConstraintViolationError,
    EvidenceMutationError,
)
from .entries import NotebookManager, NoteEntry
from .export import Exporter
from .organization import TagManager
from .timeline import Timeline

__all__ = [
    # Core notebook types
    "NoteEntry",
    "NotebookManager",
    "TagManager",
    "Timeline",
    # Export functionality
    "Exporter",
    # Constraint enforcement
    "ConstraintsValidator",
    "ConstraintViolationError",
    "EvidenceMutationError",
    "AnchorValidationError",
    # Public helper functions
    "create_investigation_notebook",
    "export_notebook",
    "validate_note_anchors",
]


# Public helper functions
def create_investigation_notebook(session_id: str) -> dict:
    """
    Create a new investigation notebook with all components.

    Args:
        session_id: Unique identifier for the investigation session

    Returns:
        Dictionary with all notebook components:
        {
            'manager': NotebookManager,
            'tag_manager': TagManager,
            'timeline': Timeline,
            'validator': ConstraintsValidator,
            'exporter': Exporter (static class)
        }
    """
    if not session_id or not isinstance(session_id, str):
        raise ValueError("session_id must be non-empty string")

    return {
        "manager": NotebookManager(),
        "tag_manager": TagManager(),
        "timeline": Timeline(),
        "validator": ConstraintsValidator(),
        "exporter": Exporter,  # Static class, not instance
    }


def export_notebook(
    notebook: dict,
    format_type: str = "markdown",
    output_path: str | None = None,
    **kwargs,
) -> str | bytes:
    """
    Export notebook contents in the specified format.

    Args:
        notebook: Notebook dictionary from create_investigation_notebook
        format_type: One of "markdown", "json", "text"
        output_path: Optional path to write file to
        **kwargs: Additional options passed to exporter

    Returns:
        Exported content as string, or bytes if writing to file

    Raises:
        KeyError: If notebook dict missing required components
        ValueError: If format_type invalid
    """
    required_keys = {"manager", "tag_manager", "timeline"}
    if not all(key in notebook for key in required_keys):
        missing = required_keys - notebook.keys()
        raise KeyError(f"Notebook missing required components: {missing}")

    manager = notebook["manager"]
    tag_manager = notebook["tag_manager"]
    timeline = notebook["timeline"]

    # Get all notes
    notes = list(manager)  # NotebookManager is iterable

    # Build tag mapping
    tags = {note.id: tag_manager.get_tags_for_note(note) for note in notes}

    if output_path:
        # Write to file
        return Exporter.export_to_file(
            notes=notes,
            output_path=output_path,
            format_type=format_type,
            tags=tags,
            timeline=timeline,
            **kwargs,
        )
    else:
        # Return content directly
        format_type = format_type.lower()
        if format_type == "markdown":
            return Exporter.export_markdown(
                notes=notes, tags=tags, timeline=timeline, **kwargs
            )
        elif format_type == "json":
            return Exporter.export_json(notes=notes, tags=tags, timeline=timeline)
        elif format_type == "text":
            return Exporter.export_text(
                notes=notes, tags=tags, timeline=timeline, **kwargs
            )
        else:
            raise ValueError(f"Unsupported format: {format_type}")


def validate_note_anchors(notebook: dict, note: NoteEntry | UUID | str) -> list[str]:
    """
    Validate that a note's anchors reference valid, immutable evidence.

    Args:
        notebook: Notebook dictionary from create_investigation_notebook
        note: NoteEntry, note ID (UUID), or note ID string

    Returns:
        List of validated anchor IDs

    Raises:
        KeyError: If notebook missing validator or note not found
        ConstraintViolationError: If validation fails
    """
    if "validator" not in notebook:
        raise KeyError("Notebook missing validator component")

    validator = notebook["validator"]
    manager = notebook["manager"]

    # Get NoteEntry object
    if isinstance(note, NoteEntry):
        note_entry = note
    elif isinstance(note, UUID):
        note_entry = manager.get_note(note)
    elif isinstance(note, str):
        try:
            note_uuid = UUID(note)
            note_entry = manager.get_note(note_uuid)
        except ValueError:
            raise ValueError(f"Invalid UUID string: {note}") from None
    else:
        raise TypeError(
            f"Expected NoteEntry, UUID, or string, got {type(note).__name__}"
        )

    if note_entry is None:
        raise KeyError(f"Note not found: {note}")

    return validator.validate_note_anchors(note_entry)


# Version information
__version__ = "1.0.0"
__author__ = "CodeMarshal Team"
__description__ = "Truth-preserving notebook for code investigation"


# Import validation (prevent circular imports)
def _validate_imports() -> None:
    """Validate that all required imports are available."""
    required_classes = [
        NoteEntry,
        NotebookManager,
        TagManager,
        Timeline,
        Exporter,
        ConstraintsValidator,
    ]

    for cls in required_classes:
        if cls is None:
            raise ImportError(f"Failed to import required class: {cls}")


# Run validation on import
try:
    _validate_imports()
except ImportError as e:
    raise ImportError(f"Notebook module initialization failed: {e}") from e
