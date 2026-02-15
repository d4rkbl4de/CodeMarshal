"""Reusable contextual hint panel for desktop views."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class HintPanel(QtWidgets.QFrame):
    """Small helper card with optional action button."""

    action_requested = QtCore.Signal()

    def __init__(
        self,
        title: str = "",
        body: str = "",
        action_text: str | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("hintPanel")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("hintTitle")
        self.body_label = QtWidgets.QLabel(body)
        self.body_label.setObjectName("hintBody")
        self.body_label.setWordWrap(True)

        self.action_button = QtWidgets.QPushButton(action_text or "")
        self.action_button.clicked.connect(self.action_requested.emit)
        self.action_button.setVisible(bool(action_text))
        self.action_button.setProperty("variant", "secondary")

        layout.addWidget(self.title_label)
        layout.addWidget(self.body_label)
        layout.addWidget(self.action_button, alignment=QtCore.Qt.AlignLeft)

        self.setVisible(bool(title or body or action_text))

    def set_content(
        self,
        title: str,
        body: str,
        action_text: str | None = None,
    ) -> None:
        self.title_label.setText(title)
        self.body_label.setText(body)
        self.action_button.setText(action_text or "")
        self.action_button.setVisible(bool(action_text))
        self.setVisible(bool(title or body or action_text))
