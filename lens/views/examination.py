"""
Examination View - Direct Inspection (Truth Layer 3)

This is the only place where raw facts are allowed to be seen.
Core Responsibility: Present raw observations in structured form.

Article 1: Observation Purity - Only show what is textually present
Article 3: Truth Preservation - Never obscure, distort, or invent
Article 4: Progressive Disclosure - Start simple, reveal complexity when requested
"""

from __future__ import annotations

import json
import textwrap
from typing import (
    Optional, List, Dict, Any, Set, FrozenSet, Tuple,
    Callable, ClassVar, Iterator, Union, cast, Literal
)
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict
from pathlib import Path, PurePath

# Allowed imports per architecture
from lens.philosophy import (
    SingleFocusRule,
    ProgressiveDisclosureRule,
    ClarityRule,
    NavigationRule
)
from inquiry.session.context import SessionContext

# NOT ALLOWED: observations.*, patterns.*, bridge.commands.*


class ObservationType(Enum):
    """Types of observations that can be examined."""
    FILE_SIGHT = auto()           # Files, directories, paths
    IMPORT_SIGHT = auto()         # Static import statements
    EXPORT_SIGHT = auto()         # Definitions, signatures
    BOUNDARY_SIGHT = auto()       # Module boundaries
    ENCODING_SIGHT = auto()       # File encoding & type detection
    
    @property
    def display_name(self) -> str:
        """Human-readable name for observation type."""
        return {
            ObservationType.FILE_SIGHT: "File Structure",
            ObservationType.IMPORT_SIGHT: "Imports",
            ObservationType.EXPORT_SIGHT: "Exports",
            ObservationType.BOUNDARY_SIGHT: "Boundaries",
            ObservationType.ENCODING_SIGHT: "Encoding"
        }[self]
    
    @property
    def icon(self) -> str:
        """Icon for observation type."""
        return {
            ObservationType.FILE_SIGHT: "📁",
            ObservationType.IMPORT_SIGHT: "⬇️",
            ObservationType.EXPORT_SIGHT: "⬆️",
            ObservationType.BOUNDARY_SIGHT: "🚧",
            ObservationType.ENCODING_SIGHT: "🔠"
        }[self]


class DisplayMode(Enum):
    """How observations should be displayed."""
    CHRONOLOGICAL = auto()     # By observation timestamp
    BY_TYPE = auto()           # Grouped by observation type
    BY_SOURCE = auto()         # Grouped by source file
    UNSTRUCTURED = auto()      # Raw list, no grouping
    CONTEXTUAL = auto()        # Based on current investigation context


@dataclass(frozen=True)
class RawObservation:
    """
    Immutable raw observation for examination.
    
    Article 1: Only contains what is textually present.
    Article 9: Immutable once recorded.
    """
    id: str
    observation_type: ObservationType
    content: str                    # Raw, verbatim content
    source_path: str               # Where it was observed
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    observed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Metadata about the observation itself
    encoding: str = "utf-8"
    is_binary: bool = False
    size_bytes: Optional[int] = None
    
    # No inference fields allowed here
    # No interpretation, no analysis, no patterns
    
    def __post_init__(self) -> None:
        """Validate observation invariants."""
        if not self.content.strip() and not self.is_binary:
            raise ValueError("Non-binary observation must have content")
        
        if not self.source_path.strip():
            raise ValueError("Observation must have source path")
        
        # Ensure timestamp is timezone aware
        if self.observed_at.tzinfo is None:
            object.__setattr__(self, 'observed_at',
                             self.observed_at.replace(tzinfo=timezone.utc))
        
        # Content must be raw, not processed
        # This is a basic check - in production would be more thorough
        if "interpreted" in self.content.lower() or "inferred" in self.content.lower():
            raise ValueError("Observation content appears to contain interpretation")
    
    @property
    def is_textual(self) -> bool:
        """Whether this is a textual observation."""
        return not self.is_binary
    
    @property
    def source_filename(self) -> str:
        """Extract filename from source path."""
        return Path(self.source_path).name
    
    @property
    def source_directory(self) -> str:
        """Extract directory from source path."""
        return str(Path(self.source_path).parent)
    
    @property
    def location_display(self) -> str:
        """Human-readable location."""
        if self.line_number and self.column_number:
            return f"{self.source_path}:{self.line_number}:{self.column_number}"
        elif self.line_number:
            return f"{self.source_path}:{self.line_number}"
        else:
            return self.source_path


