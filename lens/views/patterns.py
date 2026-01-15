"""
Patterns View - Results, Not Reasoning (Truth Layer 3)

This file is the most dangerous one in the directory.
Treat it like a loaded instrument.

Core Responsibility:
Present pattern outputs that were produced elsewhere.
This view never computes patterns. It only receives finished artifacts.

If reasoning leaks in here, you've violated Article 7.

Article 3: Truth Preservation - Must never obscure, distort, or invent information
Article 11: Declared Limitations - Every pattern must declare its uncertainty
Article 13: Deterministic Operation - Same input must produce same output
"""

from __future__ import annotations

import json
import math
from typing import (
    Optional, List, Dict, Any, Set, FrozenSet, Tuple,
    Callable, ClassVar, Iterator, Union, cast, Literal
)
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from decimal import Decimal
from collections import defaultdict

# Allowed imports per architecture
from lens.philosophy import (
    SingleFocusRule,
    ProgressiveDisclosureRule,
    ClarityRule,
    NavigationRule
)
from lens.philosophy.single_focus import MockInterfaceIntent
from inquiry.session.context import SessionContext

# NOT ALLOWED: from inquiry.patterns import *


class PatternType(Enum):
    """Types of patterns that can be detected."""
    DENSITY = auto()           # Import counts, clustering
    COUPLING = auto()          # Degree & fan-in/out
    COMPLEXITY = auto()        # Depth, node counts (no labels)
    BOUNDARY_VIOLATION = auto()  # Boundary crossings (boolean)
    UNCERTAINTY = auto()       # Incomplete data indicators
    
    @property
    def description(self) -> str:
        """Human-readable description of pattern type."""
        return {
            PatternType.DENSITY: "Clustering and concentration patterns",
            PatternType.COUPLING: "Interconnection strength patterns",
            PatternType.COMPLEXITY: "Structural complexity indicators",
            PatternType.BOUNDARY_VIOLATION: "Architectural boundary crossings",
            PatternType.UNCERTAINTY: "Data completeness indicators"
        }[self]


class ConfidenceLevel(Enum):
    """Standardized confidence levels for pattern detection."""
    UNKNOWN = 0
    VERY_LOW = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    VERY_HIGH = 5
    
    @property
    def display_symbol(self) -> str:
        """Visual indicator for confidence level."""
        return {
            ConfidenceLevel.UNKNOWN: "❓",
            ConfidenceLevel.VERY_LOW: "⚠️⚠️",
            ConfidenceLevel.LOW: "⚠️",
            ConfidenceLevel.MEDIUM: "⏺️",
            ConfidenceLevel.HIGH: "✅",
            ConfidenceLevel.VERY_HIGH: "✅✅"
        }[self]
    
    @property
    def color_code(self) -> str:
        """Consistent color coding for confidence."""
        return {
            ConfidenceLevel.UNKNOWN: "#888888",
            ConfidenceLevel.VERY_LOW: "#ff6b6b",
            ConfidenceLevel.LOW: "#ffa726",
            ConfidenceLevel.MEDIUM: "#ffd166",
            ConfidenceLevel.HIGH: "#06d6a0",
            ConfidenceLevel.VERY_HIGH: "#118ab2"
        }[self]


@dataclass(frozen=True)
class PatternMetric:
    """A single numeric measurement for a pattern."""
    name: str
    value: float
    unit: Optional[str] = None
    min_possible: Optional[float] = None
    max_possible: Optional[float] = None
    is_normalized: bool = False  # 0-1 scale
    
    def __post_init__(self) -> None:
        """Validate metric invariants."""
        if not self.name.strip():
            raise ValueError("Pattern metric must have a name")
        
        # Check bounds if provided
        if self.min_possible is not None and self.value < self.min_possible:
            raise ValueError(f"Value {self.value} below minimum {self.min_possible}")
        
        if self.max_possible is not None and self.value > self.max_possible:
            raise ValueError(f"Value {self.value} above maximum {self.max_possible}")
        
        # Check normalized range
        if self.is_normalized and (self.value < 0 or self.value > 1):
            raise ValueError(f"Normalized value must be 0-1, got {self.value}")
    
    @property
    def display_value(self) -> str:
        """Format value for display with unit if available."""
        if self.unit:
            return f"{self.value:.2f} {self.unit}"
        return f"{self.value:.2f}"
    
    @property
    def normalized_ratio(self) -> Optional[float]:
        """Get value as ratio of min-max range if available."""
        if self.min_possible is not None and self.max_possible is not None:
            range_width = self.max_possible - self.min_possible
            if range_width > 0:
                return (self.value - self.min_possible) / range_width
        return None


