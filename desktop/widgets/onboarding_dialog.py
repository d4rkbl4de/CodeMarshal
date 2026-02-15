"""First-run onboarding dialog for desktop GUI users."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6 import QtGui, QtWidgets

from .a11y import apply_accessible


class OnboardingDialog(QtWidgets.QDialog):
    """Collect quick-start preferences for first-time GUI usage."""

    def __init__(
        self,
        default_path: str = "",
        *,
        show_hints: bool = True,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Welcome to CodeMarshal")
        self.setModal(True)
        self.resize(640, 420)
        self._build_ui(default_path=default_path, show_hints=show_hints)

    def _build_ui(self, default_path: str, show_hints: bool) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)

        intro = QtWidgets.QLabel("Set up your first investigation in under a minute.")
        intro.setObjectName("subtitle")
        layout.addWidget(intro)

        steps = QtWidgets.QGroupBox("Getting Started")
        steps_layout = QtWidgets.QVBoxLayout(steps)
        for text in [
            "1. Choose your project path.",
            "2. Pick your first workflow.",
            "3. Keep context hints enabled while learning.",
        ]:
            label = QtWidgets.QLabel(text)
            label.setWordWrap(True)
            steps_layout.addWidget(label)
        layout.addWidget(steps)

        form_group = QtWidgets.QGroupBox("Setup")
        form = QtWidgets.QFormLayout(form_group)

        path_row = QtWidgets.QHBoxLayout()
        self.path_input = QtWidgets.QLineEdit(default_path)
        self.path_input.setPlaceholderText("Choose a file or directory")
        apply_accessible(
            self.path_input,
            name="Onboarding project path",
            description="Path to the project or file to analyze first.",
        )
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.browse_btn.clicked.connect(self._on_browse)
        apply_accessible(
            self.browse_btn,
            name="Browse project path",
            description="Open file or folder chooser for the project path.",
        )
        path_row.addWidget(self.path_input, stretch=1)
        path_row.addWidget(self.browse_btn)
        form.addRow("Project Path:", path_row)

        self.first_action_combo = QtWidgets.QComboBox()
        self.first_action_combo.addItem("Investigate", "investigate")
        self.first_action_combo.addItem("Observe", "observe")
        apply_accessible(
            self.first_action_combo,
            name="Onboarding first action",
            description="Select the first workflow opened after onboarding.",
        )
        form.addRow("First Action:", self.first_action_combo)

        self.hints_check = QtWidgets.QCheckBox("Show contextual hints")
        self.hints_check.setChecked(bool(show_hints))
        apply_accessible(
            self.hints_check,
            name="Show contextual hints",
            description="Enable helper guidance panels throughout the GUI.",
        )
        form.addRow("", self.hints_check)

        self.dont_show_again_check = QtWidgets.QCheckBox("Don't show onboarding again")
        self.dont_show_again_check.setChecked(False)
        apply_accessible(
            self.dont_show_again_check,
            name="Disable onboarding",
            description="When checked, onboarding will not appear on startup again.",
        )
        form.addRow("", self.dont_show_again_check)

        layout.addWidget(form_group)
        layout.addStretch(1)

        buttons = QtWidgets.QHBoxLayout()
        self.skip_btn = QtWidgets.QPushButton("Skip for Now")
        self.skip_btn.clicked.connect(self.reject)
        apply_accessible(
            self.skip_btn,
            name="Skip onboarding",
            description="Close onboarding without applying a guided start.",
        )
        self.start_btn = QtWidgets.QPushButton("Start Guided")
        self.start_btn.setProperty("variant", "primary")
        self.start_btn.clicked.connect(self.accept)
        apply_accessible(
            self.start_btn,
            name="Start guided onboarding",
            description="Apply selected onboarding choices and continue to the app.",
        )
        buttons.addStretch(1)
        buttons.addWidget(self.skip_btn)
        buttons.addWidget(self.start_btn)
        layout.addLayout(buttons)

        self.setTabOrder(self.path_input, self.browse_btn)
        self.setTabOrder(self.browse_btn, self.first_action_combo)
        self.setTabOrder(self.first_action_combo, self.hints_check)
        self.setTabOrder(self.hints_check, self.dont_show_again_check)
        self.setTabOrder(self.dont_show_again_check, self.skip_btn)
        self.setTabOrder(self.skip_btn, self.start_btn)

    def _on_browse(self) -> None:
        start = self.path_input.text().strip() or str(Path(".").resolve())
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Choose Project", start)
        if not path:
            file_path, _filter = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Choose File",
                start,
                "All Files (*.*)",
            )
            path = file_path
        if path:
            self.path_input.setText(path)

    def result_payload(self) -> dict[str, Any]:
        path = self.path_input.text().strip()
        return {
            "accepted": self.result() == QtWidgets.QDialog.Accepted,
            "path": path or None,
            "first_action": str(self.first_action_combo.currentData() or "investigate"),
            "show_hints": bool(self.hints_check.isChecked()),
            "dont_show_again": bool(self.dont_show_again_check.isChecked()),
        }

    def showEvent(self, event: QtGui.QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        self.path_input.setFocus()
