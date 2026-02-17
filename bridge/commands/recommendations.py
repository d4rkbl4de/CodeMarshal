"""
bridge.commands.recommendations - Knowledge recommendation command helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge import RecommendationService


def execute_recommendations(
    session_id: str,
    limit: int = 10,
    category: str | None = None,
    refresh: bool = False,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Generate recommendations for an investigation session."""
    service = RecommendationService(storage_root=storage_root)
    recommendations = service.generate(
        session_id,
        limit=max(int(limit), 0),
        category=category,
        refresh=refresh,
    )
    return {
        "success": True,
        "session_id": session_id,
        "category": category,
        "count": len(recommendations),
        "recommendations": recommendations,
    }

