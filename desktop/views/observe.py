"""
Observe view for the desktop GUI.
"""

from PySide6 import QtWidgets


class ObserveView(QtWidgets.QWidget):
    """Single-focus observe view (placeholder)."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Observe: run a local observation."))
