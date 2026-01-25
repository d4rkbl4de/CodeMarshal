"""
Help View - Orientation, Not Rescue (Truth Layer 3)

Core Responsibility: Explain how to use the system, not what to think.

Article 7: Clear Affordances - Explain what can be done
Article 8: Honest Performance - Explain limitations
Article 16: Truth-Preserving Aesthetics - Clear explanations
"""

from __future__ import annotations

import json
import textwrap
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import Enum, auto
from typing import (
    Any,
    ClassVar,
)

from inquiry.session.context import SessionContext

# Allowed imports per architecture
from lens.philosophy import (
    SingleFocusRule,
)
from lens.philosophy.single_focus import MockInterfaceIntent

# NOT ALLOWED: patterns.*, bridge.commands.*


class HelpCategory(Enum):
    """Categories of help content."""

    SYSTEM_PHILOSOPHY = auto()
    VIEWS_AND_PURPOSE = auto()
    INVESTIGATION_FLOW = auto()
    CONSTITUTIONAL_RULES = auto()
    TECHNICAL_DETAILS = auto()
    TROUBLESHOOTING = auto()

    @property
    def display_name(self) -> str:
        """Human-readable category name."""
        return {
            HelpCategory.SYSTEM_PHILOSOPHY: "System Philosophy",
            HelpCategory.VIEWS_AND_PURPOSE: "Views & Purpose",
            HelpCategory.INVESTIGATION_FLOW: "Investigation Flow",
            HelpCategory.CONSTITUTIONAL_RULES: "Constitutional Rules",
            HelpCategory.TECHNICAL_DETAILS: "Technical Details",
            HelpCategory.TROUBLESHOOTING: "Troubleshooting",
        }[self]

    @property
    def icon(self) -> str:
        """Icon for category."""
        return {
            HelpCategory.SYSTEM_PHILOSOPHY: "",
            HelpCategory.VIEWS_AND_PURPOSE: "",
            HelpCategory.INVESTIGATION_FLOW: "",
            HelpCategory.CONSTITUTIONAL_RULES: "",
            HelpCategory.TECHNICAL_DETAILS: "",
            HelpCategory.TROUBLESHOOTING: "",
        }[self]


class HelpEntryType(Enum):
    """Types of help entries."""

    CONCEPT = auto()
    HOW_TO = auto()
    CONSTRAINT = auto()
    WARNING = auto()
    EXAMPLE = auto()

    @property
    def display_style(self) -> str:
        """CSS style for display."""
        return {
            HelpEntryType.CONCEPT: "concept",
            HelpEntryType.HOW_TO: "how-to",
            HelpEntryType.CONSTRAINT: "constraint",
            HelpEntryType.WARNING: "warning",
            HelpEntryType.EXAMPLE: "example",
        }[self]

    @property
    def prefix(self) -> str:
        """Text prefix for entry type."""
        return {
            HelpEntryType.CONCEPT: "Concept: ",
            HelpEntryType.HOW_TO: "How to: ",
            HelpEntryType.CONSTRAINT: "Constraint: ",
            HelpEntryType.WARNING: "Warning: ",
            HelpEntryType.EXAMPLE: "Example: ",
        }[self]


@dataclass(frozen=True)
class HelpEntry:
    """A single help entry."""

    id: str
    title: str
    content: str
    category: HelpCategory
    entry_type: HelpEntryType
    related_entries: frozenset[str] = field(default_factory=frozenset)
    requires_context: bool = False  # Whether this help needs current context

    def __post_init__(self) -> None:
        """Validate help entry invariants."""
        if not self.title.strip():
            raise ValueError("Help entry must have a title")

        if not self.content.strip():
            raise ValueError("Help entry must have content")

        if len(self.content.strip()) < 10:
            raise ValueError("Help content too short")

    @property
    def display_title(self) -> str:
        """Title with type prefix if needed."""
        if self.entry_type in (HelpEntryType.CONCEPT, HelpEntryType.EXAMPLE):
            return self.title
        return self.entry_type.prefix + self.title

    def contextualize(self, context: SessionContext) -> str:
        """Add context-specific information if needed."""
        if not self.requires_context:
            return self.content

        # Add context-aware explanations
        contextual_additions = []

        if "current_focus" in self.content.lower():
            if context.current_focus:
                contextual_additions.append(
                    f"\n\nYour current focus is: {context.current_focus}"
                )
            else:
                contextual_additions.append(
                    "\n\nYou don't have a current focus. Use 'observe' to focus on something."
                )

        if "investigation_path" in self.content.lower():
            if context.investigation_path:
                contextual_additions.append(
                    f"\n\nYour investigation path: {' → '.join(context.investigation_path)}"
                )

        return self.content + "".join(contextual_additions)


