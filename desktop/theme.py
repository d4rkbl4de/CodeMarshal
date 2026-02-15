"""Theme definitions for the desktop GUI."""

from __future__ import annotations

from pathlib import Path

THEME_VARIANTS: dict[str, dict[str, str]] = {
    "noir_premium": {
        "color.background": "#090A0D",
        "color.surface.1": "#131722",
        "color.surface.2": "#1A2030",
        "color.surface.3": "#232A3D",
        "color.surface.4": "#2D3650",
        "color.border": "#3B4762",
        "color.accent": "#E9C774",
        "color.accent.hover": "#F3D89A",
        "color.warning": "#EC7D7D",
        "color.success": "#7CDDAE",
        "color.info": "#79C7FF",
        "color.text.1": "#F4F7FF",
        "color.text.2": "#B6C0D7",
        "color.text.muted": "#8793AC",
        "sidebar.gradient.start": "#121A2B",
        "sidebar.gradient.end": "#0B101A",
        "focus.ring": "#7FCBFF",
        "space.control.y": "9px",
        "space.control.x": "12px",
        "radius.control": "10px",
    },
    "noir": {
        "color.background": "#0A0A0B",
        "color.surface.1": "#141518",
        "color.surface.2": "#1B1C20",
        "color.surface.3": "#242631",
        "color.surface.4": "#2A2D39",
        "color.border": "#2E3140",
        "color.accent": "#E7C87A",
        "color.accent.hover": "#F2D89A",
        "color.warning": "#EA7A7A",
        "color.success": "#76DDA3",
        "color.info": "#73BDF2",
        "color.text.1": "#F3F5F8",
        "color.text.2": "#A8AFBC",
        "color.text.muted": "#7F8796",
        "sidebar.gradient.start": "#12131A",
        "sidebar.gradient.end": "#0B0C10",
        "focus.ring": "#7BC7FF",
        "space.control.y": "9px",
        "space.control.x": "12px",
        "radius.control": "8px",
    },
    "ledger": {
        "color.background": "#12110F",
        "color.surface.1": "#1B1A16",
        "color.surface.2": "#24211B",
        "color.surface.3": "#2E2921",
        "color.surface.4": "#383022",
        "color.border": "#4B4030",
        "color.accent": "#DFAE6B",
        "color.accent.hover": "#EDC48D",
        "color.warning": "#F0876D",
        "color.success": "#8CD28A",
        "color.info": "#7ABAE1",
        "color.text.1": "#F2EBDC",
        "color.text.2": "#C2B59A",
        "color.text.muted": "#9E927C",
        "sidebar.gradient.start": "#201C15",
        "sidebar.gradient.end": "#15120E",
        "focus.ring": "#8FD6FF",
        "space.control.y": "9px",
        "space.control.x": "12px",
        "radius.control": "8px",
    },
}

HIGH_CONTRAST_OVERRIDES: dict[str, str] = {
    "color.background": "#000000",
    "color.surface.1": "#101010",
    "color.surface.2": "#171717",
    "color.surface.3": "#232323",
    "color.surface.4": "#303030",
    "color.border": "#F0F0F0",
    "color.accent": "#FFD84D",
    "color.accent.hover": "#FFEA86",
    "color.warning": "#FF6B6B",
    "color.success": "#8AFFA8",
    "color.info": "#7BC7FF",
    "color.text.1": "#FFFFFF",
    "color.text.2": "#E2E2E2",
    "color.text.muted": "#C6C6C6",
    "sidebar.gradient.start": "#0E0E0E",
    "sidebar.gradient.end": "#070707",
    "space.control.y": "10px",
    "space.control.x": "14px",
    "radius.control": "4px",
    "focus.ring": "#00FFFF",
}


def _asset_url(name: str) -> str:
    asset = Path(__file__).resolve().parent / "assets" / name
    if not asset.exists():
        return ""
    return asset.resolve().as_posix()


