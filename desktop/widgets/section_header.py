"""Reusable view section header with title, subtitle, and action slot."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class SectionHeader(QtWidgets.QFrame):
    """Structured section heading for consistent desktop view hierarchy."""

    def __init__(
        self,
        title: str,
        subtitle: str = "",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sectionHeader")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        text_layout = QtWidgets.QVBoxLayout()
        text_layout.setSpacing(2)
        self.title_label = QtWidgets.QLabel(title)
        self.title_label.setObjectName("sectionHeaderTitle")
        self.subtitle_label = QtWidgets.QLabel(subtitle)
        self.subtitle_label.setObjectName("sectionHeaderSubtitle")
        self.subtitle_label.setVisible(bool(subtitle))
        self.subtitle_label.setWordWrap(True)
        text_layout.addWidget(self.title_label)
        text_layout.addWidget(self.subtitle_label)

        layout.addLayout(text_layout, stretch=1)

        self.actions_container = QtWidgets.QWidget()
        self.actions_layout = QtWidgets.QHBoxLayout(self.actions_container)
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(6)
        self.actions_layout.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        layout.addWidget(self.actions_container)

    def set_title(self, title: str) -> None:
        self.title_label.setText(str(title or ""))

    def set_subtitle(self, subtitle: str) -> None:
        text = str(subtitle or "")
        self.subtitle_label.setText(text)
        self.subtitle_label.setVisible(bool(text))

    def add_action(self, widget: QtWidgets.QWidget) -> None:
        self.actions_layout.addWidget(widget)