@dataclass(frozen=True)
class HelpSection:
    """A section of help content."""

    category: HelpCategory
    entries: tuple[HelpEntry, ...]
    display_order: int = 0

    def __post_init__(self) -> None:
        """Validate section invariants."""
        if len(self.entries) == 0:
            raise ValueError("Help section must contain at least one entry")

        # All entries must belong to the section's category
        for entry in self.entries:
            if entry.category != self.category:
                raise ValueError(f"Entry {entry.id} has wrong category")

    @property
    def entry_count(self) -> int:
        """Number of entries in this section."""
        return len(self.entries)


class HelpDatabase:
    """
    Immutable database of help content.

    Contains all help entries organized by category.
    This is a static database - no runtime generation.
    """

    # System Philosophy entries
    _PHILOSOPHY_ENTRIES = (
        HelpEntry(
            id="philosophy:truth-preservation",
            title="Truth Preservation",
            content=textwrap.dedent("""
                The system records only what is textually present in source code.
                No inference, no guessing, no interpretation.

                When truth is uncertain, it shows uncertainty clearly (⚠️).
                When truth is unknown, it says "I cannot see this."

                This ensures that what you see is what actually exists in the code.
            """),
            category=HelpCategory.SYSTEM_PHILOSOPHY,
            entry_type=HelpEntryType.CONCEPT,
        ),
        HelpEntry(
            id="philosophy:human-primacy",
            title="Human Primacy",
            content=textwrap.dedent("""
                Humans ask questions, see patterns, and think thoughts.
                The system provides observations, detects anomalies, and preserves thinking.

                The system never:
                • Draws conclusions for you
                • Makes decisions for you
                • Tells you what is important

                You are the investigator. The system is your notebook.
            """),
            category=HelpCategory.SYSTEM_PHILOSOPHY,
            entry_type=HelpEntryType.CONCEPT,
        ),
        HelpEntry(
            id="philosophy:progressive-disclosure",
            title="Progressive Disclosure",
            content=textwrap.dedent("""
                The system starts with simple observations and reveals complexity only when requested.

                At each step:
                1. It shows you exactly what you asked for
                2. It never overwhelms with information
                3. It clearly indicates what more can be learned

                This follows natural human curiosity without cognitive overload.
            """),
            category=HelpCategory.SYSTEM_PHILOSOPHY,
            entry_type=HelpEntryType.CONCEPT,
        ),
    )

    # Views and Purpose entries
    _VIEWS_ENTRIES = (
        HelpEntry(
            id="views:overview",
            title="Overview View",
            content=textwrap.dedent("""
                The overview shows situational awareness without analysis.

                It tells you:
                • What you're currently examining
                • What stage your investigation is at
                • What information exists (counts, presence)
                • What is explicitly unknown

                It never draws conclusions or makes recommendations.

                Think of it as a map legend, not a guided tour.
            """),
            category=HelpCategory.VIEWS_AND_PURPOSE,
            entry_type=HelpEntryType.CONCEPT,
        ),
        HelpEntry(
            id="views:examination",
            title="Examination View",
            content=textwrap.dedent("""
                The examination view presents raw observations in structured form.

                It shows:
                • Observations verbatim, as recorded
                • Source metadata (file, line, timestamp)
                • Grouping by category (not by pattern)

                It never:
                • Summarizes or clusters observations
                • Detects anomalies
                • Ranks by importance

                This view is deliberately tedious. That's a feature.
            """),
            category=HelpCategory.VIEWS_AND_PURPOSE,
            entry_type=HelpEntryType.CONCEPT,
        ),
        HelpEntry(
            id="views:patterns",
            title="Patterns View",
            content=textwrap.dedent("""
                The patterns view shows pattern outputs that were produced elsewhere.

                Important: This view NEVER computes patterns. It only displays results.

                For each pattern, you see:
                • Pattern name and type
                • Confidence level (with uncertainty)
                • Supporting references
                • Known limitations

                It never explains patterns or suggests actions based on them.
            """),
            category=HelpCategory.VIEWS_AND_PURPOSE,
            entry_type=HelpEntryType.WARNING,
            related_entries=frozenset(["patterns:danger"]),
        ),
        HelpEntry(
            id="views:thinking",
            title="Thinking View",
            content=textwrap.dedent("""
                The thinking view exposes deliberate reasoning traces.

                It shows:
                • Your recorded thoughts and notes
                • Assumptions you've documented
                • Open questions
                • Known blind spots

                All thinking must be anchored to specific observations.
                No floating opinions, no unattached ideas.

                This is a scratchpad made visible, not a polished narrative.
            """),
            category=HelpCategory.VIEWS_AND_PURPOSE,
            entry_type=HelpEntryType.CONCEPT,
        ),
    )

    # Investigation Flow entries
    _FLOW_ENTRIES = (
        HelpEntry(
            id="flow:linear-investigation",
            title="Linear Investigation",
            content=textwrap.dedent("""
                The system follows natural human curiosity:

                1. Orientation: What exists?
                2. Observation: What do I see?
                3. Patterns: What patterns emerge?
                4. Thinking: What do I think?
                5. Synthesis: What have I learned?

                You cannot jump randomly between steps.
                Each step builds on the previous one.

                This prevents confusion and maintains focus.
            """),
            category=HelpCategory.INVESTIGATION_FLOW,
            entry_type=HelpEntryType.HOW_TO,
        ),
        HelpEntry(
            id="flow:single-focus",
            title="Single Focus",
            content=textwrap.dedent("""
                Only one primary content area is visible at a time.
                No competing information streams.

                The interface feels like looking through a magnifying glass,
                not at a dashboard.

                This reduces cognitive load and prevents distraction.
            """),
            category=HelpCategory.INVESTIGATION_FLOW,
            entry_type=HelpEntryType.CONCEPT,
        ),
        HelpEntry(
            id="flow:clear-affordances",
            title="Clear Affordances",
            content=textwrap.dedent("""
                At every moment, the system shows what can be done next.

                You'll see:
                • Obvious, consistent actions
                • No hidden capabilities
                • No Easter eggs

                If something can be done, it's clearly indicated.
                If it can't be done, the reason is explained.
            """),
            category=HelpCategory.INVESTIGATION_FLOW,
            entry_type=HelpEntryType.CONCEPT,
            requires_context=True,
        ),
    )

    # Constitutional Rules entries
    _RULES_ENTRIES = (
        HelpEntry(
            id="rules:observation-purity",
            title="Observation Purity",
            content=textwrap.dedent("""
                Observations record only what is textually present in source code.

                The system never:
                • Infers meaning
                • Guesses intent
                • Interprets semantics

                Observations are immutable once recorded.
                New observations create new versions.
            """),
            category=HelpCategory.CONSTITUTIONAL_RULES,
            entry_type=HelpEntryType.CONSTRAINT,
        ),
        HelpEntry(
            id="rules:anchored-thinking",
            title="Anchored Thinking",
            content=textwrap.dedent("""
                All human thoughts must be anchored to specific observations.

                You cannot:
                • Create floating opinions
                • Make unattached claims
                • State conclusions without evidence

                This creates traceable reasoning chains from observation to understanding.
            """),
            category=HelpCategory.CONSTITUTIONAL_RULES,
            entry_type=HelpEntryType.CONSTRAINT,
        ),
        HelpEntry(
            id="rules:declared-limitations",
            title="Declared Limitations",
            content=textwrap.dedent("""
                Every observation method declares what it cannot see.
                Every pattern detector declares its uncertainty.

                These declarations are first-class system outputs.
                They appear as "Known Unknowns" in the overview.

                Ignoring limitations leads to false confidence.
            """),
            category=HelpCategory.CONSTITUTIONAL_RULES,
            entry_type=HelpEntryType.CONSTRAINT,
        ),
        HelpEntry(
            id="rules:local-operation",
            title="Local Operation",
            content=textwrap.dedent("""
                All analysis works without network connectivity.

                The system:
                • Never requires cloud services
                • Never calls external APIs for core functionality
                • Stores everything locally

                Truth should not depend on external services.
            """),
            category=HelpCategory.CONSTITUTIONAL_RULES,
            entry_type=HelpEntryType.CONSTRAINT,
        ),
    )

    # Technical Details entries
    _TECHNICAL_ENTRIES = (
        HelpEntry(
            id="technical:three-layer-model",
            title="Three-Layer Truth Model",
            content=textwrap.dedent("""
                The system separates:

                1. Observations: What exists (immutable facts)
                2. Inquiry: What questions we ask and patterns we see
                3. Lens: How we look at truth (interface constraints)

                This prevents mixing what is with what we think about it.
            """),
            category=HelpCategory.TECHNICAL_DETAILS,
            entry_type=HelpEntryType.CONCEPT,
        ),
        HelpEntry(
            id="technical:deterministic-operation",
            title="Deterministic Operation",
            content=textwrap.dedent("""
                Same input must produce same output, regardless of when or where it runs.

                The system never:
                • Uses randomness in analysis
                • Changes behavior based on time
                • Has hidden state that affects output

                This ensures reproducibility and auditability.
            """),
            category=HelpCategory.TECHNICAL_DETAILS,
            entry_type=HelpEntryType.CONSTRAINT,
        ),
        HelpEntry(
            id="technical:graceful-degradation",
            title="Graceful Degradation",
            content=textwrap.dedent("""
                When parts fail, the system preserves what works.

                It shows:
                • Available observations even when some cannot be collected
                • Simple, honest explanations of failures
                • Options for continuing investigation

                Truth should survive partial system failure.
            """),
            category=HelpCategory.TECHNICAL_DETAILS,
            entry_type=HelpEntryType.CONCEPT,
        ),
    )

    # Troubleshooting entries
    _TROUBLESHOOTING_ENTRIES = (
        HelpEntry(
            id="troubleshooting:no-patterns",
            title="No Patterns Detected",
            content=textwrap.dedent("""
                If no patterns appear:

                1. Check if you have enough observations (at least 10 recommended)
                2. Ensure pattern detection has been run
                3. Check filter settings (low-confidence patterns might be hidden)
                4. Verify that observations are of the right type for pattern detection

                Pattern detection requires substantial observation data.
            """),
            category=HelpCategory.TROUBLESHOOTING,
            entry_type=HelpEntryType.HOW_TO,
        ),
        HelpEntry(
            id="troubleshooting:empty-views",
            title="Empty Views",
            content=textwrap.dedent("""
                If a view appears empty:

                1. Check the current focus (some views require a specific focus)
                2. Verify that relevant data has been collected
                3. Look for filter indicators
                4. Check if you're at the right investigation stage

                Empty views often indicate missing prerequisites.
            """),
            category=HelpCategory.TROUBLESHOOTING,
            entry_type=HelpEntryType.HOW_TO,
            requires_context=True,
        ),
        HelpEntry(
            id="troubleshooting:performance",
            title="Slow Performance",
            content=textwrap.dedent("""
                If the system seems slow:

                1. Large codebases take time to observe (this is honest)
                2. Complex pattern detection is computationally intensive
                3. The system shows progress indicators for long operations
                4. Consider focusing on smaller sections of the codebase

                The system never pretends to be faster than it is.
            """),
            category=HelpCategory.TROUBLESHOOTING,
            entry_type=HelpEntryType.HOW_TO,
        ),
    )

    # Special warning entries
    _WARNING_ENTRIES = (
        HelpEntry(
            id="patterns:danger",
            title="Patterns Are Dangerous",
            content=textwrap.dedent("""
                WARNING: The patterns view is the most dangerous part of the system.

                Patterns can:
                • Create false confidence
                • Suggest non-existent relationships
                • Hide important details in aggregates

                Always:
                • Check the confidence level
                • Review supporting references
                • Note declared limitations
                • Remember that patterns are signals, not truths
            """),
            category=HelpCategory.TROUBLESHOOTING,
            entry_type=HelpEntryType.WARNING,
        ),
    )

    @classmethod
    def get_sections(cls) -> tuple[HelpSection, ...]:
        """Get all help sections in display order."""
        return (
            HelpSection(
                category=HelpCategory.SYSTEM_PHILOSOPHY,
                entries=cls._PHILOSOPHY_ENTRIES,
                display_order=1,
            ),
            HelpSection(
                category=HelpCategory.VIEWS_AND_PURPOSE,
                entries=cls._VIEWS_ENTRIES,
                display_order=2,
            ),
            HelpSection(
                category=HelpCategory.INVESTIGATION_FLOW,
                entries=cls._FLOW_ENTRIES,
                display_order=3,
            ),
            HelpSection(
                category=HelpCategory.CONSTITUTIONAL_RULES,
                entries=cls._RULES_ENTRIES,
                display_order=4,
            ),
            HelpSection(
                category=HelpCategory.TECHNICAL_DETAILS,
                entries=cls._TECHNICAL_ENTRIES,
                display_order=5,
            ),
            HelpSection(
                category=HelpCategory.TROUBLESHOOTING,
                entries=cls._TROUBLESHOOTING_ENTRIES + cls._WARNING_ENTRIES,
                display_order=6,
            ),
        )

    @classmethod
    def get_entry(cls, entry_id: str) -> HelpEntry | None:
        """Get a specific help entry by ID."""
        all_entries = []
        for section in cls.get_sections():
            all_entries.extend(section.entries)

        for entry in all_entries:
            if entry.id == entry_id:
                return entry

        return None

    @classmethod
    def get_entries_by_category(cls, category: HelpCategory) -> tuple[HelpEntry, ...]:
        """Get all entries for a category."""
        for section in cls.get_sections():
            if section.category == category:
                return section.entries
        return ()


