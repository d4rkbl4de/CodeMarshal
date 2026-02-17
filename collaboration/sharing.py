"""
collaboration/sharing.py

Local sharing service with encrypted payloads and permission checks.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from collaboration.encryption import EncryptionService
from storage.collaboration_storage import CollaborationStorage


class SharePermission(str, Enum):
    READ = "read"
    COMMENT = "comment"
    MANAGE = "manage"


@dataclass(frozen=True)
class ShareTarget:
    target_type: str  # "team" or "user"
    target_id: str
    permission: SharePermission


@dataclass(frozen=True)
class SharedArtifact:
    share_id: str
    session_id: str
    created_at: str
    created_by: str
    title: str
    summary: str
    targets: list[ShareTarget] = field(default_factory=list)
    encrypted_payload_ref: str = ""
    status: str = "active"


class SharingService:
    """Service for creating and managing local shares."""

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

    def create_share(
        self,
        session_id: str,
        created_by: str,
        targets: list[ShareTarget],
        *,
        title: str = "",
        summary: str = "",
        payload: dict[str, Any] | None = None,
    ) -> SharedArtifact:
        """Create shared artifact with encrypted payload."""
        clean_session = str(session_id or "").strip()
        clean_creator = str(created_by or "").strip()
        if not clean_session:
            raise ValueError("session_id is required")
        if not clean_creator:
            raise ValueError("created_by is required")
        if not targets:
            raise ValueError("At least one share target is required")

        share_id = f"share_{uuid.uuid4().hex[:12]}"
        payload_to_encrypt = payload or {
            "session_id": clean_session,
            "title": str(title or "").strip(),
            "summary": str(summary or "").strip(),
        }
        envelope = self.encryption.encrypt_json(
            payload_to_encrypt,
            context=f"share:{share_id}",
            workspace_id=self.workspace_id,
        )
        payload_ref = self.storage.save_payload_envelope(share_id, envelope)

        artifact = SharedArtifact(
            share_id=share_id,
            session_id=clean_session,
            created_at=_now_iso(),
            created_by=clean_creator,
            title=str(title or "").strip(),
            summary=str(summary or "").strip(),
            targets=targets,
            encrypted_payload_ref=payload_ref,
            status="active",
        )
        self.storage.save_share(_serialize_share(artifact))
        return artifact

    def list_shares(
        self,
        *,
        session_id: str | None = None,
        team_id: str | None = None,
        limit: int = 100,
    ) -> list[SharedArtifact]:
        """List shared artifacts."""
        rows = self.storage.list_shares(
            session_id=session_id,
            team_id=team_id,
            limit=limit,
        )
        artifacts = [_deserialize_share(item) for item in rows if isinstance(item, dict)]
        return [item for item in artifacts if item is not None]

    def revoke_share(self, share_id: str, revoked_by: str) -> bool:
        """Revoke one share if actor can manage it."""
        artifact = self.get_share(share_id)
        if artifact is None:
            return False
        if not self._has_access(artifact, revoked_by, SharePermission.MANAGE):
            raise PermissionError("User does not have manage permission for this share")
        payload = _serialize_share(artifact)
        payload["status"] = "revoked"
        payload["revoked_at"] = _now_iso()
        payload["revoked_by"] = revoked_by
        self.storage.save_share(payload)
        return True

    def resolve_share_payload(self, share_id: str, accessor_id: str) -> dict[str, Any]:
        """Resolve and decrypt share payload for accessor."""
        artifact = self.get_share(share_id)
        if artifact is None:
            raise ValueError(f"Share not found: {share_id}")
        if artifact.status != "active":
            raise ValueError(f"Share is not active: {share_id}")
        if not self._has_access(artifact, accessor_id, SharePermission.READ):
            raise PermissionError("Accessor does not have read permission")

        envelope = self.storage.load_payload_envelope(share_id)
        if not isinstance(envelope, dict):
            raise ValueError(f"Encrypted payload missing for share: {share_id}")
        return self.encryption.decrypt_json(
            envelope,
            context=f"share:{share_id}",
            workspace_id=self.workspace_id,
        )

    def get_share(self, share_id: str) -> SharedArtifact | None:
        """Load share metadata."""
        payload = self.storage.load_share(share_id)
        if not isinstance(payload, dict):
            return None
        return _deserialize_share(payload)

    @staticmethod
    def _has_access(
        artifact: SharedArtifact,
        accessor_id: str,
        required: SharePermission,
    ) -> bool:
        if str(artifact.created_by) == str(accessor_id):
            return True
        order = {
            SharePermission.READ: 1,
            SharePermission.COMMENT: 2,
            SharePermission.MANAGE: 3,
        }
        needed = order[required]
        for target in artifact.targets:
            if str(target.target_id) != str(accessor_id):
                continue
            if order[target.permission] >= needed:
                return True
        return False


def _serialize_share(artifact: SharedArtifact) -> dict[str, Any]:
    return {
        "share_id": artifact.share_id,
        "session_id": artifact.session_id,
        "created_at": artifact.created_at,
        "created_by": artifact.created_by,
        "title": artifact.title,
        "summary": artifact.summary,
        "targets": [
            {
                "target_type": target.target_type,
                "target_id": target.target_id,
                "permission": target.permission.value,
            }
            for target in artifact.targets
        ],
        "encrypted_payload_ref": artifact.encrypted_payload_ref,
        "status": artifact.status,
    }


def _deserialize_share(payload: dict[str, Any]) -> SharedArtifact | None:
    share_id = str(payload.get("share_id") or "").strip()
    if not share_id:
        return None
    targets_raw = payload.get("targets", [])
    targets: list[ShareTarget] = []
    if isinstance(targets_raw, list):
        for item in targets_raw:
            if not isinstance(item, dict):
                continue
            try:
                permission = SharePermission(str(item.get("permission") or "read"))
            except ValueError:
                permission = SharePermission.READ
            targets.append(
                ShareTarget(
                    target_type=str(item.get("target_type") or "user"),
                    target_id=str(item.get("target_id") or ""),
                    permission=permission,
                )
            )

    return SharedArtifact(
        share_id=share_id,
        session_id=str(payload.get("session_id") or ""),
        created_at=str(payload.get("created_at") or ""),
        created_by=str(payload.get("created_by") or ""),
        title=str(payload.get("title") or ""),
        summary=str(payload.get("summary") or ""),
        targets=targets,
        encrypted_payload_ref=str(payload.get("encrypted_payload_ref") or ""),
        status=str(payload.get("status") or "active"),
    )


def share_to_dict(artifact: SharedArtifact) -> dict[str, Any]:
    """Public serializer helper for command layer."""
    payload = asdict(artifact)
    payload["targets"] = [
        {
            "target_type": target.target_type,
            "target_id": target.target_id,
            "permission": target.permission.value,
        }
        for target in artifact.targets
    ]
    return payload


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()

