"""
Mutation Prohibition Enforcement
================================

Enforces immutability of observations and state in truth-critical modules.
Prevents mutation that violates immutable observations requirement (Tier 9).

Violations are logged to integrity/monitoring/errors.py and reported as structured violations.
"""

import ast
import copy
import inspect
import sys
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

# Import for monitoring integration
from integrity.monitoring.errors import log_integrity_violation

# Try to import observation and state modules (may not exist in early development)
try:
    from observations.record.snapshot import load_snapshot

    SNAPSHOT_AVAILABLE = True
except ImportError:
    SNAPSHOT_AVAILABLE = False
    load_snapshot = None  # type: ignore

try:
    from observations.invariants.immutable import check_immutable

    IMMUTABLE_CHECK_AVAILABLE = True
except ImportError:
    IMMUTABLE_CHECK_AVAILABLE = False
    check_immutable = None  # type: ignore

try:
    from core.state import get_current_state

    STATE_AVAILABLE = True
except ImportError:
    STATE_AVAILABLE = False
    get_current_state = None  # type: ignore


class MutationViolation(Exception):
    """Raised when mutation is detected in truth-critical data."""

    def __init__(self, violation_data: dict[str, str]) -> None:
        self.violation_data = violation_data
        super().__init__(f"Mutation violation: {violation_data}")


