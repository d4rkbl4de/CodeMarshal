"""
lens.aesthetic.icons.py

Icon semantics for truth preservation.
Icons are signals, not illustrations.

CONSTRAINTS:
1. No decorative or novelty icons
2. One-to-one mapping: icon → concept (no ambiguity)
3. No context-dependent meaning
4. Icons must signal truth states, not emotions
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field


class SemanticIcon(Enum):
    """Semantic icons representing truth states and operations."""
    
    # Observation states
    OBSERVATION_COMPLETE = auto()      # Observation is unambiguous
    OBSERVATION_PARTIAL = auto()       # Observation has limitations
    OBSERVATION_FAILED = auto()        # Observation cannot be made
    OBSERVATION_IN_PROGRESS = auto()   # Observation is being collected
    
    # Uncertainty and warnings
    UNCERTAINTY = auto()               # Known limitations or incompleteness
    WARNING = auto()                   # Caution about interpretation
    ERROR = auto()                     # System or observation error
    
    # Navigation and investigation
    FOCUS = auto()                     # Current object of investigation
    NAVIGATE_BACK = auto()             # Move to previous observation
    NAVIGATE_FORWARD = auto()          # Move to next observation
    ZOOM_IN = auto()                   # Examine in more detail
    ZOOM_OUT = auto()                  # See broader context
    ANCHOR = auto()                    # Evidence anchor point
    
    # Information categories
    INFORMATION = auto()               # Additional factual information
    METADATA = auto()                  # Ancillary information
    PATTERN = auto()                   # Detected pattern (numeric only)
    CONNECTION = auto()                # Relationship between observations
    
    # System states
    SYSTEM_ACTIVE = auto()             # System is processing
    SYSTEM_IDLE = auto()               # System is waiting
    SYSTEM_HALTED = auto()             # System is stopped
    
    # User actions
    USER_QUESTION = auto()             # User is asking a question
    USER_THINKING = auto()             # User is adding a note
    USER_COMMAND = auto()              # User issued a command


@dataclass(frozen=True)
class IconRule:
    """Immutable rule defining an icon's meaning and constraints."""
    
    icon: SemanticIcon
    meaning: str  # Unambiguous semantic meaning
    precedence: int  # Higher number overrides lower in conflicts
    must_be_alone: bool = False  # Cannot appear with other icons
    prohibited_with: Set[SemanticIcon] = field(default_factory=lambda: set())
    required_context: Optional[str] = None  # Required context to show icon
    
    def __post_init__(self) -> None:
        """Validate icon rule consistency."""
        if self.must_be_alone and self.prohibited_with:
            raise ValueError(
                f"Icon {self.icon} cannot have prohibited_with if must_be_alone is True"
            )


