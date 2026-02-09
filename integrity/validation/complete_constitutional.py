import json
import sys
from dataclasses import dataclass
from typing import Any

from .. import (
    ValidationResult,
    validate_interface,
    validate_integration,
    validate_observations,
    validate_patterns,
)


@dataclass
class ConstitutionalAudit:
    results: dict[str, ValidationResult]
    violations: list[dict[str, Any]]

    def get_compliance_score(self) -> float:
        total = len(self.results)
        if total == 0:
            return 0.0
        passed = sum(1 for result in self.results.values() if result.passed)
        return round((passed / total) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "compliance_score": self.get_compliance_score(),
            "results": {name: result.to_dict() for name, result in self.results.items()},
            "violations": self.violations,
        }


def _run_checks() -> dict[str, ValidationResult]:
    checks = [
        ("observations", validate_observations),
        ("patterns", validate_patterns),
        ("interface", validate_interface),
        ("integration", validate_integration),
    ]

    results: dict[str, ValidationResult] = {}

    for check_name, check_func in checks:
        try:
            results[check_name] = check_func()
        except Exception as exc:
            results[check_name] = ValidationResult(
                passed=False,
                violations=[{"check": check_name, "error": str(exc)}],
                details=str(exc),
            )

    return results


def run_constitutional_audit() -> ConstitutionalAudit:
    results = _run_checks()
    violations: list[dict[str, Any]] = []

    for check_name, result in results.items():
        if result.passed:
            continue
        if result.violations:
            for violation in result.violations:
                if "check" not in violation:
                    violation = dict(violation)
                    violation["check"] = check_name
                violations.append(violation)
        else:
            violations.append(
                {
                    "check": check_name,
                    "details": result.details or "validation failed",
                }
            )

    return ConstitutionalAudit(results=results, violations=violations)


def run_all_constitutional_validations() -> bool:
    audit = run_constitutional_audit()
    print(json.dumps(audit.to_dict()["results"], indent=2))
    return audit.get_compliance_score() == 100.0


if __name__ == "__main__":
    sys.exit(0 if run_all_constitutional_validations() else 1)
