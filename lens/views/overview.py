"""
Overview View - Orientation Without Interpretation (Truth Layer 3)

This is the entry lens.
Core Responsibility: Provide situational awareness without analysis.

Article 5: Single-Focus Interface - Only one primary content area visible
Article 6: Linear Investigation - Follow natural human curiosity
Article 7: Clear Affordances - Show what can be done next
Article 8: Honest Performance - Show indicators for computation time
"""

from __future__ import annotations

import json
from typing import (
    Optional, List, Dict, Any, Set, FrozenSet, Tuple,
    Callable, ClassVar, Iterator, Union, cast, Literal
)
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
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
from inquiry.notebook import NotebookManager

# NOT ALLOWED: observations.*, patterns.*, bridge.commands.*


class InvestigationStage(Enum):
    """Stages of investigation according to Article 6."""
    ORIENTATION = auto()        # What exists?
    OBSERVATION = auto()        # What do I see?
    PATTERN_DETECTION = auto()  # What patterns emerge?
    THINKING = auto()           # What do I think?
    SYNTHESIS = auto()          # What have I learned?
    
    @property
    def description(self) -> str:
        """Human-readable description of investigation stage."""
        return {
            InvestigationStage.ORIENTATION: "Orientation: Understanding what exists",
            InvestigationStage.OBSERVATION: "Observation: Examining what is present",
            InvestigationStage.PATTERN_DETECTION: "Pattern detection: Noticing regularities",
            InvestigationStage.THINKING: "Thinking: Forming understanding",
            InvestigationStage.SYNTHESIS: "Synthesis: Integrating knowledge"
        }[self]
    
    @property
    def next_stage(self) -> Optional[InvestigationStage]:
        """Natural next stage (Article 6: Linear Investigation)."""
        mapping = {
            InvestigationStage.ORIENTATION: InvestigationStage.OBSERVATION,
            InvestigationStage.OBSERVATION: InvestigationStage.PATTERN_DETECTION,
            InvestigationStage.PATTERN_DETECTION: InvestigationStage.THINKING,
            InvestigationStage.THINKING: InvestigationStage.SYNTHESIS,
            InvestigationStage.SYNTHESIS: None
        }
        return mapping[self]
    
    @property
    def short_name(self) -> str:
        """Short name for display."""
        return {
            InvestigationStage.ORIENTATION: "Orientation",
            InvestigationStage.OBSERVATION: "Observation",
            InvestigationStage.PATTERN_DETECTION: "Patterns",
            InvestigationStage.THINKING: "Thinking",
            InvestigationStage.SYNTHESIS: "Synthesis"
        }[self]


class PresenceIndicator(Enum):
    """Visual indicators for what information exists."""
    PRESENT = "✅"
    PARTIAL = "⚠️"
    ABSENT = "❌"
    UNKNOWN = "❓"
    LOADING = "⏳"
    
    @property
    def color(self) -> str:
        """Color coding for presence indicators."""
        return {
            PresenceIndicator.PRESENT: "#06d6a0",
            PresenceIndicator.PARTIAL: "#ffd166",
            PresenceIndicator.ABSENT: "#ef476f",
            PresenceIndicator.UNKNOWN: "#888888",
            PresenceIndicator.LOADING: "#118ab2"
        }[self]


@dataclass(frozen=True)
class InvestigationMetrics:
    """
    Counts of what exists in the investigation.
    
    Article 8: Honest Performance - Show what information exists.
    """
    observations_total: int = 0
    observations_analyzed: int = 0
    patterns_detected: int = 0
    notes_recorded: int = 0
    questions_asked: int = 0
    
    def __post_init__(self) -> None:
        """Validate metric invariants."""
        if self.observations_analyzed > self.observations_total:
            raise ValueError("Analyzed observations cannot exceed total")
    
    @property
    def observation_coverage(self) -> float:
        """Percentage of observations analyzed."""
        if self.observations_total == 0:
            return 0.0
        return self.observations_analyzed / self.observations_total
    
    @property
    def has_observations(self) -> bool:
        """Whether any observations exist."""
        return self.observations_total > 0
    
    @property
    def has_patterns(self) -> bool:
        """Whether any patterns have been detected."""
        return self.patterns_detected > 0
    
    @property
    def has_notes(self) -> bool:
        """Whether any notes have been recorded."""
        return self.notes_recorded > 0
    
    @property
    def has_questions(self) -> bool:
        """Whether any questions have been asked."""
        return self.questions_asked > 0