@dataclass(frozen=True)
class HelpRenderConfig:
    """
    Configuration for help rendering.

    Article 7: Clear Affordances - Help must be clear
    Article 16: Truth-Preserving Aesthetics - Help should be readable
    """

    show_category_descriptions: bool = True
    group_by_category: bool = True
    include_related_entries: bool = True
    show_context_hints: bool = True
    max_entries_per_category: int = 10

    @classmethod
    def default(cls) -> HelpRenderConfig:
        """Default configuration adhering to constitutional rules."""
        return cls()


class HelpView:
    """
    Deterministic projection from help database → instructional display.

    Core Responsibility:
    Explain how to use the system, not what to think.

    What this view MAY SHOW:
    1. What each view does
    2. What the rules are
    3. Why constraints exist
    4. How to proceed correctly

    What this view MUST NOT SHOW:
    1. No domain advice
    2. No shortcuts
    3. No "recommended next steps"

    Mental Model: An instruction manual, not a hint system.
    """

    # Display constants
    _SEARCH_ICON: ClassVar[str] = ""
    _BACK_ICON: ClassVar[str] = ""
    _HOME_ICON: ClassVar[str] = ""

    def __init__(
        self,
        context: SessionContext,
        current_entry_id: str | None = None,
        config: HelpRenderConfig | None = None,
    ) -> None:
        """
        Initialize help view.

        Args:
            context: Read-only investigation context
            current_entry_id: ID of specific help entry to show
            config: Optional rendering configuration

        Raises:
            ValueError: If current_entry_id doesn't exist
        """
        # Validate inputs
        if not isinstance(context, SessionContext):
            raise TypeError(f"context must be SessionContext, got {type(context)}")

        # Validate entry ID if provided
        if current_entry_id and not HelpDatabase.get_entry(current_entry_id):
            raise ValueError(f"Help entry not found: {current_entry_id}")

        # Store read-only state
        self._context: SessionContext = context
        self._current_entry_id: str | None = current_entry_id
        self._config: HelpRenderConfig = config or HelpRenderConfig.default()

        # Apply philosophy rules
        self._apply_philosophy_rules()

    def _apply_philosophy_rules(self) -> None:
        """Apply lens philosophy rules to this view."""
        # Article 5: Single-Focus Interface
        SingleFocusRule().validate_interface_intent(
            MockInterfaceIntent(primary_focus=None)
        )

        # Article 6: Linear Investigation
        # Help is available at any time, not part of linear flow

        # Article 7: Clear Affordances
        # Help itself must be clear and actionable

        # Article 8: Honest Performance
        # Help must explain limitations honestly

    def render(self) -> dict[str, Any]:
        """
        Render help for display.

        Returns:
            Structured data ready for display layer

        Article 7: Must show clear instructions
        Article 16: Must be readable and well-organized
        """
        if self._current_entry_id:
            return self._render_single_entry()
        else:
            return self._render_overview()

    def _render_overview(self) -> dict[str, Any]:
        """Render help overview (all categories)."""
        sections = HelpDatabase.get_sections()

        # Prepare category overviews
        category_overviews = []

        for section in sections:
            # Limit entries per category if configured
            entries = section.entries
            if len(entries) > self._config.max_entries_per_category:
                entries = entries[: self._config.max_entries_per_category]

            category_overviews.append(
                {
                    "category": section.category.name,
                    "category_display": section.category.display_name,
                    "icon": section.category.icon,
                    "entry_count": section.entry_count,
                    "entries": [
                        {
                            "id": entry.id,
                            "title": entry.display_title,
                            "type": entry.entry_type.name,
                            "type_style": entry.entry_type.display_style,
                        }
                        for entry in entries
                    ],
                }
            )

        # Sort by display order
        category_overviews.sort(
            key=lambda c: next(
                s.display_order for s in sections if s.category.name == c["category"]
            )
        )

        return {
            "view_type": "help",
            "view_mode": "overview",
            "title": "CodeMarshal Help",
            "icon": "❓",
            "content": {
                "categories": category_overviews,
                "total_entries": sum(len(s.entries) for s in sections),
                "welcome_message": self._get_welcome_message(),
            },
            "navigation": {
                "can_drill_down": True,
                "can_search": True,
                "can_go_back": False,  # We're at top level
            },
            "is_primary": True,
        }

    def _render_single_entry(self) -> dict[str, Any]:
        """Render a single help entry."""
        if not self._current_entry_id:
            raise ValueError("Cannot render single entry without entry ID")

        entry = HelpDatabase.get_entry(self._current_entry_id)
        if not entry:
            raise ValueError(f"Help entry not found: {self._current_entry_id}")

        # Get contextualized content
        content = entry.contextualize(self._context)

        # Get related entries if configured
        related_entries = []
        if self._config.include_related_entries and entry.related_entries:
            for related_id in entry.related_entries:
                related_entry = HelpDatabase.get_entry(related_id)
                if related_entry:
                    related_entries.append(
                        {
                            "id": related_entry.id,
                            "title": related_entry.display_title,
                            "category": related_entry.category.display_name,
                        }
                    )

        return {
            "view_type": "help",
            "view_mode": "single_entry",
            "title": entry.display_title,
            "icon": entry.category.icon,
            "content": {
                "id": entry.id,
                "full_content": content,
                "category": entry.category.display_name,
                "entry_type": entry.entry_type.name,
                "type_style": entry.entry_type.display_style,
                "is_warning": entry.entry_type == HelpEntryType.WARNING,
                "requires_context": entry.requires_context,
                "related_entries": related_entries,
            },
            "navigation": {
                "can_drill_down": bool(related_entries),
                "can_search": True,
                "can_go_back": True,
                "back_target": "help:overview",
            },
            "context_hints": self._get_context_hints(entry)
            if self._config.show_context_hints
            else None,
            "is_primary": True,
        }

    def _get_welcome_message(self) -> str:
        """Get welcome message for help overview."""
        return textwrap.dedent("""
            Welcome to CodeMarshal help.

            This is a truth-preserving investigation environment.
            It helps you understand code without lying, guessing, or overwhelming.

            Remember:
            • You are the investigator
            • The system is your notebook
            • Truth comes from observation, not inference

            Select a category to learn more.
        """).strip()

    def _get_context_hints(self, entry: HelpEntry) -> list[str] | None:
        """Get context-specific hints for a help entry."""
        hints = []

        # Add context-based hints
        if entry.requires_context:
            if not self._context.current_focus and "focus" in entry.content.lower():
                hints.append(
                    "You don't have a current focus. Set one to use this feature."
                )

            if (
                not self._context.investigation_path
                and "investigation" in entry.content.lower()
            ):
                hints.append("Start an investigation to use this feature.")

        # Add entry-type specific hints
        if entry.entry_type == HelpEntryType.WARNING:
            hints.append(
                "This is a warning about potential misuse or misunderstanding."
            )

        if entry.entry_type == HelpEntryType.CONSTRAINT:
            hints.append("This is a system constraint that cannot be violated.")

        if entry.category == HelpCategory.TROUBLESHOOTING:
            hints.append(
                "If problem persists, check the constitutional rules for deeper issues."
            )

        return hints if hints else None

    def search(self, query: str) -> dict[str, Any]:
        """
        Search help entries.

        This is a pure function - no external calls, deterministic.

        Args:
            query: Search query string

        Returns:
            Search results structure

        Note: This is simple string matching. For production, you might want
        more sophisticated search, but that would require external dependencies.
        """
        query_lower = query.lower().strip()

        if not query_lower:
            return {"results": [], "count": 0, "query": query}

        # Collect all entries
        all_entries = []
        for section in HelpDatabase.get_sections():
            all_entries.extend(section.entries)

        # Simple keyword matching
        results = []
        for entry in all_entries:
            # Check title and content
            title_match = query_lower in entry.title.lower()
            content_match = query_lower in entry.content.lower()

            # Check category
            category_match = query_lower in entry.category.display_name.lower()

            if title_match or content_match or category_match:
                # Calculate simple relevance score
                relevance = 0
                if title_match:
                    relevance += 3
                if content_match:
                    relevance += 1
                if category_match:
                    relevance += 2

                results.append(
                    {
                        "id": entry.id,
                        "title": entry.display_title,
                        "category": entry.category.display_name,
                        "icon": entry.category.icon,
                        "relevance": relevance,
                        "excerpt": self._get_excerpt(entry.content, query_lower),
                    }
                )

        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)

        return {
            "view_type": "help",
            "view_mode": "search_results",
            "title": f"Search: {query}",
            "icon": self._SEARCH_ICON,
            "content": {
                "results": results[:10],  # Limit results
                "count": len(results),
                "query": query,
            },
            "navigation": {
                "can_drill_down": True,
                "can_search": True,
                "can_go_back": True,
                "back_target": "help:overview",
            },
            "is_primary": True,
        }

    def _get_excerpt(self, content: str, query: str, max_length: int = 100) -> str:
        """Get excerpt from content containing query."""
        content_lower = content.lower()
        query_pos = content_lower.find(query)

        if query_pos == -1:
            # Query not found in content (but matched in title)
            return (
                content[:max_length] + "..." if len(content) > max_length else content
            )

        # Get excerpt around query
        start = max(0, query_pos - 30)
        end = min(len(content), query_pos + len(query) + 70)

        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."

        return excerpt

    def get_quick_reference(self) -> dict[str, Any]:
        """
        Get a quick reference card.

        Shows the most important rules and concepts at a glance.
        """
        # Get key entries from each category
        key_entries = []

        # One from each category
        for category in HelpCategory:
            entries = HelpDatabase.get_entries_by_category(category)
            if entries:
                # Prefer CONCEPT or CONSTRAINT entries for quick reference
                concept_entries = [
                    e
                    for e in entries
                    if e.entry_type in (HelpEntryType.CONCEPT, HelpEntryType.CONSTRAINT)
                ]
                if concept_entries:
                    key_entries.append(concept_entries[0])
                else:
                    key_entries.append(entries[0])

        return {
            "view_type": "help",
            "view_mode": "quick_reference",
            "title": "Quick Reference",
            "icon": "📋",
            "content": {
                "entries": [
                    {
                        "id": entry.id,
                        "title": entry.title,
                        "category": entry.category.display_name,
                        "icon": entry.category.icon,
                        "summary": self._summarize_entry(entry),
                    }
                    for entry in key_entries
                ],
                "total_concepts": len(key_entries),
                "message": "Essential concepts at a glance",
            },
            "navigation": {
                "can_drill_down": True,
                "can_search": True,
                "can_go_back": True,
                "back_target": "help:overview",
            },
            "is_primary": True,
        }

    def _summarize_entry(self, entry: HelpEntry, max_length: int = 80) -> str:
        """Create a short summary of a help entry."""
        # Extract first sentence or first 80 characters
        content = entry.content.strip()

        # Find first sentence end
        sentence_end = min(
            content.find(".") if content.find(".") != -1 else len(content),
            content.find("!") if content.find("!") != -1 else len(content),
            content.find("?") if content.find("?") != -1 else len(content),
            max_length,
        )

        summary = content[:sentence_end].strip()
        if not summary.endswith((".", "!", "?")):
            summary += "..."

        return summary

    def _get_view_metadata(self) -> dict[str, Any]:
        """Get metadata about this view rendering."""
        return {
            "metadata": {
                "rendered_at": datetime.now(UTC).isoformat(),
                "config": asdict(self._config),
                "current_entry": self._current_entry_id,
                "context_provided": bool(self._context),
                "philosophy_rules_applied": [
                    "SingleFocusRule",
                    "ProgressiveDisclosureRule",
                    "ClarityRule",
                    "NavigationRule",
                ],
                "constitutional_compliance": [
                    "Article 7: Clear Affordances",
                    "Article 8: Honest Performance",
                    "Article 16: Truth-Preserving Aesthetics",
                ],
            }
        }

    def validate_integrity(self) -> list[str]:
        """
        Validate that this view adheres to truth-preserving constraints.

        Returns:
            List of violations (empty if valid)
        """
        violations = []

        # Check 1: No domain advice
        for section in HelpDatabase.get_sections():
            for entry in section.entries:
                # Check for code-specific advice
                code_keywords = [
                    "should refactor",
                    "better to",
                    "recommend",
                    "best practice",
                ]
                for keyword in code_keywords:
                    if keyword in entry.content.lower():
                        violations.append(
                            f"Entry {entry.id} contains domain advice: '{keyword}'"
                        )

        # Check 2: No shortcuts or workarounds
        shortcut_keywords = ["shortcut", "workaround", "bypass", "trick"]
        for section in HelpDatabase.get_sections():
            for entry in section.entries:
                for keyword in shortcut_keywords:
                    if keyword in entry.content.lower():
                        violations.append(
                            f"Entry {entry.id} suggests shortcuts: '{keyword}'"
                        )

        # Check 3: No recommended next steps for investigation
        # (Except for the natural investigation flow)
        if self._current_entry_id:
            entry = HelpDatabase.get_entry(self._current_entry_id)
            if entry and "next you should" in entry.content.lower():
                violations.append(f"Entry {entry.id} recommends investigation steps")

        # Check 4: Help must explain constraints
        # All constraint entries should be in the database
        constraint_entries = [
            e
            for s in HelpDatabase.get_sections()
            for e in s.entries
            if e.entry_type == HelpEntryType.CONSTRAINT
        ]
        if len(constraint_entries) < 5:  # Should have several key constraints
            violations.append("Insufficient constraint documentation")

        return violations

    @classmethod
    def create_test_view(cls) -> HelpView:
        """
        Create a test view for development and testing.

        Returns:
            A HelpView with test data
        """

        # Create test context
        class TestContext:
            def __init__(self) -> None:
                self.current_focus = "module:example.py"
                self.investigation_path = ["started", "observing"]
                self.created_at = datetime.now(UTC)

        return cls(TestContext())


