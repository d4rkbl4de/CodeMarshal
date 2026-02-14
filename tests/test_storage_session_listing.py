"""Tests for session listing helpers in InvestigationStorage."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from storage.investigation_storage import InvestigationStorage


def test_list_sessions_orders_by_latest_timestamp(tmp_path) -> None:
    storage = InvestigationStorage(base_path=tmp_path)

    older = datetime.now(UTC) - timedelta(days=1)
    newer = datetime.now(UTC)

    storage.save_session(
        {
            "id": "session-old",
            "name": "Old Session",
            "modified_at": older.isoformat(),
        }
    )
    storage.save_session(
        {
            "id": "session-new",
            "name": "New Session",
            "modified_at": newer.isoformat(),
        }
    )

    sessions = storage.list_sessions(limit=10)
    assert len(sessions) == 2
    assert sessions[0]["id"] == "session-new"
    assert sessions[1]["id"] == "session-old"


def test_load_session_metadata_returns_none_when_missing(tmp_path) -> None:
    storage = InvestigationStorage(base_path=tmp_path)
    assert storage.load_session_metadata("missing") is None


def test_delete_session_metadata_removes_file(tmp_path) -> None:
    storage = InvestigationStorage(base_path=tmp_path)
    storage.save_session({"id": "session-delete"})

    assert storage.delete_session_metadata("session-delete") is True
    assert storage.load_session_metadata("session-delete") is None
    assert storage.delete_session_metadata("session-delete") is False

