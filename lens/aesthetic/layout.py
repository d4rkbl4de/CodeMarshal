"""
lens.aesthetic.layout.py

Spatial truth rules for cognitive load control.
Layout is epistemology expressed as geometry.

CONSTRAINTS:
1. No responsive logic, grid systems, or pixel math
2. Only define spatial relationships and constraints
3. Enforce single-focus interface at all times
4. Prevent competing information streams
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import cast


class LayoutRegion(Enum):
    """Semantic regions of the interface, not pixel positions."""

    PRIMARY = auto()  # Single object of investigation
    SECONDARY = auto()  # Supporting information (must be passive)
    WARNING = auto()  # Uncertainty or limitation alerts
    NAVIGATION = auto()  # Investigation path and controls
    STATUS = auto()  # System operation state
    METADATA = auto()  # Ancillary information
    PROMPT = auto()  # User input area
    THINKING = auto()  # Human notes and reasoning (must be anchored)


class LayoutConstraint(Enum):
    """Constraints that define spatial truth relationships."""

    SINGLE_FOCUS = auto()  # Only one active region at a time
    MUST_INTERRUPT = auto()  # Must break flow (e.g., warnings)
    MUST_BE_PROXIMATE = auto()  # Must be near related content
    MUST_BE_ISOLATED = auto()  # Cannot appear with other regions
    PASSIVE_ONLY = auto()  # Cannot accept user input
    REQUIRES_ANCHOR = auto()  # Must be anchored to specific content
    CANNOT_COMPETE = auto()  # Must not draw attention from primary


@dataclass(frozen=True)
class RegionRule:
    """Immutable rule defining a region's spatial behavior."""

    region: LayoutRegion
    purpose: str
    constraints: set[LayoutConstraint]
    prohibited_with: set[LayoutRegion] = field(
        default_factory=lambda: cast(set[LayoutRegion], set())
    )
    required_with: set[LayoutRegion] = field(
        default_factory=lambda: cast(set[LayoutRegion], set())
    )
    max_concurrent: int | None = None

    def __post_init__(self) -> None:
        """Validate region rule consistency."""
        if (
            LayoutConstraint.SINGLE_FOCUS in self.constraints
            and self.max_concurrent != 1
        ):
            raise ValueError(
                f"Region {self.region} with SINGLE_FOCUS must have max_concurrent=1"
            )


