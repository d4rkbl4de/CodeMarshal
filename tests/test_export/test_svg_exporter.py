"""Tests for bridge.integration.svg_exporter."""

from bridge.integration.svg_exporter import SVGExporter


def test_svg_export_contains_nodes_and_edges() -> None:
    exporter = SVGExporter()
    session = {"id": "session-graph"}
    observations = [
        {
            "type": "import_sight",
            "file": "src/main.py",
            "statements": [{"module": "os"}, {"module": "app.service"}],
        },
        {
            "type": "boundary_sight",
            "crossings": [
                {
                    "source_module": "app.service",
                    "target_module": "core.model",
                    "source_boundary": "application",
                    "target_boundary": "domain",
                }
            ],
        },
    ]

    output = exporter.export(session, observations)

    assert output.lstrip().startswith("<svg")
    assert "<circle" in output
    assert "<line" in output
    assert "app.service" in output
    assert "core.model" in output


def test_svg_export_empty_state() -> None:
    exporter = SVGExporter()

    output = exporter.export({"id": "session-empty"}, [])

    assert output.lstrip().startswith("<svg")
    assert "No import or boundary data available" in output


def test_svg_export_escapes_labels() -> None:
    exporter = SVGExporter()
    observations = [
        {
            "type": "import_sight",
            "file": "src/<main>.py",
            "statements": [{"module": "lib<&>"}],
        }
    ]

    output = exporter.export({"id": "escape-test"}, observations)

    assert "src/&lt;main&gt;.py" in output
    assert "lib&lt;&amp;&gt;" in output
