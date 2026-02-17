"""
storage/collaboration_storage.py

Persistent local storage for collaboration artifacts:
- teams
- shares
- comments
- encrypted payload envelopes
- workspace key metadata
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from storage.atomic import atomic_write_json_compatible


class CollaborationStorage:
    """Storage adapter for collaboration features."""

    def __init__(self, storage_root: Path | str | None = None) -> None:
        self.storage_root = Path(storage_root or "storage")
        self.base_path = self.storage_root / "collaboration"
        self.teams_dir = self.base_path / "teams"
        self.shares_dir = self.base_path / "shares"
        self.comments_dir = self.base_path / "comments"
        self.payloads_dir = self.base_path / "payloads"
        self.keys_dir = self.base_path / "keys"
        self._lock = threading.RLock()
        self._ensure_layout()

    def _ensure_layout(self) -> None:
        self.teams_dir.mkdir(parents=True, exist_ok=True)
        self.shares_dir.mkdir(parents=True, exist_ok=True)
        self.comments_dir.mkdir(parents=True, exist_ok=True)
        self.payloads_dir.mkdir(parents=True, exist_ok=True)
        self.keys_dir.mkdir(parents=True, exist_ok=True)

    def save_team(self, team: dict[str, Any]) -> dict[str, Any]:
        """Persist team payload."""
        team_id = str(team.get("team_id") or "").strip()
        if not team_id:
            raise ValueError("team_id is required")
        with self._lock:
            path = self.teams_dir / f"{team_id}.team.json"
            atomic_write_json_compatible(path, team)
        return team

    def load_team(self, team_id: str) -> dict[str, Any] | None:
        """Load one team payload."""
        path = self.teams_dir / f"{team_id}.team.json"
        return self._load_json_file(path)

    def list_teams(self, limit: int = 100) -> list[dict[str, Any]]:
        """List teams in recency-like order by filename."""
        rows: list[dict[str, Any]] = []
        for path in sorted(self.teams_dir.glob("*.team.json"), reverse=True):
            payload = self._load_json_file(path)
            if isinstance(payload, dict):
                rows.append(payload)
        if limit <= 0:
            return rows
        return rows[:limit]

    def save_share(self, share: dict[str, Any]) -> dict[str, Any]:
        """Persist share metadata payload."""
        share_id = str(share.get("share_id") or "").strip()
        if not share_id:
            raise ValueError("share_id is required")
        with self._lock:
            path = self.shares_dir / f"{share_id}.share.json"
            atomic_write_json_compatible(path, share)
        return share

    def load_share(self, share_id: str) -> dict[str, Any] | None:
        """Load share metadata payload."""
        path = self.shares_dir / f"{share_id}.share.json"
        return self._load_json_file(path)

    def list_shares(
        self,
        *,
        session_id: str | None = None,
        team_id: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List share metadata with optional filters."""
        rows: list[dict[str, Any]] = []
        for path in sorted(self.shares_dir.glob("*.share.json"), reverse=True):
            payload = self._load_json_file(path)
            if not isinstance(payload, dict):
                continue
            if session_id and str(payload.get("session_id") or "") != session_id:
                continue
            if team_id:
                targets = payload.get("targets", [])
                if not isinstance(targets, list):
                    continue
                has_team = any(
                    isinstance(item, dict)
                    and str(item.get("target_type") or "") == "team"
                    and str(item.get("target_id") or "") == team_id
                    for item in targets
                )
                if not has_team:
                    continue
            rows.append(payload)
        if limit <= 0:
            return rows
        return rows[:limit]

    def save_comment(self, comment: dict[str, Any]) -> dict[str, Any]:
        """Persist comment metadata payload."""
        comment_id = str(comment.get("comment_id") or "").strip()
        if not comment_id:
            raise ValueError("comment_id is required")
        with self._lock:
            path = self.comments_dir / f"{comment_id}.comment.json"
            atomic_write_json_compatible(path, comment)
        return comment

    def load_comment(self, comment_id: str) -> dict[str, Any] | None:
        """Load one comment payload."""
        path = self.comments_dir / f"{comment_id}.comment.json"
        return self._load_json_file(path)

    def list_comments(
        self,
        *,
        share_id: str,
        thread_root_id: str | None = None,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """List comments for one share."""
        rows: list[dict[str, Any]] = []
        for path in sorted(self.comments_dir.glob("*.comment.json")):
            payload = self._load_json_file(path)
            if not isinstance(payload, dict):
                continue
            if str(payload.get("share_id") or "") != share_id:
                continue
            if thread_root_id and str(payload.get("thread_root_id") or "") != thread_root_id:
                continue
            rows.append(payload)
        rows.sort(key=lambda item: str(item.get("created_at") or ""))
        if limit <= 0:
            return rows
        return rows[:limit]

    def save_payload_envelope(self, payload_id: str, envelope: dict[str, Any]) -> str:
        """Save encrypted payload envelope and return payload ref path."""
        clean_payload_id = str(payload_id or "").strip()
        if not clean_payload_id:
            raise ValueError("payload_id is required")
        with self._lock:
            path = self.payloads_dir / f"{clean_payload_id}.enc.json"
            atomic_write_json_compatible(path, envelope)
        return str(path)

    def load_payload_envelope(self, payload_id: str) -> dict[str, Any] | None:
        """Load encrypted payload envelope by payload id."""
        path = self.payloads_dir / f"{payload_id}.enc.json"
        return self._load_json_file(path)

    def save_key_metadata(self, workspace_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        """Save key metadata for one workspace."""
        key = _normalize_workspace_id(workspace_id)
        with self._lock:
            path = self.keys_dir / f"{key}.workspace_key.meta.json"
            atomic_write_json_compatible(path, metadata)
        return metadata

    def load_key_metadata(self, workspace_id: str) -> dict[str, Any] | None:
        """Load key metadata for one workspace."""
        key = _normalize_workspace_id(workspace_id)
        path = self.keys_dir / f"{key}.workspace_key.meta.json"
        return self._load_json_file(path)

    @staticmethod
    def _load_json_file(path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if isinstance(payload, dict):
            return payload
        return None


def _normalize_workspace_id(workspace_id: str) -> str:
    raw = str(workspace_id or "default").strip().lower()
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in raw)
    collapsed = "_".join(part for part in cleaned.split("_") if part)
    return collapsed or "default"

