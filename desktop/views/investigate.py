"""
Investigate view for the desktop GUI.
"""

from PySide6 import QtWidgets


class InvestigateView(QtWidgets.QWidget):
    """Single-focus investigate view (placeholder)."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Investigate: guided questions flow."))
