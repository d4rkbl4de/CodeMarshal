"""
End-to-end integration tests for full CodeMarshal workflows.
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

import pytest

from bridge.commands.backup import BackupCreateCommand, BackupRestoreCommand
from bridge.entry.cli import CodeMarshalCLI
from observations.eyes.export_sight import ExportSight
from observations.eyes.file_sight import FileSight
from observations.eyes.go_sight import GoSight
from observations.eyes.import_sight import ImportSight
from observations.eyes.java_sight import JavaSight
from observations.eyes.javascript_sight import JavaScriptSight
from patterns.loader import PatternLoader, PatternScanner
from storage.investigation_storage import InvestigationStorage


@contextmanager
def _working_directory(path: Path) -> Iterator[None]:
    previous = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)


def _create_mixed_language_project(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "web").mkdir(parents=True, exist_ok=True)
    (root / "java" / "src").mkdir(parents=True, exist_ok=True)
    (root / "go").mkdir(parents=True, exist_ok=True)

    (root / "app.py").write_text(
        "import os\nfrom utils import helper\n\n\ndef main():\n    return helper() + os.sep\n",
        encoding="utf-8",
    )
    (root / "utils.py").write_text(
        "def helper():\n    return 'ok'\n",
        encoding="utf-8",
    )
    (root / "web" / "app.js").write_text(
        "import { util } from './util.js';\nexport function run() { return util(); }\n",
        encoding="utf-8",
    )
    (root / "web" / "util.js").write_text(
        "export function util() { return 'js'; }\n",
        encoding="utf-8",
    )
    (root / "web" / "lib.ts").write_text(
        "import type { Config } from './types';\nexport const value = 1;\n",
        encoding="utf-8",
    )
    (root / "java" / "src" / "Main.java").write_text(
        "package demo;\nimport java.util.List;\npublic class Main {}\n",
        encoding="utf-8",
    )
    (root / "go" / "main.go").write_text(
        "package main\nimport (\n    \"fmt\"\n    \"os\"\n)\nfunc Run() { fmt.Println(os.Args) }\n",
        encoding="utf-8",
    )
    return root


def _collect_normalized_observations(project_root: Path) -> list[dict[str, Any]]:
    observations: list[dict[str, Any]] = []

    file_count = sum(1 for candidate in project_root.rglob("*") if candidate.is_file())
    file_result = FileSight().observe(project_root)
    observations.append(
        {
            "type": "file_sight",
            "file": str(project_root),
            "result": {
                "path": str(project_root),
                "file_count": file_count,
                "confidence": file_result.confidence,
            },
        }
    )

    def normalize_import_statement(statement: Any) -> dict[str, Any]:
        names = list(getattr(statement, "names", ()) or ())
        alias = getattr(statement, "alias", None)
        if alias:
            names.append(alias)
        return {"module": getattr(statement, "module", ""), "names": names}

    import_sight = ImportSight()
    export_sight = ExportSight()

    for py_file in sorted(project_root.rglob("*.py")):
        import_payload = import_sight.observe(py_file).raw_payload
        statements = [
            normalize_import_statement(statement)
            for statement in import_payload.statements
            if statement.module
        ]
        observations.append(
            {
                "type": "import_sight",
                "file": str(py_file),
                "statements": statements,
            }
        )

        export_payload = export_sight.observe(py_file).raw_payload
        exports = [{"name": definition.name} for definition in export_payload.public_definitions]
        observations.append(
            {
                "type": "export_sight",
                "file": str(py_file),
                "result": {"exports": exports},
            }
        )

    js_sight = JavaScriptSight()
    for pattern in ("*.js", "*.ts"):
        for script_file in sorted(project_root.rglob(pattern)):
            js_payload = js_sight.observe(script_file).raw_payload
            statements = [
                normalize_import_statement(statement)
                for statement in js_payload.imports
                if statement.module
            ]
            exports = [{"name": export.name} for export in js_payload.exports]
            observations.append(
                {
                    "type": "import_sight",
                    "file": str(script_file),
                    "statements": statements,
                }
            )
            observations.append(
                {
                    "type": "export_sight",
                    "file": str(script_file),
                    "result": {"exports": exports},
                }
            )

    java_sight = JavaSight()
    for java_file in sorted(project_root.rglob("*.java")):
        java_payload = java_sight.observe(java_file).raw_payload
        statements = [
            normalize_import_statement(statement)
            for statement in java_payload.imports
            if statement.module
        ]
        exports = [{"name": java_class.name} for java_class in java_payload.classes]
        observations.append(
            {
                "type": "import_sight",
                "file": str(java_file),
                "statements": statements,
            }
        )
        observations.append(
            {
                "type": "export_sight",
                "file": str(java_file),
                "result": {"exports": exports},
            }
        )

    go_sight = GoSight()
    for go_file in sorted(project_root.rglob("*.go")):
        go_payload = go_sight.observe(go_file).raw_payload
        statements = [
            normalize_import_statement(statement)
            for statement in go_payload.imports
            if statement.module
        ]
        exports = [{"name": export.name} for export in go_payload.exports]
        observations.append(
            {
                "type": "import_sight",
                "file": str(go_file),
                "statements": statements,
            }
        )
        observations.append(
            {
                "type": "export_sight",
                "file": str(go_file),
                "result": {"exports": exports},
            }
        )

    return observations


def _persist_session_data(
    storage: InvestigationStorage,
    project_root: Path,
    observations: list[dict[str, Any]],
    session_id: str,
) -> None:
    file_count = sum(1 for candidate in project_root.rglob("*") if candidate.is_file())
    observation_payload = {
        "id": "obs_e2e",
        "data": {
            "path": str(project_root),
            "file_count": file_count,
            "observations": observations,
        },
    }
    observation_id = storage.save_observation(observation_payload, session_id=session_id)

    session_payload = {
        "id": session_id,
        "path": str(project_root),
        "state": "complete",
        "created_at": datetime.now(UTC).isoformat(),
        "observation_ids": [observation_id],
        "question_ids": [],
        "pattern_ids": [],
    }
    storage.save_session(session_payload)


@pytest.mark.e2e
@pytest.mark.integration
class TestEndToEndWorkflow:
    def test_full_investigation_flow(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        project_root = _create_mixed_language_project(workspace / "repo")
        storage = InvestigationStorage(base_path=workspace / "storage", enable_backups=False)
        observations = _collect_normalized_observations(project_root)
        session_id = "e2e_session_full_flow"
        _persist_session_data(storage, project_root, observations, session_id)

        cli = CodeMarshalCLI()
        with _working_directory(workspace):
            session_data = cli._load_session_data(storage, session_id)
            assert session_data is not None
            assert session_data["id"] == session_id

            loaded_observations = cli._load_observations(storage, session_data)
            assert loaded_observations
            assert any(obs.get("type") == "import_sight" for obs in loaded_observations)
            assert any(obs.get("type") == "export_sight" for obs in loaded_observations)

            answer = cli._generate_answer(
                "Show import relationships for this codebase",
                "connections",
                loaded_observations,
            )
            assert isinstance(answer, str)
            assert "Import" in answer or "Dependency" in answer

            export_content = cli._generate_export_content(
                "json",
                session_data,
                loaded_observations,
                include_notes=False,
                include_patterns=False,
            )
            payload = json.loads(export_content)
            assert payload["investigation"]["id"] == session_id
            assert len(payload["observations"]) == len(loaded_observations)

    def test_session_persistence(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        project_root = _create_mixed_language_project(workspace / "repo")
        storage = InvestigationStorage(base_path=workspace / "storage", enable_backups=False)
        observations = _collect_normalized_observations(project_root)
        session_id = "e2e_session_persistence"
        _persist_session_data(storage, project_root, observations, session_id)

        cli = CodeMarshalCLI()
        with _working_directory(workspace):
            first_load = cli._load_session_data(storage, session_id)
            second_load = cli._load_session_data(storage, session_id)

            assert first_load is not None
            assert second_load is not None
            assert first_load["id"] == second_load["id"] == session_id
            assert first_load["observation_ids"] == second_load["observation_ids"]

            loaded_observations = cli._load_observations(storage, first_load)
            assert loaded_observations
            assert any(obs.get("file", "").endswith("app.py") for obs in loaded_observations)

    def test_constitutional_violation_detection(self, tmp_path: Path) -> None:
        project_root = tmp_path / "repo"
        project_root.mkdir(parents=True, exist_ok=True)
        (project_root / "bad_code.py").write_text(
            "password = 'secret123'\n",
            encoding="utf-8",
        )

        loader = PatternLoader()
        patterns = [
            pattern
            for pattern in loader.load_builtin_patterns("security")
            if pattern.id == "hardcoded_password"
        ]

        assert patterns

        scanner = PatternScanner(max_workers=1, context_lines=0)
        result = scanner.scan(project_root, patterns=patterns, glob="*.py", max_files=20)

        assert result.success
        assert any(match.pattern_id == "hardcoded_password" for match in result.matches)

    def test_backup_and_restore(self, tmp_path: Path) -> None:
        workspace = tmp_path / "workspace"
        project_root = _create_mixed_language_project(workspace / "repo")
        storage = InvestigationStorage(base_path=workspace / "storage", enable_backups=False)
        observations = _collect_normalized_observations(project_root)
        session_id = "e2e_session_backup"
        _persist_session_data(storage, project_root, observations, session_id)

        backup_dir = workspace / "backups"
        create_command = BackupCreateCommand(backup_dir=backup_dir)
        create_result = create_command.execute(source_path=workspace / "storage")

        assert create_result.success
        assert create_result.backup_id

        original_session_file = workspace / "storage" / "sessions" / f"{session_id}.session.json"
        assert original_session_file.exists()
        original_session_file.unlink()
        assert not original_session_file.exists()

        restore_target = workspace / "restored_storage"
        restore_command = BackupRestoreCommand(backup_dir=backup_dir)
        restore_result = restore_command.execute(
            backup_id=create_result.backup_id,
            target_path=restore_target,
            dry_run=False,
        )

        assert restore_result.success
        restored_session_file = restore_target / "sessions" / f"{session_id}.session.json"
        assert restored_session_file.exists()
        restored_data = json.loads(restored_session_file.read_text(encoding="utf-8"))
        assert restored_data["id"] == session_id
