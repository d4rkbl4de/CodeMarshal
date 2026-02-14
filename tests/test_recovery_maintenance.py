"""Reliability tests for recovery backup/restore compatibility and incrementals."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import integrity.recovery.backup as backup_mod
import integrity.recovery.restore as restore_mod
from integrity.recovery._compat import compute_integrity_hash


class _Serializable:
    """Small helper object with deterministic to_dict output for tests."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def to_dict(self) -> dict[str, Any]:
        return dict(self._payload)


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def test_perform_backup_writes_snapshot_and_observations_alias(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(
        backup_mod,
        "collect_observations_snapshot",
        lambda: _Serializable({"files": {"a.py": {"size": 1}}}),
    )
    monkeypatch.setattr(
        backup_mod,
        "collect_investigation_state",
        lambda: _Serializable({"session_id": "abc"}),
    )
    monkeypatch.setattr(backup_mod, "collect_configuration", lambda: {"theme": "light"})
    monkeypatch.setattr(backup_mod, "audit_recovery", lambda *args, **kwargs: None)
    monkeypatch.setattr(backup_mod, "cleanup_old_backups", lambda *args, **kwargs: None)

    outcome = backup_mod.perform_backup(str(tmp_path / "backups"), backup_type="full")
    assert outcome.success is True
    assert outcome.backup_path is not None
    data = json.loads(outcome.backup_path.read_text(encoding="utf-8"))

    assert "snapshot" in data
    assert "observations" in data
    assert data["snapshot"] == data["observations"]
    assert data["metadata"]["system_version"] != "1.0.0"
    assert data["metadata"]["backup_format_version"] >= 2

    is_valid, error_msg, _ = restore_mod.validate_backup_file(outcome.backup_path)
    assert is_valid is True, error_msg


def test_validate_backup_file_accepts_legacy_observations_only(tmp_path) -> None:
    legacy_payload: dict[str, Any] = {
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "system_version": "2.0.0",
            "backup_format_version": 1,
            "backup_type": "full",
        },
        "observations": {"files": {"legacy.py": {"size": 3}}},
        "state": {"session_id": "legacy"},
        "config": {"key": "value"},
        "integrity_hashes": {},
    }

    # Legacy writer hash style: all keys except integrity_hashes.
    legacy_hash_payload = {
        key: value for key, value in legacy_payload.items() if key != "integrity_hashes"
    }
    legacy_payload["integrity_hash"] = hashlib.sha256(
        json.dumps(legacy_hash_payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()

    path = tmp_path / "legacy.json"
    _write_json(path, legacy_payload)

    is_valid, error_msg, normalized = restore_mod.validate_backup_file(path)
    assert is_valid is True, error_msg
    assert normalized is not None
    assert normalized["snapshot"] == legacy_payload["observations"]


def test_incremental_backup_records_parent_and_changed_components(
    tmp_path, monkeypatch
) -> None:
    backup_root = backup_mod.create_backup_directory(tmp_path / "backups")

    base_payload: dict[str, Any] = {
        "metadata": {
            "timestamp": (datetime.now(UTC) - timedelta(minutes=1)).isoformat(),
            "system_version": "2.1.0",
            "backup_format_version": 2,
            "backup_type": "full",
        },
        "snapshot": {"files": {"a.py": {"size": 1}}},
        "observations": {"files": {"a.py": {"size": 1}}},
        "state": {"counter": 1},
        "config": {"theme": "light"},
        "integrity_hashes": {},
    }
    base_payload["integrity_hash"] = compute_integrity_hash(base_payload)
    base_file = backup_root / "full" / "backup_base_full.json"
    _write_json(base_file, base_payload)

    monkeypatch.setattr(
        backup_mod,
        "collect_observations_snapshot",
        lambda: _Serializable({"files": {"a.py": {"size": 1}}}),
    )
    monkeypatch.setattr(
        backup_mod,
        "collect_investigation_state",
        lambda: _Serializable({"counter": 2}),
    )
    monkeypatch.setattr(backup_mod, "collect_configuration", lambda: {"theme": "light"})
    monkeypatch.setattr(backup_mod, "audit_recovery", lambda *args, **kwargs: None)
    monkeypatch.setattr(backup_mod, "cleanup_old_backups", lambda *args, **kwargs: None)

    outcome = backup_mod.perform_incremental_backup(
        backup_root, since_timestamp=datetime.now(UTC)
    )
    assert outcome.success is True
    assert outcome.backup_path is not None

    payload = json.loads(outcome.backup_path.read_text(encoding="utf-8"))
    assert payload["metadata"]["backup_type"] == "incremental"
    assert payload["metadata"]["parent_backup_path"] == str(base_file.resolve())
    assert "state" in payload["changed_components"]
    assert "snapshot" not in payload["changed_components"]

    is_valid, error_msg, _ = restore_mod.validate_backup_file(outcome.backup_path)
    assert is_valid is True, error_msg


def test_restore_materializes_incremental_chain(tmp_path, monkeypatch) -> None:
    base_file = tmp_path / "backups" / "full" / "backup_full.json"
    inc_file = tmp_path / "backups" / "incremental" / "backup_inc.json"

    base_payload: dict[str, Any] = {
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "system_version": "2.1.0",
            "backup_format_version": 2,
            "backup_type": "full",
        },
        "snapshot": {"files": {"a.py": {"size": 1}}},
        "observations": {"files": {"a.py": {"size": 1}}},
        "state": {"counter": 1},
        "config": {"theme": "light"},
    }
    base_payload["integrity_hash"] = compute_integrity_hash(base_payload)
    _write_json(base_file, base_payload)

    inc_payload: dict[str, Any] = {
        "metadata": {
            "timestamp": datetime.now(UTC).isoformat(),
            "system_version": "2.1.1",
            "backup_format_version": 2,
            "backup_type": "incremental",
            "parent_backup_path": str(base_file.resolve()),
        },
        "changed_components": ["state"],
        "state": {"counter": 2},
    }
    inc_payload["integrity_hash"] = compute_integrity_hash(inc_payload)
    _write_json(inc_file, inc_payload)

    captured: dict[str, Any] = {}

    class _Snapshot:
        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> dict[str, Any]:
            return payload

    class _State:
        @classmethod
        def from_dict(cls, payload: dict[str, Any]) -> dict[str, Any]:
            return payload

    monkeypatch.setattr(restore_mod, "Snapshot", _Snapshot)
    monkeypatch.setattr(restore_mod, "InvestigationState", _State)
    monkeypatch.setattr(restore_mod, "save_snapshot", lambda payload: captured.setdefault("snapshot", payload))
    monkeypatch.setattr(restore_mod, "set_current_state", lambda payload: captured.setdefault("state", payload))
    monkeypatch.setattr(restore_mod, "create_restoration_checkpoint", lambda _: None)
    monkeypatch.setattr(restore_mod, "audit_recovery", lambda *args, **kwargs: None)

    outcome = restore_mod.perform_restore(str(inc_file))
    assert outcome.success is True
    assert captured["snapshot"] == {"files": {"a.py": {"size": 1}}}
    assert captured["state"] == {"counter": 2}
