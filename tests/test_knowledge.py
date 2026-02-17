from pathlib import Path

from knowledge import KnowledgeBase


def test_history_record_and_query(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")

    kb.record_event("session-1", "query", question="where are imports?")
    kb.record_event("session-1", "observe", path=str(tmp_path))

    events = kb.history(session_id="session-1", event_type="query", limit=10)
    assert len(events) == 1
    assert events[0]["event_type"] == "query"

    suggestions = kb.history_service.suggestions(session_id="session-1", limit=5)
    assert suggestions
    assert suggestions[0]["query"] == "where are imports?"


def test_graph_ingest_observations(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")

    observations = [
        {
            "type": "import_sight",
            "file": "src/main.py",
            "statements": [{"module": "os"}, {"module": "json"}],
        },
        {
            "type": "boundary_sight",
            "crossings": [
                {"source_module": "core.runtime", "target_module": "storage.layout"}
            ],
        },
    ]
    kb.ingest_observations("session-graph", observations)
    kb.ingest_query("session-graph", "show dependencies", "connections")

    graph = kb.graph(session_id="session-graph", depth=2, limit=100)
    assert graph["summary"]["node_count"] > 0
    assert graph["summary"]["edge_count"] > 0

    edge_types = {str(edge.get("edge_type")) for edge in graph["edges"]}
    assert "imports" in edge_types or "depends_on" in edge_types


def test_recommendations_generation(tmp_path: Path) -> None:
    storage_root = tmp_path / "storage"
    kb = KnowledgeBase(base_path=storage_root / "knowledge")

    kb.record_event("session-rec", "observe", path=str(tmp_path))
    kb.ingest_query("session-rec", "what modules exist", "structure")

    recommendations = kb.recommendations("session-rec", refresh=True, limit=10)
    assert recommendations
    assert all("title" in item for item in recommendations)
    assert all("confidence" in item for item in recommendations)