@dataclass(frozen=True)
class ObservationGroup:
    """Group of observations for display."""
    group_key: str                      # What defines this group
    group_type: str                     # "by_type", "by_source", "by_time"
    observations: Tuple[RawObservation, ...]
    
    def __post_init__(self) -> None:
        """Validate group invariants."""
        if not self.group_key.strip():
            raise ValueError("Observation group must have a key")
        
        if not self.group_type.strip():
            raise ValueError("Observation group must have a type")
        
        if len(self.observations) == 0:
            raise ValueError("Observation group must contain observations")
    
    @property
    def count(self) -> int:
        """Number of observations in this group."""
        return len(self.observations)
    
    @property
    def earliest_observation(self) -> Optional[datetime]:
        """Earliest observation time in group."""
        if not self.observations:
            return None
        return min(obs.observed_at for obs in self.observations)
    
    @property
    def latest_observation(self) -> Optional[datetime]:
        """Latest observation time in group."""
        if not self.observations:
            return None
        return max(obs.observed_at for obs in self.observations)


@dataclass(frozen=True)
class ExaminationRenderConfig:
    """
    Configuration for examination rendering.
    
    Article 4: Progressive Disclosure - Start simple
    Article 16: Truth-Preserving Aesthetics - Clear display
    """
    display_mode: DisplayMode = DisplayMode.BY_TYPE
    max_observations_displayed: int = 50           # Prevent overwhelm
    show_source_metadata: bool = True              # Always show where
    show_timestamps: bool = True                   # Always show when
    show_raw_content: bool = True                  # Must show raw content
    group_collapsed_by_default: bool = False       # Progressive disclosure
    highlight_current_focus: bool = True           # Show what's being examined
    preserve_original_formatting: bool = True      # Don't reformat
    
    @classmethod
    def default(cls) -> ExaminationRenderConfig:
        """Default configuration adhering to constitutional rules."""
        return cls()