class LayoutSystem:
    """
    Central authority for spatial truth preservation.

    Enforces:
    1. One primary focus at a time
    2. Warnings interrupt flow appropriately
    3. No competing attention streams
    4. Spatial relationships preserve truth relationships
    """

    def __init__(self) -> None:
        self._rules = self._build_rules()
        self._current_primary: LayoutRegion | None = None

    def _build_rules(self) -> dict[LayoutRegion, RegionRule]:
        """Construct the immutable layout rule system."""

        return {
            LayoutRegion.PRIMARY: RegionRule(
                region=LayoutRegion.PRIMARY,
                purpose="The single object of current investigation",
                constraints={
                    LayoutConstraint.CANNOT_COMPETE,
                },
                prohibited_with={
                    LayoutRegion.WARNING,  # Warnings obscure investigation
                    LayoutRegion.PROMPT,  # Input competes with observation
                },
                max_concurrent=1,
            ),
            LayoutRegion.SECONDARY: RegionRule(
                region=LayoutRegion.SECONDARY,
                purpose="Passive supporting information",
                constraints={
                    LayoutConstraint.PASSIVE_ONLY,
                    LayoutConstraint.REQUIRES_ANCHOR,
                    LayoutConstraint.MUST_BE_PROXIMATE,
                },
                required_with={LayoutRegion.PRIMARY},  # Requires primary to exist
                prohibited_with={
                    LayoutRegion.WARNING,
                    LayoutRegion.PROMPT,
                },
                max_concurrent=3,  # Limit supporting info to prevent overload
            ),
            LayoutRegion.WARNING: RegionRule(
                region=LayoutRegion.WARNING,
                purpose="Signal uncertainty, limitation, or caution",
                constraints={
                    LayoutConstraint.MUST_INTERRUPT,
                    LayoutConstraint.REQUIRES_ANCHOR,
                },
                prohibited_with={
                    LayoutRegion.PRIMARY,  # Cannot obscure investigation
                    LayoutRegion.PROMPT,  # Cannot interfere with input
                    LayoutRegion.SECONDARY,  # Warning should not be background
                },
                max_concurrent=None,  # All warnings must be shown
            ),
            LayoutRegion.NAVIGATION: RegionRule(
                region=LayoutRegion.NAVIGATION,
                purpose="Investigation path and movement controls",
                constraints={
                    LayoutConstraint.PASSIVE_ONLY,  # Navigation responds to user
                },
                prohibited_with=set(),
                max_concurrent=1,
            ),
            LayoutRegion.STATUS: RegionRule(
                region=LayoutRegion.STATUS,
                purpose="System operation state",
                constraints={
                    LayoutConstraint.PASSIVE_ONLY,
                },
                prohibited_with={
                    LayoutRegion.WARNING,
                    LayoutRegion.PROMPT,
                },
                max_concurrent=2,
            ),
            LayoutRegion.METADATA: RegionRule(
                region=LayoutRegion.METADATA,
                purpose="Ancillary information about observations",
                constraints={
                    LayoutConstraint.PASSIVE_ONLY,
                    LayoutConstraint.REQUIRES_ANCHOR,
                },
                prohibited_with={
                    LayoutRegion.PRIMARY,
                    LayoutRegion.WARNING,
                    LayoutRegion.PROMPT,
                },
                max_concurrent=None,
            ),
            LayoutRegion.PROMPT: RegionRule(
                region=LayoutRegion.PROMPT,
                purpose="User input and commands",
                constraints=set(),  # No special constraints
                prohibited_with={
                    LayoutRegion.PRIMARY,  # Input and observation compete
                    LayoutRegion.WARNING,  # Input should not have warnings
                },
                max_concurrent=1,
            ),
            LayoutRegion.THINKING: RegionRule(
                region=LayoutRegion.THINKING,
                purpose="Human notes and reasoning anchored to observations",
                constraints={
                    LayoutConstraint.REQUIRES_ANCHOR,
                    LayoutConstraint.MUST_BE_PROXIMATE,
                },
                required_with={
                    LayoutRegion.PRIMARY
                },  # Must have something to think about
                prohibited_with={
                    LayoutRegion.WARNING,  # Thinking should not mix with warnings
                    LayoutRegion.PROMPT,  # Input and thinking compete
                },
                max_concurrent=1,
            ),
        }

    def validate_regions(self, regions: set[LayoutRegion]) -> list[str]:
        """
        Validate that regions can appear together without truth distortion.

        Returns:
            List of violation messages, empty if valid.
        """
        violations: list[str] = []

        # Count occurrences
        region_counts: dict[LayoutRegion, int] = {}
        for region in regions:
            region_counts[region] = region_counts.get(region, 0) + 1

        # Check each rule
        for region, count in region_counts.items():
            rule = self._rules[region]

            # Check max concurrent
            if rule.max_concurrent is not None and count > rule.max_concurrent:
                violations.append(
                    f"Too many {region.name} regions ({count} > {rule.max_concurrent})"
                )

            # Check prohibited combinations
            for other_region in region_counts:
                if other_region in rule.prohibited_with:
                    violations.append(
                        f"{region.name} cannot appear with {other_region.name}"
                    )

            # Check required companions
            for required_region in rule.required_with:
                if required_region not in region_counts:
                    violations.append(
                        f"{region.name} requires {required_region.name} to be present"
                    )

        # Check for single focus violation
        primary_count = region_counts.get(LayoutRegion.PRIMARY, 0)
        if primary_count > 1:
            violations.append(f"Multiple primary regions ({primary_count})")

        # Check for constraint violations
        for region in regions:
            rule = self._rules[region]

            if LayoutConstraint.SINGLE_FOCUS in rule.constraints and len(regions) > 1:
                violations.append(
                    f"{region.name} requires single focus but other regions present"
                )

            if (
                LayoutConstraint.MUST_INTERRUPT in rule.constraints
                and self._has_persistent_regions(regions)
            ):
                violations.append(
                    f"{region.name} must interrupt but persistent regions present"
                )

            if (
                LayoutConstraint.MUST_BE_ISOLATED in rule.constraints
                and len(regions) > 1
            ):
                violations.append(
                    f"{region.name} must be isolated but other regions present"
                )

        return violations

    def _has_persistent_regions(self, regions: set[LayoutRegion]) -> bool:
        """Check if any regions are typically persistent (not interruptive)."""
        persistent_regions = {
            LayoutRegion.NAVIGATION,
            LayoutRegion.STATUS,
            LayoutRegion.METADATA,
        }
        return bool(regions.intersection(persistent_regions))

    def get_allowed_combinations(self) -> list[tuple[LayoutRegion, ...]]:
        """
        Get all pre-approved region combinations.

        These combinations preserve truth relationships and prevent cognitive overload.
        """
        allowed: list[tuple[LayoutRegion, ...]] = []

        # Single regions are always allowed
        for region in LayoutRegion:
            allowed.append((region,))

        # Pre-approved combinations that preserve truth
        approved_combinations: list[tuple[LayoutRegion, ...]] = [
            # Standard investigation view
            (LayoutRegion.PRIMARY, LayoutRegion.SECONDARY, LayoutRegion.NAVIGATION),
            # Investigation with thinking
            (LayoutRegion.PRIMARY, LayoutRegion.THINKING, LayoutRegion.NAVIGATION),
            # Prompt-only view
            (LayoutRegion.PROMPT, LayoutRegion.STATUS),
            # Warning interrupting investigation
            (LayoutRegion.WARNING, LayoutRegion.PRIMARY),
            # Investigation with metadata
            (LayoutRegion.PRIMARY, LayoutRegion.METADATA, LayoutRegion.NAVIGATION),
        ]

        for combo in approved_combinations:
            if not self.validate_regions(set(combo)):
                allowed.append(combo)

        return allowed

    def get_recommended_arrangement(
        self, regions: set[LayoutRegion]
    ) -> dict[LayoutRegion, str]:
        """
        Suggest spatial arrangement for regions based on truth relationships.

        Returns:
            Dictionary mapping region to suggested position (e.g., "top", "bottom-right")
            These are semantic positions, not pixel coordinates.
        """
        arrangement: dict[LayoutRegion, str] = {}

        # Core rules
        if LayoutRegion.PRIMARY in regions:
            arrangement[LayoutRegion.PRIMARY] = "center"

        if LayoutRegion.WARNING in regions:
            arrangement[LayoutRegion.WARNING] = "top"

        if LayoutRegion.NAVIGATION in regions:
            arrangement[LayoutRegion.NAVIGATION] = "bottom"

        if LayoutRegion.STATUS in regions:
            arrangement[LayoutRegion.STATUS] = "bottom-right"

        if LayoutRegion.PROMPT in regions:
            arrangement[LayoutRegion.PROMPT] = "bottom"

        # Secondary and thinking must be proximate to primary
        if LayoutRegion.SECONDARY in regions and LayoutRegion.PRIMARY in regions:
            arrangement[LayoutRegion.SECONDARY] = "right"

        if LayoutRegion.THINKING in regions and LayoutRegion.PRIMARY in regions:
            arrangement[LayoutRegion.THINKING] = "right"

        # Metadata is less important
        if LayoutRegion.METADATA in regions:
            arrangement[LayoutRegion.METADATA] = "bottom-left"

        # Ensure no two regions get same position
        self._resolve_position_conflicts(arrangement)

        return arrangement

    def _resolve_position_conflicts(self, arrangement: dict[LayoutRegion, str]) -> None:
        """Adjust positions to avoid conflicts."""
        position_counts: dict[str, int] = {}
        for position in arrangement.values():
            position_counts[position] = position_counts.get(position, 0) + 1

        # If conflicts, adjust secondary positions
        for position, count in position_counts.items():
            if count > 1:
                # Move things to nearby positions
                regions_at_position: list[LayoutRegion] = [
                    r for r, p in arrangement.items() if p == position
                ]

                # Prioritize primary stays where it is
                if LayoutRegion.PRIMARY in regions_at_position:
                    regions_to_move = [
                        r for r in regions_at_position if r != LayoutRegion.PRIMARY
                    ]
                else:
                    regions_to_move = cast(list[LayoutRegion], regions_at_position[1:])

                # Move to nearby positions
                nearby: dict[str, list[str]] = {
                    "center": ["right", "left"],
                    "right": ["left", "center"],
                    "left": ["right", "center"],
                    "top": ["bottom", "right"],
                    "bottom": ["top", "left"],
                    "bottom-right": ["bottom-left", "top-right"],
                    "bottom-left": ["bottom-right", "top-left"],
                    "top-right": ["top-left", "bottom-right"],
                    "top-left": ["top-right", "bottom-left"],
                }

                for region in regions_to_move:
                    current = arrangement[region]
                    for candidate in nearby.get(current, []):
                        if candidate not in arrangement.values():
                            arrangement[region] = candidate
                            break

    def get_constraint_explanations(self) -> dict[LayoutConstraint, str]:
        """Get human-readable explanations of each constraint."""
        return {
            LayoutConstraint.SINGLE_FOCUS: "Only one active region at a time to prevent cognitive overload",
            LayoutConstraint.MUST_INTERRUPT: "Must break normal flow to ensure visibility (e.g., warnings)",
            LayoutConstraint.MUST_BE_PROXIMATE: "Must be near related content to preserve truth relationships",
            LayoutConstraint.MUST_BE_ISOLATED: "Cannot appear with other regions to prevent competition",
            LayoutConstraint.PASSIVE_ONLY: "Cannot accept user input to maintain focus on primary",
            LayoutConstraint.REQUIRES_ANCHOR: "Must be anchored to specific content to prevent floating ideas",
            LayoutConstraint.CANNOT_COMPETE: "Must not draw attention away from primary content",
        }


