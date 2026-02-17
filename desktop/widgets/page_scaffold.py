"""Reusable page scaffold with header and responsive split body."""

from __future__ import annotations

from PySide6 import QtCore, QtGui, QtWidgets


class PageScaffold(QtWidgets.QFrame):
    """Layout shell for view header + form panel + results panel."""

    splitter_ratio_changed = QtCore.Signal(float)

    def __init__(
        self,
        parent: QtWidgets.QWidget | None = None,
        *,
        default_ratio: float = 0.42,
        narrow_breakpoint: int = 1260,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("pageScaffold")
        self._ratio = max(0.2, min(0.8, float(default_ratio)))
        self._narrow_breakpoint = max(int(narrow_breakpoint), 900)
        self._orientation = QtCore.Qt.Horizontal
        self._has_shown = False

        root_layout = QtWidgets.QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(10)

        self.header = QtWidgets.QFrame(self)
        self.header.setObjectName("pageHeader")
        self.header_layout = QtWidgets.QHBoxLayout(self.header)
        self.header_layout.setContentsMargins(0, 0, 0, 0)
        self.header_layout.setSpacing(10)
        root_layout.addWidget(self.header)

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        self.splitter.setObjectName("pageSplitter")
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(8)
        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        self.form_panel = QtWidgets.QFrame(self.splitter)
        self.form_panel.setObjectName("formPanel")
        self.form_layout = QtWidgets.QVBoxLayout(self.form_panel)
        self.form_layout.setContentsMargins(14, 14, 14, 14)
        self.form_layout.setSpacing(10)

        self.results_panel = QtWidgets.QFrame(self.splitter)
        self.results_panel.setObjectName("resultsPanel")
        self.results_layout = QtWidgets.QVBoxLayout(self.results_panel)
        self.results_layout.setContentsMargins(14, 14, 14, 14)
        self.results_layout.setSpacing(10)

        self.form_panel.setMinimumWidth(340)
        self.results_panel.setMinimumWidth(340)
        root_layout.addWidget(self.splitter, stretch=1)

    def set_header_widget(self, widget: QtWidgets.QWidget) -> None:
        while self.header_layout.count():
            item = self.header_layout.takeAt(0)
            if item and item.widget():
                item.widget().setParent(None)
        self.header_layout.addWidget(widget, stretch=1)

    def set_splitter_ratio(self, ratio: float) -> None:
        self._ratio = max(0.2, min(0.8, float(ratio)))
        self._apply_sizes()

    def splitter_ratio(self) -> float:
        return self._ratio

    def set_narrow_breakpoint(self, width: int) -> None:
        self._narrow_breakpoint = max(int(width), 900)
        self._sync_orientation()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        super().resizeEvent(event)
        self._sync_orientation()

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        super().showEvent(event)
        if not self._has_shown:
            self._has_shown = True
            self._sync_orientation()
            self._apply_sizes()

    def _sync_orientation(self) -> None:
        desired = (
            QtCore.Qt.Vertical
            if self.width() < self._narrow_breakpoint
            else QtCore.Qt.Horizontal
        )
        if desired == self._orientation:
            return
        self._orientation = desired
        self.splitter.setOrientation(desired)
        self._apply_sizes()

    def _apply_sizes(self) -> None:
        try:
            extent = (
                max(self.splitter.width(), 1)
                if self._orientation == QtCore.Qt.Horizontal
                else max(self.splitter.height(), 1)
            )
            first = max(int(extent * self._ratio), 1)
            second = max(extent - first, 1)
            self.splitter.setSizes([first, second])
        except RuntimeError:
            return

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        try:
            sizes = self.splitter.sizes()
            if len(sizes) < 2:
                return
            total = max(sizes[0] + sizes[1], 1)
            self._ratio = max(0.2, min(0.8, sizes[0] / total))
            self.splitter_ratio_changed.emit(self._ratio)
        except RuntimeError:
            return
