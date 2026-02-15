"""Structured results viewer widget."""

from __future__ import annotations

import json
from typing import Any

from PySide6 import QtWidgets

from .a11y import apply_accessible


class ResultsViewer(QtWidgets.QWidget):
    """Read-only viewer with helpers for text and JSON output."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        controls = QtWidgets.QHBoxLayout()
        self.copy_summary_btn = QtWidgets.QPushButton("Copy Summary")
        self.copy_summary_btn.clicked.connect(self._copy_summary)
        self.copy_summary_btn.setShortcut("Alt+S")
        self.copy_summary_btn.setToolTip("Copy summary text (Alt+S)")
        apply_accessible(self.copy_summary_btn, name="Copy summary text")
        self.copy_raw_btn = QtWidgets.QPushButton("Copy Raw")
        self.copy_raw_btn.clicked.connect(self._copy_raw)
        self.copy_raw_btn.setShortcut("Alt+R")
        self.copy_raw_btn.setToolTip("Copy raw text (Alt+R)")
        apply_accessible(self.copy_raw_btn, name="Copy raw text")
        controls.addWidget(self.copy_summary_btn)
        controls.addWidget(self.copy_raw_btn)
        controls.addStretch(1)
        layout.addLayout(controls)

        self._tabs = QtWidgets.QTabWidget(self)
        self._summary = QtWidgets.QPlainTextEdit(self)
        self._summary.setReadOnly(True)
        self._summary.setLineWrapMode(QtWidgets.QPlainTextEdit.WidgetWidth)
        apply_accessible(
            self._summary,
            name="Result summary pane",
            description="Human-readable summary of operation output.",
        )
        self._raw = QtWidgets.QPlainTextEdit(self)
        self._raw.setReadOnly(True)
        self._raw.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        apply_accessible(
            self._raw,
            name="Result raw pane",
            description="Raw payload of operation output.",
        )

        self._tabs.addTab(self._summary, "Summary")
        self._tabs.addTab(self._raw, "Raw")
        layout.addWidget(self._tabs)

    def clear(self) -> None:
        self._summary.clear()
        self._raw.clear()

    def set_text(self, text: str) -> None:
        self.set_sections(text, text)

    def append_text(self, text: str) -> None:
        if self._raw.toPlainText():
            self._raw.appendPlainText(text)
        else:
            self._raw.setPlainText(text)
        if self._summary.toPlainText():
            self._summary.appendPlainText(text)
        else:
            self._summary.setPlainText(text)

    def set_json(self, payload: Any) -> None:
        raw = json.dumps(payload, indent=2, default=str)
        summary = self._summarize_payload(payload)
        self.set_sections(summary, raw)

    def set_sections(self, summary: str, raw: str) -> None:
        self._summary.setPlainText(summary)
        self._raw.setPlainText(raw)

    def show_raw(self) -> None:
        self._tabs.setCurrentWidget(self._raw)

    def _copy_summary(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._summary.toPlainText())

    def _copy_raw(self) -> None:
        QtWidgets.QApplication.clipboard().setText(self._raw.toPlainText())

    def _summarize_payload(self, payload: Any) -> str:
        if isinstance(payload, dict):
            lines = [f"Keys: {len(payload)}"]
            for key in sorted(payload.keys())[:15]:
                value = payload[key]
                if isinstance(value, list):
                    info = f"list[{len(value)}]"
                elif isinstance(value, dict):
                    info = f"dict[{len(value)}]"
                else:
                    info = type(value).__name__
                lines.append(f"- {key}: {info}")
            return "\n".join(lines)
        if isinstance(payload, list):
            return f"List payload with {len(payload)} item(s)."
        return "Result payload received."
