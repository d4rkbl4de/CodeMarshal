"""
knowledge/knowledge_graph.py

Incremental graph construction and traversal for investigation artifacts.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from storage.knowledge_storage import KnowledgeStorage


class KnowledgeGraphService:
    """Build and query a lightweight investigation graph."""

    def __init__(
        self,
        storage: KnowledgeStorage | None = None,
        storage_root: Path | str | None = None,
    ) -> None:
        self.storage = storage or KnowledgeStorage(storage_root=storage_root)

    def ensure_session_node(self, session_id: str, path: str | None = None) -> dict[str, Any]:
        """Ensure the session root node exists."""
        return self.storage.upsert_graph_node(
            {
                "node_id": f"session:{session_id}",
                "node_type": "session",
                "label": session_id,
                "session_ids": [session_id],
                "attributes": {"path": path or ""},
            }
        )

    def ingest_observations(
        self,
        session_id: str,
        observations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Ingest observations into graph nodes/edges."""
        self.ensure_session_node(session_id)
        node_count = 0
        edge_count = 0

        for observation in observations:
            if not isinstance(observation, dict):
                continue

            obs_type = str(observation.get("type") or "unknown")
            file_path = (
                str(observation.get("path") or "")
                or str(observation.get("file") or "")
                or str(observation.get("module_path") or "")
            )
            file_node_id = ""
            if file_path:
                file_node_id = self._file_node_id(file_path)
                self.storage.upsert_graph_node(
                    {
                        "node_id": file_node_id,
                        "node_type": "file",
                        "label": file_path,
                        "session_ids": [session_id],
                        "attributes": {"path": file_path},
                    }
                )
                node_count += 1
                self._add_edge(
                    from_node=f"session:{session_id}",
                    to_node=file_node_id,
                    edge_type="contains_file",
                    session_id=session_id,
                )
                edge_count += 1

            if obs_type == "import_sight":
                statements = observation.get("statements", []) or []
                for statement in statements:
                    if not isinstance(statement, dict):
                        continue
                    imported = str(
                        statement.get("imported_module")
                        or statement.get("module")
                        or statement.get("target_module")
                        or ""
                    ).strip()
                    if not imported:
                        continue
                    module_node = self._module_node_id(imported)
                    self.storage.upsert_graph_node(
                        {
                            "node_id": module_node,
                            "node_type": "module",
                            "label": imported,
                            "session_ids": [session_id],
                            "attributes": {"module": imported},
                        }
                    )
                    node_count += 1
                    source = file_node_id or f"session:{session_id}"
                    self._add_edge(
                        from_node=source,
                        to_node=module_node,
                        edge_type="imports",
                        session_id=session_id,
                    )
                    edge_count += 1

            if obs_type == "export_sight":
                exports = observation.get("exports", []) or []
                for export in exports:
                    if not isinstance(export, dict):
                        continue
                    symbol_name = str(export.get("name") or "").strip()
                    if not symbol_name:
                        continue
                    symbol_node = self._symbol_node_id(file_path, symbol_name)
                    self.storage.upsert_graph_node(
                        {
                            "node_id": symbol_node,
                            "node_type": "symbol",
                            "label": symbol_name,
                            "session_ids": [session_id],
                            "attributes": {
                                "symbol": symbol_name,
                                "file_path": file_path,
                            },
                        }
                    )
                    node_count += 1
                    source = file_node_id or f"session:{session_id}"
                    self._add_edge(
                        from_node=source,
                        to_node=symbol_node,
                        edge_type="exports",
                        session_id=session_id,
                    )
                    edge_count += 1

            if obs_type == "boundary_sight":
                crossings = observation.get("crossings", []) or []
                for crossing in crossings:
                    if not isinstance(crossing, dict):
                        continue
                    source_mod = str(crossing.get("source_module") or "").strip()
                    target_mod = str(crossing.get("target_module") or "").strip()
                    if not source_mod or not target_mod:
                        continue
                    source_node = self._module_node_id(source_mod)
                    target_node = self._module_node_id(target_mod)
                    self.storage.upsert_graph_node(
                        {
                            "node_id": source_node,
                            "node_type": "module",
                            "label": source_mod,
                            "session_ids": [session_id],
                            "attributes": {"module": source_mod},
                        }
                    )
                    self.storage.upsert_graph_node(
                        {
                            "node_id": target_node,
                            "node_type": "module",
                            "label": target_mod,
                            "session_ids": [session_id],
                            "attributes": {"module": target_mod},
                        }
                    )
                    node_count += 2
                    self._add_edge(
                        from_node=source_node,
                        to_node=target_node,
                        edge_type="depends_on",
                        session_id=session_id,
                    )
                    edge_count += 1

        return {
            "session_id": session_id,
            "nodes_added": node_count,
            "edges_added": edge_count,
        }

    def ingest_query(
        self,
        session_id: str,
        question: str,
        question_type: str,
    ) -> dict[str, Any]:
        """Add query events to graph for traversal and context."""
        self.ensure_session_node(session_id)
        query_id = self._query_node_id(question, question_type)
        self.storage.upsert_graph_node(
            {
                "node_id": query_id,
                "node_type": "query",
                "label": question,
                "session_ids": [session_id],
                "attributes": {"question_type": question_type},
            }
        )
        edge = self._add_edge(
            from_node=f"session:{session_id}",
            to_node=query_id,
            edge_type="asked_question",
            session_id=session_id,
        )
        return {
            "session_id": session_id,
            "query_node_id": query_id,
            "edge_id": edge.get("edge_id"),
        }

    def ingest_pattern_matches(
        self,
        session_id: str,
        matches: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Project pattern scan matches onto the graph."""
        self.ensure_session_node(session_id)
        edges = 0
        nodes = 0

        for match in matches:
            if not isinstance(match, dict):
                continue
            pattern_id = str(match.get("pattern_id") or "").strip()
            if not pattern_id:
                continue
            pattern_node = f"pattern:{pattern_id}"
            self.storage.upsert_graph_node(
                {
                    "node_id": pattern_node,
                    "node_type": "pattern",
                    "label": pattern_id,
                    "session_ids": [session_id],
                    "attributes": {
                        "severity": str(match.get("severity") or ""),
                    },
                }
            )
            nodes += 1
            self._add_edge(
                from_node=f"session:{session_id}",
                to_node=pattern_node,
                edge_type="mentions_pattern",
                session_id=session_id,
            )
            edges += 1

            file_path = str(match.get("file") or "").strip()
            if file_path:
                file_node = self._file_node_id(file_path)
                self.storage.upsert_graph_node(
                    {
                        "node_id": file_node,
                        "node_type": "file",
                        "label": file_path,
                        "session_ids": [session_id],
                        "attributes": {"path": file_path},
                    }
                )
                nodes += 1
                self._add_edge(
                    from_node=pattern_node,
                    to_node=file_node,
                    edge_type="hits_file",
                    session_id=session_id,
                )
                edges += 1

        return {"session_id": session_id, "nodes_added": nodes, "edges_added": edges}

    def get_graph(
        self,
        session_id: str | None = None,
        *,
        focus: str | None = None,
        depth: int = 2,
        edge_type: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        """Return a bounded graph projection."""
        return self.storage.get_graph(
            session_id=session_id,
            focus=focus,
            depth=depth,
            edge_type=edge_type,
            limit=limit,
        )

    def _add_edge(
        self,
        *,
        from_node: str,
        to_node: str,
        edge_type: str,
        session_id: str,
        weight: float = 1.0,
    ) -> dict[str, Any]:
        return self.storage.add_graph_edge(
            {
                "from_node": from_node,
                "to_node": to_node,
                "edge_type": edge_type,
                "session_id": session_id,
                "weight": weight,
            }
        )

    def _file_node_id(self, file_path: str) -> str:
        digest = hashlib.sha256(file_path.encode("utf-8")).hexdigest()[:16]
        return f"file:{digest}"

    def _module_node_id(self, module_name: str) -> str:
        digest = hashlib.sha256(module_name.encode("utf-8")).hexdigest()[:16]
        return f"module:{digest}"

    def _symbol_node_id(self, file_path: str, symbol_name: str) -> str:
        raw = f"{file_path}:{symbol_name}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"symbol:{digest}"

    def _query_node_id(self, question: str, question_type: str) -> str:
        raw = f"{question_type}:{question}"
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        return f"query:{digest}"

