"""
SVG exporter for architecture visualization.
"""

from __future__ import annotations

from html import escape
from typing import Any


class SVGExporter:
    """Export investigation graph as an SVG diagram."""

    _BOUNDARY_COLORS = [
        "#1f77b4",
        "#ff7f0e",
        "#2ca02c",
        "#d62728",
        "#9467bd",
        "#8c564b",
        "#e377c2",
        "#7f7f7f",
        "#bcbd22",
        "#17becf",
    ]

    def export(
        self,
        session_data: dict[str, Any],
        observations: list[dict[str, Any]],
        include_notes: bool = False,
        include_patterns: bool = False,
    ) -> str:
        del include_notes
        del include_patterns
        nodes, edges, boundary_map = self._extract_graph(observations)

        if not nodes:
            return self._empty_svg(
                "No import or boundary data available for diagram generation."
            )

        width = 1200
        height = max(500, ((len(nodes) + 3) // 4) * 170)
        columns = 4
        x_spacing = width // (columns + 1)
        y_spacing = 140

        positions: dict[str, tuple[int, int]] = {}
        for index, node in enumerate(nodes):
            row = index // columns
            col = index % columns
            positions[node] = ((col + 1) * x_spacing, 90 + (row * y_spacing))

        boundary_names = sorted(set(boundary_map.values()))
        boundary_color_map = {
            name: self._BOUNDARY_COLORS[index % len(self._BOUNDARY_COLORS)]
            for index, name in enumerate(boundary_names)
        }

        lines: list[str] = [
            '<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f"<title>{escape(str(session_data.get('id', 'investigation')))} architecture graph</title>",
            "<desc>Nodes are modules/files. Edges represent imports and boundary crossings.</desc>",
            '<rect width="100%" height="100%" fill="#f7f8fa" />',
        ]

        if not boundary_names:
            lines.append(
                '<text x="20" y="24" font-size="12" fill="#555">Boundary data unavailable; neutral node coloring is used.</text>'
            )

        for source, target, edge_type in edges:
            if source not in positions or target not in positions:
                continue
            x1, y1 = positions[source]
            x2, y2 = positions[target]
            stroke = "#555" if edge_type == "import" else "#b22222"
            lines.extend(
                [
                    (
                        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                        f'stroke="{stroke}" stroke-width="1.6" opacity="0.75">'
                    ),
                    f"<title>{escape(source)} -> {escape(target)} ({edge_type})</title>",
                    "</line>",
                ]
            )

        for node in nodes:
            x, y = positions[node]
            boundary = boundary_map.get(node)
            fill = boundary_color_map.get(boundary, "#4a90e2")
            lines.extend(
                [
                    f'<g transform="translate({x},{y})">',
                    f'<circle r="28" fill="{fill}" opacity="0.9" />',
                    '<circle r="28" fill="none" stroke="#222" stroke-width="1" opacity="0.35" />',
                    f"<title>{escape(node)} ({escape(boundary or 'unmapped')})</title>",
                    (
                        '<text x="0" y="45" text-anchor="middle" font-size="10" '
                        f'fill="#111">{escape(self._truncate(node, 30))}</text>'
                    ),
                    "</g>",
                ]
            )

        lines.append("</svg>")
        return "\n".join(lines)

    def _extract_graph(
        self, observations: list[dict[str, Any]]
    ) -> tuple[list[str], list[tuple[str, str, str]], dict[str, str]]:
        nodes: set[str] = set()
        edges: set[tuple[str, str, str]] = set()
        boundary_map: dict[str, str] = {}

        for observation in observations:
            observation_type = observation.get("type", "")

            if observation_type == "import_sight":
                source = str(observation.get("file") or "").strip()
                if not source:
                    continue
                nodes.add(source)
                statements = observation.get("statements", [])
                for statement in statements:
                    if not isinstance(statement, dict):
                        continue
                    module = str(statement.get("module") or "").strip()
                    if not module:
                        continue
                    nodes.add(module)
                    edges.add((source, module, "import"))

            elif observation_type == "boundary_sight":
                crossings = observation.get("crossings")
                if crossings is None:
                    crossings = observation.get("result", {}).get("crossings", [])
                if not isinstance(crossings, list):
                    continue

                for crossing in crossings:
                    if not isinstance(crossing, dict):
                        continue
                    source_module = str(
                        crossing.get("source_module")
                        or crossing.get("source")
                        or ""
                    ).strip()
                    target_module = str(
                        crossing.get("target_module")
                        or crossing.get("target")
                        or ""
                    ).strip()
                    source_boundary = str(crossing.get("source_boundary") or "").strip()
                    target_boundary = str(crossing.get("target_boundary") or "").strip()

                    if source_module:
                        nodes.add(source_module)
                        if source_boundary:
                            boundary_map[source_module] = source_boundary
                    if target_module:
                        nodes.add(target_module)
                        if target_boundary:
                            boundary_map[target_module] = target_boundary
                    if source_module and target_module:
                        edges.add((source_module, target_module, "boundary"))

        return sorted(nodes), sorted(edges), boundary_map

    @staticmethod
    def _truncate(value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[: max_length - 3] + "..."

    @staticmethod
    def _empty_svg(message: str) -> str:
        safe_message = escape(message)
        return "\n".join(
            [
                '<svg xmlns="http://www.w3.org/2000/svg" width="900" height="240" viewBox="0 0 900 240">',
                "<title>CodeMarshal architecture diagram</title>",
                "<desc>No graph data available.</desc>",
                '<rect width="100%" height="100%" fill="#f7f8fa" />',
                '<text x="450" y="120" text-anchor="middle" font-size="16" fill="#333">'
                + safe_message
                + "</text>",
                "</svg>",
            ]
        )
