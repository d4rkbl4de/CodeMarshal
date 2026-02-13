"""
knowledge/base.py

Minimal knowledge base for CodeMarshal.
Stores insights as JSONL and provides lightweight search and trend aggregation.
"""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class KnowledgeBase:
    """Lightweight knowledge base backed by JSON artifacts."""

    def __init__(self, base_path: Path | None = None) -> None:
        self.base_path = base_path or Path("storage") / "knowledge"
        self.storage_root = self.base_path.parent
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.insights_path = self.base_path / "insights.jsonl"
        self.trends_path = self.base_path / "pattern_trends.json"
        self.similarity_path = self.base_path / "similarity_index.json"

    def add_insight(self, investigation_id: str, insight: dict[str, Any]) -> dict[str, Any]:
        record = {
            "id": str(uuid.uuid4()),
            "investigation_id": investigation_id,
            "timestamp": datetime.now(UTC).isoformat(),
            "insight": insight,
        }
        with self.insights_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
        return record

    def search_insights(self, query: str) -> list[dict[str, Any]]:
        if not self.insights_path.exists():
            return []
        results: list[dict[str, Any]] = []
        needle = query.lower()
        with self.insights_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                if needle not in line.lower():
                    continue
                try:
                    results.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return results

    def get_pattern_trends(self, pattern_id: str) -> dict[str, Any]:
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
        self.trends_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False)
        )
        return payload

    def find_similar_codebases(self, investigation_id: str) -> list[dict[str, Any]]:
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
            sessions[session_id] = pattern_ids
            if session_id == investigation_id:
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
        self.similarity_path.write_text(
            json.dumps(results, indent=2, ensure_ascii=False)
        )
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
