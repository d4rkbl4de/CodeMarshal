"""Marketplace browsing and sharing panel for patterns."""

from __future__ import annotations

from PySide6 import QtCore, QtWidgets

from .a11y import apply_accessible


class MarketplacePanel(QtWidgets.QGroupBox):
    """Panel for marketplace search, apply, share, and rating actions."""

    search_requested = QtCore.Signal(dict)
    apply_requested = QtCore.Signal(str)
    share_requested = QtCore.Signal(dict)
    rating_changed = QtCore.Signal(str, int)

    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__("Marketplace", parent)
        self._build_ui()

    def _build_ui(self) -> None:
        form = QtWidgets.QFormLayout(self)
        form.setContentsMargins(10, 10, 10, 10)
        form.setSpacing(8)

        search_row = QtWidgets.QHBoxLayout()
        self.marketplace_query_input = QtWidgets.QLineEdit()
        self.marketplace_query_input.setPlaceholderText("Search query (optional)")
        self.marketplace_tag_input = QtWidgets.QLineEdit()
        self.marketplace_tag_input.setPlaceholderText("Tags: security,performance")
        self.search_marketplace_btn = QtWidgets.QPushButton("Search Marketplace")
        self.search_marketplace_btn.clicked.connect(self._emit_search)
        apply_accessible(self.marketplace_query_input, name="Pattern marketplace query input")
        apply_accessible(self.marketplace_tag_input, name="Pattern marketplace tags input")
        apply_accessible(self.search_marketplace_btn, name="Search pattern marketplace")
        search_row.addWidget(self.marketplace_query_input, stretch=2)
        search_row.addWidget(self.marketplace_tag_input, stretch=1)
        search_row.addWidget(self.search_marketplace_btn)
        form.addRow("Search:", search_row)

        apply_row = QtWidgets.QHBoxLayout()
        self.apply_pattern_input = QtWidgets.QLineEdit()
        self.apply_pattern_input.setPlaceholderText("Pattern ID or bundle path")
        self.apply_pattern_btn = QtWidgets.QPushButton("Apply Pattern")
        self.apply_pattern_btn.clicked.connect(self._emit_apply)
        apply_accessible(self.apply_pattern_input, name="Pattern apply reference")
        apply_accessible(self.apply_pattern_btn, name="Apply selected pattern")
        apply_row.addWidget(self.apply_pattern_input, stretch=1)
        apply_row.addWidget(self.apply_pattern_btn)
        form.addRow("Apply:", apply_row)

        share_row = QtWidgets.QHBoxLayout()
        self.share_pattern_input = QtWidgets.QLineEdit()
        self.share_pattern_input.setPlaceholderText("Pattern ID to share")
        self.share_bundle_output_input = QtWidgets.QLineEdit()
        self.share_bundle_output_input.setPlaceholderText("Optional bundle output path")
        self.share_pattern_btn = QtWidgets.QPushButton("Share Pattern")
        self.share_pattern_btn.clicked.connect(self._emit_share)
        apply_accessible(self.share_pattern_input, name="Pattern share id input")
        apply_accessible(self.share_bundle_output_input, name="Pattern share output path")
        apply_accessible(self.share_pattern_btn, name="Share selected pattern")
        share_row.addWidget(self.share_pattern_input, stretch=1)
        share_row.addWidget(self.share_bundle_output_input, stretch=2)
        share_row.addWidget(self.share_pattern_btn)
        form.addRow("Share:", share_row)

        rate_row = QtWidgets.QHBoxLayout()
        self.rating_pattern_input = QtWidgets.QLineEdit()
        self.rating_pattern_input.setPlaceholderText("Pattern ID to rate")
        self.rating_spin = QtWidgets.QSpinBox()
        self.rating_spin.setRange(1, 5)
        self.rating_spin.setValue(5)
        self.rate_btn = QtWidgets.QPushButton("Rate")
        self.rate_btn.clicked.connect(self._emit_rate)
        apply_accessible(self.rating_pattern_input, name="Pattern rating id input")
        apply_accessible(self.rating_spin, name="Pattern rating value")
        apply_accessible(self.rate_btn, name="Submit pattern rating")
        rate_row.addWidget(self.rating_pattern_input, stretch=2)
        rate_row.addWidget(self.rating_spin)
        rate_row.addWidget(self.rate_btn)
        form.addRow("Rate:", rate_row)

    def _emit_search(self) -> None:
        tag_text = self.marketplace_tag_input.text().strip()
        tags = [item.strip() for item in tag_text.replace(";", ",").split(",") if item.strip()]
        self.search_requested.emit(
            {
                "query": self.marketplace_query_input.text().strip(),
                "tags": tags,
            }
        )

    def _emit_apply(self) -> None:
        self.apply_requested.emit(self.apply_pattern_input.text().strip())

    def _emit_share(self) -> None:
        self.share_requested.emit(
            {
                "pattern_id": self.share_pattern_input.text().strip(),
                "bundle_out": self.share_bundle_output_input.text().strip() or None,
                "include_examples": False,
            }
        )

    def _emit_rate(self) -> None:
        pattern_id = self.rating_pattern_input.text().strip()
        if not pattern_id:
            return
        self.rating_changed.emit(pattern_id, int(self.rating_spin.value()))

