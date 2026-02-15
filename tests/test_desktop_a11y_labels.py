"""Tests for desktop accessibility labels on key widgets."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from desktop.views.export import ExportView
from desktop.views.home import HomeView
from desktop.views.investigate import InvestigateView
from desktop.views.observe import ObserveView
from desktop.views.patterns import PatternsView
from desktop.widgets.onboarding_dialog import OnboardingDialog
from desktop.widgets.results_viewer import ResultsViewer


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


class _FakeBridge(QtCore.QObject):
    operation_started = QtCore.Signal(str)
    operation_progress = QtCore.Signal(str, int, int, str)
    operation_finished = QtCore.Signal(str, object)
    operation_error = QtCore.Signal(str, str, str, str)
    operation_cancelled = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)

    def observe(self, **_kwargs):
        return

    def investigate(self, **_kwargs):
        return

    def query(self, **_kwargs):
        return

    def pattern_list(self, **_kwargs):
        return

    def pattern_scan(self, **_kwargs):
        return

    def preview_export(self, **_kwargs):
        return

    def export(self, **_kwargs):
        return

    def cancel_operation(self, _name: str):
        return


def test_key_views_have_accessible_names() -> None:
    _ensure_qt_app()
    bridge = _FakeBridge()

    home = HomeView()
    observe = ObserveView(command_bridge=bridge)
    investigate = InvestigateView(command_bridge=bridge)
    patterns = PatternsView(command_bridge=bridge)
    export = ExportView(command_bridge=bridge)
    onboarding = OnboardingDialog(default_path="", show_hints=True)
    viewer = ResultsViewer()

    widgets = [
        home.path_input,
        home.recent_paths,
        home.recent_table,
        observe.path_input,
        observe.session_combo,
        observe.start_btn,
        investigate.path_input,
        investigate.question_input,
        investigate.start_btn,
        patterns.path_input,
        patterns.pattern_table,
        patterns.scan_btn,
        export.session_combo,
        export.output_input,
        export.export_btn,
        onboarding.path_input,
        onboarding.first_action_combo,
        onboarding.start_btn,
        viewer.copy_summary_btn,
        viewer.copy_raw_btn,
    ]

    for widget in widgets:
        assert widget.accessibleName().strip() != ""
