"""
Patterns view for the desktop GUI.
"""

from PySide6 import QtWidgets


class PatternsView(QtWidgets.QWidget):
    """Single-focus patterns view (placeholder)."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Patterns: filter and review results."))
