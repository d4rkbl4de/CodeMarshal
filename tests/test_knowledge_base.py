import json
from pathlib import Path

from knowledge import KnowledgeBase


def test_add_and_search_insights(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")

    kb.add_insight("inv1", {"summary": "cache warmup strategy"})
    results = kb.search_insights("warmup")

    assert len(results) == 1
    assert results[0]["investigation_id"] == "inv1"


def test_pattern_trends(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    patterns_dir = storage_root / "patterns"
    patterns_dir.mkdir(parents=True)
    pattern_file = patterns_dir / "p_test.pattern.json"

    sample = {
        "data": {
            "matches": [
                {"pattern_id": "p1"},
                {"pattern_id": "p2"},
                {"pattern_id": "p1"},
            ]
        }
    }
    pattern_file.write_text(json.dumps(sample), encoding="utf-8")

    kb = KnowledgeBase(base_path=storage_root / "knowledge")
    trends = kb.get_pattern_trends("p1")

    assert trends["match_count"] == 2
    assert trends["files_scanned"] == 1
