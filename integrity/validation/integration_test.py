"""
integrity/validation/integration_test.py - Integration validation checks

Validates that core modules can be imported together without errors.
"""

import importlib


REQUIRED_MODULES = [
    "core.engine",
    "core.runtime",
    "observations.interface",
    "inquiry.interface",
    "lens.interface",
    "bridge.entry.cli",
]


def validate_integration() -> "ValidationResult":
    from integrity import ValidationResult

    violations = []
    for module in REQUIRED_MODULES:
        try:
            importlib.import_module(module)
        except Exception as exc:
            violations.append({"check": "integration", "module": module, "error": str(exc)})

    passed = len(violations) == 0
    details = "All required modules imported" if passed else f"{len(violations)} module(s) failed to import"

    return ValidationResult(passed=passed, violations=violations, details=details)
