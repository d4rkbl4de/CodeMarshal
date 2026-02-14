"""Tests for bridge.integration.jupyter_exporter."""

import json

from bridge.integration.jupyter_exporter import JupyterExporter


def test_jupyter_export_structure() -> None:
    exporter = JupyterExporter()
    session = {"id": "session-1", "path": "/repo", "state": "complete"}
    observations = [
        {"type": "import_sight", "file": "main.py", "statements": [{"module": "os"}]},
        {"type": "file_sight", "result": {"file_count": 3}},
    ]

    output = exporter.export(session, observations, include_notes=False, include_patterns=False)
    notebook = json.loads(output)

    assert notebook["nbformat"] == 4
    assert notebook["nbformat_minor"] == 5
    assert "cells" in notebook
    assert len(notebook["cells"]) >= 5
    assert notebook["metadata"]["codemarshal"]["include_notes"] is False
    assert notebook["metadata"]["codemarshal"]["include_patterns"] is False


def test_jupyter_export_includes_notes_and_patterns() -> None:
    exporter = JupyterExporter()
    session = {
        "id": "session-2",
        "path": "/repo",
        "state": "complete",
        "notes": ["note-a", "note-b"],
        "patterns": ["pattern-x"],
    }
    observations: list[dict[str, object]] = []

    output = exporter.export(session, observations, include_notes=True, include_patterns=True)
    notebook = json.loads(output)
    cell_sources = "\n".join(str(cell.get("source", "")) for cell in notebook["cells"])

    assert "## Notes" in cell_sources
    assert "note-a" in cell_sources
    assert "## Patterns" in cell_sources
    assert "pattern-x" in cell_sources


def test_jupyter_export_contains_type_counts() -> None:
    exporter = JupyterExporter()
    session = {"id": "session-3"}
    observations = [
        {"type": "import_sight"},
        {"type": "import_sight"},
        {"type": "boundary_sight"},
    ]

    output = exporter.export(session, observations)
    notebook = json.loads(output)
    cell_sources = "\n".join(str(cell.get("source", "")) for cell in notebook["cells"])

    assert "observation_type_counts" in cell_sources
    assert "import_sight" in cell_sources
    assert "boundary_sight" in cell_sources
