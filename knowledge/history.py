"""
knowledge/history.py

Investigation history tracking and query suggestion services.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from storage.knowledge_storage import KnowledgeStorage


class HistoryService:
    """Track and query investigation history events."""

    def __init__(
        self,
        storage: KnowledgeStorage | None = None,
        storage_root: Path | str | None = None,
    ) -> None:
        self.storage = storage or KnowledgeStorage(storage_root=storage_root)

    def record_event(
        self,
        session_id: str,
        event_type: str,
        *,
        question: str | None = None,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Any]:
        """Record a new history event."""
        payload = {
            "session_id": session_id,
            "event_type": event_type,
            "question": question or "",
            "path": path or "",
            "metadata": dict(metadata or {}),
            "timestamp": timestamp or datetime.now(UTC).isoformat(),
        }
        return self.storage.record_history_event(payload)

    def search(
        self,
        *,
        session_id: str | None = None,
        query: str | None = None,
        event_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Search history records using multiple filters."""
        return self.storage.query_history(
            session_id=session_id,
            query=query,
            event_type=event_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

    def timeline(
        self,
        *,
        session_id: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Return chronological timeline for display."""
        events = self.search(session_id=session_id, limit=limit)
        return sorted(events, key=lambda item: str(item.get("timestamp") or ""))

    def suggestions(
        self,
        *,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return query suggestions ranked by reuse count."""
        return self.storage.get_query_suggestions(session_id=session_id, limit=limit)

