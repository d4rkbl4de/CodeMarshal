"""
Theme definitions for the desktop GUI.

High-contrast, dark palette with detective-inspired accents.
"""

PALETTE = {
    "background": "#0B0B0C",
    "surface_primary": "#151518",
    "surface_secondary": "#1D1E22",
    "accent": "#E0C469",
    "warning": "#D96C6C",
    "success": "#6BD98C",
    "text_primary": "#F0F0F0",
    "text_secondary": "#A0A0A0",
}


def build_stylesheet() -> str:
    """Return a global stylesheet for the desktop GUI."""
    return f"""
    QWidget {{
        background: {PALETTE['background']};
        color: {PALETTE['text_primary']};
        font-family: "IBM Plex Mono", "Source Code Pro", monospace;
        font-size: 13px;
    }}
    QLabel#title {{
        color: {PALETTE['text_primary']};
        font-family: "Cinzel", "Playfair Display", serif;
        font-size: 34px;
        letter-spacing: 2px;
    }}
    QLabel#subtitle {{
        color: {PALETTE['text_secondary']};
        font-size: 12px;
    }}
    QLabel#sectionTitle {{
        font-family: "Cinzel", "Playfair Display", serif;
        font-size: 20px;
        color: {PALETTE['accent']};
    }}
    QPushButton {{
        background: {PALETTE['surface_primary']};
        border: 1px solid {PALETTE['surface_secondary']};
        padding: 10px 14px;
        border-radius: 6px;
    }}
    QPushButton:hover {{
        border-color: {PALETTE['accent']};
    }}
    QPushButton:disabled {{
        color: {PALETTE['text_secondary']};
        border-color: {PALETTE['surface_secondary']};
    }}
    QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QTreeWidget, QTableWidget {{
        background: {PALETTE['surface_primary']};
        border: 1px solid {PALETTE['surface_secondary']};
        border-radius: 4px;
        padding: 6px;
    }}
    QGroupBox {{
        border: 1px solid {PALETTE['surface_secondary']};
        border-radius: 8px;
        margin-top: 8px;
        padding-top: 12px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 4px;
        color: {PALETTE['accent']};
    }}
    QProgressBar {{
        border: 1px solid {PALETTE['surface_secondary']};
        border-radius: 6px;
        text-align: center;
        background: {PALETTE['surface_primary']};
    }}
    QProgressBar::chunk {{
        background: {PALETTE['accent']};
    }}
    QFrame#panel {{
        background: {PALETTE['surface_primary']};
        border: 1px solid {PALETTE['surface_secondary']};
        border-radius: 8px;
    }}
    """
