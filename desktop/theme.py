"""Compatibility wrapper for desktop theme exports."""

from __future__ import annotations

from .ui.themes import (
    HIGH_CONTRAST_OVERRIDES,
    THEME_FAMILIES,
    THEME_PREVIEWS,
    THEME_VARIANTS,
    build_stylesheet,
    list_theme_previews,
)

__all__ = [
    "THEME_VARIANTS",
    "THEME_FAMILIES",
    "THEME_PREVIEWS",
    "HIGH_CONTRAST_OVERRIDES",
    "build_stylesheet",
    "list_theme_previews",
]
