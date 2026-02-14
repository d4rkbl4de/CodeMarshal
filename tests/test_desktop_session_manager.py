"""Tests for desktop SessionManager persistence behavior."""

from __future__ import annotations

from pathlib import Path

from desktop.core.session_manager import SessionManager


def test_recent_investigations_are_capped_to_ten(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")

    for index in range(15):
        manager.add_recent_investigation(
            {
                "id": f"session-{index}",
                "name": f"Session {index}",
                "path": f"/tmp/{index}",
            }
        )

    recent = manager.get_recent_investigations(limit=20)
    assert len(recent) == 10
    assert recent[0]["session_id"] == "session-14"
    assert recent[-1]["session_id"] == "session-5"


def test_recovery_state_round_trip(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")
    manager.save_recovery_state("abc123", "/tmp/project")

    recovery = manager.get_recovery_state()
    assert recovery is not None
    assert recovery["session_id"] == "abc123"
    assert recovery["path"] == "/tmp/project"

    manager.clear_recovery_state()
    assert manager.get_recovery_state() is None


def test_default_export_format_setting(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")
    assert manager.get_default_export_format() == "json"

    manager.set_default_export_format("markdown")
    assert manager.get_default_export_format() == "markdown"


def test_last_path_is_persisted(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")
    project_path = tmp_path / "workspace"
    project_path.mkdir()

    manager.set_last_path(project_path)
    assert manager.get_last_path() == str(Path(project_path).resolve())


def test_recent_paths_are_capped(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")
    for index in range(15):
        path = tmp_path / f"p{index}"
        path.mkdir(exist_ok=True)
        manager.add_recent_path(path)

    recent_paths = manager.get_recent_paths(limit=20)
    assert len(recent_paths) == 10
    assert recent_paths[0].endswith("p14")
    assert recent_paths[-1].endswith("p5")


def test_window_state_and_last_view_round_trip(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")
    manager.set_last_view("patterns")
    manager.set_window_geometry("aa55")
    manager.set_window_state("ff11")

    assert manager.get_last_view() == "patterns"
    assert manager.get_window_geometry() == "aa55"
    assert manager.get_window_state() == "ff11"


def test_auto_run_options_setting(tmp_path) -> None:
    manager = SessionManager(state_path=tmp_path / "gui_state.json")
    assert manager.get_auto_run_last_used_options() is False
    manager.set_auto_run_last_used_options(True)
    assert manager.get_auto_run_last_used_options() is True
