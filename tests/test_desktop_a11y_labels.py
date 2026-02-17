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
from desktop.widgets.comments_panel import CommentsPanel
from desktop.widgets.diff_viewer import DiffViewer
from desktop.widgets.history_sidebar import HistorySidebar
from desktop.widgets.knowledge_canvas import KnowledgeCanvas
from desktop.widgets.marketplace_panel import MarketplacePanel
from desktop.widgets.onboarding_dialog import OnboardingDialog
from desktop.widgets.results_viewer import ResultsViewer
from desktop.widgets.templates_panel import TemplatesPanel


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
    diff_viewer = DiffViewer()
    templates_panel = TemplatesPanel(template_ids=["security.keyword_assignment"])
    marketplace_panel = MarketplacePanel()
    knowledge_canvas = KnowledgeCanvas()
    history_sidebar = HistorySidebar()
    comments_panel = CommentsPanel()

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
        diff_viewer.hunks_tree,
        diff_viewer.diff_text,
        templates_panel.template_search_input,
        templates_panel.template_values_input,
        templates_panel.create_pattern_btn,
        marketplace_panel.marketplace_query_input,
        marketplace_panel.share_pattern_input,
        marketplace_panel.rate_btn,
        knowledge_canvas.edge_type_filter,
        knowledge_canvas.node_query_filter,
        history_sidebar.query_input,
        history_sidebar.timeline_list,
        comments_panel.share_id_input,
        comments_panel.comment_body_input,
        comments_panel.load_btn,
    ]

    for widget in widgets:
        assert widget.accessibleName().strip() != ""
