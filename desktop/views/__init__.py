"""
Desktop GUI views.
"""

from .export import ExportView
from .home import HomeView
from .investigate import InvestigateView
from .knowledge import KnowledgeView
from .observe import ObserveView
from .patterns import PatternsView

__all__ = [
    "HomeView",
    "ObserveView",
    "InvestigateView",
    "KnowledgeView",
    "PatternsView",
    "ExportView",
]
