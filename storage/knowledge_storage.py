"""
storage/knowledge_storage.py

Persistent storage for knowledge history, graph artifacts, and recommendations.
"""

from __future__ import annotations

import hashlib
import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from storage.atomic import atomic_write_json_compatible


class KnowledgeStorage:
    """Storage adapter for knowledge base artifacts."""

    def __init__(self, storage_root: Path | str | None = None) -> None:
        self.storage_root = Path(storage_root or "storage")
        self._lock = threading.RLock()
        self._configure_paths(self.storage_root / "knowledge")
        self._ensure_layout()

    def _configure_paths(self, base_path: Path) -> None:
        self.base_path = base_path
        self.recommendations_dir = self.base_path / "recommendations"
        self.history_path = self.base_path / "history.jsonl"
        self.history_index_path = self.base_path / "history_index.json"
        self.graph_nodes_path = self.base_path / "graph_nodes.jsonl"
        self.graph_edges_path = self.base_path / "graph_edges.jsonl"
        self.graph_index_path = self.base_path / "graph_index.json"
        self.stats_path = self.base_path / "stats.json"

    def _ensure_layout(self) -> None:
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.recommendations_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            fallback = self.storage_root / "knowledge_runtime"
            self._configure_paths(fallback)
            self.base_path.mkdir(parents=True, exist_ok=True)
            self.recommendations_dir.mkdir(parents=True, exist_ok=True)
        if not self.history_index_path.exists():
            atomic_write_json_compatible(self.history_index_path, self._default_history_index())
        if not self.graph_index_path.exists():
            atomic_write_json_compatible(self.graph_index_path, self._default_graph_index())
        if not self.stats_path.exists():
            atomic_write_json_compatible(self.stats_path, {"updated_at": _now_iso()})

    def _default_history_index(self) -> dict[str, Any]:
        return {
            "total_events": 0,
            "by_session": {},
            "by_type": {},
            "query_terms": {},
            "updated_at": _now_iso(),
        }

    def _default_graph_index(self) -> dict[str, Any]:
        return {
            "nodes": {},
            "edges": {},
            "adjacency": {},
            "reverse_adjacency": {},
            "updated_at": _now_iso(),
        }

    def _load_json(self, path: Path, default: Any) -> Any:
        if not path.exists():
            return default
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return default

    def _append_jsonl(self, path: Path, payload: dict[str, Any]) -> None:
        serialized = json.dumps(payload, ensure_ascii=False)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(serialized)
            handle.write("\n")

    def _iter_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        records: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    records.append(payload)
        return records

    def record_history_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Persist a history event and refresh query/session indexes."""
        event = dict(payload)
        event.setdefault("event_id", _event_id(event))
        event.setdefault("timestamp", _now_iso())
        event.setdefault("event_type", "unknown")
        event.setdefault("session_id", "unknown")

        with self._lock:
            self._append_jsonl(self.history_path, event)
            index = self._load_json(self.history_index_path, self._default_history_index())
            session_id = str(event.get("session_id") or "unknown")
            event_type = str(event.get("event_type") or "unknown")

            index["total_events"] = int(index.get("total_events", 0)) + 1
            by_session = dict(index.get("by_session", {}))
            by_type = dict(index.get("by_type", {}))
            by_session[session_id] = int(by_session.get(session_id, 0)) + 1
            by_type[event_type] = int(by_type.get(event_type, 0)) + 1
            index["by_session"] = by_session
            index["by_type"] = by_type

            question = str(event.get("question") or "").strip()
            if question:
                terms = dict(index.get("query_terms", {}))
                for token in _tokenize(question):
                    terms[token] = int(terms.get(token, 0)) + 1
                index["query_terms"] = terms

            index["updated_at"] = _now_iso()
            atomic_write_json_compatible(self.history_index_path, index)
            self._touch_stats("history_event")

        return event

    def query_history(
        self,
        session_id: str | None = None,
        query: str | None = None,
        event_type: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Query history events using exact and text filters."""
        needle = (query or "").strip().lower()
        start_ts = _parse_date_or_datetime(from_date) if from_date else None
        end_ts = _parse_date_or_datetime(to_date, end_of_day=True) if to_date else None

        events = []
        for event in self._iter_jsonl(self.history_path):
            if session_id and str(event.get("session_id")) != session_id:
                continue
            if event_type and str(event.get("event_type")) != event_type:
                continue
            ts = _parse_date_or_datetime(str(event.get("timestamp") or ""))
            if start_ts and ts and ts < start_ts:
                continue
            if end_ts and ts and ts > end_ts:
                continue
            if needle and needle not in json.dumps(event, ensure_ascii=False).lower():
                continue
            events.append(event)

        events.sort(key=lambda item: str(item.get("timestamp") or ""), reverse=True)
        if limit <= 0:
            return events
        return events[:limit]

    def get_query_suggestions(
        self,
        session_id: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Return most frequent previous query strings."""
        counts: dict[str, int] = {}
        for event in self._iter_jsonl(self.history_path):
            if str(event.get("event_type") or "") != "query":
                continue
            if session_id and str(event.get("session_id")) != session_id:
                continue
            question = str(event.get("question") or "").strip()
            if not question:
                continue
            counts[question] = int(counts.get(question, 0)) + 1

        ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0].lower()))
        return [
            {"query": query, "count": count}
            for query, count in ranked[: max(limit, 0)]
        ]

    def upsert_graph_node(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Insert or update a graph node in index and append-only log."""
        node = dict(payload)
        node_id = str(node.get("node_id") or "").strip()
        if not node_id:
            raise ValueError("node_id is required")
        node.setdefault("node_type", "unknown")
        node.setdefault("label", node_id)
        node.setdefault("session_ids", [])
        node.setdefault("attributes", {})
        node["updated_at"] = _now_iso()

        with self._lock:
            index = self._load_json(self.graph_index_path, self._default_graph_index())
            nodes = dict(index.get("nodes", {}))
            existing = dict(nodes.get(node_id, {}))

            merged_sessions = set(existing.get("session_ids", []) or [])
            merged_sessions.update(node.get("session_ids", []) or [])
            merged_attrs = dict(existing.get("attributes", {}) or {})
            merged_attrs.update(node.get("attributes", {}) or {})

            merged_node = {
                "node_id": node_id,
                "node_type": str(node.get("node_type") or existing.get("node_type") or "unknown"),
                "label": str(node.get("label") or existing.get("label") or node_id),
                "session_ids": sorted(merged_sessions),
                "attributes": merged_attrs,
                "updated_at": _now_iso(),
            }
            nodes[node_id] = merged_node
            index["nodes"] = nodes
            index["updated_at"] = _now_iso()
            atomic_write_json_compatible(self.graph_index_path, index)
            self._append_jsonl(self.graph_nodes_path, merged_node)
            self._touch_stats("graph_node")
            return merged_node

    def add_graph_edge(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Insert or update graph edges and adjacency index."""
        edge = dict(payload)
        from_node = str(edge.get("from_node") or "").strip()
        to_node = str(edge.get("to_node") or "").strip()
        edge_type = str(edge.get("edge_type") or "related_to")
        session_id = str(edge.get("session_id") or "unknown")
        if not from_node or not to_node:
            raise ValueError("from_node and to_node are required")

        edge_id = str(edge.get("edge_id") or _edge_id(from_node, to_node, edge_type, session_id))
        weight = float(edge.get("weight") or 1.0)

        with self._lock:
            index = self._load_json(self.graph_index_path, self._default_graph_index())
            edges = dict(index.get("edges", {}))
            adjacency = _copy_list_map(index.get("adjacency", {}))
            reverse = _copy_list_map(index.get("reverse_adjacency", {}))

            existing = dict(edges.get(edge_id, {}))
            merged = {
                "edge_id": edge_id,
                "from_node": from_node,
                "to_node": to_node,
                "edge_type": edge_type,
                "session_id": session_id,
                "weight": float(existing.get("weight", 0.0)) + weight,
                "timestamp": str(edge.get("timestamp") or _now_iso()),
            }
            edges[edge_id] = merged

            adjacency.setdefault(from_node, [])
            reverse.setdefault(to_node, [])
            if edge_id not in adjacency[from_node]:
                adjacency[from_node].append(edge_id)
            if edge_id not in reverse[to_node]:
                reverse[to_node].append(edge_id)

            index["edges"] = edges
            index["adjacency"] = adjacency
            index["reverse_adjacency"] = reverse
            index["updated_at"] = _now_iso()
            atomic_write_json_compatible(self.graph_index_path, index)
            self._append_jsonl(self.graph_edges_path, merged)
            self._touch_stats("graph_edge")
            return merged

    def get_graph(
        self,
        session_id: str | None = None,
        focus: str | None = None,
        depth: int = 2,
        edge_type: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """Return graph projection and bounded neighborhood."""
        index = self._load_json(self.graph_index_path, self._default_graph_index())
        nodes = dict(index.get("nodes", {}))
        edges = dict(index.get("edges", {}))
        adjacency = _copy_list_map(index.get("adjacency", {}))
        reverse = _copy_list_map(index.get("reverse_adjacency", {}))

        focus_id = str(focus or "").strip() or None
        selected_nodes: set[str]

        if focus_id and focus_id in nodes:
            selected_nodes = _bfs_nodes(
                focus_id=focus_id,
                max_depth=max(int(depth), 1),
                edges=edges,
                adjacency=adjacency,
                reverse_adjacency=reverse,
                edge_type=edge_type,
            )
        else:
            selected_nodes = set(nodes.keys())

        if session_id:
            selected_nodes = {
                node_id
                for node_id in selected_nodes
                if session_id in set(nodes.get(node_id, {}).get("session_ids", []) or [])
            }

        selected_edges: list[dict[str, Any]] = []
        for edge in edges.values():
            if not isinstance(edge, dict):
                continue
            if edge_type and str(edge.get("edge_type")) != edge_type:
                continue
            if session_id and str(edge.get("session_id")) != session_id:
                continue
            src = str(edge.get("from_node") or "")
            dst = str(edge.get("to_node") or "")
            if src in selected_nodes and dst in selected_nodes:
                selected_edges.append(edge)

        selected_edges.sort(
            key=lambda item: (
                str(item.get("edge_type") or ""),
                str(item.get("from_node") or ""),
                str(item.get("to_node") or ""),
            )
        )

        if limit > 0:
            selected_edges = selected_edges[:limit]
            nodes_from_edges = {str(edge.get("from_node")) for edge in selected_edges}
            nodes_from_edges.update(str(edge.get("to_node")) for edge in selected_edges)
            if focus_id:
                nodes_from_edges.add(focus_id)
            selected_nodes = selected_nodes.intersection(nodes_from_edges)

        selected_node_payloads = [
            nodes[node_id]
            for node_id in sorted(selected_nodes)
            if node_id in nodes
        ]

        return {
            "focus": focus_id,
            "depth": max(int(depth), 1),
            "nodes": selected_node_payloads,
            "edges": selected_edges,
            "summary": {
                "node_count": len(selected_node_payloads),
                "edge_count": len(selected_edges),
            },
        }

    def save_recommendations(
        self,
        session_id: str,
        recommendations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Persist recommendations for a session."""
        payload = {
            "session_id": session_id,
            "created_at": _now_iso(),
            "recommendations": recommendations,
        }
        with self._lock:
            output = self.recommendations_dir / f"{session_id}.json"
            atomic_write_json_compatible(output, payload)
            self._touch_stats("recommendations")
        return payload

    def load_recommendations(self, session_id: str) -> list[dict[str, Any]]:
        """Load cached recommendations for a session."""
        output = self.recommendations_dir / f"{session_id}.json"
        payload = self._load_json(output, {})
        if not isinstance(payload, dict):
            return []
        values = payload.get("recommendations", [])
        if not isinstance(values, list):
            return []
        return [item for item in values if isinstance(item, dict)]

    def _touch_stats(self, reason: str) -> None:
        stats = self._load_json(self.stats_path, {})
        if not isinstance(stats, dict):
            stats = {}
        stats["updated_at"] = _now_iso()
        stats["last_reason"] = reason
        atomic_write_json_compatible(self.stats_path, stats)


def _tokenize(text: str) -> list[str]:
    tokens = []
    for chunk in text.lower().split():
        cleaned = "".join(ch for ch in chunk if ch.isalnum() or ch in {"_", "-"})
        if cleaned:
            tokens.append(cleaned)
    return tokens


def _event_id(payload: dict[str, Any]) -> str:
    basis = {
        "session_id": payload.get("session_id"),
        "event_type": payload.get("event_type"),
        "question": payload.get("question"),
        "timestamp": payload.get("timestamp") or _now_iso(),
    }
    digest = hashlib.sha256(
        json.dumps(basis, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return f"evt_{digest[:16]}"


def _edge_id(from_node: str, to_node: str, edge_type: str, session_id: str) -> str:
    raw = f"{from_node}|{to_node}|{edge_type}|{session_id}"
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return f"edge_{digest[:16]}"


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


def _parse_date_or_datetime(
    value: str | None,
    *,
    end_of_day: bool = False,
) -> datetime | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None

    candidates = [text]
    if "T" not in text and " " not in text:
        suffix = "T23:59:59+00:00" if end_of_day else "T00:00:00+00:00"
        candidates.append(f"{text}{suffix}")
    for candidate in candidates:
        normalized = candidate.replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
        except ValueError:
            continue
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _copy_list_map(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict):
        return {}
    result: dict[str, list[str]] = {}
    for key, value in raw.items():
        if isinstance(value, list):
            result[str(key)] = [str(item) for item in value]
    return result


def _bfs_nodes(
    focus_id: str,
    max_depth: int,
    edges: dict[str, dict[str, Any]],
    adjacency: dict[str, list[str]],
    reverse_adjacency: dict[str, list[str]],
    edge_type: str | None,
) -> set[str]:
    seen = {focus_id}
    frontier = {focus_id}
    for _ in range(max_depth):
        next_frontier: set[str] = set()
        for node_id in frontier:
            edge_ids = list(adjacency.get(node_id, [])) + list(reverse_adjacency.get(node_id, []))
            for edge_id in edge_ids:
                edge = edges.get(edge_id)
                if not edge:
                    continue
                if edge_type and str(edge.get("edge_type")) != edge_type:
                    continue
                src = str(edge.get("from_node") or "")
                dst = str(edge.get("to_node") or "")
                if not src or not dst:
                    continue
                other = dst if src == node_id else src
                if other not in seen:
                    seen.add(other)
                    next_frontier.add(other)
        if not next_frontier:
            break
        frontier = next_frontier
    return seen
