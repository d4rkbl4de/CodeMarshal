"""
inquiry.answers - Answer generation from observations.

This module generates answers to questions based on collected observations.
All answers are derived from facts only - no inference or interpretation.
"""

from .anomaly_detector import AnomalyDetector
from .connection_mapper import ConnectionMapper
from .purpose_extractor import PurposeExtractor
from .structure_analyzer import StructureAnalyzer
from .thinking_engine import ThinkingEngine

__all__ = [
    "StructureAnalyzer",
    "ConnectionMapper",
    "AnomalyDetector",
    "PurposeExtractor",
    "ThinkingEngine",
]
