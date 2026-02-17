"""
bridge.commands.team - Collaboration team command helpers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from collaboration import EncryptionService, TeamRole, TeamService, team_to_dict


def execute_team_unlock(
    *,
    workspace_id: str,
    passphrase: str,
    initialize: bool = False,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Unlock or initialize workspace collaboration key."""
    encryption = EncryptionService(storage_root=storage_root or "storage")
    metadata = encryption.storage.load_key_metadata(workspace_id)

    if metadata is None:
        if not initialize:
            return {
                "success": False,
                "workspace_id": workspace_id,
                "initialized": False,
                "unlocked": False,
                "error": (
                    "Workspace key metadata not found. "
                    "Re-run with initialize=True to create a new key."
                ),
            }
        created = encryption.initialize_workspace_key(passphrase, workspace_id)
        return {
            "success": True,
            "workspace_id": workspace_id,
            "initialized": True,
            "unlocked": True,
            "metadata": {
                "workspace_id": created.workspace_id,
                "kdf": created.kdf,
                "iterations": created.iterations,
                "created_at": created.created_at,
                "rotated_at": created.rotated_at,
            },
        }

    unlocked = encryption.unlock_workspace(passphrase, workspace_id)
    if not unlocked:
        return {
            "success": False,
            "workspace_id": workspace_id,
            "initialized": False,
            "unlocked": False,
            "error": "Invalid passphrase for workspace",
        }
    return {
        "success": True,
        "workspace_id": workspace_id,
        "initialized": False,
        "unlocked": True,
    }


def execute_team_create(
    *,
    name: str,
    owner_user_id: str,
    owner_name: str,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Create team with owner."""
    service = TeamService(storage_root=str(storage_root or "storage"))
    team = service.create_team(name, owner_user_id, owner_name)
    return {
        "success": True,
        "team": _normalize_team_payload(team_to_dict(team)),
    }


def execute_team_add(
    *,
    team_id: str,
    user_id: str,
    display_name: str,
    role: str,
    added_by: str,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """Add one member to team."""
    service = TeamService(storage_root=str(storage_root or "storage"))
    member_role = TeamRole(str(role))
    team = service.add_member(team_id, user_id, display_name, member_role, added_by)
    return {
        "success": True,
        "team": _normalize_team_payload(team_to_dict(team)),
    }


def execute_team_list(
    *,
    limit: int = 100,
    storage_root: Path | str | None = None,
) -> dict[str, Any]:
    """List local teams."""
    service = TeamService(storage_root=str(storage_root or "storage"))
    teams = service.list_teams(limit=max(int(limit), 0))
    payload = [_normalize_team_payload(team_to_dict(team)) for team in teams]
    return {
        "success": True,
        "count": len(payload),
        "teams": payload,
    }


def _normalize_team_payload(payload: dict[str, Any]) -> dict[str, Any]:
    members = payload.get("members", [])
    normalized_members: list[dict[str, Any]] = []
    if isinstance(members, list):
        for member in members:
            if not isinstance(member, dict):
                continue
            role = member.get("role")
            role_value = role.value if hasattr(role, "value") else str(role or "member")
            normalized_members.append(
                {
                    "user_id": str(member.get("user_id") or ""),
                    "display_name": str(member.get("display_name") or ""),
                    "role": role_value,
                    "added_at": str(member.get("added_at") or ""),
                    "added_by": str(member.get("added_by") or ""),
                }
            )
    return {
        "team_id": str(payload.get("team_id") or ""),
        "name": str(payload.get("name") or ""),
        "created_at": str(payload.get("created_at") or ""),
        "created_by": str(payload.get("created_by") or ""),
        "members": normalized_members,
    }

