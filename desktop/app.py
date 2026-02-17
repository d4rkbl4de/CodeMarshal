"""Desktop GUI application entrypoint."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6 import QtCore, QtGui, QtWidgets

from .core import GUICommandBridge, RuntimeFacade, SessionManager, ViewStateBinder
from .ui.themes import build_stylesheet, list_theme_previews
from .views import (
    ExportView,
    HomeView,
    InvestigateView,
    KnowledgeView,
    ObserveView,
    PatternsView,
)
from .widgets import (
    DiffViewer,
    ErrorDialog,
    OnboardingDialog,
    SidebarNav,
    TopContextBar,
)

# Import real-time features
try:
    from observations.eyes.watcher import FileSystemWatcher, WatcherConfig
    from observations.eyes.diff_sight import DiffSight

    WATCHER_AVAILABLE = True
except ImportError:
    WATCHER_AVAILABLE = False


class MainWindow(QtWidgets.QMainWindow):
    """Primary application window hosting desktop investigation views."""

    AUTOSAVE_INTERVAL_MS = 30_000
    ROUTES: list[tuple[str, str]] = [
        ("Home", "home"),
        ("Observe", "observe"),
        ("Investigate", "investigate"),
        ("Knowledge", "knowledge"),
        ("Patterns", "patterns"),
        ("Export", "export"),
    ]
    ROUTE_CONTEXT: dict[str, tuple[str, str]] = {
        "home": ("Home", "Choose a workspace and launch workflows."),
        "observe": ("Observe", "Fast repository signals with selected eyes."),
        "investigate": ("Investigate", "Run and query full investigation sessions."),
        "knowledge": ("Knowledge", "History, graph context, and recommendations."),
        "patterns": ("Patterns", "Load pattern library and scan targets."),
        "export": ("Export", "Preview and export investigation artifacts."),
    }

    def __init__(self, start_path: Path | None = None) -> None:
        super().__init__()
        self._start_path = (start_path or Path(".")).resolve()
        self._current_route = "home"
        self._current_path: str | None = None
        self._current_session_id: str | None = None

        self.setWindowTitle("CodeMarshal")
        self.resize(1280, 840)
        self.setMinimumSize(1120, 700)

        self._session_manager = SessionManager()
        self._runtime_facade = RuntimeFacade()
        self._view_state = ViewStateBinder()
        self._shortcuts: list[QtGui.QShortcut] = []
        self._route_animations: list[QtCore.QPropertyAnimation] = []

        self._accessibility_mode = self._session_manager.get_accessibility_mode()
        self._font_scale = self._session_manager.get_font_scale()
        self._visual_theme_variant = self._session_manager.get_visual_theme_variant()
        self._motion_level = self._session_manager.get_motion_level()
        self._reduced_motion = self._session_manager.get_reduced_motion()
        self._sidebar_collapsed = self._session_manager.get_sidebar_collapsed()
        self._ui_density = self._session_manager.get_ui_density()
        self._accent_intensity = self._session_manager.get_accent_intensity()

        self._accessibility_mode_actions: dict[str, QtGui.QAction] = {}
        self._font_scale_actions: dict[float, QtGui.QAction] = {}
        self._visual_theme_actions: dict[str, QtGui.QAction] = {}
        self._motion_level_actions: dict[str, QtGui.QAction] = {}
        self._density_actions: dict[str, QtGui.QAction] = {}
        self._accent_actions: dict[str, QtGui.QAction] = {}
        self._force_reduced_motion_action: QtGui.QAction | None = None

        # File system watcher for real-time updates
        self._file_watcher: FileSystemWatcher | None = None
        self._diff_sight = DiffSight() if WATCHER_AVAILABLE else None
        self._detected_changes: list = []
        self._watching_enabled = False

        if GUICommandBridge is None:
            raise RuntimeError(
                "GUICommandBridge unavailable. Ensure PySide6 is installed."
            )
        self._bridge = GUICommandBridge(facade=self._runtime_facade)

        self._build_shell()
        self.statusBar().showMessage("Ready")
        self._sidebar.set_status("Ready")
        self._context_bar.set_operation("Idle", "idle")

        self._views = {
            "home": HomeView(),
            "observe": ObserveView(command_bridge=self._bridge),
            "investigate": InvestigateView(command_bridge=self._bridge),
            "knowledge": KnowledgeView(command_bridge=self._bridge),
            "patterns": PatternsView(command_bridge=self._bridge),
            "export": ExportView(command_bridge=self._bridge),
        }
        for view in self._views.values():
            self._stack.addWidget(view)
            self._view_state.register(view)
        self._wire_layout_preferences()

        self._build_menu()
        self._wire_navigation()
        self._wire_bridge_signals()
        self._register_shortcuts()

        self._set_current_path(self._start_path)
        self._sync_recent_sessions()
        self._apply_settings()
        self._restore_window_state()
        self._restore_recovery_state()
        self._maybe_run_onboarding()

        self._autosave_timer = QtCore.QTimer(self)
        self._autosave_timer.setInterval(self.AUTOSAVE_INTERVAL_MS)
        self._autosave_timer.timeout.connect(self._autosave_recovery_state)
        self._autosave_timer.start()

        last_view = self._session_manager.get_last_view()
        self._navigate(last_view if last_view in self._views else "home")

    def _build_shell(self) -> None:
        shell_root = QtWidgets.QWidget(self)
        shell_layout = QtWidgets.QHBoxLayout(shell_root)
        shell_layout.setContentsMargins(0, 0, 0, 0)
        shell_layout.setSpacing(0)

        self._sidebar = SidebarNav(routes=self.ROUTES, parent=shell_root)
        self._sidebar.route_selected.connect(self._navigate)
        self._sidebar.collapsed_changed.connect(self._on_sidebar_collapsed_changed)
        shell_layout.addWidget(self._sidebar)

        content_root = QtWidgets.QWidget(shell_root)
        content_layout = QtWidgets.QVBoxLayout(content_root)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self._context_bar = TopContextBar(parent=content_root)
        content_layout.addWidget(self._context_bar)

        stack_container = QtWidgets.QWidget(content_root)
        stack_container.setObjectName("shellContentGutter")
        stack_layout = QtWidgets.QVBoxLayout(stack_container)
        stack_layout.setContentsMargins(0, 0, 0, 0)
        stack_layout.setSpacing(0)
        self._stack = QtWidgets.QStackedWidget(stack_container)
        stack_layout.addWidget(self._stack)
        content_layout.addWidget(stack_container, stretch=1)

        shell_layout.addWidget(content_root, stretch=1)
        self.setCentralWidget(shell_root)

    def _wire_layout_preferences(self) -> None:
        for route_name, view in self._views.items():
            if hasattr(view, "set_layout_splitter_ratio"):
                ratio = self._session_manager.get_layout_splitter_ratio(route_name)
                view.set_layout_splitter_ratio(ratio)
            if hasattr(view, "layout_splitter_ratio_changed"):
                view.layout_splitter_ratio_changed.connect(
                    lambda ratio,
                    name=route_name: self._session_manager.set_layout_splitter_ratio(
                        name,
                        ratio,
                    )
                )

    def _wire_navigation(self) -> None:
        home = self._views["home"]
        home.navigate_requested.connect(self._navigate)
        home.path_selected.connect(self._set_current_path)
        home.refresh_requested.connect(self._sync_recent_sessions)
        home.open_investigation_requested.connect(self._open_session)
        home.resume_last_requested.connect(self._resume_last_session)
        home.quick_action_requested.connect(self._handle_quick_action)

        for name in ("observe", "investigate", "knowledge", "patterns", "export"):
            view = self._views[name]
            view.navigate_requested.connect(self._navigate)
            if hasattr(view, "preset_changed"):
                view.preset_changed.connect(
                    lambda preset: self._session_manager.update_settings(
                        {"observe_preset": preset}
                    )
                )

    def _wire_bridge_signals(self) -> None:
        self._bridge.operation_started.connect(self._on_operation_started)
        self._bridge.operation_progress.connect(self._on_operation_progress)
        self._bridge.operation_finished.connect(self._on_operation_finished)
        self._bridge.operation_error.connect(self._on_operation_error)
        self._bridge.operation_cancelled.connect(self._on_operation_cancelled)
        self._bridge.busy_changed.connect(self._on_busy_changed)

    def _register_shortcuts(self) -> None:
        shortcuts = [
            ("Ctrl+1", lambda: self._navigate("home")),
            ("Ctrl+2", lambda: self._navigate("observe")),
            ("Ctrl+3", lambda: self._navigate("investigate")),
            ("Ctrl+4", lambda: self._navigate("knowledge")),
            ("Ctrl+5", lambda: self._navigate("patterns")),
            ("Ctrl+6", lambda: self._navigate("export")),
            ("Ctrl+B", self._toggle_sidebar),
            ("Ctrl+Return", self._trigger_primary_action),
            ("Esc", self._bridge.cancel_all),
            ("F1", self._show_onboarding),
        ]
        self._shortcuts = []
        for key, handler in shortcuts:
            shortcut = QtGui.QShortcut(QtGui.QKeySequence(key), self)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

    def _build_menu(self) -> None:
        view_menu = self.menuBar().addMenu("&View")
        accessibility_menu = view_menu.addMenu("&Accessibility")

        mode_group = QtGui.QActionGroup(self)
        mode_group.setExclusive(True)
        for label, mode in [
            ("Standard", "standard"),
            ("High Contrast", "high_contrast"),
        ]:
            action = QtGui.QAction(label, self)
            action.setCheckable(True)
            action.setChecked(mode == self._accessibility_mode)
            action.triggered.connect(
                lambda _checked=False, value=mode: self._set_accessibility_mode(value)
            )
            mode_group.addAction(action)
            accessibility_menu.addAction(action)
            self._accessibility_mode_actions[mode] = action

        accessibility_menu.addSeparator()

        font_group = QtGui.QActionGroup(self)
        font_group.setExclusive(True)
        for label, scale in [
            ("100%", 1.0),
            ("115%", 1.15),
            ("130%", 1.3),
        ]:
            action = QtGui.QAction(label, self)
            action.setCheckable(True)
            action.setChecked(abs(scale - self._font_scale) < 0.01)
            action.triggered.connect(
                lambda _checked=False, value=scale: self._set_font_scale(value)
            )
            font_group.addAction(action)
            accessibility_menu.addAction(action)
            self._font_scale_actions[scale] = action

        accessibility_menu.addSeparator()
        reset_accessibility = QtGui.QAction("Reset Accessibility Defaults", self)
        reset_accessibility.triggered.connect(self._reset_accessibility_defaults)
        accessibility_menu.addAction(reset_accessibility)

        theme_menu = view_menu.addMenu("&Theme")
        theme_group = QtGui.QActionGroup(self)
        theme_group.setExclusive(True)
        for preview in list_theme_previews():
            label = str(preview.get("name") or "Theme")
            variant = str(preview.get("id") or "noir_premium")
            action = QtGui.QAction(label, self)
            action.setCheckable(True)
            action.setChecked(variant == self._visual_theme_variant)
            action.triggered.connect(
                lambda _checked=False, value=variant: self._set_visual_theme_variant(
                    value
                )
            )
            theme_group.addAction(action)
            theme_menu.addAction(action)
            self._visual_theme_actions[variant] = action

        density_menu = view_menu.addMenu("&Density")
        density_group = QtGui.QActionGroup(self)
        density_group.setExclusive(True)
        for label, value in [
            ("Comfortable", "comfortable"),
            ("Compact", "compact"),
        ]:
            action = QtGui.QAction(label, self)
            action.setCheckable(True)
            action.setChecked(value == self._ui_density)
            action.triggered.connect(
                lambda _checked=False, level=value: self._set_ui_density(level)
            )
            density_group.addAction(action)
            density_menu.addAction(action)
            self._density_actions[value] = action

        accent_menu = view_menu.addMenu("A&ccent")
        accent_group = QtGui.QActionGroup(self)
        accent_group.setExclusive(True)
        for label, value in [
            ("Soft", "soft"),
            ("Normal", "normal"),
            ("Bold", "bold"),
        ]:
            action = QtGui.QAction(label, self)
            action.setCheckable(True)
            action.setChecked(value == self._accent_intensity)
            action.triggered.connect(
                lambda _checked=False, level=value: self._set_accent_intensity(level)
            )
            accent_group.addAction(action)
            accent_menu.addAction(action)
            self._accent_actions[value] = action

        motion_menu = view_menu.addMenu("&Motion")
        motion_group = QtGui.QActionGroup(self)
        motion_group.setExclusive(True)
        for label, level in [
            ("Full Motion", "full"),
            ("Standard Motion", "standard"),
            ("Reduced Motion", "reduced"),
        ]:
            action = QtGui.QAction(label, self)
            action.setCheckable(True)
            action.setChecked(level == self._motion_level)
            action.triggered.connect(
                lambda _checked=False, value=level: self._set_motion_level(value)
            )
            motion_group.addAction(action)
            motion_menu.addAction(action)
            self._motion_level_actions[level] = action

        motion_menu.addSeparator()
        reduce_action = QtGui.QAction("Force Reduced Motion", self)
        reduce_action.setCheckable(True)
        reduce_action.setChecked(self._reduced_motion)
        reduce_action.triggered.connect(self._set_reduced_motion)
        motion_menu.addAction(reduce_action)
        self._force_reduced_motion_action = reduce_action

        view_menu.addSeparator()
        toggle_sidebar = QtGui.QAction("Toggle Sidebar", self)
        toggle_sidebar.setShortcut(QtGui.QKeySequence("Ctrl+B"))
        toggle_sidebar.triggered.connect(self._toggle_sidebar)
        view_menu.addAction(toggle_sidebar)

        reset_visual = QtGui.QAction("Reset Visual Defaults", self)
        reset_visual.triggered.connect(self._reset_visual_defaults)
        view_menu.addAction(reset_visual)

        help_menu = self.menuBar().addMenu("&Help")

        onboarding_action = QtGui.QAction("Show &Onboarding", self)
        onboarding_action.setShortcut(QtGui.QKeySequence("F1"))
        onboarding_action.triggered.connect(self._show_onboarding)
        help_menu.addAction(onboarding_action)

        shortcuts_action = QtGui.QAction("Keyboard &Shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts_dialog)
        help_menu.addAction(shortcuts_action)

    def _navigate(self, name: str) -> None:
        if name not in self._views:
            return
        self._current_route = name
        target = self._views[name]
        self._stack.setCurrentWidget(target)
        self._animate_route_transition(target)
        self._session_manager.set_last_view(name)
        self._sidebar.set_current_route(name)
        self._update_context_bar()

    def _animate_route_transition(self, target: QtWidgets.QWidget) -> None:
        duration = self._transition_duration_ms()
        if duration <= 0:
            return
        effect = QtWidgets.QGraphicsOpacityEffect(target)
        effect.setOpacity(0.0)
        target.setGraphicsEffect(effect)
        animation = QtCore.QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._route_animations.append(animation)

        def _cleanup() -> None:
            if target.graphicsEffect() is effect:
                target.setGraphicsEffect(None)
            if animation in self._route_animations:
                self._route_animations.remove(animation)

        animation.finished.connect(_cleanup)
        animation.start()

    def _transition_duration_ms(self) -> int:
        if self._reduced_motion or self._motion_level == "reduced":
            return 0
        if self._motion_level == "full":
            return 220
        return 170

    def _toggle_sidebar(self) -> None:
        self._sidebar.toggle_collapsed()

    def _on_sidebar_collapsed_changed(self, collapsed: bool) -> None:
        self._sidebar_collapsed = bool(collapsed)
        self._session_manager.set_sidebar_collapsed(self._sidebar_collapsed)

    def _set_current_path(self, path: str | Path) -> None:
        resolved = Path(path).resolve()
        self._current_path = str(resolved)
        self._session_manager.set_last_path(str(resolved))
        self._view_state.set_path(str(resolved))
        self._views["home"].set_recent_paths(
            self._session_manager.get_recent_paths(limit=10)
        )
        self._context_bar.set_path(self._current_path)

    def _set_current_session(self, session_id: str | None) -> None:
        self._current_session_id = session_id
        self._view_state.set_session(session_id)
        self._context_bar.set_session(session_id)

    def _sync_recent_sessions(self) -> None:
        sessions = self._bridge.list_recent_investigations(limit=10)
        self._session_manager.merge_recent_investigations(sessions)
        merged = self._session_manager.get_recent_investigations(limit=10)
        self._view_state.set_sessions(merged)
        self._views["home"].set_recent_investigations(merged)

        recent_paths = self._runtime_facade.list_recent_paths(limit=10)
        for value in recent_paths:
            self._session_manager.add_recent_path(value)
        paths = self._session_manager.get_recent_paths(limit=10)
        self._views["home"].set_recent_paths(paths)
        self._context_bar.set_metrics(
            recent_paths=len(paths), recent_sessions=len(merged)
        )

    def _apply_settings(self) -> None:
        self._apply_visual_preferences()
        settings = self._session_manager.get_settings()
        self._views["export"].set_default_export_format(
            str(settings.get("default_export_format") or "json")
        )
        preset = str(settings.get("observe_preset") or "")
        if preset:
            self._views["observe"].set_preset(preset)
        self._set_hints_enabled(self._session_manager.get_show_context_hints())
        self._update_context_bar()

    def _apply_visual_preferences(self) -> None:
        app = QtWidgets.QApplication.instance()
        if app is None:
            return

        reduced_motion = self._reduced_motion or self._motion_level == "reduced"
        app.setStyleSheet(
            build_stylesheet(
                accessibility_mode=self._accessibility_mode,
                font_scale=self._font_scale,
                visual_theme_variant=self._visual_theme_variant,
                reduced_motion=reduced_motion,
                ui_density=self._ui_density,
                accent_intensity=self._accent_intensity,
            )
        )

        self._sidebar.set_motion_enabled(not reduced_motion)
        previous = self._sidebar.blockSignals(True)
        self._sidebar.set_collapsed(self._sidebar_collapsed)
        self._sidebar.blockSignals(previous)
        self._sidebar.set_current_route(self._current_route)

    def _set_accessibility_mode(self, mode: str) -> None:
        normalized = str(mode or "standard").strip().lower()
        if normalized not in {"standard", "high_contrast"}:
            normalized = "standard"
        self._accessibility_mode = normalized
        for key, action in self._accessibility_mode_actions.items():
            action.setChecked(key == normalized)
        self._session_manager.set_accessibility_mode(normalized)
        self._apply_visual_preferences()

    def _set_font_scale(self, scale: float) -> None:
        self._font_scale = max(0.8, min(1.6, float(scale)))
        for key, action in self._font_scale_actions.items():
            action.setChecked(abs(key - self._font_scale) < 0.01)
        self._session_manager.set_font_scale(self._font_scale)
        self._apply_visual_preferences()

    def _set_visual_theme_variant(self, variant: str) -> None:
        normalized = str(variant or "noir_premium").strip().lower()
        if normalized not in {"noir_premium", "noir", "ledger"}:
            normalized = "noir_premium"
        self._visual_theme_variant = normalized
        for key, action in self._visual_theme_actions.items():
            action.setChecked(key == normalized)
        self._session_manager.set_visual_theme_variant(normalized)
        self._apply_visual_preferences()

    def _set_motion_level(self, level: str) -> None:
        normalized = str(level or "standard").strip().lower()
        if normalized not in {"full", "standard", "reduced"}:
            normalized = "standard"
        self._motion_level = normalized
        for key, action in self._motion_level_actions.items():
            action.setChecked(key == normalized)
        if normalized == "reduced":
            self._reduced_motion = True
            if self._force_reduced_motion_action is not None:
                self._force_reduced_motion_action.setChecked(True)
        self._session_manager.set_motion_level(normalized)
        self._session_manager.set_reduced_motion(self._reduced_motion)
        self._apply_visual_preferences()

    def _set_reduced_motion(self, enabled: bool) -> None:
        self._reduced_motion = bool(enabled)
        if self._reduced_motion:
            self._motion_level = "reduced"
        elif self._motion_level == "reduced":
            self._motion_level = "standard"
        for key, action in self._motion_level_actions.items():
            action.setChecked(key == self._motion_level)
        if self._force_reduced_motion_action is not None:
            self._force_reduced_motion_action.setChecked(self._reduced_motion)
        self._session_manager.set_motion_level(self._motion_level)
        self._session_manager.set_reduced_motion(self._reduced_motion)
        self._apply_visual_preferences()

    def _set_ui_density(self, density: str) -> None:
        normalized = str(density or "comfortable").strip().lower()
        if normalized not in {"comfortable", "compact"}:
            normalized = "comfortable"
        self._ui_density = normalized
        for key, action in self._density_actions.items():
            action.setChecked(key == normalized)
        self._session_manager.set_ui_density(normalized)
        self._apply_visual_preferences()

    def _set_accent_intensity(self, intensity: str) -> None:
        normalized = str(intensity or "normal").strip().lower()
        if normalized not in {"soft", "normal", "bold"}:
            normalized = "normal"
        self._accent_intensity = normalized
        for key, action in self._accent_actions.items():
            action.setChecked(key == normalized)
        self._session_manager.set_accent_intensity(normalized)
        self._apply_visual_preferences()

    def _reset_accessibility_defaults(self) -> None:
        self._set_accessibility_mode("standard")
        self._set_font_scale(1.0)
        if "standard" in self._accessibility_mode_actions:
            self._accessibility_mode_actions["standard"].setChecked(True)
        if 1.0 in self._font_scale_actions:
            self._font_scale_actions[1.0].setChecked(True)

    def _reset_visual_defaults(self) -> None:
        self._set_visual_theme_variant("noir_premium")
        self._set_ui_density("comfortable")
        self._set_accent_intensity("normal")
        self._set_motion_level("standard")
        self._set_reduced_motion(False)
        self._sidebar.set_collapsed(False)
        self._on_sidebar_collapsed_changed(False)

    def _set_hints_enabled(self, enabled: bool) -> None:
        for view in self._views.values():
            if hasattr(view, "set_hints_enabled"):
                view.set_hints_enabled(bool(enabled))

    def _update_context_bar(self) -> None:
        title, caption = self.ROUTE_CONTEXT.get(
            self._current_route, ("Home", "Desktop workspace")
        )
        self._context_bar.set_route(title, caption)
        self._context_bar.set_path(self._current_path)
        self._context_bar.set_session(self._current_session_id)

    def _restore_window_state(self) -> None:
        geometry_hex = self._session_manager.get_window_geometry()
        if geometry_hex:
            self.restoreGeometry(
                QtCore.QByteArray.fromHex(geometry_hex.encode("ascii"))
            )
        state_hex = self._session_manager.get_window_state()
        if state_hex:
            self.restoreState(QtCore.QByteArray.fromHex(state_hex.encode("ascii")))

    def _restore_recovery_state(self) -> None:
        recovery = self._session_manager.get_recovery_state()
        if not recovery:
            return
        session_id = str(recovery.get("session_id") or "")
        if not session_id:
            return

        question = (
            "A previous session may have been interrupted.\n\n"
            f"Session ID: {session_id}\n\n"
            "Do you want to restore this session now?"
        )
        answer = QtWidgets.QMessageBox.question(
            self,
            "Recover Previous Session",
            question,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.Yes,
        )
        if answer == QtWidgets.QMessageBox.Yes:
            if recovery.get("path"):
                self._set_current_path(str(recovery["path"]))
            self._open_session(session_id)
        else:
            self._session_manager.clear_recovery_state()

    def _maybe_run_onboarding(self) -> None:
        if self._session_manager.is_onboarding_completed():
            return
        self._show_onboarding()

    def _show_onboarding(self) -> None:
        default_path = (
            str(self._runtime_facade.current_path)
            if self._runtime_facade.current_path is not None
            else self._session_manager.get_last_path()
        )
        dialog = OnboardingDialog(
            default_path=default_path,
            show_hints=self._session_manager.get_show_context_hints(),
            parent=self,
        )
        dialog.exec()
        payload = dialog.result_payload()

        self._session_manager.set_show_context_hints(bool(payload["show_hints"]))
        self._set_hints_enabled(bool(payload["show_hints"]))

        if payload["accepted"]:
            path_value = str(payload.get("path") or "").strip()
            if path_value:
                self._set_current_path(path_value)
            target_view = str(payload.get("first_action") or "investigate")
            if target_view in self._views:
                self._navigate(target_view)
            self._session_manager.set_onboarding_completed(True)
            self.statusBar().showMessage("Onboarding completed", 4000)
            self._focus_current_view_primary()
            return

        if payload["dont_show_again"]:
            self._session_manager.set_onboarding_completed(True)
        self._focus_current_view_primary()

    def _show_shortcuts_dialog(self) -> None:
        text = "\n".join(
            [
                "Ctrl+1: Home",
                "Ctrl+2: Observe",
                "Ctrl+3: Investigate",
                "Ctrl+4: Knowledge",
                "Ctrl+5: Patterns",
                "Ctrl+6: Export",
                "Ctrl+B: Toggle sidebar",
                "Ctrl+Enter: Primary action in current view",
                "Esc: Cancel active operations",
                "F1: Open onboarding and quick help",
                "View > Accessibility: Contrast and font scaling",
                "View > Theme / Density / Accent / Motion: visual shell controls",
            ]
        )
        QtWidgets.QMessageBox.information(self, "Keyboard Shortcuts", text)

    def _open_session(self, session_id: str) -> None:
        metadata = self._bridge.load_session_metadata(session_id)
        if not metadata:
            ErrorDialog.show_error(
                self,
                "Session Not Found",
                f"Could not load session '{session_id}'.",
                suggestion="Refresh recent sessions and try again.",
            )
            return

        self._set_current_session(session_id)
        self._views["investigate"].set_session_metadata(metadata)
        if metadata.get("path"):
            self._set_current_path(str(metadata["path"]))
        self._navigate("investigate")

    def _resume_last_session(self) -> None:
        recent = self._session_manager.get_recent_investigations(limit=1)
        if not recent:
            self.statusBar().showMessage("No recent sessions to resume", 3000)
            return
        session_id = str(recent[0].get("session_id") or "")
        if session_id:
            self._open_session(session_id)

    def _handle_quick_action(self, action: str) -> None:
        if action == "quick_observe":
            self._navigate("observe")
            self._views["observe"].trigger_primary_action()
            return
        if action == "quick_investigate":
            self._navigate("investigate")
            self._views["investigate"].trigger_primary_action()
            return
        if action == "quick_patterns":
            self._navigate("patterns")
            self._views["patterns"].trigger_primary_action()
            return

    def _trigger_primary_action(self) -> None:
        current = self._stack.currentWidget()
        if current is None:
            return
        if hasattr(current, "trigger_primary_action"):
            current.trigger_primary_action()

    def _focus_current_view_primary(self) -> None:
        current = self._stack.currentWidget()
        if current is None:
            return
        for name in ("path_input", "session_combo", "question_input"):
            if hasattr(current, name):
                widget = getattr(current, name)
                if isinstance(widget, QtWidgets.QWidget):
                    widget.setFocus()
                    return
        current.setFocus()

    def _autosave_recovery_state(self) -> None:
        session_id = self._runtime_facade.current_investigation_id
        current_path = self._runtime_facade.current_path
        if session_id and current_path:
            self._session_manager.save_recovery_state(session_id, str(current_path))

    def _operation_label(self, operation: str) -> str:
        labels = {
            "investigate": "Investigate",
            "observe": "Observe",
            "query": "Query",
            "history": "History",
            "graph": "Graph",
            "recommendations": "Recommendations",
            "pattern_list": "Pattern List",
            "pattern_scan": "Pattern Scan",
            "pattern_search": "Marketplace Search",
            "pattern_apply": "Pattern Apply",
            "pattern_create": "Template Create",
            "pattern_share": "Pattern Share",
            "collaboration_unlock": "Collaboration Unlock",
            "team_create": "Team Create",
            "team_add": "Team Add",
            "team_list": "Team List",
            "share_create": "Share Create",
            "share_list": "Share List",
            "share_revoke": "Share Revoke",
            "share_resolve": "Share Resolve",
            "comment_add": "Comment Add",
            "comment_list": "Comment List",
            "comment_resolve": "Comment Resolve",
            "export_preview": "Export Preview",
            "export": "Export",
        }
        return labels.get(operation, operation.replace("_", " ").title())

    def _on_operation_started(self, operation: str) -> None:
        label = self._operation_label(operation)
        self._context_bar.set_operation(f"{label} running", "running", pulse=True)
        self._sidebar.set_status("Running")
        self.statusBar().showMessage(f"{label} started")

    def _on_operation_progress(
        self,
        operation: str,
        current: int,
        total: int,
        message: str,
    ) -> None:
        label = self._operation_label(operation)
        total_value = max(int(total), 1)
        current_value = max(0, int(current))
        progress_pct = int((current_value / total_value) * 100)
        progress_pct = max(0, min(100, progress_pct))
        detail = message or f"{current_value}/{total_value}"
        self._context_bar.set_operation(f"{label} {progress_pct}%", "running")
        self.statusBar().showMessage(f"{label}: {detail}")

    def _on_operation_finished(self, operation: str, payload: object) -> None:
        label = self._operation_label(operation)
        data = payload if isinstance(payload, dict) else {}

        if operation == "investigate":
            session_id = str(
                data.get("investigation_id") or data.get("session_id") or ""
            )
            if session_id:
                self._set_current_session(session_id)
        else:
            session_id = str(data.get("session_id") or "")
            if session_id:
                self._set_current_session(session_id)

        if operation in {"investigate", "observe", "query", "pattern_scan", "export"}:
            self._sync_recent_sessions()

        self._context_bar.set_operation("Idle", "idle")
        self._sidebar.set_status("Ready")
        self.statusBar().showMessage(f"{label} completed", 4000)
        self._update_context_bar()

    def _on_operation_error(
        self,
        operation: str,
        error_type: str,
        message: str,
        details: str,
    ) -> None:
        label = self._operation_label(operation)
        error_text = message or "Operation failed"
        self._context_bar.set_operation(f"{label} failed", "error", pulse=True)
        self._sidebar.set_status("Error")
        self.statusBar().showMessage(f"{label} failed: {error_text}", 6000)
        ErrorDialog.show_error(
            self,
            f"{label} Failed",
            f"{error_type}: {error_text}",
            details=details,
            suggestion="Review the operation details, then retry.",
        )

    def _on_operation_cancelled(self, operation: str) -> None:
        label = self._operation_label(operation)
        self._context_bar.set_operation(f"{label} cancelled", "idle")
        self._sidebar.set_status("Cancelled")
        self.statusBar().showMessage(f"{label} cancelled", 4000)

    def _on_busy_changed(self, is_busy: bool) -> None:
        busy = bool(is_busy)
        self._view_state.set_busy(busy)
        self._context_bar.set_busy(busy)
        if not busy and self._context_bar.busy_chip.text() == "Idle":
            self._context_bar.set_operation("Idle", "idle")
            self._sidebar.set_status("Ready")

    def _start_file_watching(self, path: Path | None = None) -> None:
        """Start watching the file system for changes."""
        if not WATCHER_AVAILABLE:
            self.statusBar().showMessage(
                "File watching not available - watchdog not installed", 4000
            )
            return

        watch_path = path or self._current_path
        if not watch_path:
            self.statusBar().showMessage("No path set for watching", 3000)
            return

        # Stop existing watcher
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher = None

        try:
            watch_path_obj = Path(watch_path)
            if not watch_path_obj.exists():
                self.statusBar().showMessage(f"Path does not exist: {watch_path}", 3000)
                return

            config = WatcherConfig(recursive=True)
            self._file_watcher = FileSystemWatcher(
                watch_path_obj, config, on_change=self._on_file_changed
            )
            self._file_watcher.start()
            self._watching_enabled = True
            self.statusBar().showMessage(f"Started watching: {watch_path}", 4000)
            self._context_bar.set_operation("Watching", "running")
        except Exception as e:
            self.statusBar().showMessage(f"Failed to start watching: {e}", 4000)

    def _stop_file_watching(self) -> None:
        """Stop watching the file system."""
        if self._file_watcher:
            self._file_watcher.stop()
            self._file_watcher = None
        self._watching_enabled = False
        self.statusBar().showMessage("Stopped file watching", 3000)
        self._context_bar.set_operation("Idle", "idle")

    def _on_file_changed(self, change) -> None:
        """Handle file change events."""
        self._detected_changes.append(change)

        # Update status bar with brief notification
        change_type_str = {
            change.change_type.CREATED: "created",
            change.change_type.MODIFIED: "modified",
            change.change_type.DELETED: "deleted",
            change.change_type.MOVED: "moved",
        }.get(change.change_type, "changed")

        self.statusBar().showMessage(
            f"File {change_type_str}: {change.path.name}", 3000
        )

        # If in observe view, refresh it
        if self._current_route == "observe":
            if hasattr(self._views["observe"], "refresh_if_auto"):
                self._views["observe"].refresh_if_auto()

    def _show_diff_dialog(self, file_path: Path | None = None) -> None:
        """Show diff viewer dialog."""
        if not self._diff_sight:
            QtWidgets.QMessageBox.information(
                self, "Diff Viewer", "Diff functionality not available."
            )
            return
        target_path = file_path or (
            Path(self._current_path) if self._current_path else None
        )
        viewer = DiffViewer(parent=self)
        if target_path is None:
            viewer.set_unified_diff("Select a file to view differences.")
        else:
            if target_path.exists() and target_path.is_file():
                placeholder = (
                    f"--- {target_path}\n"
                    f"+++ {target_path}\n"
                    "@@ -1,1 +1,1 @@\n"
                    f" {target_path.name}"
                )
                viewer.set_unified_diff(placeholder, file_path=target_path)
            else:
                viewer.set_unified_diff(f"Path not found: {target_path}", file_path=target_path)
        viewer.exec()

    def _show_status_panel(self) -> None:
        """Show investigation status panel."""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Investigation Status")
        dialog.resize(600, 400)

        layout = QtWidgets.QVBoxLayout(dialog)

        # Status information
        info_text = f"""
