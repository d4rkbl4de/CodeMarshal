"""Qt bridge for running facade operations on worker threads."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from PySide6 import QtCore

from .runtime_facade import RuntimeFacade
from .worker import BridgeWorker


class GUICommandBridge(QtCore.QObject):
    """Dispatch desktop operations asynchronously with progress signals."""

    operation_started = QtCore.Signal(str)
    operation_progress = QtCore.Signal(str, int, int, str)
    operation_finished = QtCore.Signal(str, object)
    operation_error = QtCore.Signal(str, str, str, str)
    operation_cancelled = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)

    def __init__(
        self,
        facade: RuntimeFacade | None = None,
        parent: QtCore.QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._facade = facade or RuntimeFacade()
        self._thread_pool = QtCore.QThreadPool.globalInstance()
        self._active_workers: dict[str, BridgeWorker] = {}
        self._lock = threading.RLock()

    @property
    def facade(self) -> RuntimeFacade:
        return self._facade

    @property
    def is_busy(self) -> bool:
        with self._lock:
            return bool(self._active_workers)

    def cancel_operation(self, operation: str) -> bool:
        """Request cancellation for a running operation."""
        with self._lock:
            worker = self._active_workers.get(operation)
        if not worker:
            return False
        worker.cancel()
        return True

    def cancel_all(self) -> None:
        """Request cancellation for all active operations."""
        with self._lock:
            workers = list(self._active_workers.values())
        for worker in workers:
            worker.cancel()

    def resolve_session_id(self, session_id: str | None = None) -> str | None:
        return self._facade.resolve_session_id(session_id)

    def list_recent_investigations(self, limit: int = 10) -> list[dict[str, Any]]:
        return self._facade.list_recent_investigations(limit=limit)

    def load_session_metadata(self, session_id: str) -> dict[str, Any] | None:
        return self._facade.load_session_metadata(session_id)

    def _start_worker(self, operation: str, fn: Any, **kwargs: Any) -> None:
        with self._lock:
            if operation in self._active_workers:
                raise RuntimeError(f"Operation already running: {operation}")

            worker = BridgeWorker(operation=operation, fn=fn, **kwargs)
            self._active_workers[operation] = worker
            if len(self._active_workers) == 1:
                self.busy_changed.emit(True)

        worker.signals.started.connect(self.operation_started.emit)
        worker.signals.progress.connect(self.operation_progress.emit)
        worker.signals.finished.connect(self._on_finished)
        worker.signals.error.connect(self._on_error)
        worker.signals.cancelled.connect(self._on_cancelled)
        self._thread_pool.start(worker)

    def _finalize_operation(self, operation: str) -> None:
        with self._lock:
            self._active_workers.pop(operation, None)
            idle = not self._active_workers
        if idle:
            self.busy_changed.emit(False)

    @QtCore.Slot(str, object)
    def _on_finished(self, operation: str, payload: object) -> None:
        self._finalize_operation(operation)
        self.operation_finished.emit(operation, payload)

    @QtCore.Slot(str, str, str, str)
    def _on_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        details: str,
    ) -> None:
        self._finalize_operation(operation)
        self.operation_error.emit(operation, error_type, message, details)

    @QtCore.Slot(str)
    def _on_cancelled(self, operation: str) -> None:
        self._finalize_operation(operation)
        self.operation_cancelled.emit(operation)

    def investigate(
        self,
        path: str | Path,
        scope: str,
        intent: str,
        name: str = "",
        notes: str = "",
    ) -> None:
        self._start_worker(
            "investigate",
            self._facade.run_investigation,
            path=path,
            scope=scope,
            intent=intent,
            name=name,
            notes=notes,
        )

    def observe(
        self,
        path: str | Path,
        eye_types: list[str],
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "observe",
            self._facade.run_observation,
            path=path,
            eye_types=eye_types,
            session_id=session_id,
        )

    def query(
        self,
        question: str,
        question_type: str,
        focus: str | None = None,
        limit: int = 25,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "query",
            self._facade.run_query,
            question=question,
            question_type=question_type,
            focus=focus,
            limit=limit,
            session_id=session_id,
        )

    def pattern_list(
        self,
        category: str | None = None,
        show_disabled: bool = False,
    ) -> None:
        self._start_worker(
            "pattern_list",
            self._facade.run_pattern_list,
            category=category,
            show_disabled=show_disabled,
        )

    def pattern_scan(
        self,
        path: str | Path,
        category: str | None = None,
        pattern_ids: list[str] | None = None,
        glob: str = "*",
        max_files: int = 10000,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "pattern_scan",
            self._facade.run_pattern_scan,
            path=path,
            category=category,
            pattern_ids=pattern_ids,
            glob=glob,
            max_files=max_files,
            session_id=session_id,
        )

    def pattern_search(
        self,
        query: str = "",
        tags: list[str] | None = None,
        severity: str | None = None,
        language: str | None = None,
        limit: int = 20,
    ) -> None:
        self._start_worker(
            "pattern_search",
            self._facade.run_pattern_search,
            query=query,
            tags=tags,
            severity=severity,
            language=language,
            limit=limit,
        )

    def pattern_apply(
        self,
        pattern_ref: str,
        path: str | Path,
        glob: str = "*",
        max_files: int = 10000,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "pattern_apply",
            self._facade.run_pattern_apply,
            pattern_ref=pattern_ref,
            path=path,
            glob=glob,
            max_files=max_files,
            session_id=session_id,
        )

    def pattern_create(
        self,
        template_id: str,
        values: dict[str, str] | None = None,
        pattern_id: str | None = None,
        name: str | None = None,
        description: str = "",
        severity: str | None = None,
        tags: list[str] | None = None,
        languages: list[str] | None = None,
        dry_run: bool = False,
        output_path: str | Path | None = None,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "pattern_create",
            self._facade.run_pattern_create,
            template_id=template_id,
            values=values or {},
            pattern_id=pattern_id,
            name=name,
            description=description,
            severity=severity,
            tags=tags,
            languages=languages,
            dry_run=dry_run,
            output_path=output_path,
            session_id=session_id,
        )

    def pattern_share(
        self,
        pattern_id: str,
        bundle_out: str | Path | None = None,
        include_examples: bool = False,
        session_id: str | None = None,
    ) -> None:
        self._start_worker(
            "pattern_share",
            self._facade.run_pattern_share,
            pattern_id=pattern_id,
            bundle_out=bundle_out,
            include_examples=include_examples,
            session_id=session_id,
        )

    def collaboration_unlock(
        self,
        workspace_id: str,
        passphrase: str,
        initialize: bool = False,
    ) -> None:
        self._start_worker(
            "collaboration_unlock",
            self._facade.run_collaboration_unlock,
            workspace_id=workspace_id,
            passphrase=passphrase,
            initialize=initialize,
        )

    def team_create(
        self,
        name: str,
        owner_user_id: str,
        owner_name: str,
    ) -> None:
        self._start_worker(
            "team_create",
            self._facade.run_team_create,
            name=name,
            owner_user_id=owner_user_id,
            owner_name=owner_name,
        )

    def team_add(
        self,
        team_id: str,
        user_id: str,
        display_name: str,
        role: str,
        added_by: str,
    ) -> None:
        self._start_worker(
            "team_add",
            self._facade.run_team_add,
            team_id=team_id,
            user_id=user_id,
            display_name=display_name,
            role=role,
            added_by=added_by,
        )

    def team_list(
        self,
        limit: int = 100,
    ) -> None:
        self._start_worker(
            "team_list",
            self._facade.run_team_list,
            limit=limit,
        )

    def share_create(
        self,
        session_id: str,
        created_by: str,
        targets: list[dict[str, str]],
        title: str = "",
        summary: str = "",
        passphrase: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        self._start_worker(
            "share_create",
            self._facade.run_share_create,
            session_id=session_id,
            created_by=created_by,
            targets=targets,
            title=title,
            summary=summary,
            passphrase=passphrase,
            workspace_id=workspace_id,
        )

    def share_list(
        self,
        session_id: str | None = None,
        team_id: str | None = None,
        limit: int = 100,
    ) -> None:
        self._start_worker(
            "share_list",
            self._facade.run_share_list,
            session_id=session_id,
            team_id=team_id,
            limit=limit,
        )

    def share_revoke(
        self,
        share_id: str,
        revoked_by: str,
    ) -> None:
        self._start_worker(
            "share_revoke",
            self._facade.run_share_revoke,
            share_id=share_id,
            revoked_by=revoked_by,
        )

    def share_resolve(
        self,
        share_id: str,
        accessor_id: str,
        passphrase: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        self._start_worker(
            "share_resolve",
            self._facade.run_share_resolve,
            share_id=share_id,
            accessor_id=accessor_id,
            passphrase=passphrase,
            workspace_id=workspace_id,
        )

    def comment_add(
        self,
        share_id: str,
        author_id: str,
        author_name: str,
        body: str,
        parent_comment_id: str | None = None,
        passphrase: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        self._start_worker(
            "comment_add",
            self._facade.run_comment_add,
            share_id=share_id,
            author_id=author_id,
            author_name=author_name,
            body=body,
            parent_comment_id=parent_comment_id,
            passphrase=passphrase,
            workspace_id=workspace_id,
        )

    def comment_list(
        self,
        share_id: str,
        thread_root_id: str | None = None,
        limit: int = 200,
        passphrase: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        self._start_worker(
            "comment_list",
            self._facade.run_comment_list,
            share_id=share_id,
            thread_root_id=thread_root_id,
            limit=limit,
            passphrase=passphrase,
            workspace_id=workspace_id,
        )

    def comment_resolve(
        self,
        comment_id: str,
        resolver_id: str,
        passphrase: str | None = None,
        workspace_id: str | None = None,
    ) -> None:
        self._start_worker(
            "comment_resolve",
            self._facade.run_comment_resolve,
            comment_id=comment_id,
            resolver_id=resolver_id,
            passphrase=passphrase,
            workspace_id=workspace_id,
        )

    def preview_export(
        self,
        session_id: str,
        format_name: str,
        include_notes: bool,
        include_patterns: bool,
        preview_limit: int | None = 4000,
    ) -> None:
        self._start_worker(
            "export_preview",
            self._facade.preview_export,
            session_id=session_id,
            format_name=format_name,
            include_notes=include_notes,
            include_patterns=include_patterns,
            preview_limit=preview_limit,
        )

    def export(
        self,
        session_id: str,
        format_name: str,
        output_path: str | Path,
        include_notes: bool,
        include_patterns: bool,
        include_evidence: bool,
    ) -> None:
        self._start_worker(
            "export",
            self._facade.run_export,
            session_id=session_id,
            format_name=format_name,
            output_path=output_path,
            include_notes=include_notes,
            include_patterns=include_patterns,
            include_evidence=include_evidence,
        )

    def history(
        self,
        session_id: str | None = None,
        query: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> None:
        self._start_worker(
            "history",
            self._facade.run_history,
            session_id=session_id,
            query=query,
            from_date=from_date,
            to_date=to_date,
            event_type=event_type,
            limit=limit,
        )

    def graph(
        self,
        session_id: str | None = None,
        focus: str | None = None,
        depth: int = 2,
        edge_type: str | None = None,
        limit: int = 200,
    ) -> None:
        self._start_worker(
            "graph",
            self._facade.run_graph,
            session_id=session_id,
            focus=focus,
            depth=depth,
            edge_type=edge_type,
            limit=limit,
        )

    def recommendations(
        self,
        session_id: str | None = None,
        limit: int = 10,
        category: str | None = None,
        refresh: bool = False,
    ) -> None:
        self._start_worker(
            "recommendations",
            self._facade.run_recommendations,
            session_id=session_id,
            limit=limit,
            category=category,
            refresh=refresh,
        )
