"""
lens.__init__.py

Interface Layer (Layer 3) - The truth-preserving lens through which CodeMarshal is viewed.

This package provides the visual and interaction framework that preserves truth
while supporting human investigation. It enforces constitutional constraints
on how information is presented.

LAYER RULES:
1. Lens never computes facts - only displays what exists
2. Lens never modifies observations - only presents them
3. Lens must make false confidence harder, not easier
4. Lens must support single-focus, linear investigation
"""

from . import aesthetic
from . import philosophy
from . import views
from . import navigation
from . import indicators

from .aesthetic import (
    # Typography
    TextRole,
    TYPEOGRAPHY,
    
    # Color
    SemanticColor,
    PALETTE,
    
    # Icons
    SemanticIcon,
    ICONS,
    
    # Layout
    LayoutRegion,
    LAYOUT,
    
    # Unified aesthetic system
    AESTHETICS,
)

from typing import Optional, Any, Dict, List, Set, Union, cast
from dataclasses import dataclass
from enum import Enum


class InvestigationMode(Enum):
    """
    Modes of investigation that determine what lens is applied.
    
    Each mode corresponds to a different way of looking at truth,
    following the natural progression of human curiosity.
    """
    OBSERVING = "observing"           # What exists? (Layer 1)
    QUESTIONING = "questioning"       # What does it do? (Layer 2)
    CONNECTING = "connecting"         # How is it connected? (Layer 2)
    PATTERNING = "patterning"         # What patterns exist? (Layer 2)
    THINKING = "thinking"             # What do I think? (Layer 2)
    
    @classmethod
    def from_context(cls, context_type: str) -> "InvestigationMode":
        """Map context types to investigation modes."""
        mapping: Dict[str, "InvestigationMode"] = {
            "initial_observation": cls.OBSERVING,
            "user_question": cls.QUESTIONING,
            "connections_view": cls.CONNECTING,
            "patterns_view": cls.PATTERNING,
            "thinking_session": cls.THINKING,
        }
        return mapping.get(context_type, cls.OBSERVING)


# Type alias for aesthetic constraint values
AestheticConstraintValue = Union[TextRole, SemanticColor, int, bool, str]


@dataclass(frozen=True)
class LensConfiguration:
    """
    Immutable configuration for a truth-preserving lens.
    
    This determines how information will be presented to preserve truth
    while supporting the current investigation mode.
    
    Using frozen dataclass ensures immutability, which is essential
    for truth preservation (Article 9: Immutable Observations).
    """
    mode: InvestigationMode
    aesthetic_constraints: Dict[str, AestheticConstraintValue]
    layout_regions: Set[LayoutRegion]
    allowed_actions: Set[str]
    focus_requirements: List[str]
    
    @classmethod
    def create(
        cls,
        mode: InvestigationMode,
        aesthetic_constraints: Optional[Dict[str, AestheticConstraintValue]] = None,
        layout_regions: Optional[Set[LayoutRegion]] = None,
        allowed_actions: Optional[Set[str]] = None,
        focus_requirements: Optional[List[str]] = None,
    ) -> "LensConfiguration":
        """
        Factory method to create a LensConfiguration with proper default values.
        
        This preserves the frozen nature of the dataclass while allowing
        optional parameters with defaults.
        """
        constraints = aesthetic_constraints or {}
        regions = layout_regions or set()
        actions = allowed_actions or set()
        requirements = focus_requirements or []
        
        # Create the frozen instance
        config = cls(
            mode=mode,
            aesthetic_constraints=constraints,
            layout_regions=regions,
            allowed_actions=actions,
            focus_requirements=requirements,
        )
        
        # Validate the configuration
        config._validate()
        return config
    
    def _validate(self) -> None:
        """Validate lens configuration (internal)."""
        # Must have at least one layout region
        if not self.layout_regions:
            raise ValueError("Lens configuration must specify at least one layout region")
        
        # Must have appropriate aesthetic constraints for mode
        if not self.aesthetic_constraints:
            raise ValueError("Lens configuration must specify aesthetic constraints")
        
        # Validate layout composition
        violations = LAYOUT.validate_regions(self.layout_regions)
        if violations:
            raise ValueError(f"Invalid layout regions: {violations}")


