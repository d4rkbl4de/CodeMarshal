"""Diff viewer dialog with line-level sections and fold controls."""

from __future__ import annotations

from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .a11y import apply_accessible


class _DiffHighlighter(QtGui.QSyntaxHighlighter):
    """Minimal syntax highlighter for unified diff text."""

    def __init__(self, document: QtGui.QTextDocument) -> None:
        super().__init__(document)
        self._fmt_added = QtGui.QTextCharFormat()
        self._fmt_added.setForeground(QtGui.QColor("#2E8B57"))
        self._fmt_removed = QtGui.QTextCharFormat()
        self._fmt_removed.setForeground(QtGui.QColor("#B14646"))
        self._fmt_header = QtGui.QTextCharFormat()
        self._fmt_header.setForeground(QtGui.QColor("#4A78A3"))
        self._fmt_header.setFontWeight(QtGui.QFont.Bold)

    def highlightBlock(self, text: str) -> None:
        if text.startswith("+") and not text.startswith("+++"):
            self.setFormat(0, len(text), self._fmt_added)
            return
        if text.startswith("-") and not text.startswith("---"):
            self.setFormat(0, len(text), self._fmt_removed)
            return
        if text.startswith("@@") or text.startswith("---") or text.startswith("+++"):
            self.setFormat(0, len(text), self._fmt_header)


class DiffViewer(QtWidgets.QDialog):
    """Dialog for viewing unified diff content with foldable hunks."""

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Diff Viewer")
        self.resize(980, 680)
        self._hunk_map: dict[int, str] = {}
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.path_label = QtWidgets.QLabel("Path: not set")
        apply_accessible(self.path_label, name="Diff file path label")
        layout.addWidget(self.path_label)

        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal, self)
        layout.addWidget(splitter, stretch=1)

        left = QtWidgets.QWidget(splitter)
        left_layout = QtWidgets.QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(6)

        self.hunks_tree = QtWidgets.QTreeWidget()
        self.hunks_tree.setHeaderLabels(["Section", "Lines"])
        self.hunks_tree.itemSelectionChanged.connect(self._on_selection_changed)
        apply_accessible(self.hunks_tree, name="Diff hunk tree")
        left_layout.addWidget(self.hunks_tree, stretch=1)

        fold_row = QtWidgets.QHBoxLayout()
        self.fold_all_btn = QtWidgets.QPushButton("Fold All")
        self.unfold_all_btn = QtWidgets.QPushButton("Unfold All")
        self.fold_all_btn.clicked.connect(self.hunks_tree.collapseAll)
        self.unfold_all_btn.clicked.connect(self.hunks_tree.expandAll)
        fold_row.addWidget(self.fold_all_btn)
        fold_row.addWidget(self.unfold_all_btn)
        fold_row.addStretch(1)
        left_layout.addLayout(fold_row)

        right = QtWidgets.QWidget(splitter)
        right_layout = QtWidgets.QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        self.diff_text = QtWidgets.QPlainTextEdit()
        self.diff_text.setReadOnly(True)
        apply_accessible(self.diff_text, name="Unified diff content")
        self._highlighter = _DiffHighlighter(self.diff_text.document())
        right_layout.addWidget(self.diff_text, stretch=1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setSizes([320, 640])

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def set_unified_diff(self, diff_text: str, file_path: Path | str | None = None) -> None:
        if file_path:
            self.path_label.setText(f"Path: {Path(file_path)}")
        else:
            self.path_label.setText("Path: not set")
        self.diff_text.setPlainText(str(diff_text or ""))
        self._populate_hunks(str(diff_text or ""))

    def _populate_hunks(self, content: str) -> None:
        self.hunks_tree.clear()
        self._hunk_map.clear()
        lines = content.splitlines()
        current_header = "File"
        current_buffer: list[str] = []
        section_idx = 0

        def _flush() -> None:
            nonlocal section_idx, current_buffer, current_header
            if not current_buffer:
                return
            item = QtWidgets.QTreeWidgetItem([current_header, str(len(current_buffer))])
            self.hunks_tree.addTopLevelItem(item)
            self._hunk_map[section_idx] = "\n".join(current_buffer)
            section_idx += 1
            current_buffer = []

        for line in lines:
            if line.startswith("@@"):
                _flush()
                current_header = line
                current_buffer.append(line)
                continue
            if line.startswith("---") or line.startswith("+++"):
                if current_buffer:
                    current_buffer.append(line)
                else:
                    current_header = "File Header"
                    current_buffer.append(line)
                continue
            current_buffer.append(line)
        _flush()

        if self.hunks_tree.topLevelItemCount() > 0:
            self.hunks_tree.setCurrentItem(self.hunks_tree.topLevelItem(0))
            self.hunks_tree.expandAll()

    def _on_selection_changed(self) -> None:
        selected = self.hunks_tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        index = self.hunks_tree.indexOfTopLevelItem(item)
        if index < 0:
            return
        payload = self._hunk_map.get(index, "")
        if payload:
            self.diff_text.setPlainText(payload)

