from pathlib import Path

from patterns.engine import PatternEngine
from patterns.loader import PatternDefinition, PatternMatch


def test_detect_with_context(tmp_path: Path) -> None:
    sample = tmp_path / "sample.py"
    sample.write_text("line1\nTODO: fix\nline3\n", encoding="utf-8")

    pattern = PatternDefinition(
        id="todo_marker",
        name="TODO Marker",
        pattern="TODO",
        severity="info",
    )

    engine = PatternEngine(context_lines=1)
    matches = engine.detect_with_context(sample, pattern)

    assert len(matches) == 1
    match = matches[0]
    assert match.context_before == ["line1"]
    assert match.context_after == ["line3"]


def test_detect_statistical_outliers(tmp_path: Path) -> None:
    pattern = PatternDefinition(
        id="todo_marker",
        name="TODO Marker",
        pattern="TODO",
        severity="info",
    )

    # Create 7 files with 1 match and 1 file with many matches
    for idx in range(7):
        file_path = tmp_path / f"file_{idx}.py"
        file_path.write_text("TODO\n", encoding="utf-8")

    outlier_path = tmp_path / "outlier.py"
    outlier_path.write_text("\n".join(["TODO"] * 20), encoding="utf-8")

    engine = PatternEngine(context_lines=0)
    anomalies = engine.detect_statistical_outliers(
        tmp_path, patterns=[pattern], z_threshold=2.5
    )

    assert any(anomaly.file_path == outlier_path for anomaly in anomalies)


def test_suggest_fix() -> None:
    match = PatternMatch(
        pattern_id="nested_loop_n2",
        pattern_name="Nested Loop O(n^2)",
        file_path=Path("example.py"),
        line_number=10,
        line_content="for i in items:",
        matched_text="for i in items:",
        severity="warning",
        message="Nested loop detected",
        description="Nested loops can lead to quadratic behavior.",
        tags=["performance"],
        context_before=[],
        context_after=[],
    )

    engine = PatternEngine()
    suggestion = engine.suggest_fix(match)

    assert suggestion is not None
    assert suggestion.pattern_id == "nested_loop_n2"