def main() -> None:
    """Test the help view."""
    view = HelpView.create_test_view()

    # Test overview
    print("=== HELP OVERVIEW ===")
    overview = view.render()
    print(json.dumps(overview, indent=2, default=str))

    # Test single entry
    print("\n=== SINGLE ENTRY ===")
    class TestContext:
        def __init__(self) -> None:
            self.current_focus = "module:example.py"
            self.investigation_path = ["started", "observing"]
            self.created_at = datetime.now(UTC)

    single_view = HelpView(TestContext(), "philosophy:truth-preservation")
    single_entry = single_view.render()
    print(json.dumps(single_entry, indent=2, default=str))

    # Test search
    print("\n=== SEARCH ===")
    search_results = view.search("pattern")
    print(json.dumps(search_results, indent=2, default=str))

    # Test quick reference
    print("\n=== QUICK REFERENCE ===")
    quick_ref = view.get_quick_reference()
    print(json.dumps(quick_ref, indent=2, default=str))

    # Validate integrity
    violations = view.validate_integrity()
    if violations:
        print(f"\nINTEGRITY VIOLATIONS ({len(violations)}):")
        for violation in violations:
            print(f"  ⚠️  {violation}")
    else:
        print("\n✅ View passes integrity checks.")


if __name__ == "__main__":
    main()
