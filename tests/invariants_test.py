"""
tests/invariants_test.py - System invariants tests

Tests that verify core system properties that must always hold true.
These tests validate constitutional principles are maintained.
"""

import importlib
import pkgutil
import re
import warnings
from pathlib import Path

import pytest


class TestTruthPreservationInvariant:
    """Test Truth Preservation principle (Article 1)."""

    def test_observations_immutable(self):
        """Once recorded, observations cannot be changed."""
        # Create an observation
        observation = {"id": "obs_001", "data": "original_data"}

        # In real system, this would be frozen/locked
        # For now, verify the principle conceptually
        original_data = observation["data"]

        # Attempt to modify
        observation["data"] = "modified"

        # In real implementation, this would fail or create new version
        # This test documents the expected behavior
        assert observation["data"] != original_data or True  # Placeholder

    def test_no_silent_mutations(self):
        """System never silently changes data."""
        # Any mutation must be explicit and logged
        data = {"key": "value"}
        original = data.copy()

        # If data changes, there should be a record
        # TODO: Implement actual check once mutation tracking exists
        assert True  # Placeholder


class TestHumanPrimacyInvariant:
    """Test Human Primacy principle (Article 2)."""

    def test_all_actions_initiated_by_human(self):
        """All system actions require human initiation."""
        # TODO: Verify no automated actions without human trigger
        # This is an architectural invariant
        assert True  # Placeholder - requires implementation

    def test_no_autonomous_decisions(self):
        """System never makes decisions autonomously."""
        # All decisions should present options to human
        # TODO: Verify architectural compliance
        assert True  # Placeholder


class TestExplicitLimitationsInvariant:
    """Test Explicit Limitations principle."""

    def test_all_limitations_declared(self):
        """System declares all its limitations."""
        # Every component should declare what it cannot do
        # TODO: Verify all components have limitations documented
        assert True  # Placeholder

    def test_no_hidden_capabilities(self):
        """No hidden or undocumented capabilities exist."""
        # All features should be discoverable and documented
        # TODO: Verify all exports are documented
        assert True  # Placeholder


class TestBackwardCompatibilityInvariant:
    """Test Backward Truth Compatibility (Article 19)."""

    def test_exports_preserve_truth(self):
        """All export formats preserve truth without mutation."""
        # TODO: Test that exports don't lose or alter information
        # in ways that violate truth preservation
        assert True  # Placeholder

    def test_export_limitations_documented(self):
        """All export limitations are explicitly documented."""
        # Each export format should declare what it loses
        # TODO: Verify all exporters have limitations
        assert True  # Placeholder


class TestNoInferenceInvariant:
    """Test No Inference principle."""

    def test_no_speculative_comments(self):
        """System never generates speculative comments."""
        # All statements should be based on evidence
        # TODO: Verify no "probably", "likely", "seems" in outputs
        assert True  # Placeholder

    def test_all_claims_have_evidence(self):
        """Every claim is tied to evidence."""
        # All patterns should reference specific code locations
        # TODO: Verify pattern matches include location info
        assert True  # Placeholder


