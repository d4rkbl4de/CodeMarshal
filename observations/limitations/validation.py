"""
LIMITATION VALIDATION - Consistency & Enforcement

This module ensures honesty in observational limitations, not correctness.
It validates that:
1. Every declared limitation is documented
2. No undocumented limitation is exposed
3. No duplicate or conflicting declarations exist

Violations cause immediate failure - this is the truth-preserving guardrail.
"""

from __future__ import annotations

import dataclasses
import hashlib
import sys
from collections.abc import Sequence
from typing import Any, TypeAlias

# Local imports - allowed per specification
from . import declared, documented

# Type Aliases for clarity
LimitationID: TypeAlias = str
ValidationError: TypeAlias = str


@dataclasses.dataclass(frozen=True, slots=True)
class ValidationResult:
    """Summary of validation outcomes used by inquiry layer."""

    valid_count: int
    invalid_count: int
    skipped_count: int
    errors: tuple[ValidationError, ...] = ()

    @property
    def total_count(self) -> int:
        """Total number of items considered."""
        return self.valid_count + self.invalid_count + self.skipped_count


@dataclasses.dataclass(frozen=True, slots=True)
class ValidationLimitation:
    """Simple limitation record for analysis layers."""

    source_path: str
    limitation_type: str
    description: str
    severity: str = "low"

    def to_dict(self) -> dict[str, Any]:
        """Convert to serializable dictionary."""
        return {
            "source_path": self.source_path,
            "limitation_type": self.limitation_type,
            "description": self.description,
            "severity": self.severity,
        }


@dataclasses.dataclass(frozen=True, slots=True)
class LimitationSet:
    """Immutable, validated set of observational limitations."""

    declared_limitations: Sequence[declared.Limitation]
    documented_limitations: dict[LimitationID, documented.LimitationDoc]
    declaration_hash: str

    @classmethod
    def create(cls) -> LimitationSet:
        """Factory method that validates before creation."""
        errors = validate_limitations()
        if errors:
            raise LimitationValidationError(errors)

        declared_items = declared.get_active_limitations()
        documented_items = documented.get_limitation_docs()

        # Create deterministic hash of declarations
        hash_input = "\n".join(
            f"{lim.id}:{lim.category}:{lim.scope}"
            for lim in sorted(declared_items, key=lambda x: x.id)
        )
        declaration_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        return cls(
            declared_limitations=declared_items,
            documented_limitations=documented_items,
            declaration_hash=declaration_hash,
        )

    def get_for_snapshot(self) -> SnapshotLimitations:
        """Extract limitation info for inclusion in snapshots."""
        return SnapshotLimitations(
            limitation_ids=[lim.id for lim in self.declared_limitations],
            declaration_hash=self.declaration_hash,
            timestamp=None,  # Will be set by snapshot creation
        )


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotLimitations:
    """Minimal limitation metadata embedded in every snapshot."""

    limitation_ids: list[str]
    declaration_hash: str
    timestamp: str | None  # ISO format when set

    def to_dict(self) -> dict[str, Any]:
        """Serialize for JSON storage."""
        return {
            "limitation_ids": self.limitation_ids,
            "declaration_hash": self.declaration_hash,
            "timestamp": self.timestamp,
        }


