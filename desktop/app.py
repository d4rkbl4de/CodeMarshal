"""
Desktop GUI application entrypoint.

Local-only, single-focus interface for CodeMarshal.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtWidgets

from .theme import build_stylesheet
from .views import ExportView, HomeView, InvestigateView, ObserveView, PatternsView


class MainWindow(QtWidgets.QMainWindow):
    """Primary application window hosting single-focus views."""

    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        self._start_path = start_path or Path(".").absolute()
        self.setWindowTitle("CodeMarshal")
        self.resize(1100, 720)

        self._stack = QtWidgets.QStackedWidget()
        self.setCentralWidget(self._stack)

        self._views = {
            "home": HomeView(),
            "observe": ObserveView(),
            "investigate": InvestigateView(),
            "patterns": PatternsView(),
            "export": ExportView(),
        }

        for view in self._views.values():
            self._stack.addWidget(view)

        home = self._views["home"]
        home.navigate_requested.connect(self._navigate)

        self._navigate("home")

    def _navigate(self, name: str) -> None:
        if name not in self._views:
            return
        self._stack.setCurrentWidget(self._views[name])


def main(argv: list[str] | None = None, start_path: Path | None = None) -> int:
    """Launch the desktop GUI."""
    argv = argv if argv is not None else sys.argv
    app = QtWidgets.QApplication(argv)
    app.setStyleSheet(build_stylesheet())

    window = MainWindow(start_path=start_path)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
