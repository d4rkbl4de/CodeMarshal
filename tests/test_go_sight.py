"""
Tests for GoSight import/package/export detection.
"""

from pathlib import Path
import tempfile

from observations.eyes.go_sight import GoSight


def test_go_sight_imports_exports() -> None:
    content = """
package sample

import (
    "fmt"
    alias "os"
)

import "strings"

func DoThing() {}
func (s *Service) Run() {}
type ExportedType struct {}
const ExportedConst = 1
var ExportedVar = 2
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "sample.go"
        file_path.write_text(content, encoding="utf-8")

        sight = GoSight()
        result = sight.observe(file_path)
        payload = result.raw_payload

        assert payload is not None
        assert payload.package == "sample"

        modules = {stmt.module for stmt in payload.imports}
        assert "fmt" in modules
        assert "os" in modules
        assert "strings" in modules

        export_names = {exp.name for exp in payload.exports}
        assert "DoThing" in export_names
        assert "Run" in export_names
        assert "ExportedType" in export_names
        assert "ExportedConst" in export_names
        assert "ExportedVar" in export_names
