"""Reusable horizontal action-strip container."""

from __future__ import annotations

from collections.abc import Callable

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible


class ActionStrip(QtWidgets.QFrame):
    """Compact action row with helper for creating buttons."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("actionStrip")

        self.layout = QtWidgets.QHBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)

    def add_button(
        self,
        text: str,
        callback: Callable[[], None] | None = None,
        *,
        primary: bool = False,
        tooltip: str = "",
    ) -> QtWidgets.QPushButton:
        button = QtWidgets.QPushButton(str(text))
        if primary:
            button.setProperty("variant", "primary")
        if tooltip:
            button.setToolTip(tooltip)
        if callable(callback):
            button.clicked.connect(callback)
        apply_accessible(button, name=str(text))
        self.layout.addWidget(button)
        return button

    def add_stretch(self, stretch: int = 1) -> None:
        self.layout.addStretch(max(int(stretch), 0))

