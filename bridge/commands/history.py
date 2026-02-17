"""
bridge.commands.history - Knowledge history command helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge import HistoryService


def execute_history(
    session_id: str | None = None,
    query: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Execute history query over persisted knowledge events."""
    history = HistoryService(storage_root=storage_root)
    events = history.search(
        session_id=session_id,
        query=query,
        event_type=event_type,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    suggestions = history.suggestions(session_id=session_id, limit=10)
    return {
        "success": True,
        "session_id": session_id,
        "filters": {
            "query": query,
            "event_type": event_type,
            "from_date": from_date,
            "to_date": to_date,
            "limit": limit,
        },
        "events": events,
        "count": len(events),
        "suggestions": suggestions,
    }

