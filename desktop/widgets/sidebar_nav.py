"""Persistent sidebar navigation for the desktop shell."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible


class SidebarNav(QtWidgets.QFrame):
    """Sidebar with brand block, route buttons, and collapse control."""

    route_selected = QtCore.Signal(str)
    collapsed_changed = QtCore.Signal(bool)

    EXPANDED_WIDTH = 252
    COLLAPSED_WIDTH = 86

    def __init__(
        self,
        routes: list[tuple[str, str]] | None = None,
        parent: QtWidgets.QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarRoot")
        self._collapsed = False
        self._motion_enabled = True
        self._buttons: dict[str, QtWidgets.QToolButton] = {}
        self._labels: dict[str, str] = {}
        self._short_labels: dict[str, str] = {}
        self._current_route: str | None = None
        self._width_animation = QtCore.QVariantAnimation(self)
        self._width_animation.setDuration(180)
        self._width_animation.valueChanged.connect(self._on_width_animation)
        self._indicator_animation = QtCore.QPropertyAnimation(self)
        self._indicator_animation.setDuration(160)
        self._indicator_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self._build_ui(routes or [])

    def _build_ui(self, routes: list[tuple[str, str]]) -> None:
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        self.brand_title = QtWidgets.QLabel("CodeMarshal")
        self.brand_title.setObjectName("sidebarBrandTitle")
        self.brand_subtitle = QtWidgets.QLabel("Investigation Desktop")
        self.brand_subtitle.setObjectName("sidebarBrandSubtitle")
        layout.addWidget(self.brand_title)
        layout.addWidget(self.brand_subtitle)

        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setObjectName("sidebarDivider")
        layout.addWidget(line)

        self.route_container = QtWidgets.QWidget()
        self.route_layout = QtWidgets.QVBoxLayout(self.route_container)
        self.route_layout.setContentsMargins(0, 0, 0, 0)
        self.route_layout.setSpacing(6)
        layout.addWidget(self.route_container)

        self.button_group = QtWidgets.QButtonGroup(self)
        self.button_group.setExclusive(True)
        for label, route in routes:
            button = QtWidgets.QToolButton()
            button.setObjectName("sidebarRouteButton")
            button.setText(label)
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setToolButtonStyle(QtCore.Qt.ToolButtonTextOnly)
            button.clicked.connect(
                lambda _checked=False, value=route: self.route_selected.emit(value)
            )
            apply_accessible(button, name=f"Navigate to {label} view")
            self.button_group.addButton(button)
            self._buttons[route] = button
            self._labels[route] = label
            short = "".join(part[:1] for part in label.split()).upper()
            self._short_labels[route] = short or label[:1].upper()
            self.route_layout.addWidget(button)

        self.route_layout.addStretch(1)

        self._indicator = QtWidgets.QFrame(self.route_container)
        self._indicator.setObjectName("sidebarRouteIndicator")
        self._indicator.resize(4, 28)
        self._indicator.hide()

        layout.addStretch(1)

        self.status_chip = QtWidgets.QLabel("Ready")
        self.status_chip.setObjectName("sidebarStatusChip")
        self.status_chip.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.status_chip)

        self.collapse_btn = QtWidgets.QPushButton("Collapse")
        self.collapse_btn.setObjectName("sidebarCollapseButton")
        self.collapse_btn.clicked.connect(self.toggle_collapsed)
        apply_accessible(self.collapse_btn, name="Toggle sidebar collapse")
        layout.addWidget(self.collapse_btn)

        self._set_width(self.EXPANDED_WIDTH)

    def set_current_route(self, route: str) -> None:
        button = self._buttons.get(route)
        if button is not None:
            self._current_route = route
            button.setChecked(True)
            self._move_indicator(button)

    def set_status(self, text: str) -> None:
        self.status_chip.setText(str(text or "Ready"))

    def set_motion_enabled(self, enabled: bool) -> None:
        self._motion_enabled = bool(enabled)
        if not self._motion_enabled and self._width_animation.state() == QtCore.QAbstractAnimation.Running:
            self._width_animation.stop()

    def set_collapsed(self, collapsed: bool) -> None:
        collapsed = bool(collapsed)
        changed = collapsed != self._collapsed
        self._collapsed = collapsed
        self.setProperty("collapsed", self._collapsed)

        width = self.COLLAPSED_WIDTH if self._collapsed else self.EXPANDED_WIDTH
        animate = self._motion_enabled and self.isVisible()
        if animate:
            self._width_animation.stop()
            self._width_animation.setStartValue(self.width())
            self._width_animation.setEndValue(width)
            self._width_animation.start()
        else:
            self._set_width(width)

        self.brand_subtitle.setVisible(not self._collapsed)
        self.status_chip.setVisible(not self._collapsed)
        self.collapse_btn.setText("Expand" if self._collapsed else "Collapse")
        for route, button in self._buttons.items():
            button.setText(
                self._short_labels[route] if self._collapsed else self._labels[route]
            )
            button.setProperty("collapsed", self._collapsed)
            button.style().unpolish(button)
            button.style().polish(button)
            button.setToolTip(self._labels[route] if self._collapsed else "")
        if self._current_route and self._current_route in self._buttons:
            self._move_indicator(self._buttons[self._current_route], animate=False)
        if changed:
            self.collapsed_changed.emit(self._collapsed)

    def _on_width_animation(self, value: object) -> None:
        try:
            width = int(value)
        except (TypeError, ValueError):
            return
        self._set_width(width)

    def _set_width(self, width: int) -> None:
        width = max(self.COLLAPSED_WIDTH, min(self.EXPANDED_WIDTH, int(width)))
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)

    def _move_indicator(
        self,
        button: QtWidgets.QToolButton,
        *,
        animate: bool = True,
    ) -> None:
        target = button.geometry()
        y = target.y() + max((target.height() - self._indicator.height()) // 2, 0)
        x = 0
        self._indicator.show()
        end_pos = QtCore.QPoint(x, y)
        if animate and self._motion_enabled and self._indicator.pos() != end_pos:
            self._indicator_animation.stop()
            self._indicator_animation.setTargetObject(self._indicator)
            self._indicator_animation.setPropertyName(b"pos")
            self._indicator_animation.setStartValue(self._indicator.pos())
            self._indicator_animation.setEndValue(end_pos)
            self._indicator_animation.start()
        else:
            self._indicator.move(end_pos)

    def is_collapsed(self) -> bool:
        return self._collapsed

    def toggle_collapsed(self) -> None:
        self.set_collapsed(not self._collapsed)