def _select_tokens(accessibility_mode: str, visual_theme_variant: str) -> dict[str, str]:
    variant = str(visual_theme_variant or "noir_premium").strip().lower()
    tokens = dict(THEME_VARIANTS.get(variant, THEME_VARIANTS["noir_premium"]))
    if str(accessibility_mode or "standard").strip().lower() == "high_contrast":
        tokens.update(HIGH_CONTRAST_OVERRIDES)
    return tokens


def _apply_accent_intensity(tokens: dict[str, str], accent_intensity: str) -> None:
    mode = str(accent_intensity or "normal").strip().lower()
    if mode == "soft":
        tokens["color.accent"] = "#CEB57C"
        tokens["color.accent.hover"] = "#DAC696"
    elif mode == "bold":
        tokens["color.accent"] = "#FFD070"
        tokens["color.accent.hover"] = "#FFE39E"


def _density_padding(density: str) -> tuple[str, str]:
    normalized = str(density or "comfortable").strip().lower()
    if normalized == "compact":
        return ("7px", "10px")
    return ("9px", "12px")


def build_stylesheet(
    accessibility_mode: str = "standard",
    font_scale: float = 1.0,
    visual_theme_variant: str = "noir_premium",
    reduced_motion: bool = False,
    ui_density: str = "comfortable",
    accent_intensity: str = "normal",
) -> str:
    """Return a global stylesheet for the desktop GUI."""
    del reduced_motion  # Motion is controlled by runtime widget animations.
    tokens = _select_tokens(accessibility_mode, visual_theme_variant)
    _apply_accent_intensity(tokens, accent_intensity)
    density_y, density_x = _density_padding(ui_density)

    scale = max(min(float(font_scale), 1.6), 0.8)
    base_font = max(11, int(round(13 * scale)))
    subtitle_font = max(11, int(round(12 * scale)))
    title_font = max(27, int(round(35 * scale)))
    section_font = max(17, int(round(21 * scale)))
    small_font = max(10, int(round(11 * scale)))
    texture_url = _asset_url("noise-grid.svg")
    texture_rule = (
        f'background-image: url("{texture_url}"); background-position: center;'
        if texture_url
        else ""
    )

    return f"""
    QWidget {{
        background: {tokens['color.background']};
        color: {tokens['color.text.1']};
        font-family: "IBM Plex Mono", "Source Code Pro", monospace;
        font-size: {base_font}px;
    }}
    QMainWindow {{
        background: {tokens['color.background']};
    }}
    QToolTip {{
        border: 1px solid {tokens['color.border']};
        background: {tokens['color.surface.2']};
        color: {tokens['color.text.1']};
        padding: 6px;
    }}
    QLabel#title {{
        color: {tokens['color.text.1']};
        font-family: "Cinzel", "Playfair Display", serif;
        font-size: {title_font}px;
        letter-spacing: 2px;
    }}
    QLabel#subtitle {{
        color: {tokens['color.text.2']};
        font-size: {subtitle_font}px;
    }}
    QLabel#sectionTitle {{
        font-family: "Cinzel", "Playfair Display", serif;
        font-size: {section_font}px;
        color: {tokens['color.accent']};
    }}
    QLabel#validationError {{
        color: {tokens['color.warning']};
        font-size: {small_font}px;
    }}
    QPushButton {{
        background: {tokens['color.surface.1']};
        border: 1px solid {tokens['color.border']};
        padding: {density_y} {density_x};
        border-radius: {tokens['radius.control']};
        min-height: 18px;
    }}
    QPushButton:hover {{
        border-color: {tokens['color.accent']};
    }}
    QPushButton:disabled {{
        color: {tokens['color.text.muted']};
        border-color: {tokens['color.surface.2']};
    }}
    QPushButton[variant="primary"] {{
        border-color: {tokens['color.accent']};
        color: {tokens['color.accent']};
        background: {tokens['color.surface.2']};
        font-weight: 600;
    }}
    QPushButton[variant="primary"]:hover {{
        border-color: {tokens['color.accent.hover']};
        color: {tokens['color.accent.hover']};
    }}
    QToolButton#sidebarRouteButton {{
        text-align: left;
        padding: 9px 10px;
        border: 1px solid transparent;
        border-radius: 8px;
        background: transparent;
    }}
    QToolButton#sidebarRouteButton[collapsed="true"] {{
        text-align: center;
        border-radius: 18px;
        font-weight: 700;
        min-height: 34px;
        max-height: 34px;
        padding: 0;
        background: {tokens['color.surface.2']};
    }}
    QToolButton#sidebarRouteButton:hover {{
        border-color: {tokens['color.border']};
        background: {tokens['color.surface.2']};
    }}
    QToolButton#sidebarRouteButton:checked {{
        border-color: {tokens['color.accent']};
        color: {tokens['color.accent']};
        background: {tokens['color.surface.3']};
        font-weight: 600;
    }}
    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTreeWidget, QTableWidget {{
        background: {tokens['color.surface.1']};
        border: 1px solid {tokens['color.border']};
        border-radius: 4px;
        padding: 6px;
        selection-background-color: {tokens['color.accent']};
    }}
    QTreeWidget::item:selected, QTableWidget::item:selected {{
        background: {tokens['color.surface.4']};
    }}
    QTableWidget QHeaderView::section {{
        background: {tokens['color.surface.3']};
        color: {tokens['color.text.2']};
        border: 1px solid {tokens['color.border']};
        padding: 5px 6px;
    }}
    QLineEdit[state="error"], QComboBox[state="error"] {{
        border: 2px solid {tokens['color.warning']};
    }}
    QPushButton:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QCheckBox:focus, QTreeWidget:focus, QTableWidget:focus, QPlainTextEdit:focus, QToolButton:focus {{
        border: 2px solid {tokens['focus.ring']};
        outline: none;
    }}
    QGroupBox {{
        border: 1px solid {tokens['color.surface.3']};
        border-radius: 10px;
        margin-top: 8px;
        padding-top: 12px;
        background: {tokens['color.surface.1']};
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {tokens['color.accent']};
    }}
    QProgressBar {{
        border: 1px solid {tokens['color.border']};
        border-radius: 7px;
        text-align: center;
        background: {tokens['color.surface.1']};
    }}
    QProgressBar::chunk {{
        background: {tokens['color.accent']};
    }}
    QFrame#panel {{
        background: {tokens['color.surface.1']};
        border: 1px solid {tokens['color.surface.2']};
        border-radius: 8px;
    }}
    QFrame#hintPanel {{
        background: {tokens['color.surface.1']};
        border: 1px solid {tokens['color.info']};
        border-radius: 9px;
    }}
    QLabel#hintTitle {{
        color: {tokens['color.info']};
        font-weight: 600;
    }}
    QLabel#hintBody {{
        color: {tokens['color.text.2']};
    }}
    QFrame#sidebarRoot {{
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 {tokens['sidebar.gradient.start']},
            stop: 1 {tokens['sidebar.gradient.end']}
        );
        {texture_rule}
        border-right: 1px solid {tokens['color.border']};
    }}
    QLabel#sidebarBrandTitle {{
        font-family: "Cinzel", "Playfair Display", serif;
        font-size: {section_font}px;
        color: {tokens['color.accent']};
        letter-spacing: 1px;
    }}
    QLabel#sidebarBrandSubtitle {{
        color: {tokens['color.text.2']};
        font-size: {small_font}px;
    }}
    QFrame#sidebarDivider {{
        background: {tokens['color.border']};
        min-height: 1px;
        max-height: 1px;
    }}
    QFrame#sidebarRouteIndicator {{
        background: {tokens['color.accent']};
        border-radius: 2px;
    }}
    QLabel#sidebarStatusChip {{
        background: {tokens['color.surface.3']};
        border: 1px solid {tokens['color.border']};
        border-radius: 12px;
        padding: 5px 8px;
        color: {tokens['color.text.2']};
    }}
    QPushButton#sidebarCollapseButton {{
        background: {tokens['color.surface.2']};
        color: {tokens['color.text.2']};
    }}
    QFrame#topContextBar {{
        background: {tokens['color.surface.1']};
        border-bottom: 1px solid {tokens['color.border']};
        {texture_rule}
    }}
    QLabel#contextRouteTitle {{
        font-family: "Cinzel", "Playfair Display", serif;
        color: {tokens['color.accent']};
        font-size: {section_font}px;
    }}
    QLabel#contextRouteCaption {{
        color: {tokens['color.text.2']};
        font-size: {small_font}px;
    }}
    QLabel#contextPathLabel, QLabel#contextSessionLabel {{
        color: {tokens['color.text.2']};
    }}
    QLabel#contextOperationLabel {{
        color: {tokens['color.text.muted']};
        border: 1px solid {tokens['color.border']};
        border-radius: 10px;
        padding: 4px 8px;
    }}
    QLabel#contextOperationLabel[state="running"] {{
        color: {tokens['color.info']};
        border-color: {tokens['color.info']};
    }}
    QLabel#contextOperationLabel[state="error"] {{
        color: {tokens['color.warning']};
        border-color: {tokens['color.warning']};
    }}
    QLabel#contextBusyChip {{
        background: {tokens['color.surface.2']};
        border: 1px solid {tokens['color.border']};
        border-radius: 11px;
        color: {tokens['color.text.2']};
        padding: 4px 8px;
        font-size: {small_font}px;
    }}
    QLabel#contextBusyChip[state="busy"] {{
        border-color: {tokens['color.info']};
        color: {tokens['color.info']};
    }}
    QLabel#contextBusyChip[pulse="true"] {{
        background: {tokens['color.surface.3']};
    }}
    QFrame#metricPill {{
        background: {tokens['color.surface.2']};
        border: 1px solid {tokens['color.border']};
        border-radius: 12px;
    }}
    QFrame#metricPill[state="ok"] {{
        border-color: {tokens['color.success']};
    }}
    QFrame#metricPill[state="warn"] {{
        border-color: {tokens['color.warning']};
    }}
    QLabel#metricPillLabel {{
        color: {tokens['color.text.muted']};
        font-size: {small_font}px;
    }}
    QLabel#metricPillValue {{
        color: {tokens['color.text.1']};
        font-weight: 600;
    }}
    QFrame#emptyStateCard {{
        background: {tokens['color.surface.1']};
        border: 1px dashed {tokens['color.border']};
        border-radius: 10px;
    }}
    QLabel#emptyStateTitle {{
        color: {tokens['color.accent']};
        font-weight: 600;
    }}
    QLabel#emptyStateBody {{
        color: {tokens['color.text.2']};
    }}
    QFrame#sectionHeader {{
        border-bottom: 1px solid {tokens['color.border']};
        padding-bottom: 4px;
    }}
    QLabel#sectionHeaderTitle {{
        color: {tokens['color.text.1']};
        font-family: "Cinzel", "Playfair Display", serif;
    }}
    QLabel#sectionHeaderSubtitle {{
        color: {tokens['color.text.2']};
    }}
    QFrame#actionStrip {{
        background: transparent;
    }}
    QScrollBar:vertical {{
        width: 10px;
        background: {tokens['color.surface.1']};
    }}
    QScrollBar::handle:vertical {{
        background: {tokens['color.surface.4']};
        min-height: 24px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {tokens['color.accent']};
    }}
    QTabWidget::pane {{
        border: 1px solid {tokens['color.border']};
    }}
    QTabBar::tab {{
        background: {tokens['color.surface.1']};
        border: 1px solid {tokens['color.border']};
        padding: 6px 10px;
        margin-right: 2px;
    }}
    QTabBar::tab:selected {{
        border-color: {tokens['color.accent']};
        color: {tokens['color.accent']};
    }}
    QTabBar::tab:focus {{
        border: 2px solid {tokens['focus.ring']};
    }}
    """