# Singleton instance for system-wide consistency
LAYOUT = LayoutSystem()


def validate_layout_composition(regions: set[LayoutRegion]) -> list[str]:
    """
    Validate that a set of regions can appear together.

    Args:
        regions: The regions to validate

    Returns:
        List of violation messages, empty if valid
    """
    return LAYOUT.validate_regions(regions)


def get_regions_for_context(context_type: str) -> set[LayoutRegion]:
    """
    Map common investigation contexts to appropriate regions.

    This ensures consistent spatial arrangements across the system.
    """
    mapping: dict[str, set[LayoutRegion]] = {
        "initial_observation": {
            LayoutRegion.PRIMARY,
            LayoutRegion.NAVIGATION,
            LayoutRegion.STATUS,
        },
        "detailed_investigation": {
            LayoutRegion.PRIMARY,
            LayoutRegion.SECONDARY,
            LayoutRegion.NAVIGATION,
        },
        "warning_context": {
            LayoutRegion.WARNING,
            LayoutRegion.PRIMARY,
        },
        "user_input": {
            LayoutRegion.PROMPT,
            LayoutRegion.STATUS,
        },
        "thinking_session": {
            LayoutRegion.PRIMARY,
            LayoutRegion.THINKING,
            LayoutRegion.NAVIGATION,
        },
        "metadata_view": {
            LayoutRegion.PRIMARY,
            LayoutRegion.METADATA,
            LayoutRegion.NAVIGATION,
        },
    }

    return mapping.get(context_type, {LayoutRegion.PRIMARY, LayoutRegion.NAVIGATION})


# Export the public API
__all__ = [
    "LayoutRegion",
    "LayoutConstraint",
    "LayoutSystem",
    "LAYOUT",
    "validate_layout_composition",
    "get_regions_for_context",
]