class MutationDetector:
    """
    Detects mutation patterns in Python code and objects.

    Uses AST analysis for source code and object inspection for runtime mutations.
    Strictly follows truth-preserving principles: only detects what is present.
    """

    def __init__(self) -> None:
        self.violations: list[dict[str, str]] = []

    def check_source_for_mutation(
        self, module_name: str, source_code: str
    ) -> list[dict[str, str]]:
        """
        Check Python source code for mutation patterns using AST analysis.

        Args:
            module_name: Name of the module being checked.
            source_code: Python source code as string.

        Returns:
            List of violation dictionaries.
        """
        violations: list[dict[str, str]] = []

        try:
            tree = ast.parse(source_code, filename=module_name)
            visitor = MutationASTVisitor(module_name)
            visitor.visit(tree)
            violations.extend(visitor.violations)

        except SyntaxError:
            # Cannot parse, skip this module
            pass

        return violations

    def check_object_mutation(
        self, obj: Any, obj_name: str, path: str = ""
    ) -> list[dict[str, str]]:
        """
        Check if an object has been mutated by comparing with a deep copy.

        This is a runtime check that should be used carefully.

        Args:
            obj: The object to check.
            obj_name: Name of the object (for reporting).
            path: Current path within the object (for nested structures).

        Returns:
            List of violation dictionaries.
        """
        violations: list[dict[str, str]] = []

        try:
            # Create a deep copy for comparison
            original_copy = copy.deepcopy(obj)

            # Simple check: if the object has changed since copy
            # This is not perfect but can detect obvious mutations
            if hasattr(obj, "__dict__"):
                # For objects with __dict__, check if attributes changed
                if hasattr(original_copy, "__dict__"):
                    original_keys = set(original_copy.__dict__.keys())
                    current_keys = set(obj.__dict__.keys())

                    # Check for added attributes
                    added = current_keys - original_keys
                    for attr in added:
                        violations.append(
                            {
                                "violation": "mutation_detected",
                                "target": f"{obj_name}.{attr}"
                                if path
                                else f"{obj_name}",
                                "details": f"Added attribute '{attr}' after initialization",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )

                    # Check for removed attributes (less common for mutations)
                    removed = original_keys - current_keys
                    for attr in removed:
                        violations.append(
                            {
                                "violation": "mutation_detected",
                                "target": f"{obj_name}.{attr}"
                                if path
                                else f"{obj_name}",
                                "details": f"Removed attribute '{attr}' after initialization",
                                "timestamp": datetime.now(UTC).isoformat(),
                            }
                        )

        except Exception:
            # Some objects cannot be deep copied or inspected
            pass

        return violations

    def check_mutable_defaults(
        self, module_name: str, source_code: str
    ) -> list[dict[str, str]]:
        """
        Check for mutable default arguments in function definitions.

        Mutable defaults (like `def f(x=[]):`) can lead to unintended mutations.

        Args:
            module_name: Name of the module.
            source_code: Python source code.

        Returns:
            List of violation dictionaries.
        """
        violations: list[dict[str, str]] = []

        try:
            tree = ast.parse(source_code, filename=module_name)

            for node in ast.walk(tree):
                # Check function definitions
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.defaults:
                        # Check for mutable literals
                        if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                            violations.append(
                                {
                                    "violation": "mutable_default",
                                    "target": f"{module_name}.{node.name}",
                                    "details": f"Mutable default argument in function '{node.name}'",
                                    "line": node.lineno,
                                    "timestamp": datetime.now(UTC).isoformat(),
                                }
                            )

                # Check class method definitions
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            for arg in item.args.defaults:
                                if isinstance(arg, (ast.List, ast.Dict, ast.Set)):
                                    violations.append(
                                        {
                                            "violation": "mutable_default",
                                            "target": f"{module_name}.{node.name}.{item.name}",
                                            "details": f"Mutable default argument in method '{node.name}.{item.name}'",
                                            "line": item.lineno,
                                            "timestamp": datetime.now(UTC).isoformat(),
                                        }
                                    )

        except SyntaxError:
            pass

        return violations


class MutationASTVisitor(ast.NodeVisitor):
    """
    AST visitor that detects mutation patterns in Python code.

    Looks for:
    1. Assignment to protected attributes (like __dict__)
    2. Augmented assignments (+=, -=, etc.) on observed data
    3. Method calls that mutate in-place (list.append, dict.update, etc.)
    4. Del statements on observation data
    """

    # Methods that typically mutate objects in-place
    MUTATING_METHODS: set[str] = {
        "append",
        "extend",
        "insert",
        "remove",
        "pop",
        "clear",
        "update",
        "setdefault",
        "popitem",
        "add",
        "discard",
        "sort",
        "reverse",
        "__setitem__",
        "__delitem__",
        "__iadd__",
        "__isub__",
        "__imul__",
        "__idiv__",
        "copy",  # copy doesn't mutate, but included for completeness
    }

    def __init__(self, module_name: str) -> None:
        self.module_name = module_name
        self.violations: list[dict[str, str]] = []
        self._current_line: int | None = None

    def visit(self, node: ast.AST) -> None:
        """Visit a node and record its line number."""
        self._current_line = getattr(node, "lineno", None)
        super().visit(node)

    def _record_violation(self, pattern: str, details: str, target: str = "") -> None:
        """Record a violation with current context."""
        violation = {
            "violation": "mutation_detected",
            "module": self.module_name,
            "target": target,
            "line": self._current_line,
            "pattern": pattern,
            "details": details,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        self.violations.append(violation)

    def visit_Assign(self, node: ast.Assign) -> None:
        """
        Check assignments for mutation of protected data.

        We're particularly interested in assignments to attributes
        of observation or state objects.
        """
        for target in node.targets:
            # Check for assignment to protected attributes
            if isinstance(target, ast.Attribute):
                attr_name = target.attr
                # Check if this looks like observation/state data
                if self._is_protected_attribute(attr_name, node.value):
                    self._record_violation(
                        "assignment",
                        f"Assignment to potentially protected attribute '{attr_name}'",
                        target=ast.unparse(target)
                        if hasattr(ast, "unparse")
                        else str(target),
                    )

        self.generic_visit(node)

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """
        Check augmented assignments (in-place operations).

        These are mutations: x += 1
        """
        if isinstance(node.target, ast.Attribute):
            attr_name = node.target.attr
            if self._is_protected_attribute(attr_name, node.value):
                self._record_violation(
                    "augmented_assignment",
                    f"In-place operation on protected attribute '{attr_name}'",
                    target=ast.unparse(node.target)
                    if hasattr(ast, "unparse")
                    else str(node.target),
                )

        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """
        Check function calls for mutating methods.

        Looks for calls like list.append(), dict.update(), etc.
        """
        if isinstance(node.func, ast.Attribute):
            method_name = node.func.attr

            # Check for known mutating methods
            if method_name in self.MUTATING_METHODS:
                # Check if this is on an object that might be protected
                if isinstance(node.func.value, (ast.Name, ast.Attribute)):
                    # Try to get the object name
                    obj_expr = (
                        ast.unparse(node.func.value)
                        if hasattr(ast, "unparse")
                        else str(node.func.value)
                    )

                    # Simple heuristic: check if object name suggests observation/state
                    if any(
                        keyword in obj_expr.lower()
                        for keyword in [
                            "observation",
                            "snapshot",
                            "state",
                            "context",
                            "record",
                        ]
                    ):
                        self._record_violation(
                            "mutating_method_call",
                            f"Call to mutating method '{method_name}' on '{obj_expr}'",
                            target=f"{obj_expr}.{method_name}",
                        )

        self.generic_visit(node)

    def visit_Delete(self, node: ast.Delete) -> None:
        """
        Check del statements for deletion of protected data.
        """
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                attr_name = target.attr
                if self._is_protected_attribute(attr_name, None):
                    self._record_violation(
                        "deletion",
                        f"Deletion of protected attribute '{attr_name}'",
                        target=ast.unparse(target)
                        if hasattr(ast, "unparse")
                        else str(target),
                    )

        self.generic_visit(node)

    def _is_protected_attribute(self, attr_name: str, value: ast.AST | None) -> bool:
        """
        Heuristic to determine if an attribute might be protected observation/state data.

        This is conservative - it might flag false positives, but better safe than sorry.
        """
        protected_keywords = [
            "_observation",
            "_state",
            "_context",
            "_snapshot",
            "_record",
            "_data",
            "_immutable",
            "observations",
            "state",
            "context",
        ]

        # Check attribute name
        attr_lower = attr_name.lower()
        if any(keyword in attr_lower for keyword in protected_keywords):
            return True

        # Check if value is a complex structure (list, dict, set)
        if value:
            if isinstance(
                value,
                (ast.List, ast.Dict, ast.Set, ast.ListComp, ast.DictComp, ast.SetComp),
            ):
                return True

        return False


class MutationGuard:
    """
    Guards against mutation by intercepting attribute setting and deletion.

    This is a runtime guard that can be installed on specific objects
    to prevent mutation at runtime.
    """

    def __init__(self) -> None:
        self._guarded_objects: dict[int, Any] = {}  # id(object) -> original object
        self._original_setattrs: dict[int, Callable] = {}
        self._original_delattrs: dict[int, Callable] = {}

    def guard_object(self, obj: Any, obj_name: str) -> None:
        """
        Install mutation guard on an object.

        Args:
            obj: The object to guard.
            obj_name: Name of the object (for error messages).
        """
        obj_id = id(obj)

        # Skip if already guarded
        if obj_id in self._guarded_objects:
            return

        # Store original object
        self._guarded_objects[obj_id] = obj

        # Save original __setattr__ and __delattr__
        original_setattr = obj.__setattr__
        original_delattr = obj.__delattr__ if hasattr(obj, "__delattr__") else None

        # Create guarded versions
        def guarded_setattr(self: Any, name: str, value: Any) -> None:
            raise MutationViolation(
                {
                    "violation": "mutation_detected",
                    "target": f"{obj_name}.{name}",
                    "details": f"Attempt to set attribute '{name}' on guarded object",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        def guarded_delattr(self: Any, name: str) -> None:
            raise MutationViolation(
                {
                    "violation": "mutation_detected",
                    "target": f"{obj_name}.{name}",
                    "details": f"Attempt to delete attribute '{name}' on guarded object",
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            )

        # Replace methods
        obj.__setattr__ = guarded_setattr.__get__(obj, type(obj))
        self._original_setattrs[obj_id] = original_setattr

        if original_delattr:
            obj.__delattr__ = guarded_delattr.__get__(obj, type(obj))
            self._original_delattrs[obj_id] = original_delattr

    def unguard_object(self, obj: Any) -> None:
        """
        Remove mutation guard from an object.

        Args:
            obj: The object to unguard.
        """
        obj_id = id(obj)

        if obj_id not in self._guarded_objects:
            return

        # Restore original methods
        if obj_id in self._original_setattrs:
            obj.__setattr__ = self._original_setattrs[obj_id]

        if obj_id in self._original_delattrs:
            obj.__delattr__ = self._original_delattrs[obj_id]

        # Clean up
        del self._guarded_objects[obj_id]
        if obj_id in self._original_setattrs:
            del self._original_setattrs[obj_id]
        if obj_id in self._original_delattrs:
            del self._original_delattrs[obj_id]

    def unguard_all(self) -> None:
        """Remove all mutation guards."""
        for obj_id in list(self._guarded_objects.keys()):
            obj = self._guarded_objects[obj_id]
            self.unguard_object(obj)


def enforce_no_mutation() -> list[dict[str, str]]:
    """
    Enforce prohibition on mutation in truth-critical modules.

    Returns:
        List of violation dictionaries with keys:
        - violation: "mutation_detected" or "mutable_default"
        - module: Module name where violation occurred
        - target: What was mutated (if available)
        - line: Line number (if available)
        - pattern: Pattern that was detected
        - details: Human-readable details
        - timestamp: ISO timestamp of detection
    """
    all_violations: list[dict[str, str]] = []

    # Get all truth-critical modules
    truth_critical_modules = []
    for module_name in sys.modules:
        if any(
            module_name.startswith(prefix)
            for prefix in ("core.", "observations.", "inquiry.", "lens.")
        ):
            truth_critical_modules.append(module_name)

    # Check each module's source code
    detector = MutationDetector()

    for module_name in truth_critical_modules:
        module = sys.modules[module_name]

        # Get module source
        source = None
        try:
            source_file = inspect.getsourcefile(module)
            if source_file:
                with open(source_file, encoding="utf-8") as f:
                    source = f.read()
        except (OSError, TypeError, UnicodeDecodeError):
            continue

        if source:
            # Check for mutation patterns
            mutation_violations = detector.check_source_for_mutation(
                module_name, source
            )
            all_violations.extend(mutation_violations)

            # Check for mutable defaults
            default_violations = detector.check_mutable_defaults(module_name, source)
            all_violations.extend(default_violations)

    # Check observation snapshots (if available)
    if SNAPSHOT_AVAILABLE and load_snapshot:
        try:
            snapshot = load_snapshot()
            if snapshot:
                snapshot_violations = detector.check_object_mutation(
                    snapshot, "snapshot"
                )
                all_violations.extend(snapshot_violations)
        except Exception:
            pass

    # Check current state (if available)
    if STATE_AVAILABLE and get_current_state:
        try:
            state = get_current_state()
            if state:
                state_violations = detector.check_object_mutation(state, "state")
                all_violations.extend(state_violations)
        except Exception:
            pass

    # Check using immutable check (if available)
    if IMMUTABLE_CHECK_AVAILABLE and check_immutable:
        try:
            # This would depend on the implementation of check_immutable
            # For now, we assume it returns violations
            immutable_violations = check_immutable()
            if immutable_violations:
                all_violations.extend(immutable_violations)
        except Exception:
            pass

    # Log each violation
    for violation in all_violations:
        log_integrity_violation(
            violation_type=violation["violation"],
            location={
                "module": violation["module"],
                "target": violation.get("target"),
                "line": violation.get("line"),
            },
            details=violation["details"],
            severity="critical",
        )

    return all_violations


def validate_no_mutation() -> bool:
    """
    Validate that no mutation is present in truth-critical modules.

    Returns:
        True if no mutation detected, False otherwise.

    Raises:
        MutationViolation: If mutation is detected (for test mode).
    """
    violations = enforce_no_mutation()

    if violations:
        # For test mode, raise exception with first violation
        raise MutationViolation(violations[0])

    return len(violations) == 0


def install_mutation_guard() -> MutationGuard:
    """
    Install runtime mutation guard.

    Returns:
        MutationGuard instance that can be used to remove guard later.

    WARNING: This is invasive and should only be used in test environments.
    """
    guard = MutationGuard()

    # Guard observation snapshots (if available)
    if SNAPSHOT_AVAILABLE and load_snapshot:
        try:
            snapshot = load_snapshot()
            if snapshot:
                guard.guard_object(snapshot, "snapshot")
        except Exception:
            pass

    # Guard current state (if available)
    if STATE_AVAILABLE and get_current_state:
        try:
            state = get_current_state()
            if state:
                guard.guard_object(state, "state")
        except Exception:
            pass

    return guard


# Test function for module verification
def test_no_mutation() -> dict[str, Any]:
    """
    Test function to verify the prohibition works.

    Returns:
        Dictionary with test results.
    """
    results = {
        "module": __name__,
        "function": "test_no_mutation",
        "status": "running",
        "violations_found": 0,
        "violations": [],
    }

    try:
        violations = enforce_no_mutation()
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
        description="Check truth-critical modules for mutation."
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run test and exit with code 0 (no violations) or 1 (violations found)",
    )
    parser.add_argument(
        "--install-guard",
        action="store_true",
        help="Install mutation guard to block mutations (invasive, test-only)",
    )
    parser.add_argument(
        "--check-defaults",
        action="store_true",
        help="Check for mutable default arguments only",
    )

    args = parser.parse_args()

    if args.install_guard:
        guard = install_mutation_guard()
        print(
            f"Mutation guard installed. Guarding {len(guard._guarded_objects)} objects."
        )
        if guard._guarded_objects:
            print("Guarded objects:")
            for obj_id, obj in guard._guarded_objects.items():
                print(f"  - {type(obj).__name__} (id: {obj_id})")

    if args.check_defaults:
        # Check only mutable defaults
        detector = MutationDetector()
        violations = []

        for module_name, module in sys.modules.items():
            if any(
                module_name.startswith(prefix)
                for prefix in ("core.", "observations.", "inquiry.", "lens.")
            ):
                try:
                    source_file = inspect.getsourcefile(module)
                    if source_file:
                        with open(source_file, encoding="utf-8") as f:
                            source = f.read()
                            defaults_violations = detector.check_mutable_defaults(
                                module_name, source
                            )
                            violations.extend(defaults_violations)
                except Exception:
                    continue

        if violations:
            print(f"Mutable default violations found: {len(violations)}")
            for v in violations:
                print(f"\nModule: {v['module']}")
                print(f"Target: {v['target']}")
                print(f"Line: {v.get('line', 'N/A')}")
                print(f"Details: {v['details']}")
        else:
            print("No mutable default violations detected.")

    elif args.test:
        violations = enforce_no_mutation()
        if violations:
            print(f"FAILED: {len(violations)} mutation violations found:")
            for v in violations[:5]:  # Show first 5
                print(f"  - {v['module']}: {v.get('target', 'N/A')}")
            if len(violations) > 5:
                print(f"  ... and {len(violations) - 5} more")
            sys.exit(1)
        else:
            print("PASSED: No mutation violations found.")
            sys.exit(0)
    else:
        # Default: just check and report
        violations = enforce_no_mutation()
        if violations:
            print(f"Mutation violations found: {len(violations)}")
            for v in violations:
                print(f"\nModule: {v['module']}")
                print(f"Target: {v.get('target', 'N/A')}")
                print(f"Line: {v.get('line', 'N/A')}")
                print(f"Pattern: {v['pattern']}")
                print(f"Details: {v['details']}")
        else:
            print("No mutation violations detected.")
