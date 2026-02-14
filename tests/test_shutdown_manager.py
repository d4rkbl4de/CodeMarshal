"""Tests for shutdown manager reliability integrations."""

from __future__ import annotations

from pathlib import Path

from core.context import RuntimeContext
from core.shutdown import ShutdownManager


class _Serializable:
    def __init__(self, payload):
        self._payload = payload

    def to_dict(self):
        return dict(self._payload)


def _make_context(tmp_path: Path) -> RuntimeContext:
    return RuntimeContext(
        investigation_root=tmp_path,
        constitution_hash="a" * 64,
        code_version_hash="b" * 64,
        execution_mode="CLI",
    )


def test_flush_pending_writes_uses_storage_atomic(tmp_path, monkeypatch) -> None:
    manager = ShutdownManager(_make_context(tmp_path))

    monkeypatch.setattr("storage.atomic.flush_pending_writes", lambda: True)
    assert manager._flush_pending_writes() is True

    monkeypatch.setattr("storage.atomic.flush_pending_writes", lambda: False)
    assert manager._flush_pending_writes() is False


def test_run_corruption_checks_detects_corruption(tmp_path, monkeypatch) -> None:
    manager = ShutdownManager(_make_context(tmp_path))

    monkeypatch.setattr(
        "observations.record.snapshot.load_snapshot",
        lambda: _Serializable({"groups": []}),
    )
    monkeypatch.setattr("storage.corruption.detect_corruption", lambda *_: None)
    assert manager._run_corruption_checks() is True

    monkeypatch.setattr(
        "storage.corruption.detect_corruption",
        lambda *_: {"corruption_type": "json_parse_error"},
    )
    assert manager._run_corruption_checks() is False


def test_save_session_state_writes_file(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    manager = ShutdownManager(_make_context(tmp_path))
    monkeypatch.setattr(
        "core.state.get_current_state",
        lambda: _Serializable({"status": "ok", "session": "123"}),
    )

    assert manager._save_session_state() is True
    target = (
        tmp_path / ".codemarshal" / "session_state" / f"{manager._context.session_id_str}.json"
    )
    assert target.exists()

