"""Tests for desktop runtime facade helper methods."""

from __future__ import annotations

from desktop.core.runtime_facade import RuntimeFacade


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