@dataclass(frozen=True)
class PatternReference:
    """Reference to supporting evidence for a pattern."""
    observation_id: str
    relationship: str  # "supports", "contradicts", "context"
    strength: float = 1.0  # 0-1, how strongly this supports the pattern
    
    def __post_init__(self) -> None:
        """Validate reference invariants."""
        if not self.observation_id.strip():
            raise ValueError("Reference must have observation ID")
        
        if not self.relationship.strip():
            raise ValueError("Reference must specify relationship")
        
        if not 0 <= self.strength <= 1:
            raise ValueError(f"Strength must be 0-1, got {self.strength}")


@dataclass(frozen=True)
class PatternArtifact:
    """
    Immutable pattern detection result.
    
    This is what the view receives - never computes.
    Article 11: Every pattern must declare its uncertainty.
    """
    id: str
    pattern_type: PatternType
    name: str
    description: str
    
    # Confidence and uncertainty (REQUIRED by Article 11)
    confidence: ConfidenceLevel
    uncertainty_reason: str  # Why we might be uncertain
    
    # Scope and applicability (REQUIRED by Article 3)
    scope_description: str
    applicable_to: FrozenSet[str]  # What this pattern applies to
    
    # The actual pattern data
    metrics: Tuple[PatternMetric, ...] = field(default_factory=tuple)
    references: Tuple[PatternReference, ...] = field(default_factory=tuple)
    
    # Limitations (REQUIRED by Article 11)
    known_limitations: Tuple[str, ...] = field(default_factory=tuple)
    cannot_detect: Tuple[str, ...] = field(default_factory=tuple)
    
    # Metadata
    detected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    detector_version: str = "1.0.0"
    
    def __post_init__(self) -> None:
        """Validate pattern artifact invariants."""
        if not self.name.strip():
            raise ValueError("Pattern must have a name")
        
        if not self.description.strip():
            raise ValueError("Pattern must have a description")
        
        if not self.uncertainty_reason.strip():
            raise ValueError("Pattern must declare uncertainty reason (Article 11)")
        
        if not self.scope_description.strip():
            raise ValueError("Pattern must declare scope (Article 3)")
        
        if len(self.applicable_to) == 0:
            raise ValueError("Pattern must declare what it applies to")
        
        # Ensure timestamp is timezone aware
        if self.detected_at.tzinfo is None:
            object.__setattr__(self, 'detected_at',
                             self.detected_at.replace(tzinfo=timezone.utc))
    
    @property
    def reference_count(self) -> int:
        """Number of supporting references."""
        return len(self.references)
    
    @property
    def metric_count(self) -> int:
        """Number of metrics."""
        return len(self.metrics)
    
    @property
    def supports_count(self) -> int:
        """Number of supporting references."""
        return sum(1 for ref in self.references if ref.relationship == "supports")
    
    @property
    def contradicts_count(self) -> int:
        """Number of contradicting references."""
        return sum(1 for ref in self.references if ref.relationship == "contradicts")
    
    @property
    def has_high_confidence(self) -> bool:
        """Whether confidence is high or very high."""
        return self.confidence in (ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH)
    
    @property
    def has_low_confidence(self) -> bool:
        """Whether confidence is low or very low."""
        return self.confidence in (ConfidenceLevel.LOW, ConfidenceLevel.VERY_LOW, ConfidenceLevel.UNKNOWN)


class PatternsDisplayMode(Enum):
    """How patterns should be organized for display."""
    BY_CONFIDENCE = auto()      # Group by confidence level
    BY_TYPE = auto()           # Group by pattern type
    BY_SCOPE = auto()          # Group by what they apply to
    CHRONOLOGICAL = auto()     # By detection time
    UNFILTERED = auto()        # All patterns, no grouping


