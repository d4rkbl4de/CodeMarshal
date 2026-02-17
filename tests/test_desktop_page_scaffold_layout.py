"""Tests for shared desktop page scaffold layout usage."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from desktop.views.export import ExportView
from desktop.views.home import HomeView
from desktop.views.investigate import InvestigateView
from desktop.views.observe import ObserveView
from desktop.views.patterns import PatternsView
from desktop.widgets import ActionStrip, PageScaffold, SectionHeader


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


def test_workflow_views_use_shared_scaffold() -> None:
    app = _ensure_qt_app()
    bridge = _FakeBridge()

    views = [
        ObserveView(command_bridge=bridge),
        InvestigateView(command_bridge=bridge),
        PatternsView(command_bridge=bridge),
        ExportView(command_bridge=bridge),
    ]
    for view in views:
        view.show()
        app.processEvents()
        try:
            assert isinstance(view.page_scaffold, PageScaffold)
            assert len(view.findChildren(SectionHeader)) >= 1
            assert len(view.findChildren(ActionStrip)) == 1
            assert isinstance(view.page_scaffold.splitter, QtWidgets.QSplitter)
        finally:
            view.close()


def test_home_view_uses_shared_scaffold() -> None:
    app = _ensure_qt_app()
    home = HomeView()
    home.show()
    app.processEvents()
    try:
        assert isinstance(home.page_scaffold, PageScaffold)
        assert len(home.findChildren(SectionHeader)) >= 1
        assert isinstance(home.page_scaffold.splitter, QtWidgets.QSplitter)
    finally:
        home.close()


def test_page_scaffold_switches_to_vertical_on_narrow_width() -> None:
    app = _ensure_qt_app()
    view = InvestigateView(command_bridge=_FakeBridge())
    view.page_scaffold.set_narrow_breakpoint(900)
    view.resize(1500, 900)
    view.show()
    app.processEvents()
    try:
        view.resize(1500, 900)
        app.processEvents()
        assert view.page_scaffold.splitter.orientation() == QtCore.Qt.Horizontal

        view.resize(760, 900)
        app.processEvents()
        assert view.page_scaffold.splitter.orientation() == QtCore.Qt.Vertical
    finally:
        view.close()