class LimitationValidationError(Exception):
    """Raised when limitation consistency rules are violated."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        message = "Limitation validation failed:\n" + "\n".join(
            f"  - {e}" for e in errors
        )
        super().__init__(message)


def validate_limitations() -> list[str]:
    """
    Validate consistency between declared and documented limitations.

    Returns:
        Empty list if validation passes, list of error messages otherwise.

    Raises:
        Nothing - returns errors instead of raising to allow callers to decide.
    """
    errors: list[str] = []

    # Get current limitations
    declared_items = declared.get_active_limitations()
    documented_items = documented.get_limitation_docs()

    # Check 1: Every declared limitation must be documented
    for lim in declared_items:
        if lim.id not in documented_items:
            errors.append(
                f"Declared limitation '{lim.id}' ({lim.description}) is not documented"
            )
        else:
            # Check for contradiction in basic properties
            doc = documented_items[lim.id]
            if doc.category != lim.category:
                errors.append(
                    f"Category mismatch for '{lim.id}': "
                    f"declared={lim.category}, documented={doc.category}"
                )

    # Check 2: No duplicate limitation IDs
    seen_ids: set[str] = set()
    for lim in declared_items:
        if lim.id in seen_ids:
            errors.append(f"Duplicate limitation ID: '{lim.id}'")
        seen_ids.add(lim.id)

    # Check 3: No documentation for non-existent limitations
    documented_ids = set(documented_items.keys())
    declared_ids = {lim.id for lim in declared_items}
    for doc_id in documented_ids - declared_ids:
        errors.append(f"Documentation exists for non-declared limitation: '{doc_id}'")

    # Check 4: No conflicting scope/constraint definitions
    # (This would require more complex logic based on your actual Limitation structure)
    # For now, placeholder for future expansion

    return errors


def validate_during_snapshot(snapshot_limitations: SnapshotLimitations) -> None:
    """
    Validate that snapshot limitations are consistent with current system state.

    This ensures snapshots cannot be created with invalid limitation metadata.

    Args:
        snapshot_limitations: Limitations metadata from snapshot being created

    Raises:
        LimitationValidationError: If snapshot limitations are invalid
    """
    errors: list[str] = []

    # Get current limitations
    current_set = LimitationSet.create()
    current_ids = {lim.id for lim in current_set.declared_limitations}
    snapshot_ids = set(snapshot_limitations.limitation_ids)

    # Check 1: Snapshot IDs must be subset of current IDs
    # (Snapshots cannot claim to observe more than the system can)
    if extra_ids := snapshot_ids - current_ids:
        errors.append(
            f"Snapshot claims limitations not in current system: {sorted(extra_ids)}"
        )

    # Check 2: Declaration hash must match if IDs match exactly
    # (Different hash with same IDs means declaration changed, which is invalid)
    if (
        snapshot_ids == current_ids
        and snapshot_limitations.declaration_hash != current_set.declaration_hash
    ):
        errors.append(
            "Declaration hash mismatch: same limitation IDs but different hashes. "
            "This suggests limitation definitions changed without ID update."
        )

    if errors:
        raise LimitationValidationError(errors)


def get_validation_report() -> str:
    """
    Generate human-readable validation report.

    Returns:
        Markdown-formatted report of limitation validation status.
    """
    errors = validate_limitations()

    if not errors:
        current_set = LimitationSet.create()
        limitation_count = len(current_set.declared_limitations)
        return (
            f"# Limitation Validation Report\n\n"
            f"✅ **PASSED** - All {limitation_count} limitations are consistent\n\n"
            f"**Declaration Hash:** `{current_set.declaration_hash}`\n\n"
            f"**Limitations:**\n"
            + "\n".join(
                f"- {lim.id}: {lim.description}"
                for lim in current_set.declared_limitations
            )
        )
    else:
        return (
            f"# Limitation Validation Report\n\n"
            f"❌ **FAILED** - {len(errors)} validation error(s)\n\n"
            f"**Errors:**\n"
            + "\n".join(f"1. {error}" for error in errors)
            + "\n\n**Action Required:** Fix inconsistencies before proceeding."
        )


# Standalone validation for use in pre-commit hooks or CI
def main() -> None:
    """Command-line entry point for validation."""
    try:
        errors = validate_limitations()
        if errors:
            print("❌ Limitation validation failed:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            sys.exit(1)

        current_set = LimitationSet.create()
        print(f"✅ All {len(current_set.declared_limitations)} limitations validated")
        print(f"📝 Declaration hash: {current_set.declaration_hash}")

        # Optional: Generate full report
        if "--report" in sys.argv:
            print("\n" + get_validation_report())

    except Exception as e:
        print(f"💥 Validation crashed: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
