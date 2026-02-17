"""Reusable desktop GUI widgets."""

from .action_strip import ActionStrip
from .a11y import apply_accessible, clear_invalid, mark_invalid
from .empty_state_card import EmptyStateCard
from .error_dialog import ErrorDialog
from .diff_viewer import DiffViewer
from .hint_panel import HintPanel
from .history_sidebar import HistorySidebar
from .knowledge_canvas import KnowledgeCanvas
from .comments_panel import CommentsPanel
from .marketplace_panel import MarketplacePanel
from .metric_pill import MetricPill
from .onboarding_dialog import OnboardingDialog
from .page_scaffold import PageScaffold
from .results_viewer import ResultsViewer
from .section_header import SectionHeader
from .sidebar_nav import SidebarNav
from .templates_panel import TemplatesPanel
from .top_context_bar import TopContextBar

__all__ = [
    "ActionStrip",
    "CommentsPanel",
    "DiffViewer",
    "EmptyStateCard",
    "ErrorDialog",
    "HistorySidebar",
    "HintPanel",
    "KnowledgeCanvas",
    "MarketplacePanel",
    "MetricPill",
    "OnboardingDialog",
    "PageScaffold",
    "ResultsViewer",
    "SectionHeader",
    "SidebarNav",
    "TemplatesPanel",
    "TopContextBar",
    "apply_accessible",
    "mark_invalid",
    "clear_invalid",
]
