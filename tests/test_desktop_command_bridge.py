"""Tests for desktop GUI command bridge threading behavior."""

from __future__ import annotations

import time

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtCore, QtWidgets

from desktop.core.command_bridge import GUICommandBridge
from desktop.core.exceptions import OperationCancelledError


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


class _FakeFacade:
    def run_observation(
        self,
        path,
        eye_types,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del path, eye_types, cancel_event
        if callable(progress_callback):
            progress_callback(1, 2, "step 1")
            progress_callback(2, 2, "step 2")
        return {"session_id": session_id or "fake-session", "success": True}

    def run_pattern_scan(
        self,
        path,
        category=None,
        pattern_ids=None,
        glob="*",
        max_files=10000,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del path, category, pattern_ids, glob, max_files, session_id
        for _ in range(50):
            if cancel_event is not None and cancel_event.is_set():
                raise OperationCancelledError("cancelled")
            if callable(progress_callback):
                progress_callback(1, 1, "running")
            time.sleep(0.01)
        return {"matches_found": 0}

    def run_pattern_search(
        self,
        query="",
        tags=None,
        severity=None,
        language=None,
        limit=20,
        progress_callback=None,
        cancel_event=None,
    ):
        del query, tags, severity, language, limit, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "total_count": 1, "patterns": [{"pattern_id": "p1"}]}

    def run_pattern_apply(
        self,
        pattern_ref,
        path,
        glob="*",
        max_files=10000,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del pattern_ref, path, glob, max_files, session_id, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "pattern_id": "p1", "matches_found": 0}

    def run_pattern_create(
        self,
        template_id,
        values=None,
        pattern_id=None,
        name=None,
        description="",
        severity=None,
        tags=None,
        languages=None,
        dry_run=False,
        output_path=None,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del (
            template_id,
            values,
            pattern_id,
            name,
            description,
            severity,
            tags,
            languages,
            dry_run,
            output_path,
            session_id,
            cancel_event,
        )
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "pattern_id": "created"}

    def run_pattern_share(
        self,
        pattern_id,
        bundle_out=None,
        include_examples=False,
        session_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del pattern_id, bundle_out, include_examples, session_id, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "package_id": "pkg1"}

    def run_collaboration_unlock(
        self,
        workspace_id,
        passphrase,
        initialize=False,
        progress_callback=None,
        cancel_event=None,
    ):
        del workspace_id, passphrase, initialize, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "unlocked": True}

    def run_team_create(
        self,
        name,
        owner_user_id,
        owner_name,
        progress_callback=None,
        cancel_event=None,
    ):
        del name, owner_user_id, owner_name, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "team": {"team_id": "team_1"}}

    def run_team_add(
        self,
        team_id,
        user_id,
        display_name,
        role,
        added_by,
        progress_callback=None,
        cancel_event=None,
    ):
        del team_id, user_id, display_name, role, added_by, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True}

    def run_team_list(
        self,
        limit=100,
        progress_callback=None,
        cancel_event=None,
    ):
        del limit, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "count": 1, "teams": [{"team_id": "team_1"}]}

    def run_share_create(
        self,
        session_id,
        created_by,
        targets,
        title="",
        summary="",
        passphrase=None,
        workspace_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del (
            session_id,
            created_by,
            targets,
            title,
            summary,
            passphrase,
            workspace_id,
            cancel_event,
        )
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "share": {"share_id": "share_1"}}

    def run_share_list(
        self,
        session_id=None,
        team_id=None,
        limit=100,
        progress_callback=None,
        cancel_event=None,
    ):
        del session_id, team_id, limit, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "count": 1, "shares": [{"share_id": "share_1"}]}

    def run_share_revoke(
        self,
        share_id,
        revoked_by,
        progress_callback=None,
        cancel_event=None,
    ):
        del share_id, revoked_by, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "revoked": True}

    def run_share_resolve(
        self,
        share_id,
        accessor_id,
        passphrase=None,
        workspace_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del share_id, accessor_id, passphrase, workspace_id, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "payload": {"session_id": "session_1"}}

    def run_comment_add(
        self,
        share_id,
        author_id,
        author_name,
        body,
        parent_comment_id=None,
        passphrase=None,
        workspace_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del (
            share_id,
            author_id,
            author_name,
            body,
            parent_comment_id,
            passphrase,
            workspace_id,
            cancel_event,
        )
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True}

    def run_comment_list(
        self,
        share_id,
        thread_root_id=None,
        limit=200,
        passphrase=None,
        workspace_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del share_id, thread_root_id, limit, passphrase, workspace_id, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "count": 1, "comments": [{"comment_id": "c1"}]}

    def run_comment_resolve(
        self,
        comment_id,
        resolver_id,
        passphrase=None,
        workspace_id=None,
        progress_callback=None,
        cancel_event=None,
    ):
        del comment_id, resolver_id, passphrase, workspace_id, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True}

    def list_recent_investigations(self, limit=10):
        del limit
        return []

    def load_session_metadata(self, session_id):
        return {"id": session_id}

    def resolve_session_id(self, session_id=None):
        return session_id

    def run_history(
        self,
        session_id=None,
        query=None,
        from_date=None,
        to_date=None,
        event_type=None,
        limit=100,
        progress_callback=None,
        cancel_event=None,
    ):
        del session_id, query, from_date, to_date, event_type, limit, cancel_event
        if callable(progress_callback):
            progress_callback(1, 2, "loading")
            progress_callback(2, 2, "done")
        return {"success": True, "count": 1, "events": [{"event_type": "query"}]}

    def run_graph(
        self,
        session_id=None,
        focus=None,
        depth=2,
        edge_type=None,
        limit=200,
        progress_callback=None,
        cancel_event=None,
    ):
        del session_id, focus, depth, edge_type, limit, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {"success": True, "summary": {"node_count": 1, "edge_count": 0}}

    def run_recommendations(
        self,
        session_id=None,
        limit=10,
        category=None,
        refresh=False,
        progress_callback=None,
        cancel_event=None,
    ):
        del session_id, limit, category, refresh, cancel_event
        if callable(progress_callback):
            progress_callback(1, 1, "done")
        return {
            "success": True,
            "count": 1,
            "recommendations": [{"title": "Run query", "confidence": 0.8}],
        }


