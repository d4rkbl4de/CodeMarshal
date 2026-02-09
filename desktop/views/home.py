"""
Home view for the desktop GUI.
"""

from PySide6 import QtCore, QtWidgets


class HomeView(QtWidgets.QWidget):
    """Single-focus landing view with branding and primary actions."""

    navigate_requested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)

        title = QtWidgets.QLabel("CodeMarshal")
        title.setObjectName("title")
        subtitle = QtWidgets.QLabel("made by d4rkblblade")
        subtitle.setObjectName("subtitle")

        button_row = QtWidgets.QHBoxLayout()
        observe_btn = QtWidgets.QPushButton("Observe")
        investigate_btn = QtWidgets.QPushButton("Investigate")
        patterns_btn = QtWidgets.QPushButton("Patterns")
        export_btn = QtWidgets.QPushButton("Export")

        observe_btn.clicked.connect(lambda: self.navigate_requested.emit("observe"))
        investigate_btn.clicked.connect(
            lambda: self.navigate_requested.emit("investigate")
        )
        patterns_btn.clicked.connect(lambda: self.navigate_requested.emit("patterns"))
        export_btn.clicked.connect(lambda: self.navigate_requested.emit("export"))

        button_row.addWidget(observe_btn)
        button_row.addWidget(investigate_btn)
        button_row.addWidget(patterns_btn)
        button_row.addWidget(export_btn)

        panel = QtWidgets.QFrame()
        panel.setObjectName("panel")
        panel_layout = QtWidgets.QVBoxLayout(panel)
        panel_layout.addWidget(QtWidgets.QLabel("Select a workflow to begin."))

        layout.addStretch(1)
        layout.addWidget(title, alignment=QtCore.Qt.AlignHCenter)
        layout.addWidget(subtitle, alignment=QtCore.Qt.AlignHCenter)
        layout.addSpacing(10)
        layout.addLayout(button_row)
        layout.addWidget(panel)
        layout.addStretch(2)
