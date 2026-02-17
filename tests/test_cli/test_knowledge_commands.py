from pathlib import Path

from bridge.commands import execute_graph, execute_history, execute_recommendations
from knowledge import KnowledgeBase


def test_execute_history_returns_filtered_events(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")
    kb.record_event("s-hist", "query", question="where is runtime?")
    kb.record_event("s-hist", "observe", path=str(tmp_path))

    result = execute_history(
        session_id="s-hist",
        query="runtime",
        event_type="query",
        limit=20,
        storage_root=storage_root,
    )

    assert result["success"] is True
    assert result["count"] == 1
    assert result["events"][0]["event_type"] == "query"


def test_execute_graph_returns_summary(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")
    kb.ingest_query("s-graph", "show graph", "structure")

    result = execute_graph(session_id="s-graph", depth=2, storage_root=storage_root)

    assert result["success"] is True
    assert "summary" in result
    assert result["summary"]["node_count"] >= 1


def test_execute_recommendations_returns_payload(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")
    kb.record_event("s-rec", "observe", path=str(tmp_path))

    result = execute_recommendations(
        session_id="s-rec",
        limit=5,
        refresh=True,
        storage_root=storage_root,
    )

    assert result["success"] is True
    assert result["count"] >= 1