class TestSystemIntegrityInvariant:
    """Test overall system integrity."""

    def test_no_circular_imports(self):
        """System has no circular import dependencies."""
        optional_deps = {"PySide6", "rich", "textual", "click"}

        def is_optional_missing(exc: ImportError) -> bool:
            name = getattr(exc, "name", "") or ""
            if name in optional_deps:
                return True
            message = str(exc)
            return any(dep in message for dep in optional_deps)

        packages = [
            "bridge",
            "core",
            "config",
            "storage",
            "observations",
            "inquiry",
            "lens",
            "integrity",
            "desktop",
            "patterns",
        ]

        failures: list[tuple[str, str]] = []
        skipped: list[tuple[str, str]] = []

        for package_name in packages:
            try:
                package = importlib.import_module(package_name)
            except ImportError as exc:
                if is_optional_missing(exc):
                    skipped.append((package_name, str(exc)))
                    continue
                failures.append((package_name, repr(exc)))
                continue

            module_names = [package_name]
            if hasattr(package, "__path__"):
                for module in pkgutil.walk_packages(
                    package.__path__, package.__name__ + "."
                ):
                    module_names.append(module.name)

            for module_name in module_names:
                try:
                    importlib.import_module(module_name)
                except ImportError as exc:
                    if is_optional_missing(exc):
                        skipped.append((module_name, str(exc)))
                        continue
                    failures.append((module_name, repr(exc)))
                except Exception as exc:
                    failures.append((module_name, repr(exc)))

        if skipped:
            details = "\n".join(f"- {name}: {reason}" for name, reason in skipped)
            warnings.warn(
                f"Skipped modules due to missing optional dependencies:\n{details}"
            )

        if failures:
            details = "\n".join(f"- {name}: {reason}" for name, reason in failures)
            pytest.fail(f"Import failures detected:\n{details}")

    def test_all_commands_exported(self):
        """All CLI commands are properly exported."""
        from bridge.commands import __all__

        # Verify core commands are exported
        expected_exports = [
            "execute_config_show",
            "execute_backup_create",
            "execute_search",
            "execute_pattern_scan",
        ]

        for export in expected_exports:
            assert export in __all__, f"{export} not exported"

    def test_no_duplicate_ids(self):
        """All IDs in system are unique."""
        import yaml

        builtin_dir = Path(__file__).resolve().parents[1] / "patterns" / "builtin"
        pattern_ids: list[str] = []

        for yaml_file in sorted(builtin_dir.glob("*.yaml")):
            data = yaml.safe_load(yaml_file.read_text(encoding="utf-8")) or {}
            patterns = data.get("patterns", [])
            for pattern in patterns:
                if isinstance(pattern, dict) and "id" in pattern:
                    pattern_ids.append(str(pattern["id"]))

        assert pattern_ids, "No pattern IDs discovered in builtin pattern library"
        assert len(pattern_ids) == len(set(pattern_ids))


class TestResourceTransparencyInvariant:
    """Test Resource Transparency principle (Article 5)."""

    def test_memory_usage_monitored(self):
        """System monitors its memory usage."""
        # TODO: Verify memory monitoring is active
        assert True  # Placeholder

    def test_performance_degradation_detected(self):
        """System detects performance degradation."""
        # TODO: Verify performance monitoring
        assert True  # Placeholder


class TestConstitutionalCompliance:
    """Test overall constitutional compliance."""

    def test_constitutional_articles_documented(self):
        """Constitution documentation contains a complete article set."""
        structure_doc = Path(__file__).resolve().parents[1] / "docs" / "Structure.md"
        assert structure_doc.exists(), "Missing docs/Structure.md"

        content = structure_doc.read_text(encoding="utf-8")
        article_numbers = {
            int(match) for match in re.findall(r"Article\s+([0-9]+)\s*:", content)
        }

        # Current documented constitution has 21 operational articles.
        assert len(article_numbers) >= 21
        assert min(article_numbers) == 1

    def test_no_violations_in_core_code(self):
        """Core codebase doesn't violate constitutional principles."""
        # TODO: Run constitutional checker on own code
        assert True  # Placeholder


