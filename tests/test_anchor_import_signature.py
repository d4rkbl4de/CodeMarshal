"""Tests for import-signature anchor generation."""

from __future__ import annotations

from observations.record.anchors import ImportSignatureAnchorGenerator


def test_import_signature_ignores_non_import_text_changes(tmp_path) -> None:
    source_file = tmp_path / "module.py"
    source_file.write_text(
        "import os\nfrom pathlib import Path\n\nx = 1  # note\n",
        encoding="utf-8",
    )

    generator = ImportSignatureAnchorGenerator()
    first = generator.generate(source_file)

    source_file.write_text(
        "\n# changed comments and spacing\nimport os\nfrom pathlib import Path\n\nx = 999\n",
        encoding="utf-8",
    )
    second = generator.generate(source_file)

    assert first.content_fingerprint == second.content_fingerprint


def test_import_signature_changes_when_imports_change(tmp_path) -> None:
    source_file = tmp_path / "module.py"
    source_file.write_text("import os\n", encoding="utf-8")
    generator = ImportSignatureAnchorGenerator()
    first = generator.generate(source_file)

    source_file.write_text("import os\nimport json\n", encoding="utf-8")
    second = generator.generate(source_file)

    assert first.content_fingerprint != second.content_fingerprint

