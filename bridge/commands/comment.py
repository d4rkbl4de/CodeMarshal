"""
bridge.commands.comment - Collaboration comment command helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from collaboration import CommentService, EncryptionService, comment_to_dict


def execute_comment_add(
    *,
    share_id: str,
    author_id: str,
    author_name: str,
    body: str,
    parent_comment_id: str | None = None,
    workspace_id: str = "default",
    passphrase: str | None = None,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Add encrypted comment body."""
    encryption = _prepare_encryption(
        workspace_id=workspace_id,
        passphrase=passphrase,
        storage_root=storage_root,
    )
    service = CommentService(
        storage_root=str(storage_root or "storage"),
        encryption=encryption,
        workspace_id=workspace_id,
    )
    comment = service.add_comment(
        share_id=share_id,
        author_id=author_id,
        author_name=author_name,
        body=body,
        parent_comment_id=parent_comment_id,
    )
    return {
        "success": True,
        "comment": comment_to_dict(comment),
    }


def execute_comment_list(
    *,
    share_id: str,
    thread_root_id: str | None = None,
    limit: int = 200,
    workspace_id: str = "default",
    passphrase: str | None = None,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """List decrypted comments for one share."""
    encryption = _prepare_encryption(
        workspace_id=workspace_id,
        passphrase=passphrase,
        storage_root=storage_root,
    )
    service = CommentService(
        storage_root=str(storage_root or "storage"),
        encryption=encryption,
        workspace_id=workspace_id,
    )
    comments = service.list_comments(
        share_id=share_id,
        thread_root_id=thread_root_id,
        limit=max(int(limit), 0),
    )
    payload = [comment_to_dict(item) for item in comments]
    return {
        "success": True,
        "count": len(payload),
        "comments": payload,
    }


def execute_comment_resolve(
    *,
    comment_id: str,
    resolver_id: str,
    workspace_id: str = "default",
    passphrase: str | None = None,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve one comment."""
    encryption = _prepare_encryption(
        workspace_id=workspace_id,
        passphrase=passphrase,
        storage_root=storage_root,
    )
    service = CommentService(
        storage_root=str(storage_root or "storage"),
        encryption=encryption,
        workspace_id=workspace_id,
    )
    comment = service.resolve_comment(comment_id, resolver_id)
    return {
        "success": True,
        "comment": comment_to_dict(comment),
    }


def _prepare_encryption(
    *,
    workspace_id: str,
    passphrase: str | None,
    storage_root: Path | str | None,
) -> EncryptionService:
    if passphrase is None:
        raise ValueError(
            "Encrypted comment operations require passphrase "
            "(provide via --passphrase-env)."
        )
    encryption = EncryptionService(storage_root=storage_root or "storage")
    metadata = encryption.storage.load_key_metadata(workspace_id)
    if metadata is None:
        raise ValueError(
            "Workspace key metadata not found; initialize via `team unlock --initialize`."
        )
    if not encryption.unlock_workspace(passphrase, workspace_id):
        raise ValueError("Invalid workspace passphrase")
    return encryption

