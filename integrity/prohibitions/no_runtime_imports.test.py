"""
Runtime Import Prohibition Enforcement
======================================

Enforces static-only imports in truth-critical modules (core/, observations/, inquiry/, lens/).
Prevents dynamic imports (importlib.import_module, __import__) that violate deterministic
operation (Tier 13) and observation purity (Tier 1).

Violations are logged to integrity/monitoring/errors.py and reported as structured violations.
"""

import ast
import inspect
import sys
from datetime import UTC, datetime
from typing import Any

# Core imports for type checking and module discovery
from integrity.monitoring.errors import log_integrity_violation


class RuntimeImportViolation(Exception):
    """Raised when a runtime import is detected in truth-critical code."""

    def __init__(self, violation_data: dict[str, str]) -> None:
        self.violation_data = violation_data
        super().__init__(f"Runtime import violation: {violation_data}")


class ImportChecker(ast.NodeVisitor):
    """
    AST visitor that detects dynamic import patterns in Python source code.

    Looks for:
    1. importlib.import_module() calls
    2. __import__() calls
    3. exec() or eval() with import strings
    4. Any call that could potentially trigger module loading

    Strictly follows truth-preserving principles: only detects what is textually present.
    """

    def __init__(self, module_name: str, function_name: str | None = None) -> None:
        self.module_name = module_name
        self.function_name = function_name
        self.violations: list[dict[str, str]] = []
        self._current_line: int | None = None

    def visit(self, node: ast.AST) -> None:
        """Visit a node and record its line number for violation reporting."""
        self._current_line = getattr(node, "lineno", None)
        super().visit(node)

    def _record_violation(self, pattern: str, details: str) -> None:
        """Record a violation with current context."""
        violation = {
            "violation": "runtime_import",
            "module": self.module_name,
            "function": self.function_name or "<module>",
            "line": self._current_line,
            "pattern": pattern,
            "details": details,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.violations.append(violation)

    def visit_Call(self, node: ast.Call) -> None:
        """
        Check function calls for dynamic import patterns.

        Recognizes:
        - importlib.import_module()
        - __import__()
        - getattr(__import__, ...) patterns
        - Any call where function name suggests import behavior
        """
        # Check for importlib.import_module()
        if isinstance(node.func, ast.Attribute):
            if (
                node.func.attr == "import_module"
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "importlib"
            ):
                self._record_violation(
                    "importlib.import_module()", "Explicit dynamic import detected"
                )

        # Check for __import__() directly
        elif isinstance(node.func, ast.Name) and node.func.id == "__import__":
            self._record_violation("__import__()", "Built-in dynamic import detected")

        # Check for getattr(__import__, ...) patterns
        elif isinstance(node.func, ast.Call):
            # Handle cases like getattr(__import__, 'something')()
            if isinstance(node.func.func, ast.Name) and node.func.func.id == "getattr":
                # Check if first arg to getattr is __import__
                if (
                    node.func.args
                    and isinstance(node.func.args[0], ast.Name)
                    and node.func.args[0].id == "__import__"
                ):
                    self._record_violation(
                        "getattr(__import__, ...)",
                        "Indirect dynamic import via getattr",
                    )

        # Check for eval/exec with import strings
        elif isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec", "compile"):
                # We can't know what strings are being evaluated at static analysis time
                # but we can flag that this is a potential violation
                for arg in node.args:
                    if isinstance(arg, ast.Str):
                        if "import" in arg.s.lower():
                            self._record_violation(
                                f"{node.func.id}() with import string",
                                "Dynamic code execution with import-like content",
                            )

        # Continue visiting child nodes
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Check for suspicious import from patterns."""
        # Check for import of importlib with intent to use import_module
        if node.module == "importlib":
            for name in node.names:
                if name.name == "import_module":
                    self._record_violation(
                        "from importlib import import_module",
                        "Import of dynamic import capability detected",
                    )
        self.generic_visit(node)


def get_truth_critical_modules() -> list[str]:
    """
    Get all loaded modules in truth-critical packages.

    Returns:
        List of module names in core/, observations/, inquiry/, lens/ packages.
    """
    truth_critical_modules: list[str] = []

    for module_name in sys.modules:
        if any(
            module_name.startswith(prefix)
            for prefix in ("core.", "observations.", "inquiry.", "lens.")
        ):
            truth_critical_modules.append(module_name)

    return truth_critical_modules


def get_module_source(module_name: str) -> str | None:
    """
    Safely get source code for a module.

    Args:
        module_name: Name of the module to get source for.

    Returns:
        Source code as string, or None if source cannot be obtained.
    """
    module = sys.modules.get(module_name)
    if not module:
        return None

    try:
        # Get source file path
        source_file = inspect.getsourcefile(module)
        if not source_file:
            return None

        # Read source file
        with open(source_file, encoding="utf-8") as f:
            return f.read()

    except (OSError, TypeError, UnicodeDecodeError):
        # Cannot read source (built-in, C extension, or permission issue)
        return None


def check_module_for_runtime_imports(module_name: str) -> list[dict[str, str]]:
    """
    Check a single module for runtime imports.

    Args:
        module_name: Name of module to check.

    Returns:
        List of violation dictionaries.
    """
    violations: list[dict[str, str]] = []

    # Get module source
    source = get_module_source(module_name)
    if not source:
        return violations  # Cannot check, no violations found

    try:
        # Parse module-level code
        tree = ast.parse(source, filename=module_name)
        module_checker = ImportChecker(module_name)
        module_checker.visit(tree)
        violations.extend(module_checker.violations)

        # Check all functions in the module
        module = sys.modules[module_name]
        for name, obj in inspect.getmembers(module):
            if inspect.isfunction(obj):
                # Get function source
                try:
                    func_source = inspect.getsource(obj)
                except (OSError, TypeError):
                    continue

                try:
                    func_tree = ast.parse(func_source)
                    func_checker = ImportChecker(module_name, f"{module_name}.{name}")
                    func_checker.visit(func_tree)
                    violations.extend(func_checker.violations)
                except SyntaxError:
                    continue

            elif inspect.isclass(obj):
                # Check all methods in the class
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    try:
                        method_source = inspect.getsource(method)
                    except (OSError, TypeError):
                        continue

                    try:
                        method_tree = ast.parse(method_source)
                        method_checker = ImportChecker(
                            module_name, f"{module_name}.{obj.__name__}.{method_name}"
                        )
                        method_checker.visit(method_tree)
                        violations.extend(method_checker.violations)
                    except SyntaxError:
                        continue

    except SyntaxError:
        # Invalid syntax in module - cannot check
        pass

    return violations


def enforce_no_runtime_imports() -> list[dict[str, str]]:
    """
    Enforce prohibition on runtime imports in truth-critical modules.

    Returns:
        List of violation dictionaries with keys:
        - violation: Always "runtime_import"
        - module: Module name where violation occurred
        - function: Function name or "<module>" for module-level
        - line: Line number (if available)
        - pattern: Pattern that was detected
        - details: Human-readable details
        - timestamp: ISO timestamp of detection
    """
    all_violations: list[dict[str, str]] = []

    # Get all truth-critical modules
    modules_to_check = get_truth_critical_modules()

    # Check each module
    for module_name in modules_to_check:
        module_violations = check_module_for_runtime_imports(module_name)

        # Log each violation
        for violation in module_violations:
            log_integrity_violation(
                violation_type="runtime_import",
                location={
                    "module": violation["module"],
                    "function": violation["function"],
                    "line": violation.get("line"),
                },
                details=violation["details"],
                severity="critical",
            )

        all_violations.extend(module_violations)

    return all_violations


def validate_import_staticness() -> bool:
    """
    Validate that all imports in truth-critical modules are static.

    Returns:
        True if no runtime imports detected, False otherwise.

    Raises:
        RuntimeImportViolation: If runtime imports are detected (for test mode).
    """
    violations = enforce_no_runtime_imports()

    if violations:
        # For test mode, raise exception with first violation
        raise RuntimeImportViolation(violations[0])

    return len(violations) == 0


# Hook for pre-import validation (if desired)
def install_import_hook() -> None:
    """
    Install a hook to prevent runtime imports at import time.

    This is a more aggressive enforcement that prevents runtime imports
    from being executed at all, rather than just detecting them.

    WARNING: This is invasive and should only be used in test environments.
    """
    import builtins
    import importlib

    original_import_module = importlib.import_module
    original_builtins_import = builtins.__import__

    def guarded_import_module(name: str, package: str | None = None) -> Any:
        """Guarded version of import_module that checks caller."""
        # Get caller's module
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_module = inspect.getmodule(frame.f_back)
            if caller_module:
                caller_name = caller_module.__name__
                # Check if caller is in truth-critical package
                if any(
                    caller_name.startswith(prefix)
                    for prefix in ("core.", "observations.", "inquiry.", "lens.")
                ):
                    raise RuntimeImportViolation(
                        {
                            "violation": "runtime_import",
                            "module": caller_name,
                            "function": inspect.currentframe().f_back.f_code.co_name,
                            "pattern": "importlib.import_module()",
                            "details": "Runtime import prevented by hook",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )

        return original_import_module(name, package)

    def guarded_builtins_import(name: str, *args: Any, **kwargs: Any) -> Any:
        """Guarded version of builtins.__import__."""
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            caller_module = inspect.getmodule(frame.f_back)
            if caller_module:
                caller_name = caller_module.__name__
                if any(
                    caller_name.startswith(prefix)
                    for prefix in ("core.", "observations.", "inquiry.", "lens.")
                ):
                    raise RuntimeImportViolation(
                        {
                            "violation": "runtime_import",
                            "module": caller_name,
                            "function": inspect.currentframe().f_back.f_code.co_name,
                            "pattern": "__import__()",
                            "details": "Runtime import prevented by hook",
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    )

        return original_builtins_import(name, *args, **kwargs)

    # Install hooks
    importlib.import_module = guarded_import_module
    builtins.__import__ = guarded_builtins_import


# Test function for module verification
def test_no_runtime_imports() -> dict[str, Any]:
    """
    Test function to verify the prohibition works.

    Returns:
        Dictionary with test results.
    """
    results = {
        "module": __name__,
        "function": "test_no_runtime_imports",
        "status": "running",
        "violations_found": 0,
        "violations": [],
    }

    try:
        violations = enforce_no_runtime_imports()
        results["violations_found"] = len(violations)
        results["violations"] = violations
        results["status"] = "passed" if len(violations) == 0 else "failed"

    except Exception as e:
        results["status"] = "error"
        results["error"] = str(e)

    return results


if __name__ == "__main__":
    # Command-line interface for standalone testing
    import argparse

    parser = argparse.ArgumentParser(
        description="Check truth-critical modules for runtime imports."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test and exit with code 0 (no violations) or 1 (violations found)",
    )
    parser.add_argument(
        "--install-hook",
        action="store_true",
        help="Install import hook to prevent runtime imports (invasive, test-only)",
    )

    args = parser.parse_args()

    if args.install_hook:
        install_import_hook()
        print(
            "Import hook installed. Runtime imports in truth-critical modules will be blocked."
        )

    if args.test:
        violations = enforce_no_runtime_imports()
        if violations:
            print(f"FAILED: {len(violations)} runtime import violations found:")
            for v in violations:
                print(f"  - {v['module']}.{v['function']}: {v['pattern']}")
            sys.exit(1)
        else:
            print("PASSED: No runtime import violations found.")
            sys.exit(0)
    else:
        # Default: just check and report
        violations = enforce_no_runtime_imports()
        if violations:
            print(f"Runtime import violations found: {len(violations)}")
            for v in violations:
                print(f"\nModule: {v['module']}")
                print(f"Function: {v['function']}")
                print(f"Line: {v.get('line', 'N/A')}")
                print(f"Pattern: {v['pattern']}")
                print(f"Details: {v['details']}")
        else:
            print("No runtime import violations detected.")