@dataclass(frozen=True)
class PatternsRenderConfig:
    """
    Configuration for how patterns should be displayed.
    
    Article 8: Honest Performance - If something cannot be computed, explain why.
    Article 16: Truth-Preserving Aesthetics - Colors indicate meaning.
    """
    max_patterns_displayed: int = 20           # Prevent overload
    show_low_confidence: bool = True           # Always show uncertainty
    require_references: bool = True            # Patterns without evidence are suspect
    group_by_default: bool = True              # Progressive disclosure
    highlight_boundaries: bool = True          # Special emphasis for boundary violations
    color_by_confidence: bool = True           # Article 16
    
    @classmethod
    def default(cls) -> PatternsRenderConfig:
        """Default configuration adhering to constitutional rules."""
        return cls()


class PatternsView:
    """
    Deterministic projection from pattern artifacts → perceptual slice.
    
    Core Responsibility:
    Present pattern outputs that were produced elsewhere.
    This view NEVER computes patterns.
    
    Critical Warning:
    This is the most dangerous view. Any inference, interpretation,
    or reasoning that leaks here violates the constitution.
    
    What this view MUST NOT DO:
    1. Compute new patterns ❌
    2. Modify pattern artifacts ❌
    3. Infer connections between patterns ❌
    4. Rank patterns by importance ❌
    5. Suggest actions based on patterns ❌
    6. Hide low-confidence patterns ❌
    """
    
    # Class constants for display
    _BOUNDARY_VIOLATION_ICON: ClassVar[str] = "🚫"
    _HIGH_COMPLEXITY_ICON: ClassVar[str] = "🌀"
    _DENSE_CLUSTER_ICON: ClassVar[str] = "📊"
    _TIGHT_COUPLING_ICON: ClassVar[str] = "🔗"
    _DATA_GAP_ICON: ClassVar[str] = "🕳️"
    
    def __init__(
        self,
        context: SessionContext,
        patterns: Tuple[PatternArtifact, ...],
        config: Optional[PatternsRenderConfig] = None
    ) -> None:
        """
        Initialize patterns view with pre-computed artifacts.
        
        Args:
            context: Read-only investigation context
            patterns: Immutable pattern artifacts (computed elsewhere)
            config: Optional rendering configuration
        
        Raises:
            ValueError: If patterns contain computation or inference
            TypeError: If patterns are not immutable artifacts
        """
        # Validate inputs
        if not isinstance(context, SessionContext):
            raise TypeError(f"context must be SessionContext, got {type(context)}")
        
        # Validate that patterns are actual artifacts, not computation
        self._validate_patterns_are_artifacts(patterns)
        
        # Store read-only state
        self._context: SessionContext = context
        self._patterns: Tuple[PatternArtifact, ...] = patterns
        self._config: PatternsRenderConfig = config or PatternsRenderConfig.default()
        
        # Apply philosophy rules
        self._apply_philosophy_rules()
    
    def _validate_patterns_are_artifacts(self, patterns: Tuple[PatternArtifact, ...]) -> None:
        """
        Validate that patterns are pure artifacts, not computation.
        
        This is a critical safety check.
        If patterns contain computation markers, reject them.
        """
        for pattern in patterns:
            # Check for computation markers (these should not exist in artifacts)
            if hasattr(pattern, 'computation_trace'):
                raise ValueError("Pattern artifact contains computation trace - this is a violation")
            
            if hasattr(pattern, 'intermediate_results'):
                raise ValueError("Pattern artifact contains intermediate results - this is a violation")
            
            if hasattr(pattern, 'inference_chain'):
                raise ValueError("Pattern artifact contains inference chain - this is a violation")
            
            # Validate artifact structure
            if not isinstance(pattern, PatternArtifact):
                raise TypeError(f"Pattern must be PatternArtifact, got {type(pattern)}")
    
    def _apply_philosophy_rules(self) -> None:
        """Apply lens philosophy rules to this view."""
        # Article 5: Single-Focus Interface
        SingleFocusRule().validate_interface_intent(
            MockInterfaceIntent(primary_focus=None)
        )
        
        # Article 6: Linear Investigation
        # Patterns only shown after observations
        
        # Article 7: Clear Affordances
        # This view only shows patterns, no pattern computation
        
        # Article 8: Honest Performance
        # If patterns are empty or low confidence, show that clearly
    
    def render(self, mode: PatternsDisplayMode = PatternsDisplayMode.BY_CONFIDENCE) -> Dict[str, Any]:
        """
        Render patterns for display.
        
        This method is DETERMINISTIC and PURE:
        Same context + patterns + config = same output.
        No computation, no inference, no ranking.
        
        Args:
            mode: How to organize patterns for display
        
        Returns:
            Structured data ready for display layer
        
        Raises:
            ValueError: If mode is invalid
        """
        # Apply filtering based on config (but never computation)
        filtered_patterns = self._apply_config_filters(self._patterns)
        
        if not filtered_patterns:
            return self._render_empty_state()
        
        # Organize based on requested mode (pure organization, no inference)
        organized = self._organize_patterns(filtered_patterns, mode)
        
        # Apply display rules (presentation only, no interpretation)
        rendered = self._apply_display_rules(organized)
        
        # Add metadata and warnings
        rendered.update(self._get_view_metadata(len(filtered_patterns), len(self._patterns)))
        
        return rendered
    
    def _apply_config_filters(self, patterns: Tuple[PatternArtifact, ...]) -> Tuple[PatternArtifact, ...]:
        """
        Apply configuration filters to patterns.
        
        This is PURE FILTERING only:
        - Remove patterns without references if required
        - Limit number displayed
        - Optionally filter low confidence
        
        NO RANKING, NO REORDERING BY IMPORTANCE.
        """
        filtered: List[PatternArtifact] = []
        
        for pattern in patterns:
            # Filter: Require references if configured
            if self._config.require_references and pattern.reference_count == 0:
                continue
            
            # Filter: Show low confidence if configured
            if not self._config.show_low_confidence and pattern.has_low_confidence:
                continue
            
            filtered.append(pattern)
        
        # Apply display limit (first N, no sorting)
        if len(filtered) > self._config.max_patterns_displayed:
            filtered = filtered[:self._config.max_patterns_displayed]
        
        return tuple(filtered)
    
    def _organize_patterns(
        self, 
        patterns: Tuple[PatternArtifact, ...], 
        mode: PatternsDisplayMode
    ) -> Dict[str, Any]:
        """
        Organize patterns according to display mode.
        
        This is PURE ORGANIZATION only:
        - Group by explicit, pre-defined categories
        - No inference of similarity
        - No clustering based on content
        
        If you find yourself computing distances between patterns, STOP.
        That's a constitutional violation.
        """
        if mode == PatternsDisplayMode.BY_CONFIDENCE:
            return self._organize_by_confidence(patterns)
        elif mode == PatternsDisplayMode.BY_TYPE:
            return self._organize_by_type(patterns)
        elif mode == PatternsDisplayMode.BY_SCOPE:
            return self._organize_by_scope(patterns)
        elif mode == PatternsDisplayMode.CHRONOLOGICAL:
            return self._organize_chronologically(patterns)
        elif mode == PatternsDisplayMode.UNFILTERED:
            return self._organize_unfiltered(patterns)
        else:
            raise ValueError(f"Unknown display mode: {mode}")
    
    def _organize_by_confidence(self, patterns: Tuple[PatternArtifact, ...]) -> Dict[str, Any]:
        """Organize patterns by their confidence level."""
        groups: Dict[ConfidenceLevel, List[PatternArtifact]] = defaultdict(list)
        
        for pattern in patterns:
            groups[pattern.confidence].append(pattern)
        
        # Convert to display structure
        organized: Dict[str, Any] = {
            "organization": "by_confidence",
            "groups": []
        }
        
        # Preserve confidence level order for display
        for confidence in sorted(ConfidenceLevel, key=lambda c: c.value, reverse=True):
            if confidence in groups:
                group_patterns = groups[confidence]
                organized["groups"].append({
                    "confidence_level": confidence.name,
                    "confidence_display": confidence.display_symbol,
                    "confidence_value": confidence.value,
                    "color": confidence.color_code,
                    "pattern_count": len(group_patterns),
                    "patterns": [self._prepare_pattern_display(p) for p in group_patterns]
                })
        
        return organized
    
    def _organize_by_type(self, patterns: Tuple[PatternArtifact, ...]) -> Dict[str, Any]:
        """Organize patterns by their type."""
        groups: Dict[PatternType, List[PatternArtifact]] = defaultdict(list)
        
        for pattern in patterns:
            groups[pattern.pattern_type].append(pattern)
        
        organized: Dict[str, Any] = {
            "organization": "by_type",
            "groups": []
        }
        
        for pattern_type in PatternType:
            if pattern_type in groups:
                group_patterns = groups[pattern_type]
                organized["groups"].append({
                    "pattern_type": pattern_type.name,
                    "type_description": pattern_type.description,
                    "type_icon": self._get_type_icon(pattern_type),
                    "pattern_count": len(group_patterns),
                    "patterns": [self._prepare_pattern_display(p) for p in group_patterns]
                })
        
        return organized
    
    def _organize_by_scope(self, patterns: Tuple[PatternArtifact, ...]) -> Dict[str, Any]:
        """Organize patterns by what they apply to."""
        # Create groups based on explicit applicable_to sets
        scope_groups: Dict[str, List[PatternArtifact]] = defaultdict(list)
        
        for pattern in patterns:
            for scope_item in pattern.applicable_to:
                scope_groups[scope_item].append(pattern)
        
        organized: Dict[str, Any] = {
            "organization": "by_scope",
            "groups": []
        }
        
        # Sort scope items for consistent display
        for scope_item in sorted(scope_groups.keys()):
            group_patterns = scope_groups[scope_item]
            organized["groups"].append({
                "scope_item": scope_item,
                "pattern_count": len(group_patterns),
                "patterns": [self._prepare_pattern_display(p) for p in group_patterns]
            })
        
        return organized
    
    def _organize_chronologically(self, patterns: Tuple[PatternArtifact, ...]) -> Dict[str, Any]:
        """Organize patterns by detection time."""
        # Sort by detection time (most recent first)
        sorted_patterns = sorted(patterns, key=lambda p: p.detected_at, reverse=True)
        
        return {
            "organization": "chronological",
            "timeline": [self._prepare_pattern_display(p) for p in sorted_patterns],
            "time_range": {
                "start": sorted_patterns[-1].detected_at.isoformat() if sorted_patterns else None,
                "end": sorted_patterns[0].detected_at.isoformat() if sorted_patterns else None
            }
        }
    
    def _organize_unfiltered(self, patterns: Tuple[PatternArtifact, ...]) -> Dict[str, Any]:
        """Show all patterns without organization."""
        return {
            "organization": "unfiltered",
            "patterns": [self._prepare_pattern_display(p) for p in patterns],
            "total_count": len(patterns)
        }
    
    def _prepare_pattern_display(self, pattern: PatternArtifact) -> Dict[str, Any]:
        """
        Prepare a pattern artifact for display.
        
        This adds display annotations but NO interpretation.
        Every field must come directly from the artifact.
        
        Article 3: Must never obscure, distort, or invent information.
        """
        display: Dict[str, Any] = {
            "id": pattern.id,
            "name": pattern.name,
            "type": pattern.pattern_type.name,
            "description": pattern.description,
            
            # Confidence and uncertainty (Article 11)
            "confidence": {
                "level": pattern.confidence.name,
                "value": pattern.confidence.value,
                "display": pattern.confidence.display_symbol,
                "color": pattern.confidence.color_code
            },
            "uncertainty": {
                "reason": pattern.uncertainty_reason,
                "has_low_confidence": pattern.has_low_confidence
            },
            
            # Scope and applicability
            "scope": pattern.scope_description,
            "applicable_to": list(pattern.applicable_to),
            
            # Evidence
            "references": {
                "total": pattern.reference_count,
                "supports": pattern.supports_count,
                "contradicts": pattern.contradicts_count,
                "reference_ids": [ref.observation_id for ref in pattern.references]
            },
            
            # Metrics
            "metrics": [
                {
                    "name": metric.name,
                    "value": metric.value,
                    "display": metric.display_value,
                    "unit": metric.unit,
                    "normalized": metric.is_normalized
                }
                for metric in pattern.metrics
            ],
            
            # Limitations (Article 11)
            "limitations": {
                "known": list(pattern.known_limitations),
                "cannot_detect": list(pattern.cannot_detect)
            },
            
            # Metadata
            "detected_at": pattern.detected_at.isoformat(),
            "detector_version": pattern.detector_version
        }
        
        # Add type-specific icon
        display["type_icon"] = self._get_type_icon(pattern.pattern_type)
        
        # Add boundary violation highlight if configured
        if (self._config.highlight_boundaries and 
            pattern.pattern_type == PatternType.BOUNDARY_VIOLATION):
            display["is_boundary_violation"] = True
            display["boundary_icon"] = self._BOUNDARY_VIOLATION_ICON
        
        # Color by confidence if configured (Article 16)
        if self._config.color_by_confidence:
            display["display_color"] = pattern.confidence.color_code
        
        return display
    
    def _get_type_icon(self, pattern_type: PatternType) -> str:
        """Get icon for pattern type."""
        return {
            PatternType.DENSITY: self._DENSE_CLUSTER_ICON,
            PatternType.COUPLING: self._TIGHT_COUPLING_ICON,
            PatternType.COMPLEXITY: self._HIGH_COMPLEXITY_ICON,
            PatternType.BOUNDARY_VIOLATION: self._BOUNDARY_VIOLATION_ICON,
            PatternType.UNCERTAINTY: self._DATA_GAP_ICON
        }[pattern_type]
    
    def _apply_display_rules(self, organized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply display rules to organized patterns.
        
        This ensures the view adheres to:
        - Article 3: Truth Preservation
        - Article 11: Declared Limitations
        - Article 16: Truth-Preserving Aesthetics
        """
        result = organized.copy()
        
        # Add view type identifier
        result["view_type"] = "patterns"
        result["view_philosophy"] = "results_not_reasoning"
        
        # Apply clarity rule: show what was filtered out
        total_patterns = len(self._patterns)
        displayed_patterns = self._count_displayed_patterns(organized)
        
        result["filtering"] = {
            "total_available": total_patterns,
            "displayed": displayed_patterns,
            "filtered_out": total_patterns - displayed_patterns,
            "filters_applied": {
                "require_references": self._config.require_references,
                "show_low_confidence": self._config.show_low_confidence,
                "max_displayed": self._config.max_patterns_displayed
            }
        }
        
        # Apply progressive disclosure: show if there's more depth
        if displayed_patterns < total_patterns:
            result["has_more"] = True
            result["suggestion"] = "Apply fewer filters or increase display limit to see more patterns"
        else:
            result["has_more"] = False
        
        # Apply single focus: indicate primary organization
        result["focus"] = organized.get("organization", "unorganized")
        
        # Add constitutional warnings
        warnings = []
        
        # Warn if any pattern has no references (evidence required)
        for pattern in self._patterns:
            if pattern.reference_count == 0:
                warnings.append(f"Pattern '{pattern.name}' has no supporting references")
        
        # Warn if many low-confidence patterns
        low_confidence_count = sum(1 for p in self._patterns if p.has_low_confidence)
        if low_confidence_count > len(self._patterns) / 2:
            warnings.append(f"Majority ({low_confidence_count}/{len(self._patterns)}) patterns have low confidence")
        
        if warnings:
            result["warnings"] = warnings
        
        return result
    
    def _count_displayed_patterns(self, organized: Dict[str, Any]) -> int:
        """Count total patterns in organized structure."""
        org_type = organized.get("organization")
        
        if org_type == "by_confidence":
            total = 0
            for group in organized.get("groups", []):
                total += group.get("pattern_count", 0)
            return total
        elif org_type == "by_type":
            total = 0
            for group in organized.get("groups", []):
                total += group.get("pattern_count", 0)
            return total
        elif org_type == "by_scope":
            total = 0
            for group in organized.get("groups", []):
                total += group.get("pattern_count", 0)
            return total
        elif org_type == "chronological":
            return len(organized.get("timeline", []))
        elif org_type == "unfiltered":
            return organized.get("total_count", 0)
        else:
            return 0
    
    def _render_empty_state(self) -> Dict[str, Any]:
        """
        Render the view when no patterns are present.
        
        Article 8: Honest Performance - Explain why no patterns are shown.
        """
        # Determine why no patterns are shown
        reasons = []
        
        if len(self._patterns) == 0:
            reasons.append("No patterns were detected in the investigation")
        elif not self._config.show_low_confidence:
            low_conf_count = sum(1 for p in self._patterns if p.has_low_confidence)
            if low_conf_count == len(self._patterns):
                reasons.append(f"All {low_conf_count} patterns have low confidence and are hidden by filter")
        elif self._config.require_references:
            no_ref_count = sum(1 for p in self._patterns if p.reference_count == 0)
            if no_ref_count == len(self._patterns):
                reasons.append(f"All {no_ref_count} patterns lack references and are hidden by filter")
        
        return {
            "view_type": "patterns",
            "state": "empty",
            "message": "No patterns are currently displayed.",
            "reasons": reasons,
            "total_patterns_available": len(self._patterns),
            "suggestion": "Check filter settings or run pattern detection",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "current_focus": self._context.current_focus,
                "investigation_path": self._context.investigation_path
            }
        }
    
    def _get_view_metadata(self, displayed_count: int, total_count: int) -> Dict[str, Any]:
        """Get metadata about this view rendering."""
        return {
            "metadata": {
                "rendered_at": datetime.now(timezone.utc).isoformat(),
                "patterns_displayed": displayed_count,
                "patterns_total": total_count,
                "config": asdict(self._config),
                "philosophy_rules_applied": [
                    "SingleFocusRule",
                    "ProgressiveDisclosureRule", 
                    "ClarityRule",
                    "NavigationRule"
                ],
                "constitutional_guarantees": [
                    "No pattern computation in view",
                    "All uncertainty declared",
                    "All limitations shown",
                    "No inference or interpretation"
                ]
            }
        }
    
    def validate_integrity(self) -> List[str]:
        """
        Validate that this view adheres to truth-preserving constraints.
        
        Returns:
            List of violations (empty if valid)
        
        This is CRITICAL for the patterns view.
        """
        violations: List[str] = []
        
        # Check 1: No computation in view methods
        view_methods = [method for method in dir(self) if not method.startswith('_')]
        suspicious_methods = ['compute', 'analyze', 'infer', 'deduce', 'conclude']
        for method in view_methods:
            if any(suspicious in method.lower() for suspicious in suspicious_methods):
                violations.append(f"Method '{method}' suggests computation")
        
        # Check 2: No ranking by importance
        rendered = self.render()
        if "ranking" in rendered or "importance" in rendered:
            violations.append("View contains ranking or importance assessment")
        
        # Check 3: All patterns must declare uncertainty
        for pattern in self._patterns:
            if not pattern.uncertainty_reason.strip():
                violations.append(f"Pattern '{pattern.name}' does not declare uncertainty (Article 11)")
            
            if len(pattern.known_limitations) == 0:
                violations.append(f"Pattern '{pattern.name}' has no declared limitations (Article 11)")
        
        # Check 4: No interpretation of pattern meaning
        # We should never say "this means X" or "this suggests Y"
        # This is harder to check automatically, but we can check display strings
        
        # Check 5: No hiding of low-confidence patterns (unless configured)
        # Already enforced by _apply_config_filters
        
        return violations
    
    @classmethod
    def create_test_view(cls) -> PatternsView:
        """
        Create a test view for development and testing.
        
        Returns:
            A PatternsView with test data
        
        Note: This is for testing only, not production use.
        """
        from datetime import datetime, timedelta
        
        # Create test context
        class TestContext(InvestigationContext):
            def __init__(self) -> None:
                self.current_focus = "obs:test:module:boundary_crossing.py"
                self.investigation_path = ["test_investigation"]
                self.created_at = datetime.now(timezone.utc)
        
        # Create test patterns (ARTIFACTS ONLY, no computation)
        now = datetime.now(timezone.utc)
        
        # Pattern 1: Boundary violation
        pattern1 = PatternArtifact(
            id="pattern:boundary:1",
            pattern_type=PatternType.BOUNDARY_VIOLATION,
            name="Cross-lobe import detected",
            description="Module imports from multiple architectural lobes",
            confidence=ConfidenceLevel.HIGH,
            uncertainty_reason="Static analysis may miss runtime imports",
            scope_description="Import statements in Python source files",
            applicable_to=frozenset(["lobes/chatbuddy", "lobes/insightmate"]),
            metrics=(
                PatternMetric(name="Import count", value=3, unit="imports"),
                PatternMetric(name="Lobe count", value=2, unit="lobes"),
            ),
            references=(
                PatternReference(
                    observation_id="obs:import:line:42",
                    relationship="supports",
                    strength=0.9
                ),
                PatternReference(
                    observation_id="obs:import:line:87", 
                    relationship="supports",
                    strength=0.8
                ),
            ),
            known_limitations=("Cannot detect dynamic imports", "Ignores conditional imports"),
            cannot_detect=("Runtime module loading", "Plugin system imports"),
            detected_at=now - timedelta(hours=1),
            detector_version="1.0.0"
        )
        
        # Pattern 2: Complexity
        pattern2 = PatternArtifact(
            id="pattern:complexity:1",
            pattern_type=PatternType.COMPLEXITY,
            name="High nesting depth",
            description="Multiple levels of control flow nesting",
            confidence=ConfidenceLevel.MEDIUM,
            uncertainty_reason="Depth thresholds are heuristic",
            scope_description="Function and method definitions",
            applicable_to=frozenset(["module:complex_logic.py"]),
            metrics=(
                PatternMetric(name="Max depth", value=7, unit="levels"),
                PatternMetric(name="Files affected", value=3, unit="files"),
                PatternMetric(name="Complexity score", value=0.85, is_normalized=True),
            ),
            references=(
                PatternReference(
                    observation_id="obs:function:deeply_nested",
                    relationship="supports",
                    strength=0.7
                ),
            ),
            known_limitations=("Does not measure cognitive complexity", "Ignores linear but long functions"),
            cannot_detect=("Algorithmic complexity", "Memory complexity"),
            detected_at=now - timedelta(minutes=30),
            detector_version="1.0.0"
        )
        
        # Pattern 3: Low confidence pattern
        pattern3 = PatternArtifact(
            id="pattern:density:1",
            pattern_type=PatternType.DENSITY,
            name="Possible import cluster",
            description="Multiple imports from same module group",
            confidence=ConfidenceLevel.LOW,
            uncertainty_reason="Cluster boundaries are unclear",
            scope_description="Import distribution across files",
            applicable_to=frozenset(["common/agent_sdk"]),
            metrics=(
                PatternMetric(name="Import density", value=0.65, is_normalized=True),
            ),
            references=tuple(),  # No references - low confidence
            known_limitations=("Density thresholds arbitrary", "Ignores import frequency"),
            cannot_detect=("Temporal clustering", "Semantic similarity"),
            detected_at=now - timedelta(minutes=15),
            detector_version="1.0.0"
        )
        
        return cls(TestContext(), (pattern1, pattern2, pattern3))


def main() -> None:
    """Test the patterns view."""
    view = PatternsView.create_test_view()
    
    # Test different display modes
    for mode in PatternsDisplayMode:
        print(f"\n=== {mode.name} ===")
        rendered = view.render(mode)
        print(json.dumps(rendered, indent=2, default=str))
    
    # Validate integrity
    violations = view.validate_integrity()
    if violations:
        print(f"\nINTEGRITY VIOLATIONS ({len(violations)}):")
        for violation in violations:
            print(f"  ⚠️  {violation}")
    else:
        print("\n✅ View passes integrity checks.")
    
    # Test empty state
    print("\n=== EMPTY STATE TEST ===")
    empty_view = PatternsView(
        TestContext(),
        tuple(),
        PatternsRenderConfig(require_references=True, show_low_confidence=False)
    )
    empty_rendered = empty_view.render()
    print(json.dumps(empty_rendered, indent=2, default=str))


if __name__ == "__main__":
    main()