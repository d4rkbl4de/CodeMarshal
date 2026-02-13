import json
from pathlib import Path

from storage.migration import migrate_storage


def test_migrate_storage_dry_run(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    (storage_root / "sessions").mkdir(parents=True)
    session_file = storage_root / "sessions" / "s1.session.json"
    session_file.write_text(json.dumps({"id": "s1"}), encoding="utf-8")

    result = migrate_storage(
        storage_root=storage_root, to_version="v2.1.0", dry_run=True, create_backup=False
    )

    assert result.success is True
    assert result.steps_attempted == 2


def test_migrate_storage_apply(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    (storage_root / "sessions").mkdir(parents=True)
    session_file = storage_root / "sessions" / "s1.session.json"
    session_file.write_text(json.dumps({"id": "s1"}), encoding="utf-8")

    result = migrate_storage(
        storage_root=storage_root, to_version="v2.1.0", dry_run=False, create_backup=False
    )

    assert result.success is True
    version_file = storage_root / "version.txt"
    assert version_file.exists()
    assert version_file.read_text(encoding="utf-8").strip() == "v2.1.0"

    migrated = json.loads(session_file.read_text(encoding="utf-8"))
    assert migrated["schema_version"] == "v2.1.0"
    assert migrated["storage_version"] == "2.1.0"
