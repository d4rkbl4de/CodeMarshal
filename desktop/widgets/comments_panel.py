"""Threaded comments panel for collaboration workflows."""

from __future__ import annotations

import os
from typing import Any

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible, clear_invalid, mark_invalid


class CommentsPanel(QtWidgets.QGroupBox):
    """Panel for encrypted threaded comments."""

    def __init__(
        self,
        command_bridge: Any | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__("Comments", parent)
        self._bridge = None
        self._comments: list[dict[str, Any]] = []
        self._build_ui()
        if command_bridge is not None:
            self.set_command_bridge(command_bridge)

    def _build_ui(self) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.validation_label = QtWidgets.QLabel("")
        self.validation_label.setObjectName("validationError")
        self.validation_label.setVisible(False)
        self.validation_label.setWordWrap(True)
        layout.addWidget(self.validation_label)

        env_row = QtWidgets.QHBoxLayout()
        self.passphrase_env_input = QtWidgets.QLineEdit("CM_PASS")
        self.workspace_id_input = QtWidgets.QLineEdit("default")
        self.lock_state_label = QtWidgets.QLabel("Locked")
        apply_accessible(self.passphrase_env_input, name="Comments passphrase env var")
        apply_accessible(self.workspace_id_input, name="Comments workspace id")
        apply_accessible(self.lock_state_label, name="Comments workspace lock state")
        env_row.addWidget(QtWidgets.QLabel("Passphrase Env:"))
        env_row.addWidget(self.passphrase_env_input)
        env_row.addWidget(QtWidgets.QLabel("Workspace:"))
        env_row.addWidget(self.workspace_id_input)
        env_row.addWidget(self.lock_state_label)
        layout.addLayout(env_row)

        header_row = QtWidgets.QHBoxLayout()
        self.share_id_input = QtWidgets.QLineEdit()
        self.share_id_input.setPlaceholderText("Share ID")
        self.author_id_input = QtWidgets.QLineEdit()
        self.author_id_input.setPlaceholderText("Author ID")
        self.author_name_input = QtWidgets.QLineEdit()
        self.author_name_input.setPlaceholderText("Author Name")
        apply_accessible(self.share_id_input, name="Comments share id")
        apply_accessible(self.author_id_input, name="Comments author id")
        apply_accessible(self.author_name_input, name="Comments author name")
        header_row.addWidget(self.share_id_input, stretch=2)
        header_row.addWidget(self.author_id_input, stretch=1)
        header_row.addWidget(self.author_name_input, stretch=1)
        layout.addLayout(header_row)

        self.comments_tree = QtWidgets.QTreeWidget()
        self.comments_tree.setHeaderLabels(["Comment", "Author", "Status", "ID"])
        self.comments_tree.setRootIsDecorated(True)
        self.comments_tree.setAlternatingRowColors(True)
        apply_accessible(self.comments_tree, name="Threaded comments list")
        layout.addWidget(self.comments_tree, stretch=1)

        editor_row = QtWidgets.QHBoxLayout()
        self.parent_comment_input = QtWidgets.QLineEdit()
        self.parent_comment_input.setPlaceholderText("Parent comment ID (optional)")
        self.comment_body_input = QtWidgets.QLineEdit()
        self.comment_body_input.setPlaceholderText("Add comment body")
        apply_accessible(self.parent_comment_input, name="Comment parent id")
        apply_accessible(self.comment_body_input, name="Comment body")
        editor_row.addWidget(self.parent_comment_input, stretch=1)
        editor_row.addWidget(self.comment_body_input, stretch=3)
        layout.addLayout(editor_row)

        resolve_row = QtWidgets.QHBoxLayout()
        self.resolve_comment_id_input = QtWidgets.QLineEdit()
        self.resolve_comment_id_input.setPlaceholderText("Comment ID to resolve")
        self.resolver_id_input = QtWidgets.QLineEdit()
        self.resolver_id_input.setPlaceholderText("Resolver ID")
        apply_accessible(self.resolve_comment_id_input, name="Resolve comment id")
        apply_accessible(self.resolver_id_input, name="Resolve comment actor id")
        resolve_row.addWidget(self.resolve_comment_id_input, stretch=2)
        resolve_row.addWidget(self.resolver_id_input, stretch=1)
        layout.addLayout(resolve_row)

        actions = QtWidgets.QHBoxLayout()
        self.load_btn = QtWidgets.QPushButton("Load")
        self.add_btn = QtWidgets.QPushButton("Add")
        self.resolve_btn = QtWidgets.QPushButton("Resolve")
        self.refresh_lock_btn = QtWidgets.QPushButton("Refresh Lock")
        self.load_btn.clicked.connect(self._on_load)
        self.add_btn.clicked.connect(self._on_add)
        self.resolve_btn.clicked.connect(self._on_resolve)
        self.refresh_lock_btn.clicked.connect(self._refresh_lock_state)
        apply_accessible(self.load_btn, name="Load comments")
        apply_accessible(self.add_btn, name="Add comment")
        apply_accessible(self.resolve_btn, name="Resolve comment")
        apply_accessible(self.refresh_lock_btn, name="Refresh comments lock state")
        actions.addWidget(self.load_btn)
        actions.addWidget(self.add_btn)
        actions.addWidget(self.resolve_btn)
        actions.addWidget(self.refresh_lock_btn)
        actions.addStretch(1)
        layout.addLayout(actions)
        self._refresh_lock_state()

    def set_command_bridge(self, command_bridge: Any) -> None:
        if self._bridge is command_bridge:
            return
        self._bridge = command_bridge
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)

    def _refresh_lock_state(self) -> None:
        passphrase = self._passphrase()
        self.lock_state_label.setText("Unlocked" if passphrase else "Locked")

    def _passphrase(self) -> str | None:
        env_name = self.passphrase_env_input.text().strip()
        if not env_name:
            return None
        value = os.environ.get(env_name)
        if value is None:
            return None
        value = value.strip()
        return value or None

    def _set_validation(self, message: str, widget: QtWidgets.QWidget | None = None) -> None:
        mark_invalid(widget, self.validation_label, message)

    def _clear_validation(self) -> None:
        clear_invalid(
            (
                self.share_id_input,
                self.author_id_input,
                self.author_name_input,
                self.parent_comment_input,
                self.comment_body_input,
                self.resolve_comment_id_input,
                self.resolver_id_input,
                self.passphrase_env_input,
            ),
            self.validation_label,
        )

    def _common_security_args(self) -> tuple[str, str, str]:
        share_id = self.share_id_input.text().strip()
        workspace_id = self.workspace_id_input.text().strip() or "default"
        passphrase = self._passphrase()
        if not share_id:
            raise ValueError("Share ID is required for comments.")
        if not passphrase:
            raise ValueError("Passphrase environment variable is missing or empty.")
        return share_id, workspace_id, passphrase

    def _on_load(self) -> None:
        if self._bridge is None:
            return
        try:
            share_id, workspace_id, passphrase = self._common_security_args()
            self._clear_validation()
            self._bridge.comment_list(
                share_id=share_id,
                thread_root_id=None,
                limit=200,
                passphrase=passphrase,
                workspace_id=workspace_id,
            )
        except ValueError as exc:
            self._set_validation(str(exc), self.share_id_input)
        except RuntimeError as exc:
            self._set_validation(str(exc))

    def _on_add(self) -> None:
        if self._bridge is None:
            return
        try:
            share_id, workspace_id, passphrase = self._common_security_args()
            author_id = self.author_id_input.text().strip()
            author_name = self.author_name_input.text().strip() or author_id
            body = self.comment_body_input.text().strip()
            if not author_id:
                raise ValueError("Author ID is required.")
            if not body:
                raise ValueError("Comment body is required.")
            self._clear_validation()
            self._bridge.comment_add(
                share_id=share_id,
                author_id=author_id,
                author_name=author_name,
                body=body,
                parent_comment_id=self.parent_comment_input.text().strip() or None,
                passphrase=passphrase,
                workspace_id=workspace_id,
            )
        except ValueError as exc:
            self._set_validation(str(exc), self.comment_body_input)
        except RuntimeError as exc:
            self._set_validation(str(exc))

    def _on_resolve(self) -> None:
        if self._bridge is None:
            return
        try:
            comment_id = self.resolve_comment_id_input.text().strip()
            resolver_id = self.resolver_id_input.text().strip() or self.author_id_input.text().strip()
            workspace_id = self.workspace_id_input.text().strip() or "default"
            passphrase = self._passphrase()
            if not comment_id:
                raise ValueError("Comment ID is required for resolve.")
            if not resolver_id:
                raise ValueError("Resolver ID is required for resolve.")
            if not passphrase:
                raise ValueError("Passphrase environment variable is missing or empty.")
            self._clear_validation()
            self._bridge.comment_resolve(
                comment_id=comment_id,
                resolver_id=resolver_id,
                passphrase=passphrase,
                workspace_id=workspace_id,
            )
        except ValueError as exc:
            self._set_validation(str(exc), self.resolve_comment_id_input)
        except RuntimeError as exc:
            self._set_validation(str(exc))

    def _on_operation_started(self, operation: str) -> None:
        if operation not in {"comment_add", "comment_list", "comment_resolve"}:
            return
        self.load_btn.setEnabled(False)
        self.add_btn.setEnabled(False)
        self.resolve_btn.setEnabled(False)

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        if operation not in {"comment_add", "comment_list", "comment_resolve"}:
            return
        self.load_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.resolve_btn.setEnabled(True)
        data = payload if isinstance(payload, dict) else {}
        if operation == "comment_list":
            comments = data.get("comments", [])
            self._comments = comments if isinstance(comments, list) else []
            self._render_comments()
        elif operation in {"comment_add", "comment_resolve"}:
            # Refresh list after mutations using current context.
            self._on_load()

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        _details: str,
    ) -> None:
        if operation not in {"comment_add", "comment_list", "comment_resolve"}:
            return
        self.load_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.resolve_btn.setEnabled(True)
        self._set_validation(f"{error_type}: {message}")

    def _on_operation_cancelled(self, operation: str) -> None:
        if operation not in {"comment_add", "comment_list", "comment_resolve"}:
            return
        self.load_btn.setEnabled(True)
        self.add_btn.setEnabled(True)
        self.resolve_btn.setEnabled(True)

    def _render_comments(self) -> None:
        self.comments_tree.clear()
        by_id: dict[str, QtWidgets.QTreeWidgetItem] = {}
        for item in self._comments:
            if not isinstance(item, dict):
                continue
            comment_id = str(item.get("comment_id") or "")
            author = str(item.get("author_id") or "")
            status = str(item.get("status") or "active")
            body = str(item.get("body") or "")
            parent_id = str(item.get("parent_comment_id") or "")
            row = QtWidgets.QTreeWidgetItem([body[:96], author, status, comment_id])
            row.setToolTip(0, body)
            by_id[comment_id] = row
            if parent_id and parent_id in by_id:
                by_id[parent_id].addChild(row)
            else:
                self.comments_tree.addTopLevelItem(row)
        self.comments_tree.expandAll()

