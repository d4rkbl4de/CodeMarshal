"""
inquiry.answers - Answer generation from observations.

This module generates answers to questions based on collected observations.
All answers are derived from facts only - no inference or interpretation.
"""

from .structure_analyzer import StructureAnalyzer
from .connection_mapper import ConnectionMapper
from .anomaly_detector import AnomalyDetector
from .purpose_extractor import PurposeExtractor
from .thinking_engine import ThinkingEngine

__all__ = [
    "StructureAnalyzer",
    "ConnectionMapper",
    "AnomalyDetector",
    "PurposeExtractor",
    "ThinkingEngine",
]