def test_bridge_emits_finished_signal_for_observe() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "observe":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.observe(path=".", eye_types=["file_sight"], session_id="test-session")

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["session_id"] == "test-session"


def test_bridge_cancel_operation_emits_cancelled_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, bool] = {"cancelled": False}

    def on_cancelled(operation: str) -> None:
        if operation != "pattern_scan":
            return
        received["cancelled"] = True
        loop.quit()

    bridge.operation_cancelled.connect(on_cancelled)
    bridge.pattern_scan(path=".")

    QtCore.QTimer.singleShot(40, lambda: bridge.cancel_operation("pattern_scan"))
    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert received["cancelled"] is True


def test_bridge_history_emits_finished_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "history":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.history(session_id="s1")

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["success"] is True


def test_bridge_pattern_search_emits_finished_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "pattern_search":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.pattern_search(query="security")

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["success"] is True


def test_bridge_team_list_emits_finished_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "team_list":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.team_list(limit=10)

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["success"] is True


def test_bridge_share_resolve_emits_finished_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "share_resolve":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.share_resolve(
        share_id="share_1",
        accessor_id="team_1",
        passphrase="strong-passphrase",
        workspace_id="default",
    )

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["success"] is True
    assert payload["payload"]["session_id"] == "session_1"


def test_bridge_comment_list_emits_finished_signal() -> None:
    _ensure_qt_app()
    bridge = GUICommandBridge(facade=_FakeFacade())

    loop = QtCore.QEventLoop()
    received: dict[str, object] = {}

    def on_finished(operation: str, payload: object) -> None:
        if operation != "comment_list":
            return
        received["payload"] = payload
        loop.quit()

    bridge.operation_finished.connect(on_finished)
    bridge.comment_list(
        share_id="share_1",
        passphrase="strong-passphrase",
        workspace_id="default",
    )

    QtCore.QTimer.singleShot(3000, loop.quit)
    loop.exec()

    assert "payload" in received
    payload = received["payload"]
    assert isinstance(payload, dict)
    assert payload["success"] is True
    assert payload["count"] == 1
