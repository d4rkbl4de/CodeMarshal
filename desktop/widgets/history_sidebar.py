"""History sidebar widget for knowledge workflows."""

from __future__ import annotations

from typing import Any

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible


class HistorySidebar(QtWidgets.QGroupBox):
    """History filters, timeline, and quick-restore actions."""

    history_requested = QtCore.Signal(dict)
    quick_restore_requested = QtCore.Signal(str)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("History Timeline", parent)
        self._active_session_id: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        filters = QtWidgets.QFormLayout()
        self.query_input = QtWidgets.QLineEdit()
        self.query_input.setPlaceholderText("Search history text")
        apply_accessible(self.query_input, name="History search query")
        filters.addRow("Query:", self.query_input)

        date_row = QtWidgets.QHBoxLayout()
        self.from_date_input = QtWidgets.QLineEdit()
        self.from_date_input.setPlaceholderText("YYYY-MM-DD")
        self.to_date_input = QtWidgets.QLineEdit()
        self.to_date_input.setPlaceholderText("YYYY-MM-DD")
        apply_accessible(self.from_date_input, name="History from date")
        apply_accessible(self.to_date_input, name="History to date")
        date_row.addWidget(self.from_date_input)
        date_row.addWidget(self.to_date_input)
        filters.addRow("Date Range:", date_row)

        self.event_type_combo = QtWidgets.QComboBox()
        self.event_type_combo.addItems(
            ["all", "investigate", "observe", "query", "pattern_scan", "export", "insight"]
        )
        apply_accessible(self.event_type_combo, name="History event type")
        filters.addRow("Event Type:", self.event_type_combo)

        self.limit_spin = QtWidgets.QSpinBox()
        self.limit_spin.setRange(1, 5000)
        self.limit_spin.setValue(100)
        apply_accessible(self.limit_spin, name="History result limit")
        filters.addRow("Limit:", self.limit_spin)
        layout.addLayout(filters)

        self.load_btn = QtWidgets.QPushButton("Load History")
        self.load_btn.clicked.connect(self._emit_request)
        apply_accessible(self.load_btn, name="Load history timeline")
        layout.addWidget(self.load_btn)

        self.timeline_list = QtWidgets.QListWidget()
        apply_accessible(self.timeline_list, name="History timeline entries")
        layout.addWidget(self.timeline_list, stretch=1)

        self.suggestions_list = QtWidgets.QListWidget()
        apply_accessible(self.suggestions_list, name="History query suggestions")
        layout.addWidget(self.suggestions_list, stretch=1)

        self.quick_restore_btn = QtWidgets.QPushButton("Quick Restore Session")
        self.quick_restore_btn.clicked.connect(self._emit_quick_restore)
        apply_accessible(self.quick_restore_btn, name="Restore selected history session")
        layout.addWidget(self.quick_restore_btn)

    def set_session_id(self, session_id: str | None) -> None:
        self._active_session_id = session_id

    def payload(self) -> dict[str, Any]:
        event_type = self.event_type_combo.currentText().strip().lower()
        return {
            "session_id": self._active_session_id,
            "query": self.query_input.text().strip() or None,
            "from_date": self.from_date_input.text().strip() or None,
            "to_date": self.to_date_input.text().strip() or None,
            "event_type": None if event_type == "all" else event_type,
            "limit": int(self.limit_spin.value()),
        }

    def set_history_payload(self, payload: dict[str, Any]) -> None:
        events = payload.get("events", []) if isinstance(payload, dict) else []
        self.timeline_list.clear()
        if isinstance(events, list):
            for event in events[:300]:
                if not isinstance(event, dict):
                    continue
                timestamp = str(event.get("timestamp") or "unknown")
                event_type = str(event.get("event_type") or "unknown")
                question = str(event.get("question") or "").strip()
                summary = f"[{timestamp}] {event_type}"
                if question:
                    summary = f"{summary} :: {question[:90]}"
                item = QtWidgets.QListWidgetItem(summary)
                item.setData(QtCore.Qt.UserRole, event)
                self.timeline_list.addItem(item)

        suggestions = payload.get("suggestions", []) if isinstance(payload, dict) else []
        self.suggestions_list.clear()
        if isinstance(suggestions, list):
            for suggestion in suggestions[:100]:
                if isinstance(suggestion, dict):
                    query = str(suggestion.get("query") or "")
                    count = int(suggestion.get("count") or 0)
                    text = f"{query} ({count})"
                else:
                    text = str(suggestion)
                self.suggestions_list.addItem(text)

    def _emit_request(self) -> None:
        self.history_requested.emit(self.payload())

    def _emit_quick_restore(self) -> None:
        item = self.timeline_list.currentItem()
        if item is None:
            if self._active_session_id:
                self.quick_restore_requested.emit(self._active_session_id)
            return
        event = item.data(QtCore.Qt.UserRole)
        if isinstance(event, dict):
            session_id = str(event.get("session_id") or self._active_session_id or "")
        else:
            session_id = str(self._active_session_id or "")
        if session_id:
            self.quick_restore_requested.emit(session_id)

