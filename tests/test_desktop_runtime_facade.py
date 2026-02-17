"""Tests for desktop runtime facade helper methods."""

from __future__ import annotations

from desktop.core.runtime_facade import RuntimeFacade
from collaboration.encryption import CRYPTO_AVAILABLE


def test_resolve_default_export_path_uses_extension(tmp_path) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    value = facade.resolve_default_export_path("abc123", "markdown")
    assert value.endswith("abc123.md")


def test_list_recent_paths_deduplicates(tmp_path, monkeypatch) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    monkeypatch.setattr(
        facade,
        "list_recent_investigations",
        lambda limit=10: [
            {"path": "/a", "id": "1"},
            {"path": "/b", "id": "2"},
            {"path": "/a", "id": "3"},
        ],
    )

    assert facade.list_recent_paths(limit=10) == ["/a", "/b"]


def test_get_or_create_active_session_reuses_matching_path(tmp_path, monkeypatch) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    target = tmp_path / "project"
    target.mkdir()

    monkeypatch.setattr(facade, "_ensure_runtime", lambda _: None)
    monkeypatch.setattr(
        facade,
        "list_recent_investigations",
        lambda limit=25: [{"session_id": "s-1", "path": str(target.resolve())}],
    )

    assert facade.get_or_create_active_session(target) == "s-1"


def test_get_or_create_active_session_creates_new(tmp_path, monkeypatch) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    target = tmp_path / "project_new"
    target.mkdir()

    monkeypatch.setattr(facade, "_ensure_runtime", lambda _: None)
    monkeypatch.setattr(facade, "list_recent_investigations", lambda limit=25: [])
    monkeypatch.setattr(facade, "_upsert_session_metadata", lambda metadata: "created-1")

    assert facade.get_or_create_active_session(target, intent="architecture_review") == "created-1"


def test_run_history_returns_recorded_events(tmp_path) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    facade._knowledge.record_event("session-knowledge", "query", question="where is config")

    result = facade.run_history(session_id="session-knowledge", limit=20)

    assert result["success"] is True
    assert result["count"] >= 1
    assert any(event["event_type"] == "query" for event in result["events"])


def test_run_graph_and_recommendations(tmp_path) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    facade._knowledge.record_event("session-kg", "observe", path=str(tmp_path))
    facade._knowledge.ingest_query("session-kg", "show modules", "structure")

    graph = facade.run_graph(session_id="session-kg", depth=2)
    recs = facade.run_recommendations(session_id="session-kg", refresh=True, limit=5)

    assert graph["success"] is True
    assert graph["summary"]["node_count"] >= 1
    assert recs["success"] is True
    assert recs["count"] >= 1


def test_run_pattern_marketplace_workflows(tmp_path) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")

    search = facade.run_pattern_search(query="password", limit=5)
    assert search["success"] is True
    assert search["total_count"] >= 1

    create = facade.run_pattern_create(
        template_id="security.keyword_assignment",
        values={"identifier": "sample_token"},
        dry_run=True,
    )
    assert create["success"] is True
    assert create["dry_run"] is True
    assert str(create["pattern_id"]).startswith("tpl_security.keyword_assignment")

    bundle_path = tmp_path / "hardcoded_password.cmpattern.yaml"
    share = facade.run_pattern_share(
        pattern_id="hardcoded_password",
        bundle_out=bundle_path,
    )
    assert share["success"] is True
    assert bundle_path.exists()


def test_run_team_collaboration_workflows(tmp_path) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")

    created = facade.run_team_create(
        name="Alpha Team",
        owner_user_id="owner_1",
        owner_name="Owner One",
    )
    assert created["success"] is True
    team_id = created["team"]["team_id"]

    added = facade.run_team_add(
        team_id=team_id,
        user_id="user_2",
        display_name="User Two",
        role="member",
        added_by="owner_1",
    )
    assert added["success"] is True
    assert any(member["user_id"] == "user_2" for member in added["team"]["members"])

    listed = facade.run_team_list(limit=10)
    assert listed["success"] is True
    assert listed["count"] >= 1


def test_run_share_workflow_requires_unlock(tmp_path) -> None:
    facade = RuntimeFacade(storage_root=tmp_path / "storage")
    try:
        facade.run_share_create(
            session_id="session_1",
            created_by="owner_1",
            targets=[
                {
                    "target_type": "team",
                    "target_id": "team_1",
                    "permission": "read",
                }
            ],
        )
    except ValueError as exc:
        assert "locked" in str(exc).lower()
    else:
        raise AssertionError("Expected lock error")


def test_run_unlock_and_share_workflow(tmp_path) -> None:
    if not CRYPTO_AVAILABLE:
        return
    facade = RuntimeFacade(storage_root=tmp_path / "storage")

    unlocked = facade.run_collaboration_unlock(
        workspace_id="default",
        passphrase="strong-passphrase",
        initialize=True,
    )
    assert unlocked["success"] is True

    created = facade.run_share_create(
        session_id="session_1",
        created_by="owner_1",
        targets=[
            {
                "target_type": "team",
                "target_id": "team_1",
                "permission": "read",
            }
        ],
        title="Review",
    )
    assert created["success"] is True
    share_id = created["share"]["share_id"]

    resolved = facade.run_share_resolve(
        share_id=share_id,
        accessor_id="team_1",
    )
    assert resolved["success"] is True
    assert resolved["payload"]["session_id"] == "session_1"
