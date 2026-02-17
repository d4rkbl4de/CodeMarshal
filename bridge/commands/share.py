"""
bridge.commands.share - Collaboration share command helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from collaboration import (
    EncryptionService,
    SharePermission,
    ShareTarget,
    SharingService,
    share_to_dict,
)


def execute_share_create(
    *,
    session_id: str,
    created_by: str,
    targets: list[dict[str, str]],
    title: str = "",
    summary: str = "",
    workspace_id: str = "default",
    passphrase: str | None = None,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Create encrypted shared artifact."""
    encryption, initialized = _prepare_encryption(
        workspace_id=workspace_id,
        passphrase=passphrase,
        storage_root=storage_root,
        initialize_if_missing=True,
    )
    share_targets = _to_targets(targets)
    service = SharingService(
        storage_root=str(storage_root or "storage"),
        encryption=encryption,
        workspace_id=workspace_id,
    )
    artifact = service.create_share(
        session_id=session_id,
        created_by=created_by,
        targets=share_targets,
        title=title,
        summary=summary,
    )
    return {
        "success": True,
        "initialized_workspace_key": initialized,
        "workspace_id": workspace_id,
        "share": _normalize_share_payload(share_to_dict(artifact)),
    }


def execute_share_list(
    *,
    session_id: str | None = None,
    team_id: str | None = None,
    limit: int = 100,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """List share metadata."""
    service = SharingService(storage_root=str(storage_root or "storage"))
    artifacts = service.list_shares(
        session_id=session_id,
        team_id=team_id,
        limit=max(int(limit), 0),
    )
    payload = [_normalize_share_payload(share_to_dict(item)) for item in artifacts]
    return {
        "success": True,
        "count": len(payload),
        "shares": payload,
    }


def execute_share_revoke(
    *,
    share_id: str,
    revoked_by: str,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Revoke one active share."""
    service = SharingService(storage_root=str(storage_root or "storage"))
    ok = service.revoke_share(share_id, revoked_by)
    return {
        "success": bool(ok),
        "share_id": share_id,
        "revoked": bool(ok),
    }


def execute_share_resolve(
    *,
    share_id: str,
    accessor_id: str,
    workspace_id: str = "default",
    passphrase: str | None = None,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Resolve decrypted payload for one share."""
    encryption, initialized = _prepare_encryption(
        workspace_id=workspace_id,
        passphrase=passphrase,
        storage_root=storage_root,
        initialize_if_missing=False,
    )
    service = SharingService(
        storage_root=str(storage_root or "storage"),
        encryption=encryption,
        workspace_id=workspace_id,
    )
    payload = service.resolve_share_payload(share_id, accessor_id)
    return {
        "success": True,
        "workspace_id": workspace_id,
        "initialized_workspace_key": initialized,
        "share_id": share_id,
        "payload": payload,
    }


def _to_targets(targets: list[dict[str, str]]) -> list[ShareTarget]:
    rows: list[ShareTarget] = []
    for item in targets:
        if not isinstance(item, dict):
            continue
        target_type = str(item.get("target_type") or "").strip().lower()
        target_id = str(item.get("target_id") or "").strip()
        permission_raw = str(item.get("permission") or SharePermission.READ.value).strip()
        if target_type not in {"team", "user"}:
            raise ValueError(f"Invalid target_type: {target_type}")
        if not target_id:
            raise ValueError("target_id is required for share target")
        permission = SharePermission(permission_raw)
        rows.append(
            ShareTarget(
                target_type=target_type,
                target_id=target_id,
                permission=permission,
            )
        )
    if not rows:
        raise ValueError("At least one valid share target is required")
    return rows


def _prepare_encryption(
    *,
    workspace_id: str,
    passphrase: str | None,
    storage_root: Path | str | None,
    initialize_if_missing: bool,
) -> tuple[EncryptionService, bool]:
    encryption = EncryptionService(storage_root=storage_root or "storage")
    metadata = encryption.storage.load_key_metadata(workspace_id)
    if passphrase is None:
        raise ValueError(
            "Encrypted collaboration operation requires passphrase "
            "(provide via --passphrase-env)."
        )

    initialized = False
    if metadata is None:
        if not initialize_if_missing:
            raise ValueError("Workspace key metadata not found")
        encryption.initialize_workspace_key(passphrase, workspace_id)
        initialized = True
        return encryption, initialized

    unlocked = encryption.unlock_workspace(passphrase, workspace_id)
    if not unlocked:
        raise ValueError("Invalid workspace passphrase")
    return encryption, initialized


def _normalize_share_payload(payload: dict[str, Any]) -> dict[str, Any]:
    targets_raw = payload.get("targets", [])
    targets: list[dict[str, str]] = []
    if isinstance(targets_raw, list):
        for item in targets_raw:
            if not isinstance(item, dict):
                continue
            permission = item.get("permission")
            permission_value = (
                permission.value if hasattr(permission, "value") else str(permission or "read")
            )
            targets.append(
                {
                    "target_type": str(item.get("target_type") or "user"),
                    "target_id": str(item.get("target_id") or ""),
                    "permission": permission_value,
                }
            )
    return {
        "share_id": str(payload.get("share_id") or ""),
        "session_id": str(payload.get("session_id") or ""),
        "created_at": str(payload.get("created_at") or ""),
        "created_by": str(payload.get("created_by") or ""),
        "title": str(payload.get("title") or ""),
        "summary": str(payload.get("summary") or ""),
        "targets": targets,
        "encrypted_payload_ref": str(payload.get("encrypted_payload_ref") or ""),
        "status": str(payload.get("status") or "active"),
    }

