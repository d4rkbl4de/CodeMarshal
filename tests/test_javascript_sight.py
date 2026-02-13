"""
Tests for JavaScriptSight import/export detection.
"""

from pathlib import Path
import tempfile

from observations.eyes.javascript_sight import JavaScriptSight


def test_javascript_sight_imports_exports() -> None:
    content = """
import fs from "fs";
import { readFile, writeFile as write } from "fs-extra";
import * as path from "path";
import "reflect-metadata";
const axios = require("axios");
const { join } = require("path");
import("dynamic-module");

export const foo = 1;
export function bar() {}
export default class Baz {}
export { foo as fooAlias, bar };
export * from "other";
module.exports = function() {};
exports.baz = 1;
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = Path(tmpdir) / "sample.js"
        file_path.write_text(content, encoding="utf-8")

        sight = JavaScriptSight()
        result = sight.observe(file_path)
        payload = result.raw_payload

        assert payload is not None
        modules = {stmt.module for stmt in payload.imports}
        assert "fs" in modules
        assert "fs-extra" in modules
        assert "path" in modules
        assert "reflect-metadata" in modules
        assert "axios" in modules
        assert "dynamic-module" in modules

        export_names = {exp.name for exp in payload.exports}
        assert "foo" in export_names
        assert "bar" in export_names
        assert "Baz" in export_names
        assert "fooAlias" in export_names
        assert "default" in export_names
        assert "baz" in export_names
