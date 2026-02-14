"""Structured results viewer widget."""

from __future__ import annotations

import json
from typing import Any

from PySide6 import QtWidgets


class ResultsViewer(QtWidgets.QWidget):
    """Read-only viewer with helpers for text and JSON output."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._text = QtWidgets.QPlainTextEdit(self)
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QtWidgets.QPlainTextEdit.NoWrap)
        layout.addWidget(self._text)

    def clear(self) -> None:
        self._text.clear()

    def set_text(self, text: str) -> None:
        self._text.setPlainText(text)

    def append_text(self, text: str) -> None:
        if self._text.toPlainText():
            self._text.appendPlainText(text)
        else:
            self._text.setPlainText(text)

    def set_json(self, payload: Any) -> None:
        self._text.setPlainText(json.dumps(payload, indent=2, default=str))

