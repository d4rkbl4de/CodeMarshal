"""Error presentation helpers for desktop views."""

from __future__ import annotations

from PySide6 import QtWidgets


class ErrorDialog:
    """Utility wrapper for consistent GUI error dialogs."""

    @staticmethod
    def show_error(
        parent: QtWidgets.QWidget | None,
        title: str,
        message: str,
        *,
        context: str | None = None,
        suggestion: str | None = None,
        details: str | None = None,
    ) -> None:
        lines = [message]
        if context:
            lines.append("")
            lines.append(f"Context: {context}")
        if suggestion:
            lines.append("")
            lines.append(f"Suggested action: {suggestion}")

        dialog = QtWidgets.QMessageBox(parent)
        dialog.setIcon(QtWidgets.QMessageBox.Critical)
        dialog.setWindowTitle(title)
        dialog.setText("\n".join(lines))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Ok)
        if details:
            dialog.setDetailedText(details)
        dialog.exec()