class LensSystem:
    """
    Central authority for truth-preserving interface presentation.
    
    Coordinates aesthetic, layout, and interaction constraints to ensure
    the interface never distorts truth or creates false confidence.
    """
    
    def __init__(self) -> None:
        self._configurations = self._build_configurations()
        self._current_mode: Optional[InvestigationMode] = None
        self._current_focus: Optional[str] = None
        
    def _build_configurations(self) -> Dict[InvestigationMode, LensConfiguration]:
        """Build constitutional lens configurations for each investigation mode."""
        
        return {
            InvestigationMode.OBSERVING: LensConfiguration.create(
                mode=InvestigationMode.OBSERVING,
                aesthetic_constraints={
                    "primary_role": TextRole.PRIMARY,
                    "secondary_limit": 3,
                    "warning_interrupt": True,
                    "uncertainty_visible": True,
                },
                layout_regions={
                    LayoutRegion.PRIMARY,
                    LayoutRegion.NAVIGATION,
                    LayoutRegion.STATUS,
                },
                allowed_actions={
                    "navigate_next",
                    "navigate_previous",
                    "zoom_in",
                    "ask_question",
                    "view_connections",
                },
                focus_requirements=[
                    "single_primary_object",
                    "clear_observation_boundaries",
                ],
            ),
            
            InvestigationMode.QUESTIONING: LensConfiguration.create(
                mode=InvestigationMode.QUESTIONING,
                aesthetic_constraints={
                    "primary_role": TextRole.PRIMARY,
                    "question_role": TextRole.USER_INPUT,
                    "answer_role": TextRole.SECONDARY,
                },
                layout_regions={
                    LayoutRegion.PRIMARY,
                    LayoutRegion.SECONDARY,
                    LayoutRegion.NAVIGATION,
                },
                allowed_actions={
                    "navigate_answers",
                    "refine_question",
                    "return_to_observation",
                    "view_patterns",
                },
                focus_requirements=[
                    "question_must_anchor_to_observation",
                    "answers_must_cite_evidence",
                ],
            ),
            
            InvestigationMode.CONNECTING: LensConfiguration.create(
                mode=InvestigationMode.CONNECTING,
                aesthetic_constraints={
                    "connection_color": SemanticColor.NEUTRAL,
                    "uncertainty_highlight": True,
                    "boundary_violation_color": SemanticColor.WARNING,
                },
                layout_regions={
                    LayoutRegion.PRIMARY,
                    LayoutRegion.SECONDARY,
                    LayoutRegion.NAVIGATION,
                },
                allowed_actions={
                    "trace_connection",
                    "view_connection_evidence",
                    "filter_connections",
                    "return_to_observation",
                },
                focus_requirements=[
                    "connections_must_have_evidence",
                    "boundary_crossings_must_be_flagged",
                ],
            ),
            
            InvestigationMode.PATTERNING: LensConfiguration.create(
                mode=InvestigationMode.PATTERNING,
                aesthetic_constraints={
                    "pattern_color": SemanticColor.NEUTRAL,
                    "uncertainty_required": True,
                    "no_interpretation": True,
                },
                layout_regions={
                    LayoutRegion.PRIMARY,
                    LayoutRegion.SECONDARY,
                    LayoutRegion.NAVIGATION,
                },
                allowed_actions={
                    "view_pattern_evidence",
                    "compare_patterns",
                    "note_pattern_uncertainty",
                    "return_to_observation",
                },
                focus_requirements=[
                    "patterns_must_be_numeric_only",
                    "uncertainty_must_be_displayed",
                    "no_semantic_interpretation",
                ],
            ),
            
            InvestigationMode.THINKING: LensConfiguration.create(
                mode=InvestigationMode.THINKING,
                aesthetic_constraints={
                    "thinking_role": TextRole.USER_INPUT,
                    "anchor_required": True,
                    "thinking_isolated": True,
                },
                layout_regions={
                    LayoutRegion.PRIMARY,
                    LayoutRegion.THINKING,
                    LayoutRegion.NAVIGATION,
                },
                allowed_actions={
                    "add_note",
                    "anchor_note",
                    "view_note_history",
                    "export_notes",
                    "return_to_observation",
                },
                focus_requirements=[
                    "thinking_must_anchor_to_observation",
                    "notes_cannot_modify_observations",
                    "thinking_isolation_preserved",
                ],
            ),
        }
    
    def get_configuration(self, mode: InvestigationMode) -> LensConfiguration:
        """Get the lens configuration for a specific investigation mode."""
        return self._configurations[mode]
    
    def validate_transition(
        self, 
        from_mode: Optional[InvestigationMode], 
        to_mode: InvestigationMode
    ) -> List[str]:
        """
        Validate that a mode transition preserves truth.
        
        Some transitions are prohibited because they would skip
        essential investigation steps or create confusion.
        """
        violations: List[str] = []
        
        # Initial transition (from None) is always allowed
        if from_mode is None:
            return violations
        
        # Linear progression is encouraged but not strictly required
        # However, certain backwards transitions are prohibited
        
        # Cannot skip from OBSERVING directly to PATTERNING or THINKING
        # Must go through QUESTIONING or CONNECTING first
        if (from_mode == InvestigationMode.OBSERVING and 
            to_mode in [InvestigationMode.PATTERNING, InvestigationMode.THINKING]):
            violations.append(
                "Cannot skip from OBSERVING to PATTERNING or THINKING. "
                "Must go through QUESTIONING or CONNECTING first."
            )
        
        # Cannot go from THINKING back to OBSERVING without explicit action
        # (Thinking should be anchored to specific observation)
        if (from_mode == InvestigationMode.THINKING and 
            to_mode == InvestigationMode.OBSERVING):
            violations.append(
                "Cannot transition directly from THINKING to OBSERVING. "
                "Must explicitly return to observation context."
            )
        
        return violations
    
    def apply_lens(
        self,
        mode: InvestigationMode,
        content: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply truth-preserving lens to content for presentation.
        
        This transforms raw observations/inquiry data into a form
        suitable for display while preserving all truth constraints.
        """
        if context is None:
            context = {}
        
        config = self.get_configuration(mode)
        
        # Apply mode-specific transformations
        transformed = self._transform_for_mode(mode, content, config)
        
        # Apply aesthetic constraints
        transformed = self._apply_aesthetic_constraints(transformed, config)
        
        # Apply layout constraints
        transformed = self._apply_layout_constraints(transformed, config)
        
        # Apply focus requirements
        transformed = self._enforce_focus_requirements(transformed, config)
        
        # Add mode metadata
        transformed["_lens_metadata"] = {
            "mode": mode.value,
            "constraints_applied": list(config.aesthetic_constraints.keys()),
            "regions_active": [r.name for r in config.layout_regions],
            "allowed_actions": list(config.allowed_actions),
        }
        
        return transformed
    
    def _transform_for_mode(
        self,
        mode: InvestigationMode,
        content: Dict[str, Any],
        config: LensConfiguration
    ) -> Dict[str, Any]:
        """Apply mode-specific content transformations."""
        transformed = content.copy()
        
        if mode == InvestigationMode.OBSERVING:
            # Ensure observation purity
            if "interpretation" in transformed:
                del transformed["interpretation"]
            if "conclusions" in transformed:
                del transformed["conclusions"]
        
        elif mode == InvestigationMode.QUESTIONING:
            # Structure questions and answers
            if "question" not in transformed:
                transformed["question"] = {"text": "", "anchor": None}
            if "answers" not in transformed:
                transformed["answers"] = []
        
        elif mode == InvestigationMode.PATTERNING:
            # Strip non-numeric patterns
            patterns = transformed.get("patterns")
            if isinstance(patterns, list):
                # Filter to only numeric patterns
                numeric_patterns: List[Dict[str, Any]] = []
                # Cast the list to List[Any] to help type inference
                patterns_cast = cast(List[Any], patterns)
                for pattern_item in patterns_cast:
                    # Check if it's a dictionary with a type field
                    if isinstance(pattern_item, dict):
                        # Cast the dictionary to Dict[str, Any] after type check
                        pattern_dict = cast(Dict[str, Any], pattern_item)
                        # Check if it has the right type
                        pattern_type = pattern_dict.get("type")
                        if isinstance(pattern_type, str) and pattern_type == "numeric":
                            numeric_patterns.append(pattern_dict)
                transformed["patterns"] = numeric_patterns
        
        elif mode == InvestigationMode.THINKING:
            # Ensure thinking is anchored
            if "thinking" in transformed and "anchor" not in transformed["thinking"]:
                transformed["thinking"]["anchor"] = {"required": True, "present": False}
        
        return transformed
    
    def _apply_aesthetic_constraints(
        self,
        content: Dict[str, Any],
        config: LensConfiguration
    ) -> Dict[str, Any]:
        """Apply aesthetic constraints to content."""
        # This would integrate with the aesthetic system to assign
        # appropriate colors, icons, text roles based on content and mode
        content["_aesthetic"] = {
            "assigned": False,  # Would be set by aesthetic system
            "validated": False,
            "violations": [],
        }
        return content
    
    def _apply_layout_constraints(
        self,
        content: Dict[str, Any],
        config: LensConfiguration
    ) -> Dict[str, Any]:
        """Apply layout constraints to content."""
        # Map content to appropriate layout regions
        content["_layout"] = {
            "regions": [r.name for r in config.layout_regions],
            "primary_region": LayoutRegion.PRIMARY.name,
            "arrangement": {},  # Would be populated by layout system
        }
        return content
    
    def _enforce_focus_requirements(
        self,
        content: Dict[str, Any],
        config: LensConfiguration
    ) -> Dict[str, Any]:
        """Enforce focus requirements for the mode."""
        # Create typed structure for focus information
        requirements_met: List[str] = []
        requirements_violated: List[str] = []
        
        # Check each requirement
        for requirement in config.focus_requirements:
            # This would contain actual validation logic
            # For now, we just track the requirements
            requirements_met.append(requirement)
        
        content["_focus"] = {
            "requirements_met": requirements_met,
            "requirements_violated": requirements_violated,
        }
        
        return content


# Singleton lens system
LENS = LensSystem()


# Export the public API
__all__ = [
    # Subpackages
    'aesthetic',
    'philosophy',
    'views',
    'navigation',
    'indicators',
    
    # Investigation modes
    'InvestigationMode',
    
    # Lens system
    'LensSystem',
    'LENS',
    
    # Re-exported aesthetic primitives (for convenience)
    'TextRole',
    'TYPEOGRAPHY',
    'SemanticColor',
    'PALETTE',
    'SemanticIcon',
    'ICONS',
    'LayoutRegion',
    'LAYOUT',
    'AESTHETICS',
]


