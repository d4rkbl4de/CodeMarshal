"""Tests for marketplace panel widget."""

from __future__ import annotations

import pytest

pytest.importorskip("PySide6")

from PySide6 import QtWidgets

from desktop.widgets.marketplace_panel import MarketplacePanel


def _ensure_qt_app() -> QtWidgets.QApplication:
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication([])
    return app


def test_marketplace_panel_emits_search_apply_share_and_rating() -> None:
    app = _ensure_qt_app()
    panel = MarketplacePanel()
    panel.show()
    app.processEvents()
    search_payloads: list[dict] = []
    apply_values: list[str] = []
    share_payloads: list[dict] = []
    ratings: list[tuple[str, int]] = []

    panel.search_requested.connect(search_payloads.append)
    panel.apply_requested.connect(apply_values.append)
    panel.share_requested.connect(share_payloads.append)
    panel.rating_changed.connect(lambda pattern_id, rating: ratings.append((pattern_id, rating)))

    try:
        panel.marketplace_query_input.setText("security")
        panel.marketplace_tag_input.setText("auth, secrets")
        panel.search_marketplace_btn.click()
        panel.apply_pattern_input.setText("hardcoded_password")
        panel.apply_pattern_btn.click()
        panel.share_pattern_input.setText("hardcoded_password")
        panel.share_bundle_output_input.setText("exports/hardcoded_password.cmpattern.yaml")
        panel.share_pattern_btn.click()
        panel.rating_pattern_input.setText("hardcoded_password")
        panel.rating_spin.setValue(4)
        panel.rate_btn.click()
        app.processEvents()

        assert search_payloads[0]["query"] == "security"
        assert search_payloads[0]["tags"] == ["auth", "secrets"]
        assert apply_values[0] == "hardcoded_password"
        assert share_payloads[0]["pattern_id"] == "hardcoded_password"
        assert ratings[0] == ("hardcoded_password", 4)
    finally:
        panel.close()