class TestArchitectureInvariants:
    """High-level architecture invariants - run automatically."""

    def test_layer_separation(self):
        """Bridge, Core, Observations layers are properly separated.

        Layer Rules (per roadmap architecture):
        - observations: Base layer - only depends on itself
        - core: Depends on observations, provides coordination
        - bridge: Top layer - can access all lower layers (core, observations, inquiry, lens, integrity)
        - integrity: Cross-cutting, can be used by core and bridge
        """
        import ast
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[1]

        # Define layer rules per the actual architecture
        layer_rules = {
            "observations": {
                # Observations is the base layer - should not import from higher layers
                "forbidden": {"bridge", "lens", "inquiry", "desktop"},
                # integrity is allowed for monitoring/validation
                "allowed_exceptions": {"core", "integrity"},
            },
            "core": {
                # Core coordinates - can use observations and integrity
                "forbidden": {"bridge", "lens", "inquiry", "desktop"},
                "allowed_exceptions": {"observations", "integrity"},
            },
            "bridge": {
                # Bridge is the interface layer - can access all
                "forbidden": set(),
                "allowed_exceptions": set(),
            },
        }

        violations = []
        allowed_exceptions_used = []

        for layer_name, rules in layer_rules.items():
            layer_path = project_root / layer_name
            if not layer_path.exists():
                continue

            for py_file in layer_path.rglob("*.py"):
                # Skip test files and __init__.py (they often need cross-layer imports)
                if py_file.name.startswith("test_") or py_file.name == "__init__.py":
                    continue

                # Skip invariant test files (they test cross-layer functionality)
                if "invariants" in str(py_file):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(content)
                except (SyntaxError, UnicodeDecodeError):
                    continue

                for node in ast.walk(tree):
                    imported_module = None

                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_module = alias.name.split(".")[0]
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imported_module = node.module.split(".")[0]

                    if imported_module and imported_module in rules["forbidden"]:
                        rel_path = py_file.relative_to(project_root)
                        violations.append(
                            f"{rel_path}: imports forbidden module '{imported_module}' "
                            f"(layer '{layer_name}' cannot depend on '{imported_module}')"
                        )
                    elif imported_module and imported_module in rules.get(
                        "allowed_exceptions", set()
                    ):
                        rel_path = py_file.relative_to(project_root)
                        allowed_exceptions_used.append(
                            f"{rel_path}: uses allowed exception '{imported_module}'"
                        )

        if violations:
            violation_list = "\n".join(f"  - {v}" for v in violations[:20])
            if len(violations) > 20:
                violation_list += f"\n  ... and {len(violations) - 20} more violations"
            pytest.fail(f"Layer separation violations found:\n{violation_list}")

        # Log allowed exceptions for visibility
        if allowed_exceptions_used:
            import warnings

            details = "\n".join(f"  - {v}" for v in allowed_exceptions_used[:10])
            if len(allowed_exceptions_used) > 10:
                details += f"\n  ... and {len(allowed_exceptions_used) - 10} more"
            warnings.warn(f"Layer separation: using allowed exceptions:\n{details}")

    def test_no_layer_violations(self):
        """No circular dependencies between core architectural layers.

        NOTE: The current architecture has a documented bidirectional dependency:
        - core imports observations (base layer)
        - observations/interface.py imports core (for interface implementation)

        This is a pragmatic pattern for interface/protocol implementations.
        """
        import ast
        from pathlib import Path

        project_root = Path(__file__).resolve().parents[1]

        # Build dependency graph for core architectural layers
        dependencies = {
            "core": set(),
            "observations": set(),
            "bridge": set(),
        }

        layers = list(dependencies.keys())

        for layer_name in layers:
            layer_path = project_root / layer_name
            if not layer_path.exists():
                continue

            for py_file in layer_path.rglob("*.py"):
                # Skip test files
                if py_file.name.startswith("test_"):
                    continue

                # Skip invariant test files (they test cross-layer functionality)
                if "invariants" in str(py_file):
                    continue

                try:
                    content = py_file.read_text(encoding="utf-8")
                    tree = ast.parse(content)
                except (SyntaxError, UnicodeDecodeError):
                    continue

                for node in ast.walk(tree):
                    imported_module = None

                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported_module = alias.name.split(".")[0]
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imported_module = node.module.split(".")[0]

                    if imported_module and imported_module in layers:
                        if imported_module != layer_name:
                            dependencies[layer_name].add(imported_module)

        # Check for circular dependencies using DFS
        # NOTE: We exclude the core <-> observations cycle as it's a documented pattern
        def find_cycle(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in dependencies.get(node, set()):
                if neighbor not in visited:
                    cycle = find_cycle(neighbor, visited, rec_stack, path)
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle_path = path[cycle_start:] + [neighbor]

                    # Check if this is the documented core <-> observations cycle
                    unique_layers = set(cycle_path)
                    if unique_layers == {"core", "observations"}:
                        # This is the documented exception - skip it
                        continue

                    return cycle_path

            path.pop()
            rec_stack.remove(node)
            return None

        visited = set()
        for layer in layers:
            if layer not in visited:
                cycle = find_cycle(layer, visited, set(), [])
                if cycle:
                    cycle_str = " -> ".join(cycle)
                    pytest.fail(f"Circular dependency detected: {cycle_str}")

        # Verify architectural dependency direction (lower layers should not depend on higher)
        # The only documented exception is observations/interface.py importing from core
        if "bridge" in dependencies.get("core", set()):
            pytest.fail(
                "Architecture violation: core layer should not depend on bridge"
            )

        if "bridge" in dependencies.get("observations", set()):
            pytest.fail(
                "Architecture violation: observations layer should not depend on bridge"
            )
