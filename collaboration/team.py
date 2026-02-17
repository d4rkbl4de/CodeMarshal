"""
collaboration/team.py

Local team management for collaboration workflows.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum

from storage.collaboration_storage import CollaborationStorage


class TeamRole(str, Enum):
    OWNER = "owner"
    MAINTAINER = "maintainer"
    MEMBER = "member"
    VIEWER = "viewer"


@dataclass(frozen=True)
class TeamMember:
    user_id: str
    display_name: str
    role: TeamRole
    added_at: str
    added_by: str


@dataclass(frozen=True)
class Team:
    team_id: str
    name: str
    created_at: str
    created_by: str
    members: list[TeamMember] = field(default_factory=list)


class TeamService:
    """Service for team CRUD operations."""

    def __init__(self, storage_root: str | None = None) -> None:
        self.storage = CollaborationStorage(storage_root or "storage")

    def create_team(self, name: str, owner_user_id: str, owner_name: str) -> Team:
        """Create a new local team with one owner."""
        clean_name = str(name or "").strip()
        if not clean_name:
            raise ValueError("Team name is required")
        owner_user = str(owner_user_id or "").strip()
        if not owner_user:
            raise ValueError("owner_user_id is required")
        owner_display = str(owner_name or "").strip() or owner_user

        team_id = f"team_{uuid.uuid4().hex[:12]}"
        now = _now_iso()
        team = Team(
            team_id=team_id,
            name=clean_name,
            created_at=now,
            created_by=owner_user,
            members=[
                TeamMember(
                    user_id=owner_user,
                    display_name=owner_display,
                    role=TeamRole.OWNER,
                    added_at=now,
                    added_by=owner_user,
                )
            ],
        )
        self.storage.save_team(_serialize_team(team))
        return team

    def add_member(
        self,
        team_id: str,
        user_id: str,
        display_name: str,
        role: TeamRole,
        added_by: str,
    ) -> Team:
        """Add or update a team member."""
        team = self.get_team(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")

        user = str(user_id or "").strip()
        if not user:
            raise ValueError("user_id is required")
        actor = str(added_by or "").strip()
        if not actor:
            raise ValueError("added_by is required")
        name = str(display_name or "").strip() or user

        existing = [member for member in team.members if member.user_id != user]
        existing.append(
            TeamMember(
                user_id=user,
                display_name=name,
                role=role,
                added_at=_now_iso(),
                added_by=actor,
            )
        )
        updated = Team(
            team_id=team.team_id,
            name=team.name,
            created_at=team.created_at,
            created_by=team.created_by,
            members=sorted(existing, key=lambda item: item.user_id),
        )
        self.storage.save_team(_serialize_team(updated))
        return updated

    def remove_member(self, team_id: str, user_id: str, removed_by: str) -> Team:
        """Remove team member while preserving at least one owner."""
        team = self.get_team(team_id)
        if team is None:
            raise ValueError(f"Team not found: {team_id}")
        actor = str(removed_by or "").strip()
        if not actor:
            raise ValueError("removed_by is required")

        filtered = [member for member in team.members if member.user_id != user_id]
        if len(filtered) == len(team.members):
            return team

        owner_count = sum(1 for member in filtered if member.role == TeamRole.OWNER)
        if owner_count == 0:
            raise ValueError("Team must retain at least one owner")

        updated = Team(
            team_id=team.team_id,
            name=team.name,
            created_at=team.created_at,
            created_by=team.created_by,
            members=filtered,
        )
        self.storage.save_team(_serialize_team(updated))
        return updated

    def list_teams(self, limit: int = 100) -> list[Team]:
        """List teams from storage."""
        rows = self.storage.list_teams(limit=limit)
        teams = [_deserialize_team(item) for item in rows if isinstance(item, dict)]
        return [item for item in teams if item is not None]

    def get_team(self, team_id: str) -> Team | None:
        """Load one team by id."""
        payload = self.storage.load_team(team_id)
        if not isinstance(payload, dict):
            return None
        return _deserialize_team(payload)


def _serialize_team(team: Team) -> dict[str, object]:
    return {
        "team_id": team.team_id,
        "name": team.name,
        "created_at": team.created_at,
        "created_by": team.created_by,
        "members": [
            {
                "user_id": member.user_id,
                "display_name": member.display_name,
                "role": member.role.value,
                "added_at": member.added_at,
                "added_by": member.added_by,
            }
            for member in team.members
        ],
    }


def _deserialize_team(payload: dict[str, object]) -> Team | None:
    team_id = str(payload.get("team_id") or "").strip()
    if not team_id:
        return None
    members_raw = payload.get("members", [])
    members: list[TeamMember] = []
    if isinstance(members_raw, list):
        for item in members_raw:
            if not isinstance(item, dict):
                continue
            try:
                role = TeamRole(str(item.get("role") or TeamRole.MEMBER.value))
            except ValueError:
                role = TeamRole.MEMBER
            members.append(
                TeamMember(
                    user_id=str(item.get("user_id") or ""),
                    display_name=str(item.get("display_name") or ""),
                    role=role,
                    added_at=str(item.get("added_at") or ""),
                    added_by=str(item.get("added_by") or ""),
                )
            )

    return Team(
        team_id=team_id,
        name=str(payload.get("name") or ""),
        created_at=str(payload.get("created_at") or ""),
        created_by=str(payload.get("created_by") or ""),
        members=members,
    )


def team_to_dict(team: Team) -> dict[str, object]:
    """Public serializer helper for command layer."""
    return asdict(team)


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()

