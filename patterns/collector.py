"""
patterns/collector.py - Local pattern submission and validation pipeline.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from patterns.loader import PatternDefinition, PatternLoader


@dataclass(frozen=True)
class PatternSubmission:
    """Submitted pattern payload tracked by the local collector."""

    submission_id: str
    created_at: str
    source: str
    submitter: str
    notes: str
    examples: list[str]
    pattern: PatternDefinition


@dataclass(frozen=True)
class ValidationReport:
    """Validation status for a pattern submission."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CurationDecision:
    """Local curation decision for a submission."""

    accepted: bool
    status: str
    reason: str
    labels: list[str] = field(default_factory=list)


class PatternCollector:
    """Collect and validate local pattern submissions."""

    _ALLOWED_SEVERITIES = {"critical", "warning", "info"}

    def __init__(
        self,
        *,
        storage_root: Path | str = Path("storage"),
        patterns_dir: Path | None = None,
    ) -> None:
        self.storage_root = Path(storage_root)
        self.base_dir = self.storage_root / "pattern_marketplace"
        self.submissions_dir = self.base_dir / "submissions"
        self.curation_file = self.base_dir / "curation.json"
        self.loader = PatternLoader(patterns_dir=patterns_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.submissions_dir.mkdir(parents=True, exist_ok=True)
        if not self.curation_file.exists():
            self.curation_file.write_text("[]", encoding="utf-8")

    def validate_submission(self, pattern: PatternDefinition) -> ValidationReport:
        """Validate a submitted pattern against local quality rules."""
        errors: list[str] = []
        warnings: list[str] = []
        risk_flags: list[str] = []

        pattern_id = pattern.id.strip()
        if not pattern_id:
            errors.append("Pattern id must not be empty")
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", pattern_id):
            errors.append("Pattern id must use [a-zA-Z0-9_.-] only")
        if len(pattern.name.strip()) < 3:
            errors.append("Pattern name is too short")

        if pattern.severity not in self._ALLOWED_SEVERITIES:
            errors.append(
                f"Severity must be one of: {', '.join(sorted(self._ALLOWED_SEVERITIES))}"
            )
        if not pattern.message.strip():
            errors.append("Message must not be empty")

        # Regex already compiles in PatternDefinition.__post_init__, but keep explicit
        # validation here for clear collector errors.
        try:
            re.compile(pattern.pattern)
        except re.error as exc:
            errors.append(f"Invalid regex: {exc}")

        existing_ids = {
            item.id.strip().lower()
            for item in self.loader.load_all_patterns()
            if item.id.strip()
        }
        if pattern_id.lower() in existing_ids:
            errors.append(f"Pattern id already exists: {pattern_id}")

        if ".*" in pattern.pattern:
            risk_flags.append("broad_regex")
            warnings.append("Pattern uses broad wildcard; may produce noisy matches")
        if len(pattern.pattern) > 260:
            warnings.append("Pattern regex is large; review readability and performance")
        if not pattern.tags:
            warnings.append("Pattern has no tags; discoverability will be limited")

        return ValidationReport(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            risk_flags=risk_flags,
        )

    def submit_local(
        self,
        pattern: PatternDefinition,
        *,
        submitter: str = "local",
        source: str = "manual",
        notes: str = "",
        examples: list[str] | None = None,
    ) -> tuple[PatternSubmission, ValidationReport]:
        """Store submission payload and return validation report."""
        report = self.validate_submission(pattern)
        submission = PatternSubmission(
            submission_id=f"sub_{uuid.uuid4().hex[:12]}",
            created_at=datetime.now(UTC).isoformat(),
            source=source,
            submitter=submitter,
            notes=notes,
            examples=list(examples or []),
            pattern=pattern,
        )
        self._write_submission(submission, report)
        return submission, report

    def curate(
        self,
        submission: PatternSubmission | str,
        *,
        approve: bool,
        reason: str = "",
        labels: list[str] | None = None,
    ) -> CurationDecision:
        """Record curation decision for a submission."""
        payload = self._resolve_submission(submission)
        if payload is None:
            return CurationDecision(
                accepted=False,
                status="missing",
                reason="Submission not found",
                labels=[],
            )

        decision = CurationDecision(
            accepted=bool(approve),
            status="accepted" if approve else "rejected",
            reason=reason.strip() or ("Approved" if approve else "Rejected"),
            labels=list(labels or []),
        )
        entries = self._read_json_list(self.curation_file)
        entries.append(
            {
                "submission_id": payload["submission"]["submission_id"],
                "created_at": datetime.now(UTC).isoformat(),
                "decision": asdict(decision),
            }
        )
        self._write_json(self.curation_file, entries)
        return decision

    def _write_submission(
        self,
        submission: PatternSubmission,
        report: ValidationReport,
    ) -> None:
        payload = {
            "submission": {
                "submission_id": submission.submission_id,
                "created_at": submission.created_at,
                "source": submission.source,
                "submitter": submission.submitter,
                "notes": submission.notes,
                "examples": submission.examples,
                "pattern": asdict(submission.pattern),
            },
            "validation": asdict(report),
        }
        path = self.submissions_dir / f"{submission.submission_id}.submission.json"
        self._write_json(path, payload)

    def _resolve_submission(self, submission: PatternSubmission | str) -> dict[str, Any] | None:
        if isinstance(submission, PatternSubmission):
            path = self.submissions_dir / f"{submission.submission_id}.submission.json"
            if not path.exists():
                return None
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                return None

        submission_id = str(submission).strip()
        if not submission_id:
            return None
        path = self.submissions_dir / f"{submission_id}.submission.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    @staticmethod
    def _read_json_list(path: Path) -> list[dict[str, Any]]:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            payload = []
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )

