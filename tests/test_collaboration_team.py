from pathlib import Path

from collaboration.team import TeamRole, TeamService


def test_team_create_add_list(tmp_path: Path) -> None:
    service = TeamService(storage_root=str(tmp_path / "storage"))
    team = service.create_team("Alpha Team", "owner_1", "Owner One")

    assert team.team_id.startswith("team_")
    assert team.name == "Alpha Team"
    assert len(team.members) == 1
    assert team.members[0].role == TeamRole.OWNER

    updated = service.add_member(
        team.team_id,
        "user_2",
        "User Two",
        TeamRole.MEMBER,
        "owner_1",
    )
    assert len(updated.members) == 2
    assert any(member.user_id == "user_2" for member in updated.members)

    teams = service.list_teams()
    assert len(teams) == 1
    assert teams[0].team_id == team.team_id


def test_remove_member_requires_owner(tmp_path: Path) -> None:
    service = TeamService(storage_root=str(tmp_path / "storage"))
    team = service.create_team("Beta Team", "owner_1", "Owner One")

    try:
        service.remove_member(team.team_id, "owner_1", "owner_1")
    except ValueError as exc:
        assert "at least one owner" in str(exc).lower()
    else:
        raise AssertionError("Expected owner-preservation error")

