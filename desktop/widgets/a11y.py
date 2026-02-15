"""Accessibility utility helpers for desktop views."""

from __future__ import annotations

from typing import Iterable

from PySide6 import QtWidgets


def apply_accessible(
    widget: QtWidgets.QWidget,
    *,
    name: str,
    description: str = "",
) -> None:
    """Apply accessible metadata to a widget."""
    widget.setAccessibleName(name)
    if description:
        widget.setAccessibleDescription(description)


def mark_invalid(
    widget: QtWidgets.QWidget | None,
    message_label: QtWidgets.QLabel,
    message: str,
) -> None:
    """Mark a field invalid and show a readable validation message."""
    message_label.setText(message)
    message_label.setVisible(True)
    message_label.setAccessibleDescription(message)

    if widget is None:
        return
    widget.setProperty("state", "error")
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def clear_invalid(
    widgets: Iterable[QtWidgets.QWidget],
    message_label: QtWidgets.QLabel,
) -> None:
    """Clear invalid styling and hide validation message."""
    for widget in widgets:
        if widget.property("state"):
            widget.setProperty("state", "")
            widget.style().unpolish(widget)
            widget.style().polish(widget)
    message_label.setVisible(False)