<b>Investigation Status</b><br>
<br>
<b>Current Path:</b> {self._current_path or "Not set"}<br>
<b>Session ID:</b> {self._current_session_id or "None"}<br>
<b>Watching Enabled:</b> {"Yes" if self._watching_enabled else "No"}<br>
<b>Detected Changes:</b> {len(self._detected_changes)}<br>
        """

        label = QtWidgets.QLabel(info_text)
        label.setTextFormat(QtCore.Qt.RichText)
        layout.addWidget(label)

        # Recent changes list
        if self._detected_changes:
            changes_label = QtWidgets.QLabel("<b>Recent Changes:</b>")
            layout.addWidget(changes_label)

            changes_list = QtWidgets.QListWidget()
            for change in self._detected_changes[-10:]:  # Last 10 changes
                item_text = f"[{change.change_type.name}] {change.path.name}"
                changes_list.addItem(item_text)
            layout.addWidget(changes_list)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()

        if not self._watching_enabled:
            start_watch_btn = QtWidgets.QPushButton("Start Watching")
            start_watch_btn.clicked.connect(
                lambda: (self._start_file_watching(), dialog.accept())
            )
            button_layout.addWidget(start_watch_btn)
        else:
            stop_watch_btn = QtWidgets.QPushButton("Stop Watching")
            stop_watch_btn.clicked.connect(
                lambda: (self._stop_file_watching(), dialog.accept())
            )
            button_layout.addWidget(stop_watch_btn)

        view_diff_btn = QtWidgets.QPushButton("View Diff")
        view_diff_btn.clicked.connect(
            lambda: (self._show_diff_dialog(), dialog.accept())
        )
        button_layout.addWidget(view_diff_btn)

        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        dialog.exec()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        bridge_busy = bool(getattr(self._bridge, "is_busy", False))
        if bridge_busy:
            response = QtWidgets.QMessageBox.question(
                self,
                "Operations Running",
                (
                    "One or more operations are still running.\n\n"
                    "Close anyway and cancel all running operations?"
                ),
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No,
            )
            if response != QtWidgets.QMessageBox.Yes:
                event.ignore()
                return
            self._bridge.cancel_all()

        if hasattr(self, "_autosave_timer"):
            self._autosave_timer.stop()

        geometry_hex = bytes(self.saveGeometry().toHex()).decode("ascii")
        state_hex = bytes(self.saveState().toHex()).decode("ascii")
        self._session_manager.set_window_geometry(geometry_hex)
        self._session_manager.set_window_state(state_hex)

        session_id = self._runtime_facade.current_investigation_id
        current_path = self._runtime_facade.current_path
        if session_id and current_path:
            self._session_manager.save_recovery_state(session_id, str(current_path))
        else:
            self._session_manager.clear_recovery_state()

        super().closeEvent(event)


def main(argv: list[str] | None = None, start_path: Path | None = None) -> int:
    """Run the desktop Qt application."""
    args = list(argv) if argv is not None else list(sys.argv)

    resolved_start = start_path
    if resolved_start is None and len(args) > 1:
        candidate = args[1].strip()
        if candidate:
            resolved_start = Path(candidate).expanduser()

    app = QtWidgets.QApplication.instance()
    owns_app = app is None
    if app is None:
        app = QtWidgets.QApplication(args)
    app.setApplicationName("CodeMarshal")

    window = MainWindow(start_path=resolved_start)
    window.show()

    if owns_app:
        return app.exec()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
