"""Reusable empty-state card used across desktop views."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible


class EmptyStateCard(QtWidgets.QFrame):
    """Displays an empty-state message with optional action."""

    action_requested = QtCore.Signal()

    def __init__(
        self,
        title: str,
        body: str,
        action_text: str | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("emptyStateCard")

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(8)

        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("emptyStateTitle")
        self.body_label = QtWidgets.QLabel(body)
        self.body_label.setObjectName("emptyStateBody")
        self.body_label.setWordWrap(True)
        layout.addWidget(self.title_label)
        layout.addWidget(self.body_label)

        self.action_button = QtWidgets.QPushButton(action_text or "")
        self.action_button.setVisible(bool(action_text))
        self.action_button.clicked.connect(self.action_requested.emit)
        apply_accessible(self.action_button, name=str(action_text or "Empty state action"))
        layout.addWidget(self.action_button, alignment=QtCore.Qt.AlignLeft)

    def set_content(self, title: str, body: str) -> None:
        self.title_label.setText(str(title or ""))
        self.body_label.setText(str(body or ""))

    def set_action_text(self, action_text: str | None) -> None:
        text = str(action_text or "")
        self.action_button.setText(text)
        self.action_button.setVisible(bool(text))

