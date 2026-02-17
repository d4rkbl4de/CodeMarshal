"""
collaboration/comments.py

Threaded comments for shared artifacts with encrypted comment bodies.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

from collaboration.encryption import EncryptionService
from storage.collaboration_storage import CollaborationStorage


@dataclass(frozen=True)
class Comment:
    comment_id: str
    share_id: str
    author_id: str
    author_name: str
    body: str
    created_at: str
    edited_at: str | None = None
    status: str = "active"
    parent_comment_id: str | None = None
    thread_root_id: str | None = None


class CommentService:
    """Service for comment creation and threaded retrieval."""

    def __init__(
        self,
        *,
        storage_root: str = "storage",
        encryption: EncryptionService | None = None,
        workspace_id: str = "default",
    ) -> None:
        self.storage = CollaborationStorage(storage_root)
        self.encryption = encryption or EncryptionService(storage_root=storage_root)
        self.workspace_id = workspace_id

    def add_comment(
        self,
        share_id: str,
        author_id: str,
        author_name: str,
        body: str,
        *,
        parent_comment_id: str | None = None,
    ) -> Comment:
        """Add comment with optional thread parent."""
        clean_share = str(share_id or "").strip()
        clean_author = str(author_id or "").strip()
        clean_body = str(body or "").strip()
        if not clean_share:
            raise ValueError("share_id is required")
        if not clean_author:
            raise ValueError("author_id is required")
        if not clean_body:
            raise ValueError("Comment body must not be empty")

        comment_id = f"cmt_{uuid.uuid4().hex[:14]}"
        parent_id = str(parent_comment_id or "").strip() or None
        thread_root_id = parent_id
        if parent_id:
            parent = self.storage.load_comment(parent_id)
            if isinstance(parent, dict):
                thread_root_id = str(parent.get("thread_root_id") or parent_id)

        envelope = self.encryption.encrypt_json(
            {"body": clean_body},
            context=f"comment:{comment_id}",
            workspace_id=self.workspace_id,
        )
        payload = {
            "comment_id": comment_id,
            "share_id": clean_share,
            "author_id": clean_author,
            "author_name": str(author_name or "").strip() or clean_author,
            "body_envelope": envelope,
            "created_at": _now_iso(),
            "edited_at": None,
            "status": "active",
            "parent_comment_id": parent_id,
            "thread_root_id": thread_root_id,
        }
        self.storage.save_comment(payload)
        return self._deserialize_comment(payload)

    def edit_comment(self, comment_id: str, editor_id: str, body: str) -> Comment:
        """Edit existing comment body."""
        payload = self.storage.load_comment(comment_id)
        if not isinstance(payload, dict):
            raise ValueError(f"Comment not found: {comment_id}")
        if str(payload.get("author_id") or "") != str(editor_id):
            raise PermissionError("Only the author can edit this comment")
        clean_body = str(body or "").strip()
        if not clean_body:
            raise ValueError("Comment body must not be empty")

        envelope = self.encryption.encrypt_json(
            {"body": clean_body},
            context=f"comment:{comment_id}",
            workspace_id=self.workspace_id,
        )
        payload["body_envelope"] = envelope
        payload["edited_at"] = _now_iso()
        self.storage.save_comment(payload)
        return self._deserialize_comment(payload)

    def list_comments(
        self,
        share_id: str,
        *,
        thread_root_id: str | None = None,
        limit: int = 200,
    ) -> list[Comment]:
        """List and decrypt comments."""
        rows = self.storage.list_comments(
            share_id=share_id,
            thread_root_id=thread_root_id,
            limit=limit,
        )
        comments: list[Comment] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            comments.append(self._deserialize_comment(row))
        return comments

    def resolve_comment(self, comment_id: str, resolver_id: str) -> Comment:
        """Mark comment as resolved."""
        payload = self.storage.load_comment(comment_id)
        if not isinstance(payload, dict):
            raise ValueError(f"Comment not found: {comment_id}")
        if not str(resolver_id or "").strip():
            raise ValueError("resolver_id is required")
        payload["status"] = "resolved"
        payload["resolved_at"] = _now_iso()
        payload["resolved_by"] = str(resolver_id)
        self.storage.save_comment(payload)
        return self._deserialize_comment(payload)

    def _deserialize_comment(self, payload: dict[str, Any]) -> Comment:
        comment_id = str(payload.get("comment_id") or "")
        envelope = payload.get("body_envelope", {})
        if not isinstance(envelope, dict):
            envelope = {}
        decrypted = self.encryption.decrypt_json(
            envelope,
            context=f"comment:{comment_id}",
            workspace_id=self.workspace_id,
        )
        body = str(decrypted.get("body") or "")
        return Comment(
            comment_id=comment_id,
            share_id=str(payload.get("share_id") or ""),
            author_id=str(payload.get("author_id") or ""),
            author_name=str(payload.get("author_name") or ""),
            body=body,
            created_at=str(payload.get("created_at") or ""),
            edited_at=str(payload.get("edited_at") or "") or None,
            status=str(payload.get("status") or "active"),
            parent_comment_id=str(payload.get("parent_comment_id") or "") or None,
            thread_root_id=str(payload.get("thread_root_id") or "") or None,
        )


def comment_to_dict(comment: Comment) -> dict[str, Any]:
    """Public serializer helper for command layer."""
    return asdict(comment)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()

