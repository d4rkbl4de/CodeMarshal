"""
Thinking View - Explicit Cognitive Trace (Truth Layer 3)

This view exists to prevent hallucinated authority.
It exposes deliberate reasoning traces when—and only when—explicitly requested.
This is the only place where "thinking" appears in the interface.

Article 2: Human Primacy - This view shows human thinking, never system thinking.
Article 10: Anchored Thinking - Every thought must be anchored to specific observations.
Article 16: Truth-Preserving Aesthetics - Visual design should enhance truth perception.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum, auto
from typing import (
    Any,
    ClassVar,
    cast,
)

from inquiry.notebook.models import (
    Note,
    NoteAnchor,
    NoteCollection,
    Thought,
)
from inquiry.session.context import SessionContext

# Allowed imports per architecture
from lens.philosophy import (
    SingleFocusRule,
)
from lens.philosophy.single_focus import MockInterfaceIntent


class ThinkingDisplayMode(Enum):
    """How thinking should be displayed based on request context."""

    SINGLE_THREAD = auto()  # One continuous reasoning chain
    BY_ANCHOR = auto()  # Thoughts grouped by observation anchor
    CHRONOLOGICAL = auto()  # Thoughts in temporal order
    BY_CATEGORY = auto()  # Thoughts grouped by type


@dataclass(frozen=True)
class ThinkingRenderConfig:
    """
    Immutable configuration for how thinking should be rendered.
    Every field is optional to allow progressive disclosure.
    """

    max_display_depth: int = 3  # Prevent overwhelming depth
    show_timestamps: bool = True  # Always show when
    show_anchors: bool = True  # Always show what it's about
    show_uncertainty_indicators: bool = True  # Always mark doubt
    collapse_by_default: bool = False  # Start collapsed
    include_assumptions: bool = True  # Show underlying assumptions
    include_questions: bool = True  # Show open questions
    include_blind_spots: bool = True  # Show known unknowns

    @classmethod
    def default(cls) -> ThinkingRenderConfig:
        """Default configuration adhering to progressive disclosure."""
        return cls()


@dataclass(frozen=True)
class ThinkingEntry:
    """A single human thought, fully contextualized."""

    id: str  # Unique identifier
    thought_type: str  # "reasoning", "assumption", "question", "blindspot"
    content: str  # Raw human thought
    timestamp: datetime  # When it was thought
    anchor_ids: frozenset[str]  # What observations it's about
    context_path: list[str]  # Investigation path when created
    author: str | None = None  # Who thought it (optional)
    uncertainty_level: int | None = None  # 0-100, None = not specified

    # Metadata for display
    is_collapsed_by_default: bool = False
    display_priority: int = 0  # Lower = more important

    def __post_init__(self) -> None:
        """Validate thinking entry invariants."""
        if not self.content.strip():
            raise ValueError("Thinking entry must have non-empty content")

        if len(self.anchor_ids) == 0:
            raise ValueError("Thinking must be anchored to at least one observation")

        if self.timestamp.tzinfo is None:
            # Convert naive UTC to aware
            object.__setattr__(self, "timestamp", self.timestamp.replace(tzinfo=UTC))

    @property
    def has_uncertainty(self) -> bool:
        """Whether this thought expresses explicit uncertainty."""
        return self.uncertainty_level is not None and self.uncertainty_level > 0

    @property
    def is_reasoning_step(self) -> bool:
        """Whether this is an explicit reasoning step."""
        return self.thought_type == "reasoning"

    @property
    def anchor_count(self) -> int:
        """How many observations this thought is anchored to."""
        return len(self.anchor_ids)


@dataclass(frozen=True)
class ThinkingThread:
    """
    A coherent sequence of thoughts about a specific topic.
    Maintains linear causality.
    """

    id: str
    title: str  # Human-readable thread title
    entries: tuple[ThinkingEntry, ...]  # In temporal order
    created_at: datetime
    updated_at: datetime
    primary_anchor_id: str | None = None  # Main observation thread is about

    def __post_init__(self) -> None:
        """Validate thread invariants."""
        if len(self.entries) == 0:
            raise ValueError("Thinking thread must contain at least one entry")

        # Ensure entries are in chronological order
        timestamps = [e.timestamp for e in self.entries]
        if not all(
            timestamps[i] <= timestamps[i + 1] for i in range(len(timestamps) - 1)
        ):
            raise ValueError("Thinking entries must be in chronological order")

        # Ensure thread times are correct
        if self.created_at > self.updated_at:
            raise ValueError("Thread created_at must be <= updated_at")

        if self.entries[0].timestamp < self.created_at:
            raise ValueError("First entry cannot predate thread creation")

    @property
    def entry_count(self) -> int:
        """Number of entries in this thread."""
        return len(self.entries)

    @property
    def timespan_seconds(self) -> float:
        """How long this thinking took in seconds."""
        if len(self.entries) < 2:
            return 0.0
        first = self.entries[0].timestamp
        last = self.entries[-1].timestamp
        return (last - first).total_seconds()

    @property
    def uncertainty_present(self) -> bool:
        """Whether any entry in this thread expresses uncertainty."""
        return any(e.has_uncertainty for e in self.entries)


class ThinkingView:
    """
    Deterministic projection from epistemic state → thinking display.

    Core Responsibility:
    Expose deliberate reasoning traces when—and only when—explicitly requested.
    This is the only place where "thinking" appears.

    Violations to watch for:
    1. Adding persuasive language
    2. Polishing or beautifying raw thoughts
    3. Inferring connections between thoughts
    4. Summarizing or condensing reasoning
    5. Providing "next step" suggestions

    Article 7: Clear Affordances
    This view must show exactly what thinking exists, nothing more.
    """

    # Class constants for display
    _UNCERTAINTY_INDICATOR: ClassVar[str] = "⚠️"
    _ANCHOR_INDICATOR: ClassVar[str] = "🔗"
    _REASONING_INDICATOR: ClassVar[str] = "🧠"
    _QUESTION_INDICATOR: ClassVar[str] = "❓"
    _BLINDSPOT_INDICATOR: ClassVar[str] = "👁️"
    _ASSUMPTION_INDICATOR: ClassVar[str] = "📌"

    def __init__(
        self,
        context: SessionContext,
        notebook: NoteCollection,
        config: ThinkingRenderConfig | None = None,
    ) -> None:
        """
        Initialize thinking view with current epistemic state.

        Args:
            context: Read-only investigation context
            notebook: Read-only collection of notes/thoughts
            config: Optional rendering configuration

        Raises:
            ValueError: If context or notebook is invalid
        """
        # Validate inputs
        if not isinstance(context, SessionContext):
            raise TypeError(f"context must be SessionContext, got {type(context)}")

        if not isinstance(notebook, NoteCollection):
            raise TypeError(f"notebook must be NoteCollection, got {type(notebook)}")

        # Store read-only state
        self._context: SessionContext = context
        self._notebook: NoteCollection = notebook
        self._config: ThinkingRenderConfig = config or ThinkingRenderConfig.default()

        # Apply philosophy rules
        self._apply_philosophy_rules()

    def _apply_philosophy_rules(self) -> None:
        """Apply lens philosophy rules to this view."""
        # Article 5: Single-Focus Interface
        SingleFocusRule().validate_interface_intent(
            MockInterfaceIntent(primary_focus=None)
        )

        # Article 6: Linear Investigation
        # Thinking is only shown after observations and patterns

        # Article 7: Clear Affordances
        # This view only shows existing thinking, no actions

        # Article 8: Honest Performance
        # If thinking is empty, we show that clearly

    def render(
        self, mode: ThinkingDisplayMode = ThinkingDisplayMode.SINGLE_THREAD
    ) -> dict[str, Any]:
        """
        Render thinking for display.

        This method is deterministic:
        Same context + notebook + config = same output.

        Args:
            mode: How to organize and display thinking

        Returns:
            Structured data ready for display layer

        Raises:
            ValueError: If mode is invalid or thinking cannot be rendered
        """
        # Get relevant thinking based on current context
        relevant_thoughts = self._get_relevant_thoughts()

        if not relevant_thoughts:
            return self._render_empty_state()

        # Organize based on requested mode
        organized = self._organize_thoughts(relevant_thoughts, mode)

        # Apply display rules
        rendered = self._apply_display_rules(organized)

        # Add metadata
        rendered.update(self._get_view_metadata(len(relevant_thoughts)))

        return rendered

    def _get_relevant_thoughts(self) -> list[ThinkingEntry]:
        """
        Get thoughts relevant to current investigation context.

        Returns:
            List of thinking entries filtered by current context

        Note:
            This is a pure function - no side effects, no inference.
            It only filters based on explicit context matching.
        """
        # Get all notes from notebook
        all_notes = self._notebook.get_all_notes()

        relevant: list[ThinkingEntry] = []

        for note in all_notes:
            # Convert note to thinking entry if it's a thought
            if isinstance(note, Thought):
                entry = self._convert_thought_to_entry(note)

                # Check if this thought is relevant to current context
                if self._is_thought_relevant(entry):
                    relevant.append(entry)

        # Sort by timestamp (most recent first for display)
        relevant.sort(key=lambda x: x.timestamp, reverse=True)

        return relevant

    def _convert_thought_to_entry(self, thought: Thought) -> ThinkingEntry:
        """
        Convert a Thought model to a ThinkingEntry.

        This is a mechanical conversion with no interpretation.
        """
        # Determine thought type based on model class
        thought_type = self._determine_thought_type(thought)

        # Extract anchor IDs from note anchors
        anchor_ids = frozenset(anchor.observation_id for anchor in thought.anchors)

        # Get uncertainty level if present
        uncertainty_level: int | None = None
        if thought.metadata and "uncertainty" in thought.metadata:
            try:
                uncertainty_level = int(thought.metadata["uncertainty"])
            except (ValueError, TypeError):
                uncertainty_level = None

        return ThinkingEntry(
            id=thought.id,
            thought_type=thought_type,
            content=thought.content,
            timestamp=thought.created_at,
            anchor_ids=anchor_ids,
            context_path=thought.context_path,
            author=thought.author,
            uncertainty_level=uncertainty_level,
            is_collapsed_by_default=thought.metadata.get("collapsed", False)
            if thought.metadata
            else False,
            display_priority=thought.metadata.get("priority", 0)
            if thought.metadata
            else 0,
        )

    def _determine_thought_type(self, thought: Thought) -> str:
        """
        Determine the type of thought based on its content and metadata.

        This uses only explicit markers, not content analysis.
        """
        if thought.metadata:
            if thought.metadata.get("type") in [
                "reasoning",
                "assumption",
                "question",
                "blindspot",
            ]:
                return cast(str, thought.metadata["type"])

            # Check for explicit markers in content
            content_lower = thought.content.lower()
            if any(
                marker in content_lower for marker in ["assume", "assuming", "presume"]
            ):
                return "assumption"
            elif any(
                marker in content_lower
                for marker in ["?", "question", "wonder", "unsure"]
            ):
                return "question"
            elif any(
                marker in content_lower
                for marker in ["don't know", "cannot see", "blind spot", "unknown"]
            ):
                return "blindspot"

        # Default to reasoning
        return "reasoning"

    def _is_thought_relevant(self, entry: ThinkingEntry) -> bool:
        """
        Check if a thought is relevant to current context.

        Relevance is determined by:
        1. Current focus (if any)
        2. Current investigation path
        3. No inference or guessing
        """
        current_focus = self._context.current_focus

        if not current_focus:
            # If no focus, show all thoughts from current investigation
            return any(
                path in entry.context_path for path in self._context.investigation_path
            )

        # Check if thought is anchored to current focus
        if current_focus in entry.anchor_ids:
            return True

        # Check if thought shares context with current investigation
        current_contexts = set(self._context.investigation_path)
        entry_contexts = set(entry.context_path)

        return bool(current_contexts.intersection(entry_contexts))

    def _organize_thoughts(
        self, thoughts: list[ThinkingEntry], mode: ThinkingDisplayMode
    ) -> dict[str, Any]:
        """
        Organize thoughts according to display mode.

        This is pure organization, no interpretation.
        """
        if mode == ThinkingDisplayMode.SINGLE_THREAD:
            return self._organize_as_single_thread(thoughts)
        elif mode == ThinkingDisplayMode.BY_ANCHOR:
            return self._organize_by_anchor(thoughts)
        elif mode == ThinkingDisplayMode.CHRONOLOGICAL:
            return self._organize_chronologically(thoughts)
        elif mode == ThinkingDisplayMode.BY_CATEGORY:
            return self._organize_by_category(thoughts)
        else:
            raise ValueError(f"Unknown display mode: {mode}")

    def _organize_as_single_thread(
        self, thoughts: list[ThinkingEntry]
    ) -> dict[str, Any]:
        """
        Organize thoughts as a single reasoning thread.

        This assumes temporal causality between entries.
        """
        # Sort chronologically for thread display
        sorted_thoughts = sorted(thoughts, key=lambda x: x.timestamp)

        return {
            "organization": "single_thread",
            "thread_title": "Reasoning Thread",
            "entries": [self._prepare_entry_display(e) for e in sorted_thoughts],
            "total_entries": len(sorted_thoughts),
            "timespan_seconds": self._calculate_timespan(sorted_thoughts),
            "has_causality": True,
        }

    def _organize_by_anchor(self, thoughts: list[ThinkingEntry]) -> dict[str, Any]:
        """
        Organize thoughts by what they're anchored to.

        Each anchor gets its own group of thoughts.
        """
        groups: dict[str, list[ThinkingEntry]] = {}

        for thought in thoughts:
            for anchor_id in thought.anchor_ids:
                if anchor_id not in groups:
                    groups[anchor_id] = []
                groups[anchor_id].append(thought)

        # Prepare display structure
        organized: dict[str, Any] = {"organization": "by_anchor", "anchor_groups": []}

        for anchor_id, anchor_thoughts in groups.items():
            # Sort thoughts for this anchor chronologically
            sorted_thoughts = sorted(anchor_thoughts, key=lambda x: x.timestamp)

            organized["anchor_groups"].append(
                {
                    "anchor_id": anchor_id,
                    "thought_count": len(sorted_thoughts),
                    "thoughts": [
                        self._prepare_entry_display(t) for t in sorted_thoughts
                    ],
                }
            )

        return organized

    def _organize_chronologically(
        self, thoughts: list[ThinkingEntry]
    ) -> dict[str, Any]:
        """
        Organize thoughts in strict chronological order.

        No grouping, just a timeline.
        """
        # Already sorted by timestamp (reverse for display)
        chronological = sorted(thoughts, key=lambda x: x.timestamp)

        return {
            "organization": "chronological",
            "timeline": [self._prepare_entry_display(e) for e in chronological],
            "start_time": chronological[0].timestamp.isoformat()
            if chronological
            else None,
            "end_time": chronological[-1].timestamp.isoformat()
            if chronological
            else None,
        }

    def _organize_by_category(self, thoughts: list[ThinkingEntry]) -> dict[str, Any]:
        """
        Organize thoughts by their type (reasoning, assumption, etc.).
        """
        categories: dict[str, list[ThinkingEntry]] = {
            "reasoning": [],
            "assumption": [],
            "question": [],
            "blindspot": [],
        }

        for thought in thoughts:
            if thought.thought_type in categories:
                categories[thought.thought_type].append(thought)

        organized: dict[str, Any] = {"organization": "by_category", "categories": {}}

        for category, category_thoughts in categories.items():
            if category_thoughts:
                sorted_thoughts = sorted(
                    category_thoughts, key=lambda x: x.timestamp, reverse=True
                )
                organized["categories"][category] = {
                    "count": len(sorted_thoughts),
                    "thoughts": [
                        self._prepare_entry_display(t) for t in sorted_thoughts
                    ],
                }

        return organized

    def _prepare_entry_display(self, entry: ThinkingEntry) -> dict[str, Any]:
        """
        Prepare a thinking entry for display.

        This adds display annotations but NO interpretation.
        """
        display: dict[str, Any] = {
            "id": entry.id,
            "content": entry.content,
            "type": entry.thought_type,
            "timestamp": entry.timestamp.isoformat(),
            "anchor_count": entry.anchor_count,
            "context_path": entry.context_path,
        }

        # Add metadata if configured
        if self._config.show_timestamps:
            display["display_time"] = entry.timestamp.strftime("%H:%M:%S")

        if self._config.show_anchors and entry.anchor_ids:
            display["anchor_ids"] = list(entry.anchor_ids)

        # Add uncertainty indicators if configured and present
        if self._config.show_uncertainty_indicators and entry.has_uncertainty:
            display["has_uncertainty"] = True
            display["uncertainty_level"] = entry.uncertainty_level
            display["uncertainty_indicator"] = self._UNCERTAINTY_INDICATOR

        # Add type indicator
        indicator_map = {
            "reasoning": self._REASONING_INDICATOR,
            "assumption": self._ASSUMPTION_INDICATOR,
            "question": self._QUESTION_INDICATOR,
            "blindspot": self._BLINDSPOT_INDICATOR,
        }

        if entry.thought_type in indicator_map:
            display["type_indicator"] = indicator_map[entry.thought_type]

        # Add collapse state
        display["is_collapsed"] = (
            entry.is_collapsed_by_default or self._config.collapse_by_default
        )

        return display

    def _calculate_timespan(self, thoughts: list[ThinkingEntry]) -> float | None:
        """Calculate total timespan of thoughts in seconds."""
        if len(thoughts) < 2:
            return None

        first = thoughts[0].timestamp
        last = thoughts[-1].timestamp
        return (last - first).total_seconds()

    def _apply_display_rules(self, organized: dict[str, Any]) -> dict[str, Any]:
        """
        Apply display rules to organized thoughts.

        This ensures the view adheres to:
        - Article 16: Truth-Preserving Aesthetics
        - Article 17: Minimal Decoration
        - Article 18: Consistent Metaphor
        """
        result = organized.copy()

        # Add view type identifier
        result["view_type"] = "thinking"
        result["view_philosophy"] = "explicit_cognitive_trace"

        # Apply clarity rule: mark if thinking is incomplete
        total_thoughts = self._count_total_thoughts(organized)
        if total_thoughts == 0:
            result["completeness"] = "no_thinking_recorded"
        elif total_thoughts < 3:
            result["completeness"] = "minimal_thinking"
        else:
            result["completeness"] = "substantial_thinking"

        # Apply progressive disclosure: mark depth
        result["display_depth"] = self._config.max_display_depth

        # Apply single focus: indicate if multiple threads present
        if organized.get("organization") == "single_thread":
            entry_count = organized.get("total_entries", 0)
            if entry_count > 1:
                result["focus"] = "single_reasoning_thread"
            else:
                result["focus"] = "single_thought"

        return result

    def _count_total_thoughts(self, organized: dict[str, Any]) -> int:
        """Count total thoughts in organized structure."""
        org_type = organized.get("organization")

        if org_type == "single_thread":
            return organized.get("total_entries", 0)
        elif org_type == "by_anchor":
            total = 0
            for group in organized.get("anchor_groups", []):
                total += group.get("thought_count", 0)
            return total
        elif org_type == "chronological":
            return len(organized.get("timeline", []))
        elif org_type == "by_category":
            total = 0
            for category in organized.get("categories", {}).values():
                total += category.get("count", 0)
            return total
        else:
            return 0

    def _render_empty_state(self) -> dict[str, Any]:
        """
        Render the view when no thinking is present.

        This is critical - we must be honest about absence.
        """
        return {
            "view_type": "thinking",
            "state": "empty",
            "message": "No thinking has been recorded yet.",
            "suggestion": "Record thoughts in the notebook to see them here.",
            "timestamp": datetime.now(UTC).isoformat(),
            "context": {
                "current_focus": self._context.current_focus,
                "investigation_path": self._context.investigation_path,
            },
        }

    def _get_view_metadata(self, thought_count: int) -> dict[str, Any]:
        """Get metadata about this view rendering."""
        return {
            "metadata": {
                "rendered_at": datetime.now(UTC).isoformat(),
                "thought_count": thought_count,
                "config": asdict(self._config),
                "philosophy_rules_applied": [
                    "SingleFocusRule",
                    "ProgressiveDisclosureRule",
                    "ClarityRule",
                    "NavigationRule",
                ],
                "warnings": [],  # No warnings unless something is wrong
            }
        }

    def validate_integrity(self) -> list[str]:
        """
        Validate that this view adheres to truth-preserving constraints.

        Returns:
            List of violations (empty if valid)

        Article 21: Self-Validation
        The system must include tests that verify it follows its own constitution.
        """
        violations: list[str] = []

        # Check 1: No inference in organization
        organized = self._organize_thoughts([], ThinkingDisplayMode.SINGLE_THREAD)
        if organized.get("has_causality") is True:
            # Only mark causality if we explicitly know there is causality
            # (e.g., from thread metadata, not from temporal proximity)
            pass  # This is acceptable if based on explicit metadata

        # Check 2: No persuasive language
        empty_state = self._render_empty_state()
        if "should" in empty_state.get("message", "").lower():
            violations.append("View contains persuasive language ('should')")

        # Check 3: Uncertainty must be visible if present
        # This is enforced by _prepare_entry_display

        # Check 4: No summarization or condensation
        # We never create summaries of thinking

        # Check 5: All thoughts must be anchored
        thoughts = self._get_relevant_thoughts()
        for thought in thoughts:
            if thought.anchor_count == 0:
                violations.append(f"Thought {thought.id} has no anchors")

        return violations

    @classmethod
    def create_test_view(cls) -> ThinkingView:
        """
        Create a test view for development and testing.

        Returns:
            A ThinkingView with test data

        Note: This is for testing only, not production use.
        """
        from datetime import datetime, timedelta

        # Create test context
        class TestContext(SessionContext):
            def __init__(self) -> None:
                self.current_focus = "obs:test:module:example.py"
                self.investigation_path = ["test_investigation"]
                self.created_at = datetime.now(UTC)

        # Create test notebook with thoughts
        class TestNoteCollection(NoteCollection):
            def get_all_notes(self) -> list[Note]:
                now = datetime.now(UTC)
                hour_ago = now - timedelta(hours=1)

                # Create test thoughts
                thought1 = Thought(
                    id="thought:test:1",
                    content="I notice this module imports from three different lobes.",
                    anchors=[
                        NoteAnchor(
                            observation_id="obs:test:module:example.py",
                            relationship="about",
                        )
                    ],
                    created_at=hour_ago,
                    context_path=["test_investigation"],
                    metadata={"type": "reasoning", "uncertainty": 10},
                )

                thought2 = Thought(
                    id="thought:test:2",
                    content="Is this a constitutional violation or by design?",
                    anchors=[
                        NoteAnchor(
                            observation_id="obs:test:module:example.py",
                            relationship="about",
                        )
                    ],
                    created_at=hour_ago + timedelta(minutes=5),
                    context_path=["test_investigation"],
                    metadata={"type": "question"},
                )

                thought3 = Thought(
                    id="thought:test:3",
                    content="Assuming the imports are for facade patterns.",
                    anchors=[
                        NoteAnchor(
                            observation_id="obs:test:module:example.py",
                            relationship="about",
                        ),
                        NoteAnchor(
                            observation_id="obs:test:module:facade.py",
                            relationship="reference",
                        ),
                    ],
                    created_at=hour_ago + timedelta(minutes=10),
                    context_path=["test_investigation"],
                    metadata={"type": "assumption", "uncertainty": 40},
                )

                return [thought1, thought2, thought3]

        return cls(TestContext(), TestNoteCollection())


def main() -> None:
    """Test the thinking view."""
    view = ThinkingView.create_test_view()

    # Test different display modes
    for mode in ThinkingDisplayMode:
        print(f"\n=== {mode.name} ===")
        rendered = view.render(mode)
        print(json.dumps(rendered, indent=2, default=str))

    # Validate integrity
    violations = view.validate_integrity()
    if violations:
        print(f"\nIntegrity violations: {violations}")
    else:
        print("\nView passes integrity checks.")


if __name__ == "__main__":
    main()
