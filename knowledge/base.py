"""Knowledge base facade for history, graph, and recommendations."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from knowledge.history import HistoryService
from knowledge.knowledge_graph import KnowledgeGraphService
from knowledge.recommendations import RecommendationService
from storage.atomic import atomic_write_json_compatible
from storage.knowledge_storage import KnowledgeStorage


class KnowledgeBase:
    """Compatibility facade with expanded knowledge services."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("storage") / "knowledge"
        self.storage_root = self.base_path.parent
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.trends_path = self.base_path / "pattern_trends.json"
        self.similarity_path = self.base_path / "similarity_index.json"
        self.storage = KnowledgeStorage(storage_root=self.storage_root)
        self.history_service = HistoryService(storage=self.storage)
        self.graph_service = KnowledgeGraphService(storage=self.storage)
        self.recommendation_service = RecommendationService(storage=self.storage)

    def add_insight(
        self,
        investigation_id: str,
        insight: dict[str, Any],
    ) -> dict[str, Any]:
        """Legacy API for recording insights."""
        event = self.history_service.record_event(
            investigation_id,
            "insight",
            metadata={"insight": insight},
        )
        return {
            "id": event.get("event_id"),
            "investigation_id": investigation_id,
            "timestamp": event.get("timestamp"),
            "insight": insight,
        }

    def search_insights(self, query: str) -> list[dict[str, Any]]:
        """Legacy API for searching insights."""
        events = self.history_service.search(
            query=query,
            event_type="insight",
            limit=500,
        )
        results = []
        for event in events:
            metadata = event.get("metadata", {})
            insight = metadata.get("insight", {}) if isinstance(metadata, dict) else {}
            if not isinstance(insight, dict):
                insight = {}
            results.append(
                {
                    "id": event.get("event_id"),
                    "investigation_id": event.get("session_id"),
                    "timestamp": event.get("timestamp"),
                    "insight": insight,
                }
            )
        return results

    def record_event(
        self,
        investigation_id: str,
        event_type: str,
        *,
        question: str | None = None,
        path: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record generic knowledge events."""
        return self.history_service.record_event(
            investigation_id,
            event_type,
            question=question,
            path=path,
            metadata=metadata,
        )

    def history(
        self,
        *,
        session_id: str | None = None,
        query: str | None = None,
        event_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query knowledge history."""
        return self.history_service.search(
            session_id=session_id,
            query=query,
            event_type=event_type,
            from_date=from_date,
            to_date=to_date,
            limit=limit,
        )

    def graph(
        self,
        *,
        session_id: str | None = None,
        focus: str | None = None,
        depth: int = 2,
        edge_type: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """Query knowledge graph."""
        return self.graph_service.get_graph(
            session_id=session_id,
            focus=focus,
            depth=depth,
            edge_type=edge_type,
            limit=limit,
        )

    def recommendations(
        self,
        session_id: str,
        *,
        limit: int = 10,
        category: str | None = None,
        refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """Generate or load recommendations."""
        return self.recommendation_service.generate(
            session_id,
            limit=limit,
            category=category,
            refresh=refresh,
        )

    def ingest_observations(
        self,
        investigation_id: str,
        observations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Project observation payloads into the graph index."""
        return self.graph_service.ingest_observations(investigation_id, observations)

    def ingest_query(
        self,
        investigation_id: str,
        question: str,
        question_type: str,
    ) -> dict[str, Any]:
        """Project query artifacts into the graph index."""
        return self.graph_service.ingest_query(investigation_id, question, question_type)

    def ingest_pattern_matches(
        self,
        investigation_id: str,
        matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Project pattern matches into the graph index."""
        return self.graph_service.ingest_pattern_matches(investigation_id, matches)

    def get_pattern_trends(self, pattern_id: str) -> dict[str, Any]:
        """Compute pattern trend counts from stored pattern artifacts."""
        pattern_dir = self.storage_root / "patterns"
        files_scanned = 0
        match_count = 0

        if pattern_dir.exists():
            for pattern_file in pattern_dir.glob("*.pattern.json"):
                files_scanned += 1
                try:
                    data = json.loads(pattern_file.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                match_count += _count_pattern_id(data, pattern_id)

        payload = {
            "pattern_id": pattern_id,
            "match_count": match_count,
            "files_scanned": files_scanned,
            "generated_at": datetime.now(UTC).isoformat(),
        }
        atomic_write_json_compatible(self.trends_path, payload)
        return payload

    def find_similar_codebases(self, investigation_id: str) -> list[dict[str, Any]]:
        """Compute Jaccard similarity from stored pattern references."""
        sessions_dir = self.storage_root / "sessions"
        if not sessions_dir.exists():
            return []

        target_patterns: set[str] = set()
        sessions: dict[str, set[str]] = {}

        for session_file in sessions_dir.glob("*.session.json"):
            try:
                data = json.loads(session_file.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            session_id = data.get("id")
            pattern_ids = set(data.get("pattern_ids", []) or [])
            if not session_id:
                continue
            sessions[str(session_id)] = pattern_ids
            if str(session_id) == investigation_id:
                target_patterns = pattern_ids

        results: list[dict[str, Any]] = []
        for session_id, pattern_ids in sessions.items():
            if session_id == investigation_id:
                continue
            overlap = len(target_patterns.intersection(pattern_ids))
            union = len(target_patterns.union(pattern_ids)) or 1
            score = overlap / union
            results.append(
                {
                    "session_id": session_id,
                    "overlap": overlap,
                    "score": round(score, 4),
                }
            )

        results.sort(key=lambda item: item["score"], reverse=True)
        atomic_write_json_compatible(self.similarity_path, results)
        return results


def _count_pattern_id(payload: Any, pattern_id: str) -> int:
    if isinstance(payload, dict):
        count = 0
        for key, value in payload.items():
            if key == "pattern_id" and value == pattern_id:
                count += 1
                continue
            count += _count_pattern_id(value, pattern_id)
        return count
    if isinstance(payload, list):
        return sum(_count_pattern_id(item, pattern_id) for item in payload)
    if isinstance(payload, str):
        return 1 if payload == pattern_id else 0
    return 0
