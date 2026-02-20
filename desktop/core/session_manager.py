"""Session and desktop state persistence for the GUI."""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SessionManager:
    """Persists lightweight GUI state and recent investigations."""

    _MAX_RECENTS = 10
    _MAX_RECENT_PATHS = 10

    def __init__(self, state_path: Path | None = None) -> None:
        self._state_path = state_path or Path("storage") / "gui_state.json"
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._state = self._load_state()

    @property
    def state_path(self) -> Path:
        return self._state_path

    def _default_state(self) -> dict[str, Any]:
        return {
            "recent_investigations": [],
            "recent_paths": [],
            "last_path": str(Path(".").resolve()),
            "settings": {
                "theme": "dark",
                "default_export_format": "json",
                "storage_path": "storage",
                "auto_run_last_used_options": False,
            },
            "ui": {
                "last_view": "home",
                "window_geometry": None,
                "window_state": None,
                "onboarding_completed": False,
                "onboarding_version": 1,
                "show_context_hints": True,
                "accessibility_mode": "standard",
                "font_scale": 1.0,
                "visual_theme_variant": "noir_premium",
                "theme_family": "dark",
                "motion_level": "standard",
                "sidebar_collapsed": False,
                "reduced_motion": False,
                "ui_density": "comfortable",
                "accent_intensity": "normal",
                "knowledge_canvas_filters": {},
                "history_sidebar_visible": True,
                "comments_panel_collapsed": False,
                "layout_splitter_ratios": {},
            },
            "dirty": False,
            "last_saved_at": None,
            "last_session_id": None,
            "recovery": {
                "pending": False,
                "session_id": None,
                "path": None,
                "timestamp": None,
            },
        }

    def _load_state(self) -> dict[str, Any]:
        if not self._state_path.exists():
            return self._default_state()

        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
            base = self._default_state()
            base.update({k: v for k, v in data.items() if k in base})
            if not isinstance(base.get("recent_investigations"), list):
                base["recent_investigations"] = []
            if not isinstance(base.get("recent_paths"), list):
                base["recent_paths"] = []
            if not isinstance(base.get("settings"), dict):
                base["settings"] = self._default_state()["settings"]
            else:
                merged_settings = dict(self._default_state()["settings"])
                merged_settings.update(base["settings"])
                base["settings"] = merged_settings
            if not isinstance(base.get("ui"), dict):
                base["ui"] = self._default_state()["ui"]
            else:
                merged_ui = dict(self._default_state()["ui"])
                merged_ui.update(base["ui"])
                if not isinstance(merged_ui.get("layout_splitter_ratios"), dict):
                    merged_ui["layout_splitter_ratios"] = {}
                base["ui"] = merged_ui
            return base
        except Exception:
            return self._default_state()

    def _save_state(self) -> None:
        temp_path = self._state_path.with_suffix(".tmp")
        payload = json.dumps(self._state, indent=2, ensure_ascii=True, default=str)

        for _attempt in range(3):
            try:
                temp_path.write_text(payload, encoding="utf-8")
                temp_path.replace(self._state_path)
                return
            except PermissionError:
                time.sleep(0.05)

        # Fallback when atomic replace is blocked by transient file locks.
        self._state_path.write_text(payload, encoding="utf-8")
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass

    def get_recent_investigations(self, limit: int = 10) -> list[dict[str, Any]]:
        with self._lock:
            recent = self._state.get("recent_investigations", [])
            return list(recent[: max(limit, 0)])

    def add_recent_investigation(self, metadata: dict[str, Any]) -> None:
        session_id = str(metadata.get("session_id") or metadata.get("id") or "")
        if not session_id:
            return

        now = datetime.now(UTC).isoformat()
        record = {
            "session_id": session_id,
            "name": str(metadata.get("name") or session_id),
            "path": str(metadata.get("path") or ""),
            "scope": str(metadata.get("scope") or ""),
            "intent": str(metadata.get("intent") or ""),
            "file_count": int(metadata.get("file_count") or 0),
            "modified_at": str(metadata.get("modified_at") or now),
            "created_at": str(metadata.get("created_at") or now),
        }

        with self._lock:
            current = [
                item
                for item in self._state.get("recent_investigations", [])
                if str(item.get("session_id")) != session_id
            ]
            current.insert(0, record)
            self._state["recent_investigations"] = current[: self._MAX_RECENTS]
            self._state["last_session_id"] = session_id
            self._state["last_saved_at"] = now
            self._save_state()

    def remove_recent_investigation(self, session_id: str) -> None:
        with self._lock:
            current = [
                item
                for item in self._state.get("recent_investigations", [])
                if str(item.get("session_id")) != str(session_id)
            ]
            self._state["recent_investigations"] = current
            self._save_state()

    def merge_recent_investigations(self, sessions: list[dict[str, Any]]) -> None:
        """Merge storage sessions into the GUI recent list."""
        for session in sessions:
            self.add_recent_investigation(session)

    def get_last_path(self) -> str:
        with self._lock:
            return str(self._state.get("last_path") or str(Path(".").resolve()))

    def set_last_path(self, path: str | Path) -> None:
        with self._lock:
            resolved = str(Path(path).resolve())
            self._state["last_path"] = resolved
            self._add_recent_path_locked(resolved)
            self._save_state()

    def _add_recent_path_locked(self, path: str) -> None:
        current = [item for item in self._state.get("recent_paths", []) if item != path]
        current.insert(0, path)
        self._state["recent_paths"] = current[: self._MAX_RECENT_PATHS]

    def add_recent_path(self, path: str | Path) -> None:
        with self._lock:
            self._add_recent_path_locked(str(Path(path).resolve()))
            self._save_state()

    def get_recent_paths(self, limit: int = 10) -> list[str]:
        with self._lock:
            values = [str(item) for item in self._state.get("recent_paths", [])]
            return values[: max(limit, 0)]

    def get_settings(self) -> dict[str, Any]:
        with self._lock:
            return dict(self._state.get("settings", {}))

    def update_settings(self, updates: dict[str, Any]) -> None:
        with self._lock:
            settings = dict(self._state.get("settings", {}))
            settings.update(updates)
            self._state["settings"] = settings
            self._save_state()

    def get_default_export_format(self) -> str:
        return str(self.get_settings().get("default_export_format") or "json")

    def set_default_export_format(self, fmt: str) -> None:
        self.update_settings({"default_export_format": fmt})

    def get_auto_run_last_used_options(self) -> bool:
        return bool(self.get_settings().get("auto_run_last_used_options", False))

    def set_auto_run_last_used_options(self, enabled: bool) -> None:
        self.update_settings({"auto_run_last_used_options": bool(enabled)})

    def get_last_view(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return str(ui.get("last_view") or "home")

    def set_last_view(self, view_name: str) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["last_view"] = str(view_name or "home")
            self._state["ui"] = ui
            self._save_state()

    def get_window_geometry(self) -> str | None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            value = ui.get("window_geometry")
            return str(value) if value else None

    def set_window_geometry(self, geometry_hex: str | None) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["window_geometry"] = str(geometry_hex) if geometry_hex else None
            self._state["ui"] = ui
            self._save_state()

    def get_window_state(self) -> str | None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            value = ui.get("window_state")
            return str(value) if value else None

    def set_window_state(self, state_hex: str | None) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["window_state"] = str(state_hex) if state_hex else None
            self._state["ui"] = ui
            self._save_state()

    def is_onboarding_completed(self) -> bool:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return bool(ui.get("onboarding_completed", False))

    def set_onboarding_completed(self, value: bool) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["onboarding_completed"] = bool(value)
            ui["onboarding_version"] = int(ui.get("onboarding_version") or 1)
            self._state["ui"] = ui
            self._save_state()

    def get_show_context_hints(self) -> bool:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return bool(ui.get("show_context_hints", True))

    def set_show_context_hints(self, value: bool) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["show_context_hints"] = bool(value)
            self._state["ui"] = ui
            self._save_state()

    def get_accessibility_mode(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            mode = str(ui.get("accessibility_mode") or "standard").strip().lower()
            return mode if mode in {"standard", "high_contrast"} else "standard"

    def set_accessibility_mode(self, mode: str) -> None:
        normalized = str(mode or "standard").strip().lower()
        if normalized not in {"standard", "high_contrast"}:
            normalized = "standard"
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["accessibility_mode"] = normalized
            self._state["ui"] = ui
            self._save_state()

    def get_font_scale(self) -> float:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            value = ui.get("font_scale", 1.0)
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                parsed = 1.0
            return max(0.8, min(1.6, parsed))

    def set_font_scale(self, scale: float) -> None:
        try:
            parsed = float(scale)
        except (TypeError, ValueError):
            parsed = 1.0
        parsed = max(0.8, min(1.6, parsed))
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["font_scale"] = parsed
            self._state["ui"] = ui
            self._save_state()

    def get_visual_theme_variant(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            variant = (
                str(ui.get("visual_theme_variant") or "noir_premium").strip().lower()
            )
            return (
                variant
                if variant
                in {
                    "void",
                    "noir_premium",
                    "noir",
                    "ledger",
                    "linen_day",
                    "harbor_light",
                }
                else "noir_premium"
            )

    def set_visual_theme_variant(self, variant: str) -> None:
        normalized = str(variant or "noir_premium").strip().lower()
        if normalized not in {
            "void",
            "noir_premium",
            "noir",
            "ledger",
            "linen_day",
            "harbor_light",
        }:
            normalized = "noir_premium"
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["visual_theme_variant"] = normalized
            ui["theme_family"] = (
                "light" if normalized in {"linen_day", "harbor_light"} else "dark"
            )
            self._state["ui"] = ui
            self._save_state()

    def get_theme_family(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            family = str(ui.get("theme_family") or "dark").strip().lower()
            return family if family in {"dark", "light"} else "dark"

    def set_theme_family(self, family: str) -> None:
        normalized = str(family or "dark").strip().lower()
        if normalized not in {"dark", "light"}:
            normalized = "dark"
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["theme_family"] = normalized
            self._state["ui"] = ui
            self._save_state()

    def get_motion_level(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            level = str(ui.get("motion_level") or "standard").strip().lower()
            return level if level in {"full", "standard", "reduced"} else "standard"

    def set_motion_level(self, level: str) -> None:
        normalized = str(level or "standard").strip().lower()
        if normalized not in {"full", "standard", "reduced"}:
            normalized = "standard"
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["motion_level"] = normalized
            if normalized == "reduced":
                ui["reduced_motion"] = True
            self._state["ui"] = ui
            self._save_state()

    def get_sidebar_collapsed(self) -> bool:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return bool(ui.get("sidebar_collapsed", False))

    def set_sidebar_collapsed(self, collapsed: bool) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["sidebar_collapsed"] = bool(collapsed)
            self._state["ui"] = ui
            self._save_state()

    def get_reduced_motion(self) -> bool:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return bool(ui.get("reduced_motion", False))

    def set_reduced_motion(self, enabled: bool) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["reduced_motion"] = bool(enabled)
            if enabled:
                ui["motion_level"] = "reduced"
            elif str(ui.get("motion_level") or "").strip().lower() == "reduced":
                ui["motion_level"] = "standard"
            self._state["ui"] = ui
            self._save_state()

    def get_ui_density(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            value = str(ui.get("ui_density") or "comfortable").strip().lower()
            return value if value in {"comfortable", "compact"} else "comfortable"

    def set_ui_density(self, density: str) -> None:
        normalized = str(density or "comfortable").strip().lower()
        if normalized not in {"comfortable", "compact"}:
            normalized = "comfortable"
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["ui_density"] = normalized
            self._state["ui"] = ui
            self._save_state()

    def get_accent_intensity(self) -> str:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            value = str(ui.get("accent_intensity") or "normal").strip().lower()
            return value if value in {"soft", "normal", "bold"} else "normal"

    def set_accent_intensity(self, intensity: str) -> None:
        normalized = str(intensity or "normal").strip().lower()
        if normalized not in {"soft", "normal", "bold"}:
            normalized = "normal"
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["accent_intensity"] = normalized
            self._state["ui"] = ui
            self._save_state()

    def get_knowledge_canvas_filters(self) -> dict[str, Any]:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            payload = ui.get("knowledge_canvas_filters", {})
            return dict(payload) if isinstance(payload, dict) else {}

    def set_knowledge_canvas_filters(self, filters: dict[str, Any]) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["knowledge_canvas_filters"] = (
                dict(filters) if isinstance(filters, dict) else {}
            )
            self._state["ui"] = ui
            self._save_state()

    def get_history_sidebar_visible(self) -> bool:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return bool(ui.get("history_sidebar_visible", True))

    def set_history_sidebar_visible(self, visible: bool) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["history_sidebar_visible"] = bool(visible)
            self._state["ui"] = ui
            self._save_state()

    def get_comments_panel_collapsed(self) -> bool:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            return bool(ui.get("comments_panel_collapsed", False))

    def set_comments_panel_collapsed(self, collapsed: bool) -> None:
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ui["comments_panel_collapsed"] = bool(collapsed)
            self._state["ui"] = ui
            self._save_state()

    def get_layout_splitter_ratio(self, route: str, default: float = 0.42) -> float:
        name = str(route or "").strip().lower()
        fallback = max(0.2, min(0.8, float(default)))
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ratios = ui.get("layout_splitter_ratios", {})
            if not isinstance(ratios, dict):
                return fallback
            value = ratios.get(name)
            try:
                parsed = float(value)
            except (TypeError, ValueError):
                return fallback
            return max(0.2, min(0.8, parsed))

    def set_layout_splitter_ratio(self, route: str, ratio: float) -> None:
        name = str(route or "").strip().lower()
        if not name:
            return
        try:
            parsed = float(ratio)
        except (TypeError, ValueError):
            parsed = 0.42
        normalized = max(0.2, min(0.8, parsed))
        with self._lock:
            ui = dict(self._state.get("ui", {}))
            ratios = ui.get("layout_splitter_ratios", {})
            if not isinstance(ratios, dict):
                ratios = {}
            updated = dict(ratios)
            updated[name] = normalized
            ui["layout_splitter_ratios"] = updated
            self._state["ui"] = ui
            self._save_state()

    def mark_dirty(self, dirty: bool, session_id: str | None = None) -> None:
        with self._lock:
            self._state["dirty"] = bool(dirty)
            if session_id:
                self._state["last_session_id"] = session_id
            if dirty:
                self._state["recovery"] = {
                    "pending": True,
                    "session_id": session_id or self._state.get("last_session_id"),
                    "path": self._state.get("last_path"),
                    "timestamp": datetime.now(UTC).isoformat(),
                }
            else:
                self._state["recovery"] = {
                    "pending": False,
                    "session_id": None,
                    "path": None,
                    "timestamp": None,
                }
            self._save_state()

    def save_recovery_state(self, session_id: str, path: str | Path) -> None:
        with self._lock:
            self._state["recovery"] = {
                "pending": True,
                "session_id": session_id,
                "path": str(path),
                "timestamp": datetime.now(UTC).isoformat(),
            }
            self._save_state()

    def get_recovery_state(self) -> dict[str, Any] | None:
        with self._lock:
            recovery = dict(self._state.get("recovery", {}))
            if recovery.get("pending"):
                return recovery
            return None

    def clear_recovery_state(self) -> None:
        with self._lock:
            self._state["recovery"] = {
                "pending": False,
                "session_id": None,
                "path": None,
                "timestamp": None,
            }
            self._state["dirty"] = False
            self._save_state()
