"""
Jupyter notebook exporter for investigation data.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any


class JupyterExporter:
    """Export investigation data as a .ipynb notebook."""

    def export(
        self,
        session_data: dict[str, Any],
        observations: list[dict[str, Any]],
        include_notes: bool = False,
        include_patterns: bool = False,
    ) -> str:
        observation_types: dict[str, int] = {}
        for observation in observations:
            observation_type = observation.get("type", "unknown")
            observation_types[observation_type] = (
                observation_types.get(observation_type, 0) + 1
            )

        notebook = {
            "cells": [
                self._markdown_cell(
                    "# CodeMarshal Investigation Notebook\n"
                    f"- Exported: {datetime.now(UTC).isoformat()}\n"
                    "- Format: Jupyter Notebook\n"
                    "- Note: Flattened export, context may be reduced."
                ),
                self._markdown_cell(
                    "## Investigation Summary\n"
                    f"- ID: {session_data.get('id', 'unknown')}\n"
                    f"- Path: {session_data.get('path', 'unknown')}\n"
                    f"- State: {session_data.get('state', 'unknown')}\n"
                    f"- Observation Count: {len(observations)}"
                ),
                self._code_cell(
                    "observations = " + json.dumps(observations, indent=2, default=str)
                ),
                self._markdown_cell("## Observation Type Counts"),
                self._code_cell(
                    "observation_type_counts = "
                    + json.dumps(observation_types, indent=2, sort_keys=True)
                ),
            ],
            "metadata": {
                "language_info": {"name": "python"},
                "codemarshal": {
                    "version": "2.0.0",
                    "include_notes": include_notes,
                    "include_patterns": include_patterns,
                },
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }

        if include_notes:
            notes = session_data.get("notes", [])
            notebook["cells"].append(
                self._markdown_cell(
                    "## Notes\n"
                    + (
                        "\n".join(f"- {note}" for note in notes)
                        if notes
                        else "- No notes available"
                    )
                )
            )

        if include_patterns:
            patterns = session_data.get("patterns", [])
            notebook["cells"].append(
                self._markdown_cell(
                    "## Patterns\n"
                    + (
                        "\n".join(f"- {pattern}" for pattern in patterns)
                        if patterns
                        else "- No patterns available"
                    )
                )
            )

        return json.dumps(notebook, indent=2, ensure_ascii=False, sort_keys=True)

    @staticmethod
    def _markdown_cell(content: str) -> dict[str, Any]:
        return {
            "cell_type": "markdown",
            "metadata": {},
            "source": content,
        }

    @staticmethod
    def _code_cell(content: str) -> dict[str, Any]:
        return {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": content,
        }
