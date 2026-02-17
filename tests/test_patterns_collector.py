from pathlib import Path

from patterns.collector import PatternCollector
from patterns.loader import PatternDefinition


def test_validate_submission_detects_duplicate_pattern_id(tmp_path: Path) -> None:
    collector = PatternCollector(storage_root=tmp_path / "storage")
    pattern = PatternDefinition(
        id="hardcoded_password",
        name="Duplicate",
        pattern=r"password\s*=",
        severity="warning",
    )

    report = collector.validate_submission(pattern)

    assert report.valid is False
    assert any("already exists" in item for item in report.errors)


def test_submit_local_persists_submission(tmp_path: Path) -> None:
    collector = PatternCollector(storage_root=tmp_path / "storage")
    pattern = PatternDefinition(
        id="collector_test_pattern",
        name="Collector Test Pattern",
        pattern=r"collector_test",
        severity="info",
    )

    submission, report = collector.submit_local(pattern, source="unit_test")

    assert submission.submission_id.startswith("sub_")
    assert report.valid is True
    persisted = (
        tmp_path
        / "storage"
        / "pattern_marketplace"
        / "submissions"
        / f"{submission.submission_id}.submission.json"
    )
    assert persisted.exists()


def test_curate_records_decision(tmp_path: Path) -> None:
    collector = PatternCollector(storage_root=tmp_path / "storage")
    pattern = PatternDefinition(
        id="collector_curation_pattern",
        name="Collector Curation Pattern",
        pattern=r"curation_marker",
        severity="warning",
    )
    submission, _ = collector.submit_local(pattern, source="unit_test")

    decision = collector.curate(submission, approve=True, reason="Looks good")

    assert decision.accepted is True
    assert decision.status == "accepted"