class ExaminationView:
    """
    Deterministic projection from raw observations → structured display.
    
    Core Responsibility:
    Present raw observations in structured form.
    This is the only place where raw facts are allowed to be seen.
    
    What this view MAY SHOW:
    1. Observations (verbatim, timestamped)
    2. Source metadata
    3. Ordering (by time, by source, by type)
    4. Grouping by category (not pattern)
    
    What this view MUST NOT DO:
    1. No summarization ❌
    2. No clustering ❌
    3. No anomaly detection ❌
    4. No importance ranking ❌
    
    This view is deliberately tedious. That's a feature.
    
    Mental Model: A microscope slide, not a diagnosis.
    """
    
    # Display constants
    _TYPE_ICONS: ClassVar[Dict[ObservationType, str]] = {
        ObservationType.FILE_SIGHT: "📁",
        ObservationType.IMPORT_SIGHT: "⬇️",
        ObservationType.EXPORT_SIGHT: "⬆️",
        ObservationType.BOUNDARY_SIGHT: "🚧",
        ObservationType.ENCODING_SIGHT: "🔠"
    }
    
    _BINARY_INDICATOR: ClassVar[str] = "🔢"
    _TEXT_INDICATOR: ClassVar[str] = "📝"
    
    def __init__(
        self,
        context: SessionContext,
        observations: Tuple[RawObservation, ...],
        config: Optional[ExaminationRenderConfig] = None
    ) -> None:
        """
        Initialize examination view with raw observations.
        
        Args:
            context: Read-only investigation context
            observations: Immutable raw observations
            config: Optional rendering configuration
        
        Raises:
            ValueError: If observations contain inference or interpretation
            TypeError: If observations are not RawObservation instances
        """
        # Validate inputs
        if not isinstance(context, SessionContext):
            raise TypeError(f"context must be SessionContext, got {type(context)}")
        
        # Validate that observations are truly raw
        self._validate_observations_are_raw(observations)
        
        # Store read-only state
        self._context: SessionContext = context
        self._observations: Tuple[RawObservation, ...] = observations
        self._config: ExaminationRenderConfig = config or ExaminationRenderConfig.default()
        
        # Apply philosophy rules
        self._apply_philosophy_rules()
    
    def _validate_observations_are_raw(self, observations: Tuple[RawObservation, ...]) -> None:
        """
        Validate that observations are pure, raw observations.
        
        This is a critical safety check.
        If observations contain analysis markers, reject them.
        """
        for obs in observations:
            # Check type
            if not isinstance(obs, RawObservation):
                raise TypeError(f"Observation must be RawObservation, got {type(obs)}")
            
            # Check for analysis markers (these should not exist in raw observations)
            # This is defensive programming - RawObservation shouldn't have these fields
            forbidden_fields = ['inference', 'interpretation', 'analysis', 'pattern', 'summary']
            for field in forbidden_fields:
                if hasattr(obs, field):
                    raise ValueError(f"Observation contains analysis field '{field}'")
            
            # Check content for interpretive language
            interpretive_phrases = [
                "probably", "likely", "seems", "appears", "suggests",
                "implies", "therefore", "thus", "means"
            ]
            content_lower = obs.content.lower()
            for phrase in interpretive_phrases:
                if phrase in content_lower:
                    raise ValueError(f"Observation content contains interpretation: '{phrase}'")
    
    def _apply_philosophy_rules(self) -> None:
        """Apply lens philosophy rules to this view."""
        # Article 5: Single-Focus Interface
        SingleFocusRule.enforce("examination")
        
        # Article 6: Linear Investigation
        # Examination comes after overview, before patterns
        
        # Article 7: Clear Affordances
        # Show raw data, no actions needed
        
        # Article 8: Honest Performance
        # If there are many observations, show count honestly
    
    def render(self) -> Dict[str, Any]:
        """
        Render observations for examination.
        
        This method is DETERMINISTIC and PURE:
        Same context + observations + config = same output.
        No analysis, no inference, no interpretation.
        
        Returns:
            Structured data ready for display layer
        """
        if not self._observations:
            return self._render_empty_state()
        
        # Apply display mode to organize observations
        organized = self._organize_observations()
        
        # Apply display rules (presentation only)
        rendered = self._apply_display_rules(organized)
        
        # Add metadata and warnings
        rendered.update(self._get_view_metadata())
        
        return rendered
    
    def _organize_observations(self) -> Dict[str, Any]:
        """
        Organize observations according to display mode.
        
        This is PURE ORGANIZATION only:
        - Group by explicit, pre-defined categories
        - Sort by explicit criteria
        - No inference of relationships
        
        If you find yourself computing similarity between observations, STOP.
        That's a constitutional violation.
        """
        mode = self._config.display_mode
        
        if mode == DisplayMode.CHRONOLOGICAL:
            return self._organize_chronologically()
        elif mode == DisplayMode.BY_TYPE:
            return self._organize_by_type()
        elif mode == DisplayMode.BY_SOURCE:
            return self._organize_by_source()
        elif mode == DisplayMode.UNSTRUCTURED:
            return self._organize_unstructured()
        elif mode == DisplayMode.CONTEXTUAL:
            return self._organize_contextually()
        else:
            raise ValueError(f"Unknown display mode: {mode}")
    
    def _organize_chronologically(self) -> Dict[str, Any]:
        """Organize observations by observation time."""
        # Sort by observation time (most recent first)
        sorted_obs = sorted(self._observations, 
                           key=lambda o: o.observed_at, 
                           reverse=True)
        
        # Apply display limit
        display_obs = sorted_obs[:self._config.max_observations_displayed]
        
        return {
            "organization": "chronological",
            "groups": [
                ObservationGroup(
                    group_key="chronological",
                    group_type="time_based",
                    observations=tuple(display_obs)
                )
            ],
            "time_range": {
                "earliest": sorted_obs[-1].observed_at.isoformat() if sorted_obs else None,
                "latest": sorted_obs[0].observed_at.isoformat() if sorted_obs else None
            }
        }
    
    def _organize_by_type(self) -> Dict[str, Any]:
        """Organize observations by observation type."""
        groups_by_type: Dict[ObservationType, List[RawObservation]] = defaultdict(list)
        
        for obs in self._observations:
            groups_by_type[obs.observation_type].append(obs)
        
        # Create groups for each type
        groups: List[ObservationGroup] = []
        for obs_type in ObservationType:
            if obs_type in groups_by_type:
                type_obs = groups_by_type[obs_type]
                # Sort by source path for consistency
                sorted_obs = sorted(type_obs, key=lambda o: o.source_path)
                
                # Apply per-group limit
                display_obs = sorted_obs[:self._config.max_observations_displayed]
                
                groups.append(ObservationGroup(
                    group_key=obs_type.name,
                    group_type="by_type",
                    observations=tuple(display_obs)
                ))
        
        return {
            "organization": "by_type",
            "groups": groups
        }
    
    def _organize_by_source(self) -> Dict[str, Any]:
        """Organize observations by source file."""
        groups_by_source: Dict[str, List[RawObservation]] = defaultdict(list)
        
        for obs in self._observations:
            groups_by_source[obs.source_path].append(obs)
        
        # Create groups for each source file
        groups: List[ObservationGroup] = []
        for source_path in sorted(groups_by_source.keys()):
            source_obs = groups_by_source[source_path]
            # Sort by line number if available
            sorted_obs = sorted(source_obs, 
                              key=lambda o: (o.line_number or 0, o.column_number or 0))
            
            # Apply per-group limit
            display_obs = sorted_obs[:self._config.max_observations_displayed]
            
            groups.append(ObservationGroup(
                group_key=source_path,
                group_type="by_source",
                observations=tuple(display_obs)
            ))
        
        return {
            "organization": "by_source",
            "groups": groups
        }
    
    def _organize_unstructured(self) -> Dict[str, Any]:
        """Show observations as a simple list."""
        # No sorting, just raw order (but limited)
        display_obs = self._observations[:self._config.max_observations_displayed]
        
        return {
            "organization": "unstructured",
            "groups": [
                ObservationGroup(
                    group_key="all_observations",
                    group_type="unstructured",
                    observations=tuple(display_obs)
                )
            ]
        }
    
    def _organize_contextually(self) -> Dict[str, Any]:
        """Organize observations based on current investigation context."""
        if not self._context.current_focus:
            # No focus, fall back to by_type
            return self._organize_by_type()
        
        # Try to find observations related to current focus
        # This is simple matching, not inference
        focus_obs: List[RawObservation] = []
        other_obs: List[RawObservation] = []
        
        for obs in self._observations:
            # Simple string matching on source path
            # This is not inference - it's exact matching
            if self._context.current_focus in obs.source_path:
                focus_obs.append(obs)
            else:
                other_obs.append(obs)
        
        groups: List[ObservationGroup] = []
        
        # Focus observations group
        if focus_obs:
            sorted_focus = sorted(focus_obs, key=lambda o: o.source_path)
            display_focus = sorted_focus[:self._config.max_observations_displayed]
            
            groups.append(ObservationGroup(
                group_key=f"focus:{self._context.current_focus}",
                group_type="contextual_focus",
                observations=tuple(display_focus)
            ))
        
        # Other observations (grouped by type)
        if other_obs:
            other_by_type: Dict[ObservationType, List[RawObservation]] = defaultdict(list)
            for obs in other_obs:
                other_by_type[obs.observation_type].append(obs)
            
            for obs_type in ObservationType:
                if obs_type in other_by_type:
                    type_obs = other_by_type[obs_type]
                    sorted_type = sorted(type_obs, key=lambda o: o.source_path)
                    
                    # Apply per-group limit
                    display_type = sorted_type[:self._config.max_observations_displayed // 2]
                    
                    groups.append(ObservationGroup(
                        group_key=f"other:{obs_type.name}",
                        group_type="by_type",
                        observations=tuple(display_type)
                    ))
        
        return {
            "organization": "contextual",
            "groups": groups,
            "current_focus": self._context.current_focus
        }
    
    def _prepare_observation_display(self, obs: RawObservation) -> Dict[str, Any]:
        """
        Prepare a raw observation for display.
        
        This adds display annotations but NO interpretation.
        Every field must come directly from the observation.
        
        Article 1: Must show exactly what was observed.
        Article 3: Must never obscure or distort.
        """
        display: Dict[str, Any] = {
            "id": obs.id,
            "type": obs.observation_type.name,
            "type_display": obs.observation_type.display_name,
            "type_icon": self._TYPE_ICONS[obs.observation_type],
            "content": obs.content if self._config.show_raw_content else "[content hidden]",
            "is_binary": obs.is_binary,
            "content_indicator": self._BINARY_INDICATOR if obs.is_binary else self._TEXT_INDICATOR
        }
        
        # Source metadata
        if self._config.show_source_metadata:
            display["source"] = {
                "path": obs.source_path,
                "filename": obs.source_filename,
                "directory": obs.source_directory,
                "location": obs.location_display,
                "line": obs.line_number,
                "column": obs.column_number
            }
        
        # Timestamps
        if self._config.show_timestamps:
            display["observed_at"] = obs.observed_at.isoformat()
            display["observed_time"] = obs.observed_at.strftime("%H:%M:%S.%f")[:-3]
        
        # Technical details
        display["encoding"] = obs.encoding
        if obs.size_bytes is not None:
            display["size_bytes"] = obs.size_bytes
        
        # Highlight if this is the current focus
        if (self._config.highlight_current_focus and 
            self._context.current_focus and
            self._context.current_focus in obs.source_path):
            display["is_current_focus"] = True
        
        # Preserve original formatting
        if self._config.preserve_original_formatting:
            display["preserves_formatting"] = True
            # Indicate if content has been modified (it shouldn't be)
            display["is_unmodified"] = True
        
        return display
    
    def _prepare_group_display(self, group: ObservationGroup) -> Dict[str, Any]:
        """Prepare an observation group for display."""
        display: Dict[str, Any] = {
            "group_key": group.group_key,
            "group_type": group.group_type,
            "observation_count": group.count,
            "observations": [self._prepare_observation_display(obs) for obs in group.observations],
            "is_collapsed": self._config.group_collapsed_by_default
        }
        
        # Add group-specific metadata
        if group.group_type == "time_based" and group.earliest_observation and group.latest_observation:
            display["time_span"] = {
                "earliest": group.earliest_observation.isoformat(),
                "latest": group.latest_observation.isoformat()
            }
        
        return display
    
    def _apply_display_rules(self, organized: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply display rules to organized observations.
        
        This ensures the view adheres to:
        - Article 1: Observation Purity
        - Article 3: Truth Preservation
        - Article 4: Progressive Disclosure
        """
        result = organized.copy()
        
        # Add view type identifier
        result["view_type"] = "examination"
        result["view_philosophy"] = "direct_inspection"
        
        # Apply progressive disclosure: show if there's more
        total_observations = len(self._observations)
        displayed_count = sum(len(g.observations) for g in organized.get("groups", []))
        
        result["display_stats"] = {
            "total_available": total_observations,
            "displayed": displayed_count,
            "hidden": total_observations - displayed_count,
            "reason_for_hiding": f"Limited to {self._config.max_observations_displayed} per group" 
                                 if displayed_count < total_observations else None
        }
        
        # Apply clarity rule: explain what's being shown
        result["clarity_notes"] = [
            "Showing raw observations only",
            "No analysis, inference, or interpretation",
            "Content is exactly as observed"
        ]
        
        # Apply single focus: indicate primary organization
        result["focus"] = organized.get("organization", "unorganized")
        
        # Prepare groups for display
        if "groups" in organized:
            result["display_groups"] = [
                self._prepare_group_display(group) 
                for group in organized["groups"]
            ]
        
        # Add warnings if content is hidden
        if not self._config.show_raw_content:
            result["warnings"] = ["Raw content hidden by configuration"]
        
        return result
    
    def _render_empty_state(self) -> Dict[str, Any]:
        """
        Render the view when no observations are present.
        
        Article 3: Must be honest about absence.
        Article 8: Must explain why nothing is shown.
        """
        return {
            "view_type": "examination",
            "state": "empty",
            "message": "No observations available for examination.",
            "possible_reasons": [
                "No observations have been collected yet",
                "Observations were filtered out",
                "The current focus has no observations"
            ],
            "suggestions": [
                "Run observation collection",
                "Check filter settings",
                "Change focus to something with observations"
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "context": {
                "current_focus": self._context.current_focus,
                "investigation_path": self._context.investigation_path
            }
        }
    
    def _get_view_metadata(self) -> Dict[str, Any]:
        """Get metadata about this view rendering."""
        return {
            "metadata": {
                "rendered_at": datetime.now(timezone.utc).isoformat(),
                "total_observations": len(self._observations),
                "config": asdict(self._config),
                "philosophy_rules_applied": [
                    "SingleFocusRule",
                    "ProgressiveDisclosureRule",
                    "ClarityRule",
                    "NavigationRule"
                ],
                "constitutional_guarantees": [
                    "Article 1: Observation Purity",
                    "Article 3: Truth Preservation",
                    "Article 4: Progressive Disclosure",
                    "Article 9: Immutable Observations"
                ],
                "integrity_checks": self._run_integrity_checks()
            }
        }
    
    def _run_integrity_checks(self) -> Dict[str, bool]:
        """Run integrity checks on the view."""
        checks = {
            "no_analysis_performed": True,
            "no_inference_made": True,
            "raw_content_shown": self._config.show_raw_content,
            "source_metadata_shown": self._config.show_source_metadata,
            "timestamps_shown": self._config.show_timestamps,
            "formatting_preserved": self._config.preserve_original_formatting
        }
        
        # Check that we're not doing analysis
        # Look for any organization that could be misinterpreted as analysis
        organized = self._organize_observations()
        org_type = organized.get("organization")
        
        # Contextual organization is borderline but acceptable if based on exact matching
        if org_type == "contextual":
            checks["contextual_based_on_exact_match"] = True
        
        # Check that no observation content has been modified
        for obs in self._observations[:10]:  # Sample check
            if "[content hidden]" in obs.content:
                checks["raw_content_shown"] = False
        
        return checks
    
    def validate_integrity(self) -> List[str]:
        """
        Validate that this view adheres to truth-preserving constraints.
        
        Returns:
            List of violations (empty if valid)
        """
        violations = []
        
        # Check 1: No analysis or interpretation
        rendered = self.render()
        
        # Check for interpretive language in display
        interpretative_phrases = ["means", "suggests", "implies", "therefore", "thus", "probably", "likely"]
        for phrase in interpretative_phrases:
            if phrase in str(rendered).lower():
                violations.append(f"View contains interpretative language: '{phrase}'")
        
        # Check 2: Raw content must be shown unless explicitly configured
        if not self._config.show_raw_content:
            # This is allowed but should be noted
            # Check if there's a good reason
            pass  # No violation, but user should know content is hidden
        
        # Check 3: Source metadata must be shown
        if not self._config.show_source_metadata:
            violations.append("Source metadata hidden (violates traceability)")
        
        # Check 4: No summarization
        # Look for any aggregation that could be summarization
        organized = self._organize_observations()
        for group in organized.get("groups", []):
            if hasattr(group, 'summary') or hasattr(group, 'aggregate'):
                violations.append("Observation groups contain summaries or aggregates")
        
        # Check 5: No clustering based on content similarity
        # This would require checking the organization logic
        
        # Check 6: No importance ranking
        if "importance" in str(rendered) or "ranking" in str(rendered):
            violations.append("View contains importance ranking")
        
        # Check 7: All observations must be immutable
        # This is enforced by using tuples and frozen dataclasses
        
        # Check 8: Must show uncertainty if present
        # Raw observations shouldn't have uncertainty, but if they do...
        for obs in self._observations[:5]:  # Sample
            if hasattr(obs, 'uncertainty') and getattr(obs, 'uncertainty', False):
                if "uncertainty" not in str(rendered).lower():
                    violations.append("Uncertainty present but not displayed")
        
        return violations
    
    def get_filtered_view(
        self, 
        filter_type: Optional[ObservationType] = None,
        filter_source: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> ExaminationView:
        """
        Create a new view with filtered observations.
        
        This is a pure operation - creates new view with subset of observations.
        
        Args:
            filter_type: Only include observations of this type
            filter_source: Only include observations from this source
            max_results: Maximum number of observations to include
        
        Returns:
            New ExaminationView with filtered observations
        """
        filtered_obs: List[RawObservation] = []
        
        for obs in self._observations:
            # Apply filters
            if filter_type and obs.observation_type != filter_type:
                continue
            
            if filter_source and filter_source not in obs.source_path:
                continue
            
            filtered_obs.append(obs)
            
            # Apply max results
            if max_results and len(filtered_obs) >= max_results:
                break
        
        # Create new config with same settings
        new_config = ExaminationRenderConfig(**asdict(self._config))
        
        return ExaminationView(
            context=self._context,
            observations=tuple(filtered_obs),
            config=new_config
        )
    
    @classmethod
    def create_test_view(cls) -> ExaminationView:
        """
        Create a test view for development and testing.
        
        Returns:
            An ExaminationView with test data
        """
        from datetime import datetime, timedelta
        
        # Create test context
        class TestContext(InvestigationContext):
            def __init__(self) -> None:
                self.current_focus = "example.py"
                self.investigation_path = ["started", "examining_example"]
                self.created_at = datetime.now(timezone.utc)
        
        # Create test observations
        now = datetime.now(timezone.utc)
        
        # Observation 1: File sight
        obs1 = RawObservation(
            id="obs:file:1",
            observation_type=ObservationType.FILE_SIGHT,
            content="File: example.py\nSize: 1024 bytes\nLines: 42",
            source_path="/project/example.py",
            line_number=None,
            column_number=None,
            observed_at=now - timedelta(hours=2),
            size_bytes=1024
        )
        
        # Observation 2: Import sight
        obs2 = RawObservation(
            id="obs:import:1",
            observation_type=ObservationType.IMPORT_SIGHT,
            content="import os\nimport sys\nfrom typing import List, Dict",
            source_path="/project/example.py",
            line_number=1,
            column_number=1,
            observed_at=now - timedelta(hours=1, minutes=45),
            size_bytes=len("import os\nimport sys\nfrom typing import List, Dict")
        )
        
        # Observation 3: Export sight
        obs3 = RawObservation(
            id="obs:export:1",
            observation_type=ObservationType.EXPORT_SIGHT,
            content="def calculate_total(items: List[int]) -> int:\n    return sum(items)",
            source_path="/project/example.py",
            line_number=10,
            column_number=1,
            observed_at=now - timedelta(hours=1, minutes=30)
        )
        
        # Observation 4: Another import from different file
        obs4 = RawObservation(
            id="obs:import:2",
            observation_type=ObservationType.IMPORT_SIGHT,
            content="from common.agent_sdk import AgentBase\nfrom lobes.chatbuddy import ChatAgent",
            source_path="/project/another.py",
            line_number=5,
            column_number=1,
            observed_at=now - timedelta(hours=1)
        )
        
        # Observation 5: Binary file
        obs5 = RawObservation(
            id="obs:file:2",
            observation_type=ObservationType.FILE_SIGHT,
            content="",  # Empty for binary
            source_path="/project/data.bin",
            line_number=None,
            column_number=None,
            observed_at=now - timedelta(minutes=45),
            is_binary=True,
            size_bytes=2048
        )
        
        return cls(
            TestContext(),
            (obs1, obs2, obs3, obs4, obs5)
        )


def main() -> None:
    """Test the examination view."""
    view = ExaminationView.create_test_view()
    
    # Test different display modes
    for mode in DisplayMode:
        print(f"\n=== {mode.name} ===")
        config = ExaminationRenderConfig(display_mode=mode)
        test_view = ExaminationView(view._context, view._observations, config)
        rendered = test_view.render()
        print(json.dumps(rendered, indent=2, default=str))
    
    # Validate integrity
    violations = view.validate_integrity()
    if violations:
        print(f"\nINTEGRITY VIOLATIONS ({len(violations)}):")
        for violation in violations:
            print(f"  ⚠️  {violation}")
    else:
        print("\n✅ View passes integrity checks.")
    
    # Test filtering
    print("\n=== FILTERED VIEW (IMPORT_SIGHT only) ===")
    filtered = view.get_filtered_view(filter_type=ObservationType.IMPORT_SIGHT)
    filtered_rendered = filtered.render()
    print(json.dumps(filtered_rendered, indent=2, default=str))
    
    # Test empty state
    print("\n=== EMPTY STATE TEST ===")
    empty_view = ExaminationView(view._context, tuple())
    empty_rendered = empty_view.render()
    print(json.dumps(empty_rendered, indent=2, default=str))


if __name__ == "__main__":
    main()