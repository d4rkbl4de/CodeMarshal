"""Compact metric display chip used by the desktop shell."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets


class MetricPill(QtWidgets.QFrame):
    """Shows a short label plus value in a compact shell chip."""

    def __init__(
        self,
        label: str,
        value: str = "0",
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("metricPill")

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self.label_label = QtWidgets.QLabel(label)
        self.label_label.setObjectName("metricPillLabel")
        self.value_label = QtWidgets.QLabel(value)
        self.value_label.setObjectName("metricPillValue")
        self.value_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

        layout.addWidget(self.label_label)
        layout.addWidget(self.value_label)
        self.set_state("idle")

    def set_value(self, value: int | str) -> None:
        self.value_label.setText(str(value))

    def set_state(self, state: str) -> None:
        normalized = str(state or "idle").strip().lower()
        if normalized not in {"idle", "ok", "warn"}:
            normalized = "idle"
        self.setProperty("state", normalized)
        self.style().unpolish(self)
        self.style().polish(self)
