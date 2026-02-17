"""Template creation panel for pattern workflows."""

from __future__ import annotations

from typing import Any

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible, clear_invalid, mark_invalid


class TemplatesPanel(QtWidgets.QGroupBox):
    """UI panel for template search, customization, and preview."""

    create_requested = QtCore.Signal(dict)
    validation_failed = QtCore.Signal(str)

    def __init__(
        self,
        template_ids: list[str] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__("Template Builder", parent)
        self._all_template_ids = list(template_ids or [])
        self._build_ui()
        self.set_templates(self._all_template_ids)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setObjectName("validationError")
        self.validation_label.setWordWrap(True)
        self.validation_label.setVisible(False)
        layout.addWidget(self.validation_label)

        filter_row = QtWidgets.QHBoxLayout()
        self.template_search_input = QtWidgets.QLineEdit()
        self.template_search_input.setPlaceholderText("Search templates")
        self.template_search_input.textChanged.connect(self._apply_template_filter)
        apply_accessible(self.template_search_input, name="Template search")
        filter_row.addWidget(QtWidgets.QLabel("Search:"))
        filter_row.addWidget(self.template_search_input, stretch=1)
        layout.addLayout(filter_row)

        main_row = QtWidgets.QHBoxLayout()
        self.template_combo = QtWidgets.QComboBox()
        apply_accessible(self.template_combo, name="Pattern template selector")
        self.template_values_input = QtWidgets.QLineEdit()
        self.template_values_input.setPlaceholderText("Values: key=value,key2=value2")
        self.template_values_input.textChanged.connect(self._update_preview)
        apply_accessible(self.template_values_input, name="Template value assignments")
        self.create_pattern_btn = QtWidgets.QPushButton("Create Pattern")
        self.create_pattern_btn.clicked.connect(self._on_create_clicked)
        apply_accessible(self.create_pattern_btn, name="Create pattern from template")
        main_row.addWidget(self.template_combo, stretch=1)
        main_row.addWidget(self.template_values_input, stretch=2)
        main_row.addWidget(self.create_pattern_btn)
        layout.addLayout(main_row)

        options_row = QtWidgets.QHBoxLayout()
        self.create_pattern_id_input = QtWidgets.QLineEdit()
        self.create_pattern_id_input.setPlaceholderText("Optional pattern ID")
        self.create_bundle_output_input = QtWidgets.QLineEdit()
        self.create_bundle_output_input.setPlaceholderText("Optional output bundle path")
        self.create_dry_run_checkbox = QtWidgets.QCheckBox("Dry Run")
        apply_accessible(self.create_pattern_id_input, name="Template pattern id override")
        apply_accessible(self.create_bundle_output_input, name="Template output bundle path")
        apply_accessible(self.create_dry_run_checkbox, name="Template creation dry run")
        options_row.addWidget(self.create_pattern_id_input, stretch=1)
        options_row.addWidget(self.create_bundle_output_input, stretch=2)
        options_row.addWidget(self.create_dry_run_checkbox)
        layout.addLayout(options_row)

        self.preview = QtWidgets.QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText("Template payload preview")
        self.preview.setMaximumBlockCount(120)
        apply_accessible(self.preview, name="Template payload preview")
        layout.addWidget(self.preview, stretch=1)

    def set_templates(self, template_ids: list[str]) -> None:
        self._all_template_ids = list(template_ids)
        self._apply_template_filter()
        self._update_preview()

    def current_payload(self) -> dict[str, Any]:
        template_id = self.template_combo.currentText().strip()
        values = self.parse_values(self.template_values_input.text().strip())
        return {
            "template_id": template_id,
            "values": values,
            "pattern_id": self.create_pattern_id_input.text().strip() or None,
            "output_path": self.create_bundle_output_input.text().strip() or None,
            "dry_run": self.create_dry_run_checkbox.isChecked(),
        }

    def parse_values(self, values_text: str) -> dict[str, str]:
        values: dict[str, str] = {}
        for token in values_text.split(","):
            pair = token.strip()
            if not pair:
                continue
            if "=" not in pair:
                raise ValueError(
                    f"Invalid template value '{pair}'. Use key=value pairs."
                )
            key, value = pair.split("=", 1)
            normalized_key = key.strip()
            if not normalized_key:
                raise ValueError(
                    f"Invalid template value '{pair}'. Key cannot be empty."
                )
            values[normalized_key] = value.strip()
        return values

    def _apply_template_filter(self) -> None:
        query = self.template_search_input.text().strip().lower()
        current = self.template_combo.currentText().strip()
        self.template_combo.blockSignals(True)
        self.template_combo.clear()
        for item in self._all_template_ids:
            if query and query not in item.lower():
                continue
            self.template_combo.addItem(item)
        if current:
            index = self.template_combo.findText(current)
            if index >= 0:
                self.template_combo.setCurrentIndex(index)
        self.template_combo.blockSignals(False)

    def _on_create_clicked(self) -> None:
        try:
            payload = self.current_payload()
            if not str(payload.get("template_id") or "").strip():
                raise ValueError("Select a template to create a pattern.")
        except ValueError as exc:
            self._set_validation(str(exc), self.template_values_input)
            self.validation_failed.emit(str(exc))
            return
        self._clear_validation()
        self.create_requested.emit(payload)

    def _set_validation(
        self,
        message: str,
        widget: QtWidgets.QWidget | None = None,
    ) -> None:
        mark_invalid(widget, self.validation_label, message)

    def _clear_validation(self) -> None:
        clear_invalid(
            (
                self.template_combo,
                self.template_values_input,
                self.create_pattern_id_input,
                self.create_bundle_output_input,
            ),
            self.validation_label,
        )

    def _update_preview(self) -> None:
        payload: dict[str, Any]
        try:
            payload = self.current_payload()
        except Exception:
            payload = {
                "template_id": self.template_combo.currentText().strip(),
                "values": {"error": "invalid assignment syntax"},
            }
        lines = [
            f"template_id: {payload.get('template_id')}",
            f"pattern_id: {payload.get('pattern_id')}",
            f"dry_run: {payload.get('dry_run')}",
            f"output_path: {payload.get('output_path')}",
            "values:",
        ]
        values = payload.get("values", {})
        if isinstance(values, dict) and values:
            for key, value in values.items():
                lines.append(f"  - {key}: {value}")
        else:
            lines.append("  - <none>")
        self.preview.setPlainText("\n".join(lines))

