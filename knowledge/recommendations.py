"""
knowledge/recommendations.py

Deterministic recommendation generation from history and graph artifacts.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from knowledge.history import HistoryService
from knowledge.knowledge_graph import KnowledgeGraphService
from storage.knowledge_storage import KnowledgeStorage


class RecommendationService:
    """Produce next-step recommendations from persisted investigation context."""

    def __init__(
        self,
        storage: KnowledgeStorage | None = None,
        storage_root: Path | str | None = None,
    ) -> None:
        self.storage = storage or KnowledgeStorage(storage_root=storage_root)
        self.history = HistoryService(storage=self.storage)
        self.graph = KnowledgeGraphService(storage=self.storage)

    def generate(
        self,
        session_id: str,
        *,
        limit: int = 10,
        category: str | None = None,
        refresh: bool = False,
    ) -> list[dict[str, Any]]:
        """Generate deterministic recommendations for a session."""
        if not refresh:
            cached = self.storage.load_recommendations(session_id)
            if cached:
                return _filter_and_limit(cached, category=category, limit=limit)

        events = self.history.search(session_id=session_id, limit=500)
        graph = self.graph.get_graph(session_id=session_id, depth=2, limit=1000)

        recommendations: list[dict[str, Any]] = []
        recommendations.extend(self._recommend_from_history(session_id, events))
        recommendations.extend(self._recommend_from_graph(session_id, graph))

        # Deduplicate by title/category and keep strongest confidence.
        deduped: dict[tuple[str, str], dict[str, Any]] = {}
        for item in recommendations:
            key = (str(item.get("category") or ""), str(item.get("title") or ""))
            current = deduped.get(key)
            if current is None or float(item.get("confidence") or 0.0) > float(
                current.get("confidence") or 0.0
            ):
                deduped[key] = item

        ranked = sorted(
            deduped.values(),
            key=lambda item: (
                -float(item.get("confidence") or 0.0),
                str(item.get("title") or "").lower(),
            ),
        )
        filtered = _filter_and_limit(ranked, category=category, limit=limit)
        self.storage.save_recommendations(session_id, filtered)
        return filtered

    def _recommend_from_history(
        self,
        session_id: str,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        counts: dict[str, int] = {}
        query_counts: dict[str, int] = {}
        for event in events:
            event_type = str(event.get("event_type") or "unknown")
            counts[event_type] = counts.get(event_type, 0) + 1
            if event_type == "query":
                question = str(event.get("question") or "").strip()
                if question:
                    query_counts[question] = query_counts.get(question, 0) + 1

        output: list[dict[str, Any]] = []

        if counts.get("query", 0) == 0:
            output.append(
                {
                    "recommendation_id": f"{session_id}:next:query",
                    "session_id": session_id,
                    "category": "next_step",
                    "title": "Ask a structure question",
                    "reason": "No query activity found in this session history.",
                    "confidence": 0.92,
                    "actions": [
                        "codemarshal query <session_id> --question-type=structure --question='What modules exist?'"
                    ],
                }
            )

        if counts.get("pattern_scan", 0) == 0 and counts.get("pattern", 0) == 0:
            output.append(
                {
                    "recommendation_id": f"{session_id}:next:pattern",
                    "session_id": session_id,
                    "category": "next_step",
                    "title": "Run a pattern scan",
                    "reason": "No pattern analysis event was found for the session.",
                    "confidence": 0.84,
                    "actions": [
                        "codemarshal pattern scan . --glob='*.py'",
                    ],
                }
            )

        if counts.get("export", 0) == 0:
            output.append(
                {
                    "recommendation_id": f"{session_id}:workflow:export",
                    "session_id": session_id,
                    "category": "workflow",
                    "title": "Export the current findings",
                    "reason": "Session has no export event; capture a durable report.",
                    "confidence": 0.78,
                    "actions": [
                        "codemarshal export <session_id> --format=markdown --output=report.md",
                    ],
                }
            )

        repeated = sorted(
            query_counts.items(),
            key=lambda item: (-item[1], item[0].lower()),
        )
        if repeated and repeated[0][1] >= 2:
            top_query, count = repeated[0]
            output.append(
                {
                    "recommendation_id": f"{session_id}:workflow:repeat_query",
                    "session_id": session_id,
                    "category": "workflow",
                    "title": "Refine repeated query into targeted follow-up",
                    "reason": f"Query repeated {count} times: '{top_query[:120]}'.",
                    "confidence": 0.74,
                    "actions": [
                        "Use --focus with the repeated query target to reduce noise.",
                    ],
                }
            )

        return output

    def _recommend_from_graph(
        self,
        session_id: str,
        graph_payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        nodes = graph_payload.get("nodes", [])
        edges = graph_payload.get("edges", [])
        if not isinstance(nodes, list) or not isinstance(edges, list):
            return []

        degree: dict[str, int] = {}
        node_labels: dict[str, str] = {}
        node_types: dict[str, str] = {}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_id = str(node.get("node_id") or "")
            if not node_id:
                continue
            node_labels[node_id] = str(node.get("label") or node_id)
            node_types[node_id] = str(node.get("node_type") or "unknown")
            degree[node_id] = degree.get(node_id, 0)

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            src = str(edge.get("from_node") or "")
            dst = str(edge.get("to_node") or "")
            if src:
                degree[src] = degree.get(src, 0) + 1
            if dst:
                degree[dst] = degree.get(dst, 0) + 1

        ranked = sorted(
            degree.items(),
            key=lambda item: (-item[1], node_labels.get(item[0], "").lower()),
        )
        recommendations: list[dict[str, Any]] = []
        for node_id, count in ranked[:3]:
            if count <= 1:
                continue
            label = node_labels.get(node_id, node_id)
            node_type = node_types.get(node_id, "unknown")
            recommendations.append(
                {
                    "recommendation_id": f"{session_id}:hotspot:{node_id}",
                    "session_id": session_id,
                    "category": "hotspot",
                    "title": f"Inspect high-connectivity {node_type}",
                    "reason": f"'{label}' has {count} graph connections.",
                    "confidence": min(0.65 + (count * 0.03), 0.9),
                    "actions": [
                        f"codemarshal graph {session_id} --focus {node_id} --depth 2",
                    ],
                }
            )

        return recommendations


def _filter_and_limit(
    recommendations: list[dict[str, Any]],
    *,
    category: str | None,
    limit: int,
) -> list[dict[str, Any]]:
    filtered = recommendations
    if category:
        filtered = [
            item
            for item in filtered
            if str(item.get("category") or "").strip().lower() == category.strip().lower()
        ]
    if limit <= 0:
        return filtered
    return filtered[:limit]