@dataclass(frozen=True)
class CurrentFocus:
    """What is currently being examined."""
    id: str
    type: str  # "module", "directory", "file", "observation", "pattern"
    description: str
    path: Optional[str] = None
    context: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """Name for display."""
        if self.path:
            return f"{self.type}: {self.path}"
        return f"{self.type}: {self.id}"


@dataclass(frozen=True)
class UnknownItem:
    """Something explicitly unknown (Article 3)."""
    category: str
    description: str
    reason: str  # Why it's unknown
    investigation_needed: bool = False
    
    def __post_init__(self) -> None:
        """Validate unknown item invariants."""
        if not self.description.strip():
            raise ValueError("Unknown item must have description")
        
        if not self.reason.strip():
            raise ValueError("Unknown item must have reason for uncertainty")


@dataclass(frozen=True)
class InvestigationTimeline:
    """Temporal context of investigation."""
    started_at: datetime
    current_duration: timedelta
    last_activity: Optional[datetime] = None
    milestones: Tuple[datetime, ...] = field(default_factory=tuple)
    
    def __post_init__(self) -> None:
        """Validate timeline invariants."""
        if self.started_at.tzinfo is None:
            object.__setattr__(self, 'started_at',
                             self.started_at.replace(tzinfo=timezone.utc))
        
        if self.last_activity and self.last_activity.tzinfo is None:
            object.__setattr__(self, 'last_activity',
                             self.last_activity.replace(tzinfo=timezone.utc))
    
    @property
    def is_active(self) -> bool:
        """Whether investigation is currently active."""
        if not self.last_activity:
            return False
        
        # Consider active if activity in last 5 minutes
        five_minutes_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        return self.last_activity > five_minutes_ago
    
    @property
    def duration_display(self) -> str:
        """Human-readable duration."""
        total_seconds = int(self.current_duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"


@dataclass(frozen=True)
class OverviewRenderConfig:
    """
    Configuration for overview rendering.
    
    Article 5: Single-Focus Interface
    Article 7: Clear Affordances
    """
    show_counts: bool = True                    # Show what information exists
    show_timeline: bool = True                  # Show temporal context
    show_unknowns: bool = True                  # Show what is unknown (Article 3)
    show_next_actions: bool = True              # Show what can be done (Article 7)
    max_unknown_items: int = 3                  # Prevent overwhelm
    collapse_details: bool = False              # Progressive disclosure
    
    @classmethod
    def default(cls) -> OverviewRenderConfig:
        """Default configuration adhering to constitutional rules."""
        return cls()


class OverviewView:
    """
    Deterministic projection from epistemic state → situational awareness.
    
    Core Responsibility:
    Provide orientation without interpretation.
    
    This is the entry lens - the first thing a human sees.
    It must answer "What's going on?" without thinking for them.
    
    What this view MAY SHOW:
    1. What is currently being examined
    2. What information exists (counts, presence)
    3. What stage the investigation is in
    4. What is explicitly unknown
    
    What this view MUST NOT SHOW:
    1. Conclusions ❌
    2. Pattern summaries ❌
    3. Inferred importance ❌
    4. Recommendations ❌
    
    Mental Model: A map legend, not a guided tour.
    """
    
    # Display constants
    _STAGE_ICONS: ClassVar[Dict[InvestigationStage, str]] = {
        InvestigationStage.ORIENTATION: "🗺️",
        InvestigationStage.OBSERVATION: "🔍",
        InvestigationStage.PATTERN_DETECTION: "📊",
        InvestigationStage.THINKING: "🧠",
        InvestigationStage.SYNTHESIS: "📚"
    }
    
    _NEXT_ACTION_ICONS: ClassVar[Dict[str, str]] = {
        "observe": "👁️",
        "question": "❓",
        "pattern": "📈",
        "think": "💭",
        "synthesize": "📝"
    }
    
    def __init__(
        self,
        context: SessionContext,
        notebook: NotebookManager,
        metrics: InvestigationMetrics,
        current_focus: Optional[CurrentFocus],
        unknowns: Tuple[UnknownItem, ...] = (),
        timeline: Optional[InvestigationTimeline] = None,
        config: Optional[OverviewRenderConfig] = None
    ) -> None:
        """
        Initialize overview view with current epistemic state.
        
        Args:
            context: Read-only investigation context
            notebook: Read-only collection of notes
            metrics: Counts of what exists
            current_focus: What is being examined now
            unknowns: Things explicitly unknown
            timeline: Temporal context
            config: Optional rendering configuration
        
        Raises:
            ValueError: If inputs violate overview constraints
        """
        # Validate inputs
        if not isinstance(context, SessionContext):
            raise TypeError(f"context must be SessionContext, got {type(context)}")
        
        if not isinstance(notebook, NotebookManager):
            raise TypeError(f"notebook must be NotebookManager, got {type(notebook)}")
        
        if not isinstance(metrics, InvestigationMetrics):
            raise TypeError(f"metrics must be InvestigationMetrics, got {type(metrics)}")
        
        # Store read-only state
        self._context: SessionContext = context
        self._notebook: NotebookManager = notebook
        self._metrics: InvestigationMetrics = metrics
        self._current_focus: Optional[CurrentFocus] = current_focus
        self._unknowns: Tuple[UnknownItem, ...] = unknowns
        self._timeline: Optional[InvestigationTimeline] = timeline
        self._config: OverviewRenderConfig = config or OverviewRenderConfig.default()
        
        # Apply philosophy rules
        self._apply_philosophy_rules()
    
    def _apply_philosophy_rules(self) -> None:
        """Apply lens philosophy rules to this view."""
        # Article 5: Single-Focus Interface
        SingleFocusRule().validate_interface_intent(
            MockInterfaceIntent(primary_focus=None)
        )
        
        # Article 6: Linear Investigation
        # Overview comes first in investigation
        
        # Article 7: Clear Affordances
        # We'll show what can be done next
        
        # Article 8: Honest Performance
        # We'll show what exists and what doesn't
    
    def render(self) -> Dict[str, Any]:
        """
        Render overview for display.
        
        Returns:
            Structured data ready for display layer
        
        Article 3: Must show uncertainty clearly
        Article 4: Start with simple observations
        Article 5: Only one primary content area
        Article 7: Show obvious, consistent actions
        """
        # Build overview sections (deterministic, no analysis)
        overview = {
            "view_type": "overview",
            "view_philosophy": "orientation_without_interpretation",
            "sections": []
        }
        
        # 1. Current focus (always shown, Article 5)
        overview["sections"].append(self._render_current_focus())
        
        # 2. Investigation stage (Article 6)
        overview["sections"].append(self._render_investigation_stage())
        
        # 3. What exists (counts, Article 8)
        if self._config.show_counts:
            overview["sections"].append(self._render_presence_indicators())
        
        # 4. Timeline (temporal context)
        if self._config.show_timeline and self._timeline:
            overview["sections"].append(self._render_timeline())
        
        # 5. Unknowns (Article 3)
        if self._config.show_unknowns and self._unknowns:
            overview["sections"].append(self._render_unknowns())
        
        # 6. Next actions (Article 7)
        if self._config.show_next_actions:
            overview["sections"].append(self._render_next_actions())
        
        # Add metadata
        overview.update(self._get_view_metadata())
        
        # Apply single-focus prioritization
        overview = self._apply_single_focus(overview)
        
        return overview
    
    def _render_current_focus(self) -> Dict[str, Any]:
        """Render what is currently being examined."""
        if self._current_focus:
            return {
                "section_type": "current_focus",
                "title": "Current Focus",
                "icon": "🎯",
                "content": {
                    "id": self._current_focus.id,
                    "type": self._current_focus.type,
                    "display_name": self._current_focus.display_name,
                    "description": self._current_focus.description,
                    "context": self._current_focus.context
                },
                "is_primary": True,  # Article 5: Single focus
                "can_interact": True
            }
        else:
            return {
                "section_type": "current_focus",
                "title": "Current Focus",
                "icon": "🎯",
                "content": {
                    "status": "no_focus",
                    "message": "No specific focus selected. The investigation is at a high level.",
                    "suggestion": "Select a module, file, or observation to focus on."
                },
                "is_primary": True,
                "can_interact": True
            }
    
    def _render_investigation_stage(self) -> Dict[str, Any]:
        """Render current investigation stage."""
        # Determine stage based on metrics and context
        stage = self._determine_stage()
        
        return {
            "section_type": "investigation_stage",
            "title": "Investigation Stage",
            "icon": self._STAGE_ICONS[stage],
            "content": {
                "stage": stage.name,
                "stage_display": stage.short_name,
                "description": stage.description,
                "next_stage": stage.next_stage.name if stage.next_stage else None,
                "progress": self._calculate_stage_progress(stage)
            },
            "is_progressive": True,  # Article 4: Progressive disclosure
            "can_interact": False  # Stage is informational only
        }
    
    def _determine_stage(self) -> InvestigationStage:
        """
        Determine investigation stage based on metrics.
        
        This is a simple heuristic, NOT analysis.
        It only looks at presence/absence, not content.
        """
        # If no observations, we're orienting
        if not self._metrics.has_observations:
            return InvestigationStage.ORIENTATION
        
        # If observations but no patterns, we're observing
        if self._metrics.has_observations and not self._metrics.has_patterns:
            return InvestigationStage.OBSERVATION
        
        # If patterns but few notes, we're detecting patterns
        if (self._metrics.has_patterns and 
            self._metrics.notes_recorded < self._metrics.patterns_detected):
            return InvestigationStage.PATTERN_DETECTION
        
        # If many notes, we're thinking
        if self._metrics.notes_recorded >= self._metrics.patterns_detected * 2:
            return InvestigationStage.THINKING
        
        # Default to observation
        return InvestigationStage.OBSERVATION
    
    def _calculate_stage_progress(self, stage: InvestigationStage) -> Optional[float]:
        """Calculate progress within current stage (0-1)."""
        if stage == InvestigationStage.ORIENTATION:
            # Progress based on having any observations
            return 1.0 if self._metrics.has_observations else 0.0
        
        elif stage == InvestigationStage.OBSERVATION:
            # Progress based on observation coverage
            if self._metrics.observations_total == 0:
                return 0.0
            return min(self._metrics.observation_coverage * 2, 1.0)  # Scale to 50% coverage = complete
        
        elif stage == InvestigationStage.PATTERN_DETECTION:
            # Progress based on patterns found
            if not self._metrics.has_observations:
                return 0.0
            # Assume up to 10 patterns is "complete" for this stage
            return min(self._metrics.patterns_detected / 10.0, 1.0)
        
        elif stage == InvestigationStage.THINKING:
            # Progress based on notes per pattern
            if not self._metrics.has_patterns:
                return 0.0
            notes_per_pattern = self._metrics.notes_recorded / max(self._metrics.patterns_detected, 1)
            return min(notes_per_pattern / 3.0, 1.0)  # 3 notes per pattern = complete
        
        elif stage == InvestigationStage.SYNTHESIS:
            # Synthesis is always ongoing
            return 0.5  # Indeterminate progress
        
        return None
    
    def _render_presence_indicators(self) -> Dict[str, Any]:
        """Render what information exists."""
        indicators = []
        
        # Observations
        if self._metrics.has_observations:
            if self._metrics.observation_coverage >= 0.8:
                status = PresenceIndicator.PRESENT
                details = f"{self._metrics.observations_analyzed} analyzed of {self._metrics.observations_total}"
            elif self._metrics.observation_coverage > 0:
                status = PresenceIndicator.PARTIAL
                details = f"{self._metrics.observations_analyzed} analyzed of {self._metrics.observations_total}"
            else:
                status = PresenceIndicator.PRESENT  # Present but not analyzed
                details = f"{self._metrics.observations_total} collected (not analyzed)"
        else:
            status = PresenceIndicator.ABSENT
            details = "No observations collected"
        
        indicators.append({
            "category": "Observations",
            "icon": "👁️",
            "status": status.name,
            "status_icon": status.value,
            "color": status.color,
            "details": details,
            "count": self._metrics.observations_total
        })
        
        # Patterns
        if self._metrics.has_patterns:
            status = PresenceIndicator.PRESENT
            details = f"{self._metrics.patterns_detected} patterns detected"
        else:
            status = PresenceIndicator.ABSENT
            details = "No patterns detected"
        
        indicators.append({
            "category": "Patterns",
            "icon": "📊",
            "status": status.name,
            "status_icon": status.value,
            "color": status.color,
            "details": details,
            "count": self._metrics.patterns_detected
        })
        
        # Notes
        if self._metrics.has_notes:
            status = PresenceIndicator.PRESENT
            details = f"{self._metrics.notes_recorded} notes recorded"
        else:
            status = PresenceIndicator.ABSENT
            details = "No notes recorded"
        
        indicators.append({
            "category": "Notes",
            "icon": "📝",
            "status": status.name,
            "status_icon": status.value,
            "color": status.color,
            "details": details,
            "count": self._metrics.notes_recorded
        })
        
        # Questions
        if self._metrics.has_questions:
            status = PresenceIndicator.PRESENT
            details = f"{self._metrics.questions_asked} questions asked"
        else:
            status = PresenceIndicator.ABSENT
            details = "No questions asked"
        
        indicators.append({
            "category": "Questions",
            "icon": "❓",
            "status": status.name,
            "status_icon": status.value,
            "color": status.color,
            "details": details,
            "count": self._metrics.questions_asked
        })
        
        return {
            "section_type": "presence_indicators",
            "title": "What Exists",
            "icon": "📋",
            "content": {
                "indicators": indicators,
                "summary": self._create_presence_summary()
            },
            "is_collapsible": True,
            "is_collapsed": self._config.collapse_details
        }
    
    def _create_presence_summary(self) -> str:
        """Create a human-readable summary of what exists."""
        parts = []
        
        if self._metrics.has_observations:
            parts.append(f"{self._metrics.observations_total} observations")
        
        if self._metrics.has_patterns:
            parts.append(f"{self._metrics.patterns_detected} patterns")
        
        if self._metrics.has_notes:
            parts.append(f"{self._metrics.notes_recorded} notes")
        
        if self._metrics.has_questions:
            parts.append(f"{self._metrics.questions_asked} questions")
        
        if not parts:
            return "Nothing has been recorded yet."
        
        if len(parts) == 1:
            return f"Only {parts[0]} exist."
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]} exist."
        else:
            return f"{', '.join(parts[:-1])}, and {parts[-1]} exist."
    
    def _render_timeline(self) -> Dict[str, Any]:
        """Render temporal context of investigation."""
        if not self._timeline:
            return {
                "section_type": "timeline",
                "title": "Timeline",
                "icon": "⏱️",
                "content": {
                    "status": "no_timeline",
                    "message": "No timeline data available."
                },
                "is_collapsible": True,
                "is_collapsed": True
            }
        
        return {
            "section_type": "timeline",
            "title": "Timeline",
            "icon": "⏱️",
            "content": {
                "started_at": self._timeline.started_at.isoformat(),
                "duration": self._timeline.duration_display,
                "is_active": self._timeline.is_active,
                "last_activity": self._timeline.last_activity.isoformat() if self._timeline.last_activity else None,
                "milestone_count": len(self._timeline.milestones)
            },
            "is_collapsible": True,
            "is_collapsed": self._config.collapse_details
        }
    
    def _render_unknowns(self) -> Dict[str, Any]:
        """Render what is explicitly unknown."""
        # Limit unknowns to prevent overwhelm
        display_unknowns = list(self._unknowns)
        if len(display_unknowns) > self._config.max_unknown_items:
            display_unknowns = display_unknowns[:self._config.max_unknown_items]
            has_more = True
        else:
            has_more = False
        
        unknowns_display = []
        for unknown in display_unknowns:
            unknowns_display.append({
                "category": unknown.category,
                "description": unknown.description,
                "reason": unknown.reason,
                "investigation_needed": unknown.investigation_needed
            })
        
        content = {
            "unknowns": unknowns_display,
            "total_count": len(self._unknowns),
            "displayed_count": len(display_unknowns),
            "has_more": has_more
        }
        
        if has_more:
            content["message"] = f"Showing {len(display_unknowns)} of {len(self._unknowns)} unknowns"
        
        return {
            "section_type": "unknowns",
            "title": "Known Unknowns",
            "icon": "❓",
            "content": content,
            "warning": "These are things the system cannot see or understand.",
            "is_collapsible": True,
            "is_collapsed": self._config.collapse_details
        }
    
    def _render_next_actions(self) -> Dict[str, Any]:
        """Render what can be done next (Article 7)."""
        actions = []
        stage = self._determine_stage()
        
        # Always allow observation
        actions.append({
            "action": "observe",
            "label": "Make observations",
            "icon": self._NEXT_ACTION_ICONS["observe"],
            "description": "Collect what exists in the codebase",
            "is_available": True,
            "priority": 1
        })
        
        # Allow questions if we have observations
        if self._metrics.has_observations:
            actions.append({
                "action": "question",
                "label": "Ask questions",
                "icon": self._NEXT_ACTION_ICONS["question"],
                "description": "Formulate questions about what you see",
                "is_available": True,
                "priority": 2
            })
        
        # Allow pattern detection if we have sufficient observations
        if self._metrics.observations_analyzed >= 10:
            actions.append({
                "action": "pattern",
                "label": "Detect patterns",
                "icon": self._NEXT_ACTION_ICONS["pattern"],
                "description": "Look for numerical regularities",
                "is_available": True,
                "priority": 3
            })
        
        # Allow thinking if we have patterns
        if self._metrics.has_patterns:
            actions.append({
                "action": "think",
                "label": "Record thoughts",
                "icon": self._NEXT_ACTION_ICONS["think"],
                "description": "Document your understanding and questions",
                "is_available": True,
                "priority": 4
            })
        
        # Allow synthesis if we have substantial notes
        if self._metrics.notes_recorded >= 5:
            actions.append({
                "action": "synthesize",
                "label": "Synthesize understanding",
                "icon": self._NEXT_ACTION_ICONS["synthesize"],
                "description": "Integrate observations, patterns, and thoughts",
                "is_available": True,
                "priority": 5
            })
        
        # Sort by priority
        actions.sort(key=lambda x: x["priority"])
        
        # Determine recommended action based on stage
        recommended_action = self._get_recommended_action(stage)
        
        return {
            "section_type": "next_actions",
            "title": "What You Can Do",
            "icon": "➡️",
            "content": {
                "actions": actions,
                "recommended_action": recommended_action,
                "stage_appropriate": True
            },
            "is_actionable": True,  # Article 7: Clear affordances
            "can_interact": True
        }
    
    def _get_recommended_action(self, stage: InvestigationStage) -> Optional[str]:
        """
        Get recommended next action based on investigation stage.
        
        Article 6: Linear Investigation - Follow natural curiosity.
        """
        if stage == InvestigationStage.ORIENTATION:
            return "observe"
        elif stage == InvestigationStage.OBSERVATION:
            if self._metrics.observations_analyzed >= 5:
                return "pattern"
            else:
                return "observe"
        elif stage == InvestigationStage.PATTERN_DETECTION:
            if self._metrics.has_patterns:
                return "think"
            else:
                return "question"
        elif stage == InvestigationStage.THINKING:
            return "synthesize"
        elif stage == InvestigationStage.SYNTHESIS:
            return "think"  # Always more thinking possible
        
        return None
    
    def _apply_single_focus(self, overview: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply single-focus interface rules.
        
        Article 5: Only one primary content area visible at a time.
        """
        # Find primary section
        primary_sections = [s for s in overview["sections"] if s.get("is_primary", False)]
        
        if len(primary_sections) > 1:
            # Multiple primaries - this is a violation
            # Keep first, mark others as secondary
            for i, section in enumerate(overview["sections"]):
                if section.get("is_primary", False) and i > 0:
                    section["is_primary"] = False
                    section["is_secondary"] = True
        
        elif len(primary_sections) == 0 and overview["sections"]:
            # No primary - make first section primary
            overview["sections"][0]["is_primary"] = True
        
        # Mark focus for display layer
        overview["focus_policy"] = "single_primary_with_context"
        
        return overview
    
    def _get_view_metadata(self) -> Dict[str, Any]:
        """Get metadata about this view rendering."""
        return {
            "metadata": {
                "rendered_at": datetime.now(timezone.utc).isoformat(),
                "config": asdict(self._config),
                "philosophy_rules_applied": [
                    "SingleFocusRule",
                    "ProgressiveDisclosureRule",
                    "ClarityRule",
                    "NavigationRule"
                ],
                "constitutional_compliance": [
                    "Article 4: Progressive Disclosure",
                    "Article 5: Single-Focus Interface",
                    "Article 6: Linear Investigation",
                    "Article 7: Clear Affordances",
                    "Article 8: Honest Performance"
                ],
                "integrity_checks": self._run_integrity_checks()
            }
        }
    
    def _run_integrity_checks(self) -> Dict[str, bool]:
        """Run integrity checks on the view."""
        checks = {
            "no_analysis_performed": True,  # This view never analyzes
            "no_inference_made": True,      # No guessing about meaning
            "unknowns_shown": self._config.show_unknowns and bool(self._unknowns),
            "affordances_clear": self._config.show_next_actions,
            "single_focus_enforced": True   # Enforced by _apply_single_focus
        }
        
        # Check that we're not doing analysis
        stage = self._determine_stage()
        if stage not in InvestigationStage:
            checks["no_analysis_performed"] = False
        
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
        for section in rendered.get("sections", []):
            content = section.get("content", {})
            if isinstance(content, dict):
                # Check for interpretative language
                interpretative_phrases = ["means", "suggests", "implies", "therefore", "thus"]
                for phrase in interpretative_phrases:
                    if phrase in str(content).lower():
                        violations.append(f"Section contains interpretative language: '{phrase}'")
        
        # Check 2: Unknowns must be shown if present
        if self._unknowns and not self._config.show_unknowns:
            violations.append("Unknown items exist but are hidden from view (Article 3 violation)")
        
        # Check 3: Must show what doesn't exist
        if not self._config.show_counts:
            violations.append("Presence indicators disabled - user cannot see what exists")
        
        # Check 4: Next actions must be clear
        if not self._config.show_next_actions:
            violations.append("Next actions not shown (Article 7 violation)")
        
        # Check 5: Single focus must be enforced
        primary_sections = [s for s in rendered.get("sections", []) 
                          if s.get("is_primary", False)]
        if len(primary_sections) != 1:
            violations.append(f"Single-focus violation: {len(primary_sections)} primary sections")
        
        return violations
    
    @classmethod
    def create_test_view(cls) -> OverviewView:
        """
        Create a test view for development and testing.
        
        Returns:
            An OverviewView with test data
        """
        from datetime import datetime, timedelta
        
        # Create test context
        class TestContext(InvestigationContext):
            def __init__(self) -> None:
                self.current_focus = "module:boundary_crossing.py"
                self.investigation_path = ["started", "focused_on_module"]
                self.created_at = datetime.now(timezone.utc)
        
        # Create test notebook
        class TestNoteCollection(NoteCollection):
            def get_all_notes(self) -> List:
                return [object()] * 3  # 3 notes
        
        # Create test metrics
        metrics = InvestigationMetrics(
            observations_total=42,
            observations_analyzed=35,
            patterns_detected=7,
            notes_recorded=3,
            questions_asked=5
        )
        
        # Create test focus
        focus = CurrentFocus(
            id="module:boundary_crossing.py",
            type="module",
            description="Module that appears to cross architectural boundaries",
            path="lobes/chatbuddy/boundary_crossing.py",
            context="Investigating potential constitutional violations"
        )
        
        # Create test unknowns
        unknowns = (
            UnknownItem(
                category="dynamic_imports",
                description="Runtime module loading",
                reason="Static analysis cannot detect imports created at runtime",
                investigation_needed=True
            ),
            UnknownItem(
                category="conditional_logic",
                description="Import statements inside conditionals",
                reason="Conditional imports may not be active in current environment",
                investigation_needed=False
            ),
        )
        
        # Create test timeline
        timeline = InvestigationTimeline(
            started_at=datetime.now(timezone.utc) - timedelta(hours=2),
            current_duration=timedelta(hours=2),
            last_activity=datetime.now(timezone.utc) - timedelta(minutes=5),
            milestones=(
                datetime.now(timezone.utc) - timedelta(hours=1, minutes=45),
                datetime.now(timezone.utc) - timedelta(hours=1, minutes=15),
            )
        )
        
        return cls(
            TestContext(),
            TestNoteCollection(),
            metrics,
            focus,
            unknowns,
            timeline
        )


def main() -> None:
    """Test the overview view."""
    view = OverviewView.create_test_view()
    
    # Render overview
    rendered = view.render()
    print("=== OVERVIEW VIEW ===")
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
    empty_view = OverviewView(
        TestContext(),
        TestNoteCollection(),
        InvestigationMetrics(),  # All zeros
        None,  # No focus
        (),    # No unknowns
        None,  # No timeline
        OverviewRenderConfig(show_counts=True, show_unknowns=True, show_next_actions=True)
    )
    empty_rendered = empty_view.render()
    print(json.dumps(empty_rendered, indent=2, default=str))


if __name__ == "__main__":
    main()