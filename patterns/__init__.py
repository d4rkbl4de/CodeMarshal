"""
Pattern detection package.

Provides pattern loading, scanning, and engine utilities.
"""

from patterns.engine import FixSuggestion, PatternEngine, StatisticalAnomaly
from patterns.loader import (
    PatternDefinition,
    PatternLoader,
    PatternManager,
    PatternMatch,
    PatternScanResult,
    PatternScanner,
    load_patterns,
    scan_patterns,
)

__all__ = [
    "FixSuggestion",
    "PatternEngine",
    "StatisticalAnomaly",
    "PatternDefinition",
    "PatternLoader",
    "PatternManager",
    "PatternMatch",
    "PatternScanResult",
    "PatternScanner",
    "load_patterns",
    "scan_patterns",
]
