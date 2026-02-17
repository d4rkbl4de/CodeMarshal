"""
Pattern detection package.

Provides pattern loading, scanning, and engine utilities.
"""

from patterns.engine import FixSuggestion, PatternEngine, StatisticalAnomaly
from patterns.collector import (
    CurationDecision,
    PatternCollector,
    PatternSubmission,
    ValidationReport,
)
from patterns.loader import (
    PatternDefinition,
    PatternLoader,
    PatternManager,
    PatternMatch,
    PatternScanner,
    PatternScanResult,
    load_patterns,
    scan_patterns,
)
from patterns.marketplace import (
    MarketplacePattern,
    MarketplaceQuery,
    MarketplaceSearchResult,
    PatternMarketplace,
    PatternPackage,
    PatternRatingSummary,
    PatternReview,
)
from patterns.templates import (
    PatternTemplate,
    PatternTemplateRegistry,
    TemplateField,
    TemplateInstance,
)

__all__ = [
    "FixSuggestion",
    "PatternEngine",
    "StatisticalAnomaly",
    "PatternCollector",
    "PatternSubmission",
    "ValidationReport",
    "CurationDecision",
    "PatternDefinition",
    "PatternLoader",
    "PatternManager",
    "PatternMatch",
    "PatternScanResult",
    "PatternScanner",
    "load_patterns",
    "scan_patterns",
    "PatternMarketplace",
    "MarketplacePattern",
    "MarketplaceQuery",
    "MarketplaceSearchResult",
    "PatternPackage",
    "PatternRatingSummary",
    "PatternReview",
    "PatternTemplate",
    "TemplateField",
    "TemplateInstance",
    "PatternTemplateRegistry",
]