class IconSystem:
    """
    Central authority for semantic icon usage.
    
    Enforces:
    1. Icons have fixed, unambiguous meanings
    2. No ambiguous or decorative icons
    3. Icon conflicts are prevented
    4. Icons signal truth, not emotion
    """
    
    def __init__(self) -> None:
        self._rules = self._build_rules()
        self._icon_meanings = self._build_meanings()
        
    def _build_rules(self) -> Dict[SemanticIcon, IconRule]:
        """Construct the immutable icon rule system."""
        
        return {
            SemanticIcon.ERROR: IconRule(
                icon=SemanticIcon.ERROR,
                meaning="System or observation error - cannot proceed",
                precedence=100,  # Highest precedence
                must_be_alone=True,  # Error must be clear and unambiguous
            ),
            
            SemanticIcon.OBSERVATION_FAILED: IconRule(
                icon=SemanticIcon.OBSERVATION_FAILED,
                meaning="Observation cannot be made due to limitations",
                precedence=90,
                prohibited_with={
                    SemanticIcon.OBSERVATION_COMPLETE,
                    SemanticIcon.OBSERVATION_PARTIAL,
                },
            ),
            
            SemanticIcon.WARNING: IconRule(
                icon=SemanticIcon.WARNING,
                meaning="Caution about interpretation or system limitations",
                precedence=80,
                prohibited_with={
                    SemanticIcon.OBSERVATION_COMPLETE,
                    SemanticIcon.INFORMATION,
                },
            ),
            
            SemanticIcon.UNCERTAINTY: IconRule(
                icon=SemanticIcon.UNCERTAINTY,
                meaning="Observation has known limitations or incompleteness",
                precedence=70,
                prohibited_with={
                    SemanticIcon.OBSERVATION_COMPLETE,
                    SemanticIcon.PATTERN,  # Patterns with uncertainty need special handling
                },
            ),
            
            SemanticIcon.OBSERVATION_PARTIAL: IconRule(
                icon=SemanticIcon.OBSERVATION_PARTIAL,
                meaning="Observation is partially complete with acknowledged gaps",
                precedence=60,
                prohibited_with={
                    SemanticIcon.OBSERVATION_COMPLETE,
                },
            ),
            
            SemanticIcon.OBSERVATION_COMPLETE: IconRule(
                icon=SemanticIcon.OBSERVATION_COMPLETE,
                meaning="Observation is complete and unambiguous",
                precedence=50,
                prohibited_with={
                    SemanticIcon.UNCERTAINTY,
                    SemanticIcon.WARNING,
                    SemanticIcon.OBSERVATION_FAILED,
                    SemanticIcon.OBSERVATION_PARTIAL,
                },
            ),
            
            SemanticIcon.FOCUS: IconRule(
                icon=SemanticIcon.FOCUS,
                meaning="Current object of investigation",
                precedence=40,
                prohibited_with={
                    SemanticIcon.WARNING,
                    SemanticIcon.ERROR,
                },
            ),
            
            SemanticIcon.SYSTEM_HALTED: IconRule(
                icon=SemanticIcon.SYSTEM_HALTED,
                meaning="System is stopped and cannot proceed",
                precedence=95,  # Very high - stopped system is critical
                must_be_alone=True,
            ),
            
            SemanticIcon.SYSTEM_ACTIVE: IconRule(
                icon=SemanticIcon.SYSTEM_ACTIVE,
                meaning="System is processing or collecting observations",
                precedence=30,
                prohibited_with={
                    SemanticIcon.SYSTEM_IDLE,
                    SemanticIcon.SYSTEM_HALTED,
                },
            ),
            
            SemanticIcon.SYSTEM_IDLE: IconRule(
                icon=SemanticIcon.SYSTEM_IDLE,
                meaning="System is waiting for user input",
                precedence=20,
                prohibited_with={
                    SemanticIcon.SYSTEM_ACTIVE,
                    SemanticIcon.SYSTEM_HALTED,
                },
            ),
            
            SemanticIcon.USER_QUESTION: IconRule(
                icon=SemanticIcon.USER_QUESTION,
                meaning="User is asking a question about observations",
                precedence=35,
                prohibited_with={
                    SemanticIcon.USER_COMMAND,
                    SemanticIcon.USER_THINKING,
                },
            ),
            
            SemanticIcon.USER_THINKING: IconRule(
                icon=SemanticIcon.USER_THINKING,
                meaning="User is adding a note or thought anchored to observation",
                precedence=34,
                required_context="thinking_enabled",
                prohibited_with={
                    SemanticIcon.USER_QUESTION,
                    SemanticIcon.USER_COMMAND,
                },
            ),
            
            SemanticIcon.USER_COMMAND: IconRule(
                icon=SemanticIcon.USER_COMMAND,
                meaning="User issued a system command",
                precedence=33,
                prohibited_with={
                    SemanticIcon.USER_QUESTION,
                    SemanticIcon.USER_THINKING,
                },
            ),
            
            SemanticIcon.PATTERN: IconRule(
                icon=SemanticIcon.PATTERN,
                meaning="Numeric pattern detected in observations",
                precedence=25,
                required_context="pattern_detected",
                prohibited_with={
                    SemanticIcon.INFORMATION,  # Patterns are distinct from general info
                },
            ),
            
            SemanticIcon.CONNECTION: IconRule(
                icon=SemanticIcon.CONNECTION,
                meaning="Relationship between observations detected",
                precedence=24,
                required_context="connections_visible",
            ),
            
            SemanticIcon.INFORMATION: IconRule(
                icon=SemanticIcon.INFORMATION,
                meaning="Additional factual information available",
                precedence=15,
                prohibited_with={
                    SemanticIcon.WARNING,  # Information should not look like warning
                    SemanticIcon.ERROR,
                },
            ),
            
            SemanticIcon.METADATA: IconRule(
                icon=SemanticIcon.METADATA,
                meaning="Ancillary information about observations",
                precedence=10,
                prohibited_with={
                    SemanticIcon.FOCUS,  # Metadata should not compete with focus
                    SemanticIcon.WARNING,
                },
            ),
            
            SemanticIcon.ANCHOR: IconRule(
                icon=SemanticIcon.ANCHOR,
                meaning="Evidence anchor point - observation reference",
                precedence=5,
                required_context="requires_anchor",
            ),
            
            # Navigation icons (low precedence, can coexist with most things)
            SemanticIcon.NAVIGATE_BACK: IconRule(
                icon=SemanticIcon.NAVIGATE_BACK,
                meaning="Navigate to previous observation in investigation",
                precedence=1,
            ),
            
            SemanticIcon.NAVIGATE_FORWARD: IconRule(
                icon=SemanticIcon.NAVIGATE_FORWARD,
                meaning="Navigate to next observation in investigation",
                precedence=1,
            ),
            
            SemanticIcon.ZOOM_IN: IconRule(
                icon=SemanticIcon.ZOOM_IN,
                meaning="Examine current observation in more detail",
                precedence=1,
            ),
            
            SemanticIcon.ZOOM_OUT: IconRule(
                icon=SemanticIcon.ZOOM_OUT,
                meaning="See broader context around current observation",
                precedence=1,
            ),
        }
    
    def _build_meanings(self) -> Dict[SemanticIcon, str]:
        """Create a direct mapping of icon to meaning for quick reference."""
        return {rule.icon: rule.meaning for rule in self._rules.values()}
    
    def get_meaning(self, icon: SemanticIcon) -> str:
        """Get the unambiguous meaning of a semantic icon."""
        return self._icon_meanings[icon]
    
    def get_required_context(self, icon: SemanticIcon) -> Optional[str]:
        """Get the required context for an icon, if any."""
        rule = self._rules[icon]
        return rule.required_context
    
    def validate_icons(
        self, 
        icons: Set[SemanticIcon], 
        context: Optional[Set[str]] = None
    ) -> List[str]:
        """
        Validate that icons can appear together in given context.
        
        Args:
            icons: The icons to validate
            context: Set of context flags (e.g., {"thinking_enabled", "pattern_detected"})
            
        Returns:
            List of violation messages, empty if valid.
        """
        violations: List[str] = []
        
        if context is None:
            context = set()
        
        # Check each icon against others and context
        for icon in icons:
            rule = self._rules[icon]
            
            # Check context requirements
            if rule.required_context and rule.required_context not in context:
                violations.append(
                    f"Icon {icon.name} requires context '{rule.required_context}'"
                )
            
            # Check if must be alone
            if rule.must_be_alone and len(icons) > 1:
                violations.append(
                    f"Icon {icon.name} must appear alone (cannot combine with other icons)"
                )
                continue
            
            # Check prohibited combinations
            for other_icon in icons:
                if other_icon == icon:
                    continue
                    
                if other_icon in rule.prohibited_with:
                    violations.append(
                        f"Icon {icon.name} cannot appear with {other_icon.name}"
                    )
        
        # Resolve precedence conflicts
        if not violations and len(icons) > 1:
            # Find the highest precedence icon
            precedences = [(i, self._rules[i].precedence) for i in icons]
            precedences.sort(key=lambda x: x[1], reverse=True)
            
            highest_icon = precedences[0][0]
            highest_precedence = precedences[0][1]
            
            # Check if any lower precedence icons conflict with highest
            for icon, precedence in precedences[1:]:
                if precedence < highest_precedence:
                    if icon in self._rules[highest_icon].prohibited_with:
                        violations.append(
                            f"Icon {highest_icon.name} (precedence {highest_precedence}) "
                            f"conflicts with {icon.name}"
                        )
        
        return violations
    
    def resolve_conflict(
        self, 
        icons: Set[SemanticIcon]
    ) -> Optional[SemanticIcon]:
        """
        When icons conflict, determine which should be shown.
        
        Returns:
            The icon that should be displayed, or None if no resolution possible.
        """
        if not icons:
            return None
        
        # Single icon - no conflict
        if len(icons) == 1:
            return next(iter(icons))
        
        # Check for must-be-alone icons
        for icon in icons:
            if self._rules[icon].must_be_alone:
                return icon
        
        # Use precedence
        precedences = [(i, self._rules[i].precedence) for i in icons]
        precedences.sort(key=lambda x: x[1], reverse=True)
        
        highest_icon = precedences[0][0]
        
        # Verify highest doesn't conflict with others
        for icon, _ in precedences[1:]:
            if icon in self._rules[highest_icon].prohibited_with:
                # Conflict - cannot resolve
                return None
        
        return highest_icon
    
    def get_icon_for_state(self, state_type: str) -> SemanticIcon:
        """
        Map common observation/inquiry states to semantic icons.
        
        This ensures consistent mapping across the system.
        """
        mapping: Dict[str, SemanticIcon] = {
            # Observation states
            "observation_complete": SemanticIcon.OBSERVATION_COMPLETE,
            "observation_partial": SemanticIcon.OBSERVATION_PARTIAL,
            "observation_failed": SemanticIcon.OBSERVATION_FAILED,
            "observation_in_progress": SemanticIcon.OBSERVATION_IN_PROGRESS,
            
            # Truth states
            "uncertainty": SemanticIcon.UNCERTAINTY,
            "warning": SemanticIcon.WARNING,
            "error": SemanticIcon.ERROR,
            
            # Investigation states
            "current_focus": SemanticIcon.FOCUS,
            "has_anchor": SemanticIcon.ANCHOR,
            
            # System states
            "system_active": SemanticIcon.SYSTEM_ACTIVE,
            "system_idle": SemanticIcon.SYSTEM_IDLE,
            "system_halted": SemanticIcon.SYSTEM_HALTED,
            
            # User states
            "user_question": SemanticIcon.USER_QUESTION,
            "user_thinking": SemanticIcon.USER_THINKING,
            "user_command": SemanticIcon.USER_COMMAND,
            
            # Information states
            "pattern_detected": SemanticIcon.PATTERN,
            "connection_detected": SemanticIcon.CONNECTION,
            "has_information": SemanticIcon.INFORMATION,
            "has_metadata": SemanticIcon.METADATA,
        }
        
        return mapping.get(state_type, SemanticIcon.INFORMATION)
    
    def get_navigation_icons(self) -> Set[SemanticIcon]:
        """Get all icons that are primarily for navigation."""
        return {
            SemanticIcon.NAVIGATE_BACK,
            SemanticIcon.NAVIGATE_FORWARD,
            SemanticIcon.ZOOM_IN,
            SemanticIcon.ZOOM_OUT,
        }
    
    def get_truth_state_icons(self) -> Set[SemanticIcon]:
        """Get all icons that represent truth states (vs. actions)."""
        return {
            SemanticIcon.OBSERVATION_COMPLETE,
            SemanticIcon.OBSERVATION_PARTIAL,
            SemanticIcon.OBSERVATION_FAILED,
            SemanticIcon.UNCERTAINTY,
            SemanticIcon.WARNING,
            SemanticIcon.ERROR,
        }
    
    def get_allowed_combinations(self) -> List[Tuple[SemanticIcon, ...]]:
        """
        Get all pre-approved icon combinations.
        
        Useful for UI components that need to know valid combinations.
        """
        allowed: List[Tuple[SemanticIcon, ...]] = []
        
        # Single icons are always allowed
        for icon in SemanticIcon:
            allowed.append((icon,))
        
        # Pre-approved combinations that preserve meaning
        approved_combinations: List[Tuple[SemanticIcon, ...]] = [
            # Navigation can accompany most things
            (SemanticIcon.FOCUS, SemanticIcon.NAVIGATE_BACK, SemanticIcon.NAVIGATE_FORWARD),
            (SemanticIcon.OBSERVATION_COMPLETE, SemanticIcon.ZOOM_IN),
            (SemanticIcon.OBSERVATION_PARTIAL, SemanticIcon.UNCERTAINTY),
            
            # User actions with system state
            (SemanticIcon.USER_QUESTION, SemanticIcon.SYSTEM_IDLE),
            (SemanticIcon.USER_THINKING, SemanticIcon.ANCHOR),
            
            # Information combinations
            (SemanticIcon.PATTERN, SemanticIcon.INFORMATION),
            (SemanticIcon.CONNECTION, SemanticIcon.INFORMATION),
        ]
        
        for combo in approved_combinations:
            if not self.validate_icons(set(combo)):
                allowed.append(combo)
        
        return allowed


# Singleton instance for system-wide consistency
ICONS = IconSystem()


def validate_icon_usage(
    primary_icon: SemanticIcon,
    context_icons: Optional[Set[SemanticIcon]] = None,
    context: Optional[Set[str]] = None
) -> List[str]:
    """
    Validate that an icon can be used in the given context.
    
    Args:
        primary_icon: The main icon to validate
        context_icons: Other icons present
        context: Context flags
        
    Returns:
        List of violation messages, empty if valid
    """
    if context_icons is None:
        context_icons = set()
    
    all_icons = context_icons.union({primary_icon})
    return ICONS.validate_icons(all_icons, context)


def icon_requires_context(icon: SemanticIcon) -> Optional[str]:
    """Check if an icon requires a specific context to be shown."""
    return ICONS.get_required_context(icon)


def get_icon_for_state(state_type: str) -> SemanticIcon:
    """Map common observation/inquiry states to semantic icons."""
    return ICONS.get_icon_for_state(state_type)


# Export the public API
__all__ = [
    'SemanticIcon',
    'IconSystem',
    'ICONS',
    'validate_icon_usage',
    'icon_requires_context',
    'get_icon_for_state',
]