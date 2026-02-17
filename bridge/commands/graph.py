"""
bridge.commands.graph - Knowledge graph command helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge import KnowledgeGraphService


def execute_graph(
    session_id: str | None = None,
    focus: str | None = None,
    depth: int = 2,
    edge_type: str | None = None,
    limit: int = 200,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute graph query over persisted knowledge graph."""
    graph_service = KnowledgeGraphService(storage_root=storage_root)
    payload = graph_service.get_graph(
        session_id=session_id,
        focus=focus,
        depth=max(int(depth), 1),
        edge_type=edge_type,
        limit=limit,
    )
    payload["success"] = True
    payload["session_id"] = session_id
    return payload

