"""
Export view for the desktop GUI.
"""

from PySide6 import QtWidgets


class ExportView(QtWidgets.QWidget):
    """Single-focus export view (placeholder)."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("Export: select format and output."))
