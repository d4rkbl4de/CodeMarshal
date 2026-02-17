"""
Tests for JavaSight import/class detection.
"""

from pathlib import Path

from observations.eyes.java_sight import JavaSight


def test_java_sight_imports_classes(tmp_path: Path) -> None:
    content = """
package com.example.demo;

import java.util.List;
import static java.util.Collections.*;

public class Foo {}
interface Bar {}
enum Baz { ONE }
"""

    file_path = tmp_path / "Sample.java"
    file_path.write_text(content, encoding="utf-8")

    sight = JavaSight()
    result = sight.observe(file_path)
    payload = result.raw_payload

    assert payload is not None
    assert payload.package == "com.example.demo"

    modules = {stmt.module for stmt in payload.imports}
    assert "java.util.List" in modules
    assert "java.util.Collections.*" in modules

    class_names = {cls.name for cls in payload.classes}
    assert "Foo" in class_names
    assert "Bar" in class_names
    assert "Baz" in class_names
