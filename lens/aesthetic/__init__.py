"""
lens.aesthetic.__init__.py

Canonical aesthetic vocabulary for CodeMarshal.
This module defines the truth-preserving visual language.

CONSTRAINTS:
1. Only semantic visual concepts exported here
2. No implementation details, only interfaces
3. All visual concepts must have clear epistemic meaning
4. No emotional or decorative elements
"""

from .icons import (
    ICONS,
    IconSystem,
    SemanticIcon,
    get_icon_for_state,
    icon_requires_context,
    validate_icon_usage,
)
from .layout import (
    LAYOUT,
    LayoutConstraint,
    LayoutRegion,
    LayoutSystem,
    get_regions_for_context,
    validate_layout_composition,
)
from .palette import (
    PALETTE,
    PaletteSystem,
    SemanticColor,
    get_color_for_state,
    validate_color_usage,
)
from .typography import (
    TYPEOGRAPHY,
    TextRole,
    TypographySystem,
    get_roles_for_content_type,
    validate_text_role,
)


class AestheticVocabulary:
    """
    Unified access to truth-preserving aesthetic primitives.

    This class provides semantic mapping between different aesthetic domains
    (typography, color, icons, layout) to ensure visual consistency.
    """

    def __init__(self) -> None:
        self.typography = TYPEOGRAPHY
        self.palette = PALETTE
        self.icons = ICONS
        self.layout = LAYOUT

    def map_state_to_aesthetics(
        self, state_type: str
    ) -> tuple[TextRole, SemanticColor, SemanticIcon, set[LayoutRegion]]:
        """
        Map a semantic state to appropriate aesthetic primitives.

        This ensures consistent visual representation of truth states
        across the entire system.

        Args:
            state_type: Semantic state (e.g., "observation_complete", "warning")

        Returns:
            Tuple of (text_role, color, icon, layout_regions)
        """
        # Get base mappings from each system
        text_roles = get_roles_for_content_type(state_type)
        color = get_color_for_state(state_type)
        icon = get_icon_for_state(state_type)
        layout_regions = get_regions_for_context(state_type)

        # Use primary text role if multiple are suggested
        primary_text_role = text_roles[0] if text_roles else TextRole.SECONDARY

        return (primary_text_role, color, icon, layout_regions)

    def validate_visual_composition(
        self,
        text_roles: set[TextRole],
        colors: set[SemanticColor],
        icons: set[SemanticIcon],
        regions: set[LayoutRegion],
        context: set[str] | None = None,
    ) -> list[str]:
        """
        Validate that a complete visual composition preserves truth.

        This is the final guardrail before rendering - ensures all
        aesthetic decisions are compatible and truth-preserving.

        Args:
            text_roles: Text roles to be used
            colors: Colors to be used
            icons: Icons to be used
            regions: Layout regions to be used
            context: Context flags for icon validation

        Returns:
            List of violation messages, empty if valid
        """
        violations: list[str] = []

        # Validate each domain
        for role in text_roles:
            violations.extend(validate_text_role(role, context_roles=list(text_roles)))

        for color in colors:
            violations.extend(validate_color_usage(color, context_colors=colors))

        violations.extend(self.icons.validate_icons(icons, context))
        violations.extend(self.layout.validate_regions(regions))

        # Cross-domain validations

        # Check if colors match text roles
        for color in colors:
            # Certain colors require certain text roles
            if color == SemanticColor.ERROR:
                if TextRole.WARNING not in text_roles:
                    violations.append(
                        "ERROR color should use WARNING text role for emphasis"
                    )

        # Check if icons match regions
        navigation_icons = self.icons.get_navigation_icons()
        if (
            navigation_icons.intersection(icons)
            and LayoutRegion.NAVIGATION not in regions
        ):
            violations.append("Navigation icons should appear in NAVIGATION region")

        return violations

    def get_canonical_states(self) -> dict[str, dict[str, str]]:
        """
        Get all canonical truth states and their aesthetic meanings.

        This serves as the authoritative reference for what visual
        representations mean in CodeMarshal.

        Returns:
            Dictionary mapping state_type to aesthetic descriptions
        """
        states: dict[str, dict[str, str]] = {}

        # Observation states
        states["observation_complete"] = {
            "description": "Observation is complete and unambiguous",
            "text_role": "PRIMARY or SECONDARY",
            "color": "CERTAINTY",
            "icon": "OBSERVATION_COMPLETE",
            "layout": "PRIMARY region",
        }

        states["observation_partial"] = {
            "description": "Observation has acknowledged gaps or limitations",
            "text_role": "PRIMARY with WARNING annotation",
            "color": "UNCERTAINTY",
            "icon": "OBSERVATION_PARTIAL",
            "layout": "PRIMARY with WARNING region",
        }

        states["observation_failed"] = {
            "description": "Observation cannot be made due to limitations",
            "text_role": "WARNING",
            "color": "ERROR",
            "icon": "OBSERVATION_FAILED",
            "layout": "WARNING region interrupting flow",
        }

        # Truth states
        states["uncertainty"] = {
            "description": "Known limitations or incompleteness in observation",
            "text_role": "WARNING",
            "color": "UNCERTAINTY",
            "icon": "UNCERTAINTY",
            "layout": "WARNING region",
        }

        states["warning"] = {
            "description": "Caution about interpretation or system limitations",
            "text_role": "WARNING",
            "color": "WARNING",
            "icon": "WARNING",
            "layout": "WARNING region (must interrupt)",
        }

        states["error"] = {
            "description": "System or observation error - cannot proceed",
            "text_role": "WARNING",
            "color": "ERROR",
            "icon": "ERROR",
            "layout": "WARNING region (must be alone)",
        }

        # Investigation states
        states["current_focus"] = {
            "description": "Current object of investigation",
            "text_role": "PRIMARY",
            "color": "FOCUS",
            "icon": "FOCUS",
            "layout": "PRIMARY region (single focus)",
        }

        states["thinking_active"] = {
            "description": "User is adding thoughts anchored to observation",
            "text_role": "USER_INPUT",
            "color": "USER_ACTION",
            "icon": "USER_THINKING",
            "layout": "THINKING region (requires anchor)",
        }

        # System states
        states["system_active"] = {
            "description": "System is processing or collecting observations",
            "text_role": "STATUS",
            "color": "STATUS",
            "icon": "SYSTEM_ACTIVE",
            "layout": "STATUS region (isolated)",
        }

        states["system_halted"] = {
            "description": "System is stopped and cannot proceed",
            "text_role": "WARNING",
            "color": "ERROR",
            "icon": "SYSTEM_HALTED",
            "layout": "WARNING region (must be alone)",
        }

        return states

    def get_prohibited_patterns(self) -> list[str]:
        """
        Get list of prohibited aesthetic patterns that violate truth preservation.

        These patterns create false confidence, hide uncertainty, or distort truth.
        """
        return [
            "Certainty colors (CERTAINTY) with uncertainty icons (UNCERTAINTY)",
            "Warning colors (WARNING) without WARNING text role",
            "Error states (ERROR) combined with other visual elements",
            "Multiple PRIMARY text roles in same view",
            "WARNING region that does not interrupt flow",
            "THINKING region without PRIMARY region anchor",
            "Navigation icons outside NAVIGATION region",
            "METADATA colors or icons in PRIMARY region",
            "USER_ACTION colors for system responses",
            "SYSTEM_RESPONSE colors for user actions",
            "Uncertainty (UNCERTAINTY) hidden in secondary positions",
            "Emotional coloring (no success/failure colors)",
            "Decorative icons without semantic meaning",
            "Accent colors for emphasis without epistemic cause",
            "Multiple competing focus points (violates single-focus)",
        ]


# Singleton instance for system-wide consistency
AESTHETICS = AestheticVocabulary()


# Export the canonical vocabulary
__all__ = [
    # Typography
    "TextRole",
    "TypographySystem",
    "TYPEOGRAPHY",
    "validate_text_role",
    "get_roles_for_content_type",
    # Color
    "SemanticColor",
    "PaletteSystem",
    "PALETTE",
    "validate_color_usage",
    "get_color_for_state",
    # Icons
    "SemanticIcon",
    "IconSystem",
    "ICONS",
    "validate_icon_usage",
    "icon_requires_context",
    "get_icon_for_state",
    # Layout
    "LayoutRegion",
    "LayoutConstraint",
    "LayoutSystem",
    "LAYOUT",
    "validate_layout_composition",
    "get_regions_for_context",
    # Unified vocabulary
    "AestheticVocabulary",
    "AESTHETICS",
]
