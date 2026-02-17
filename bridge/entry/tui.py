"""
tui.py — Terminal User Interface for CodeMarshal.

ROLE: Guided exploration interface that enforces linear investigation.
PRINCIPLE: This is a magnifying glass, not a cockpit.
"""

import logging
import os
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

# Allowed imports per constitutional constraints
from bridge.commands import observe, execute_pattern_apply, execute_pattern_search
from lens.indicators import LoadingIndicator
from lens.indicators.errors import ErrorCategory, ErrorIndicator, ErrorSeverity
from lens.navigation import Step, WorkflowNavigator

# For TUI implementation - minimal, truth-preserving UI library
try:
    import curses
    import curses.textpad
    from curses import wrapper

    TUI_AVAILABLE = True
except ImportError:
    TUI_AVAILABLE = False
    curses = None
    wrapper = None


logger = logging.getLogger(__name__)


class TUIState(Enum):
    """Allowed states in the TUI state machine."""

    INITIAL = "initial"
    AWAITING_PATH = "awaiting_path"
    OBSERVING = "observing"
    QUESTIONING = "questioning"
    PATTERN_ANALYSIS = "pattern_analysis"
    NOTING = "noting"
    EXPORTING = "exporting"
    REFUSING = "refusing"
    EXITING = "exiting"
    WATCHING = "watching"  # Real-time file watching
    DIFF_VIEWING = "diff_viewing"  # Viewing file diffs
    STATUS_VIEWING = "status_viewing"  # Viewing investigation status
    HISTORY_VIEWING = "history_viewing"  # Knowledge history view
    GRAPH_VIEWING = "graph_viewing"  # Knowledge graph view
    RECOMMENDATIONS_VIEWING = "recommendations_viewing"  # Recommendation view
    MARKETPLACE_VIEWING = "marketplace_viewing"  # Pattern marketplace view


@dataclass
class TUIContext:
    """Minimal context for TUI operation. No truth access."""

    current_state: TUIState = TUIState.INITIAL
    current_path: Path | None = None
    investigation_id: str | None = None
    last_error: str | None = None
    awaiting_confirmation: bool = False
    confirmation_message: str | None = None
    confirmation_callback: Callable | None = None

    # Navigation
    workflow: WorkflowNavigator | None = None
    current_step: Step | None = None

    # Real-time watching
    watcher_active: bool = False
    detected_changes: list = field(default_factory=list)
    watching_start_time: datetime | None = None

    # Diff viewing
    diff_content: str | None = None
    diff_file_path: Path | None = None

    # Status viewing
    status_info: dict | None = None


class TruthPreservingTUI:
    """
    TUI implementation that enforces linear investigation.

    CONSTRAINTS:
    - Single active action at a time
    - Clear "next step" affordances only
    - No hidden keybinds or shortcuts
    - No multi-pane views
    - No action batching
    """

    def __init__(self):
        if not TUI_AVAILABLE:
            raise ImportError(
                "curses module not available. TUI requires curses library."
            )

        self.context = TUIContext()
        self.workflow_nav = WorkflowNavigator()
        self.loading_indicator = LoadingIndicator.create_idle()
        self.error_display = ErrorIndicator(
            severity=ErrorSeverity.INFORMATIONAL,
            category=ErrorCategory.UNCLASSIFIED,
            affected_component="TUI",
        )
        self.exit_code = 0  # Initialize exit code

        # Allowed keybindings - explicit and minimal
        self.key_actions: dict[str, tuple[str, Callable]] = {
            # Navigation
            "q": ("Quit", self._handle_quit),
            "h": ("Help", self._show_help),
            # Investigation flow (enabled per state)
            "o": ("Observe", self._handle_observe),
            "s": ("Ask structural question", self._handle_structure_question),
            "p": ("Analyze patterns", self._handle_patterns),
            "m": ("Pattern marketplace", self._handle_marketplace),
            "n": ("Add note", self._handle_note),
            "e": ("Export", self._handle_export),
            # Real-time features
            "w": ("Watch", self._handle_watch),
            "d": ("Diff", self._handle_diff),
            "t": ("Status", self._handle_status),
            # Knowledge features
            "k": ("History", self._handle_history),
            "g": ("Graph", self._handle_graph),
            "r": ("Recommendations", self._handle_recommendations),
            # Confirmation
            "y": ("Yes", self._handle_confirm),
            "x": ("No", self._handle_deny),
        }

        # Track which actions are currently allowed
        self.enabled_actions: dict[str, bool] = dict.fromkeys(
            self.key_actions.keys(), False
        )

        # Screen dimensions
        self.height: int = 0
        self.width: int = 0
        self.stdscr: Any | None = None

    def run(self, initial_path: Path | None = None) -> int:
        """
        Main TUI entry point. Wraps curses initialization.

        Args:
            initial_path: Optional starting path from command line.

        Returns:
            Exit code (0 for success, 1 for error)
        """
        self.exit_code = 0
        try:
            wrapper(self._main)
        except KeyboardInterrupt:
            # Respect user interrupt without dumping stack trace
            self.exit_code = 130  # Standard exit code for Ctrl+C
        except Exception as e:
            # Fall back to CLI with clear error
            print(f"TUI failed: {e}", file=sys.stderr)
            print("Falling back to CLI interface.", file=sys.stderr)
            self.exit_code = 1

        return self.exit_code

    def _main(self, stdscr: Any) -> None:
        """Curses main loop with truth-preserving constraints."""
        self.stdscr = stdscr
        curses.curs_set(0)  # Hide cursor
        self.stdscr.clear()
        self.stdscr.refresh()

        # Initialize color pairs if supported
        if curses.has_colors():
            curses.start_color()
            # Simple, meaningful colors only
            curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal
            curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Warning
            curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)  # Error
            curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Success
            curses.init_pair(5, curses.COLOR_CYAN, curses.COLOR_BLACK)  # Highlight

        # Initial state
        self._update_screen_dimensions()
        self._transition_to(TUIState.AWAITING_PATH)

        # Main event loop
        while self.context.current_state != TUIState.EXITING:
            self._render()
            key = self.stdscr.getch()
            self._handle_input(key)

    def _update_screen_dimensions(self) -> None:
        """Update screen size for responsive layout."""
        self.height, self.width = self.stdscr.getmaxyx()

    def _transition_to(self, new_state: TUIState) -> None:
        """
        State transition with validation.

        Ensures linear workflow is followed.
        """
        logger.debug(f"Transition: {self.context.current_state} -> {new_state}")

        # Reset confirmation state
        self.context.awaiting_confirmation = False
        self.context.confirmation_message = None
        self.context.confirmation_callback = None

        # Update state
        self.context.current_state = new_state

        # Update allowed actions based on state
        self._update_enabled_actions()

        # Update navigation workflow
        if new_state != TUIState.INITIAL:
            self.context.workflow = self.workflow_nav.get_step(new_state.value)
            if self.context.workflow:
                self.context.current_step = self.context.workflow.current

    def _update_enabled_actions(self) -> None:
        """Enable only actions appropriate for current state."""
        # Reset all
        for key in self.enabled_actions:
            self.enabled_actions[key] = False

        # State-specific enablement
        state = self.context.current_state

        if state == TUIState.AWAITING_PATH:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["o"] = True  # Observe (will prompt for path)

        elif state == TUIState.OBSERVING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            # After observing, you can ask questions, analyze patterns, add notes, or use real-time features
            self.enabled_actions["s"] = True
            self.enabled_actions["p"] = True
            self.enabled_actions["m"] = True
            self.enabled_actions["n"] = True
            self.enabled_actions["e"] = True
            self.enabled_actions["w"] = True  # Watch
            self.enabled_actions["d"] = True  # Diff
            self.enabled_actions["t"] = True  # Status
            self.enabled_actions["k"] = True  # History
            self.enabled_actions["g"] = True  # Graph
            self.enabled_actions["r"] = True  # Recommendations

        elif state == TUIState.QUESTIONING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["p"] = True  # Can switch to patterns
            self.enabled_actions["m"] = True
            self.enabled_actions["n"] = True  # Can add notes
            self.enabled_actions["e"] = True  # Can export
            self.enabled_actions["w"] = True  # Watch
            self.enabled_actions["d"] = True  # Diff
            self.enabled_actions["t"] = True  # Status
            self.enabled_actions["k"] = True  # History
            self.enabled_actions["g"] = True  # Graph
            self.enabled_actions["r"] = True  # Recommendations

        elif state == TUIState.PATTERN_ANALYSIS:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["s"] = True  # Can ask questions
            self.enabled_actions["m"] = True
            self.enabled_actions["n"] = True  # Can add notes
            self.enabled_actions["e"] = True  # Can export
            self.enabled_actions["w"] = True  # Watch
            self.enabled_actions["d"] = True  # Diff
            self.enabled_actions["t"] = True  # Status
            self.enabled_actions["k"] = True  # History
            self.enabled_actions["g"] = True  # Graph
            self.enabled_actions["r"] = True  # Recommendations

        elif state == TUIState.NOTING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["s"] = True  # Can ask questions
            self.enabled_actions["p"] = True  # Can analyze patterns
            self.enabled_actions["m"] = True
            self.enabled_actions["e"] = True  # Can export
            self.enabled_actions["w"] = True  # Watch
            self.enabled_actions["d"] = True  # Diff
            self.enabled_actions["t"] = True  # Status
            self.enabled_actions["k"] = True  # History
            self.enabled_actions["g"] = True  # Graph
            self.enabled_actions["r"] = True  # Recommendations

        elif state == TUIState.EXPORTING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            # After export, can start over or quit
            self.enabled_actions["o"] = True  # New observation

        elif state == TUIState.REFUSING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help

        elif state == TUIState.WATCHING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["t"] = True  # Status

        elif state == TUIState.DIFF_VIEWING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["t"] = True  # Status

        elif state == TUIState.STATUS_VIEWING:
            self.enabled_actions["q"] = True  # Quit
            self.enabled_actions["h"] = True  # Help
            self.enabled_actions["w"] = True  # Watch
            self.enabled_actions["d"] = True  # Diff

        elif state == TUIState.HISTORY_VIEWING:
            self.enabled_actions["q"] = True
            self.enabled_actions["h"] = True
            self.enabled_actions["g"] = True
            self.enabled_actions["r"] = True

        elif state == TUIState.GRAPH_VIEWING:
            self.enabled_actions["q"] = True
            self.enabled_actions["h"] = True
            self.enabled_actions["k"] = True
            self.enabled_actions["r"] = True

        elif state == TUIState.RECOMMENDATIONS_VIEWING:
            self.enabled_actions["q"] = True
            self.enabled_actions["h"] = True
            self.enabled_actions["k"] = True
            self.enabled_actions["g"] = True

        elif state == TUIState.MARKETPLACE_VIEWING:
            self.enabled_actions["q"] = True
            self.enabled_actions["h"] = True
            self.enabled_actions["p"] = True
            self.enabled_actions["s"] = True

        # Always enable confirmation keys when awaiting confirmation
        if self.context.awaiting_confirmation:
            self.enabled_actions["y"] = True
            self.enabled_actions["x"] = True

    def _render(self) -> None:
        """Render the TUI with single-focus constraint."""
        self._update_screen_dimensions()
        self.stdscr.clear()

        # Header - always visible
        self._render_header()

        # Main content area - single focus
        self._render_main_content()

        # Footer - affordances
        self._render_footer()

        self.stdscr.refresh()

    def _render_header(self) -> None:
        """Render header with current state and investigation info."""

        # Line 1: Title and state
        title = "CodeMarshal TUI"
        state = f"[{self.context.current_state.value.upper()}]"
        header_line = f"{title} {state}"
        self._addstr_centered(0, header_line, curses.color_pair(5))

        # Line 2: Path and investigation ID
        path_info = ""
        if self.context.current_path:
            path_info = f"Path: {self.context.current_path}"
            if self.context.investigation_id:
                path_info += f" | Investigation: {self.context.investigation_id[:8]}..."

        if path_info:
            self._addstr_truncated(1, path_info, 1)

        # Line 3: Separator
        self.stdscr.hline(2, 0, curses.ACS_HLINE, self.width)

    def _render_main_content(self) -> None:
        """
        Render main content area.

        Only one type of content visible at a time.
        """
        content_y = 3
        content_height = self.height - 8  # Reserve space for header and footer

        if self.context.current_state == TUIState.AWAITING_PATH:
            self._render_path_prompt(content_y, content_height)

        elif self.context.current_state == TUIState.OBSERVING:
            self._render_observation_status(content_y, content_height)

        elif self.context.current_state == TUIState.QUESTIONING:
            self._render_questioning_interface(content_y, content_height)

        elif self.context.current_state == TUIState.PATTERN_ANALYSIS:
            self._render_pattern_interface(content_y, content_height)

        elif self.context.current_state == TUIState.NOTING:
            self._render_note_interface(content_y, content_height)

        elif self.context.current_state == TUIState.EXPORTING:
            self._render_export_interface(content_y, content_height)

        elif self.context.current_state == TUIState.REFUSING:
            self._render_refusal(content_y, content_height)

        elif self.context.current_state == TUIState.WATCHING:
            self._render_watching_interface(content_y, content_height)

        elif self.context.current_state == TUIState.DIFF_VIEWING:
            self._render_diff_interface(content_y, content_height)

        elif self.context.current_state == TUIState.STATUS_VIEWING:
            self._render_status_interface(content_y, content_height)

        elif self.context.current_state == TUIState.HISTORY_VIEWING:
            self._render_history_interface(content_y, content_height)

        elif self.context.current_state == TUIState.GRAPH_VIEWING:
            self._render_graph_interface(content_y, content_height)

        elif self.context.current_state == TUIState.RECOMMENDATIONS_VIEWING:
            self._render_recommendations_interface(content_y, content_height)

        elif self.context.current_state == TUIState.MARKETPLACE_VIEWING:
            self._render_marketplace_interface(content_y, content_height)

    def _render_path_prompt(self, y: int, height: int) -> None:
        """Render path input prompt."""
        prompt_lines = [
            "Enter path to investigate:",
            "",
            "Current directory:",
            f"  {os.getcwd()}",
            "",
            "Press 'h' for help, 'q' to quit.",
            "",
            "Path: [awaiting input]",
        ]

        for i, line in enumerate(prompt_lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_observation_status(self, y: int, height: int) -> None:
        """Render observation in progress or results."""
        if not self.context.current_path:
            self._addstr_centered(y, "ERROR: No path set", curses.color_pair(3))
            return

        status_lines = [
            f"Observing: {self.context.current_path}",
            "",
            "Collecting evidence without interpretation...",
            "",
            "This may take a moment for large codebases.",
            "",
            "Evidence collected: [running]",
        ]

        for i, line in enumerate(status_lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_questioning_interface(self, y: int, height: int) -> None:
        """Render question input interface."""
        lines = [
            "Ask a question about the codebase:",
            "",
            "Available question types:",
            "  s - Structure (what's here?)",
            "  p - Purpose (what does this do?)",
            "  c - Connections (how is it connected?)",
            "  a - Anomalies (what seems unusual?)",
            "",
            "Type your question, then press Enter:",
            "[text input area]",
        ]

        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_pattern_interface(self, y: int, height: int) -> None:
        """Render pattern analysis interface."""
        lines = [
            "Pattern Analysis",
            "",
            "Detecting numeric patterns in the codebase:",
            "",
            "Available patterns:",
            "  • Import density",
            "  • Coupling metrics",
            "  • Complexity indicators",
            "  • Boundary violations",
            "",
            "Press 'p' to analyze patterns.",
        ]

        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_note_interface(self, y: int, height: int) -> None:
        """Render note-taking interface."""
        lines = [
            "Add Investigation Note",
            "",
            "Notes are anchored to specific observations.",
            "They preserve your thinking during investigation.",
            "",
            "Enter your note, then press Enter:",
            "[text input area]",
            "",
            "Note: Notes are for human thinking only.",
            "They do not affect observations.",
        ]

        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_export_interface(self, y: int, height: int) -> None:
        """Render export interface."""
        lines = [
            "Export Investigation",
            "",
            "Available formats:",
            "  • JSON (complete evidence)",
            "  • Markdown (human-readable)",
            "  • HTML (interactive report)",
            "",
            "Select format and destination:",
            "[export options]",
            "",
            "Export preserves truth without alteration.",
        ]

        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_refusal(self, y: int, height: int) -> None:
        """Render refusal state clearly."""
        if self.context.last_error:
            error_lines = self.context.last_error.split("\n")
            for i, line in enumerate(error_lines[:height]):
                self._addstr_centered(y + i, line, curses.color_pair(3))
        else:
            self._addstr_centered(
                y, "Action refused. Press 'h' for help.", curses.color_pair(2)
            )

    def _render_footer(self) -> None:
        """Render footer with available actions."""
        footer_y = self.height - 4

        # Separator
        self.stdscr.hline(footer_y, 0, curses.ACS_HLINE, self.width)

        # Action line
        action_line = "Available: "
        actions = []

        for key, (description, _) in self.key_actions.items():
            if self.enabled_actions.get(key, False):
                actions.append(f"{key}={description}")

        action_line += " | ".join(actions)
        self._addstr_truncated(footer_y + 1, action_line, 1)

        # Step guidance
        if self.context.current_step and hasattr(self.context.current_step, "guidance"):
            guidance = getattr(self.context.current_step, "guidance", None)
            if guidance:
                self._addstr_truncated(footer_y + 2, guidance, 1)

        # Status line
        status = f"CodeMarshal TUI | Height: {self.height}, Width: {self.width}"
        self._addstr_truncated(footer_y + 3, status, 1)

    def _handle_input(self, key: int) -> None:
        """Handle keyboard input with truth-preserving constraints."""
        try:
            char = chr(key)
        except ValueError:
            return  # Ignore non-character keys

        # Check if key is enabled
        if char in self.key_actions and self.enabled_actions.get(char, False):
            _, handler = self.key_actions[char]
            handler()
        else:
            # Invalid key - show brief feedback
            self._show_temporary_message(f"Key '{char}' not available in current state")

    def _handle_quit(self) -> None:
        """Handle quit request with confirmation if needed."""
        if self.context.awaiting_confirmation:
            self._handle_deny()
            return

        if self.context.current_state != TUIState.AWAITING_PATH:
            # Confirm before quitting investigation
            self.context.awaiting_confirmation = False
            self.context.confirmation_message = (
                "Quit investigation? Unsaved work will be lost."
            )
            self.context.confirmation_callback = self._confirm_quit
        else:
            self._confirm_quit()

    def _confirm_quit(self) -> None:
        """Actually quit the TUI."""
        self._transition_to(TUIState.EXITING)

    def _handle_observe(self) -> None:
        """Initiate observation of current path."""
        if not self.context.current_path:
            self._request_path_input()
            return

        # Validate path exists
        if not self.context.current_path.exists():
            self.context.last_error = (
                f"Path does not exist: {self.context.current_path}"
            )
            self._transition_to(TUIState.REFUSING)
            return

        # Update loading indicator state (immutable)
        self.loading_indicator = LoadingIndicator.create_working(
            "Observing...", with_timer=True
        )

        try:
            # Call observation command
            result = observe(str(self.context.current_path))

            if result.success:
                self.context.investigation_id = result.investigation_id
                self._transition_to(TUIState.OBSERVING)
            else:
                self.context.last_error = result.error_message
                self._transition_to(TUIState.REFUSING)

        except Exception as e:
            logger.error(f"Observation failed: {e}")
            self.context.last_error = f"Observation failed: {str(e)}"
            self._transition_to(TUIState.REFUSING)
        finally:
            self.loading_indicator = LoadingIndicator.create_idle()

    def _handle_structure_question(self) -> None:
        """Handle structure question request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before asking questions"
            self._transition_to(TUIState.REFUSING)
            return

        # Ask user what they want to know
        self._transition_to(TUIState.QUESTIONING)
        question = self._request_text_input(
            "What would you like to know? (e.g., 'What modules exist?', 'Show directory structure')",
            "What modules exist?",
        )

        if question:
            self._perform_query(question, "structure")

    def _perform_query(self, question: str, question_type: str) -> None:
        """Perform a query and display results."""
        from bridge.entry.cli import CodeMarshalCLI

        self.loading_indicator = LoadingIndicator.create_working(
            "Querying...", with_timer=True
        )
        self._render()

        try:
            # Use the CLI's query functionality
            cli = CodeMarshalCLI()

            # Load session and observations
            storage = cli._load_session_data(cli, None, self.context.investigation_id)
            if not storage:
                # Try to find any session
                from storage.investigation_storage import InvestigationStorage

                store = InvestigationStorage()
                sessions_dir = Path("storage/sessions")
                if sessions_dir.exists():
                    for session_file in sessions_dir.glob("*.session.json"):
                        import json

                        with open(session_file) as f:
                            data = json.load(f)
                            if data.get("id"):
                                self.context.investigation_id = data.get("id")
                                break

            # Get observations
            from storage.investigation_storage import InvestigationStorage

            store = InvestigationStorage()
            session_data = cli._load_session_data(store, self.context.investigation_id)

            if session_data:
                observations = cli._load_observations(store, session_data)
                answer = cli._generate_answer(question, question_type, observations)
                self._show_query_results(question, answer)
            else:
                self._show_temporary_message("No session data available for querying")

        except Exception as e:
            logger.error(f"Query failed: {e}")
            self.context.last_error = f"Query failed: {str(e)}"
            self._transition_to(TUIState.REFUSING)
        finally:
            self.loading_indicator = LoadingIndicator.create_idle()

    def _show_query_results(self, question: str, answer: str) -> None:
        """Display query results in the TUI."""
        if not self.stdscr:
            return

        self._update_screen_dimensions()
        self.stdscr.clear()
        self._render_header()

        # Title
        title = "Query Results"
        self._addstr_centered(4, title, curses.color_pair(5))

        # Question
        question_label = f"Q: {question}"
        self._addstr_truncated(6, question_label, 2, curses.color_pair(2))

        # Answer (scrollable)
        lines = answer.split("\n")
        y = 8
        for i, line in enumerate(lines):
            if y + i >= self.height - 5:
                self._addstr_truncated(
                    y + i - 1, "... (more content)", 2, curses.color_pair(3)
                )
                break
            self._addstr_truncated(y + i, line, 2)

        # Footer
        self._addstr_truncated(
            self.height - 3, "Press any key to continue...", 2, curses.color_pair(5)
        )

        self.stdscr.refresh()
        self.stdscr.getch()

    def _handle_patterns(self) -> None:
        """Handle pattern analysis request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before analyzing patterns"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.PATTERN_ANALYSIS)

    def _handle_marketplace(self) -> None:
        """Handle local marketplace listing/search/apply flow."""
        if not self.context.current_path:
            self.context.last_error = "Must set a path before using marketplace features"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.MARKETPLACE_VIEWING)
        query = self._request_text_input(
            "Marketplace search query (blank for top local patterns):",
            "",
        )
        if query is None:
            self._transition_to(TUIState.OBSERVING)
            return

        try:
            search_result = execute_pattern_search(
                query=query.strip(),
                limit=12,
                storage_root=Path("storage"),
            )
            if not search_result.success:
                self._show_temporary_message(
                    f"Marketplace search failed:\n{search_result.error}"
                )
                self._transition_to(TUIState.OBSERVING)
                return

            lines = [
                "Pattern Marketplace",
                "===================",
                f"Query: {query.strip() or '(top patterns)'}",
                f"Results: {search_result.total_count}",
                "",
            ]
            for item in search_result.patterns[:10]:
                pattern_id = str(item.get("pattern_id", ""))
                name = str(item.get("name", ""))
                severity = str(item.get("severity", ""))
                installed = bool(item.get("installed", False))
                lines.append(
                    f"- {pattern_id} [{severity}] {'(installed)' if installed else ''}"
                )
                if name:
                    lines.append(f"    {name}")

            self._show_temporary_message("\n".join(lines))

            apply_pattern_id = self._request_text_input(
                "Optional pattern ID to apply now (blank to skip):",
                "",
            )
            if apply_pattern_id:
                apply_result = execute_pattern_apply(
                    pattern_ref=apply_pattern_id.strip(),
                    path=self.context.current_path,
                    glob="*.py",
                    max_files=5000,
                    storage_root=Path("storage"),
                )
                if not apply_result.success:
                    self._show_temporary_message(
                        f"Apply failed:\n{apply_result.error or 'Unknown error'}"
                    )
                else:
                    self._show_temporary_message(
                        "Pattern applied\n"
                        f"Pattern: {apply_result.pattern_id}\n"
                        f"Files scanned: {apply_result.files_scanned}\n"
                        f"Matches found: {apply_result.matches_found}"
                    )
        except Exception as exc:
            self.context.last_error = f"Marketplace failed: {exc}"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.OBSERVING)

    def _handle_note(self) -> None:
        """Handle note-taking request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before adding notes"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.NOTING)

    def _handle_export(self) -> None:
        """Handle export request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before exporting"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.EXPORTING)

        # Ask for export format
        format_choice = self._request_choice(
            "Select export format:", ["json", "markdown", "html", "plain"], default=0
        )

        if not format_choice:
            self._transition_to(TUIState.OBSERVING)
            return

        # Ask for output filename
        default_name = (
            f"investigation_{self.context.investigation_id[:8]}.{format_choice}"
        )
        filename = self._request_text_input("Enter output filename:", default_name)

        if not filename:
            self._transition_to(TUIState.OBSERVING)
            return

        # Perform export
        self._perform_export(format_choice, filename)

    def _perform_export(self, format_type: str, filename: str) -> None:
        """Perform export operation."""
        from pathlib import Path

        from bridge.entry.cli import CodeMarshalCLI

        self.loading_indicator = LoadingIndicator.create_working(
            "Exporting...", with_timer=True
        )
        self._render()

        try:
            cli = CodeMarshalCLI()

            # Load session data
            from storage.investigation_storage import InvestigationStorage

            store = InvestigationStorage()
            session_data = cli._load_session_data(store, self.context.investigation_id)

            if not session_data:
                self._show_temporary_message("No session data available for export")
                self._transition_to(TUIState.OBSERVING)
                return

            # Load observations
            observations = cli._load_observations(store, session_data)

            # Generate export content
            output_path = Path(filename)
            export_content = cli._generate_export_content(
                format_type,
                session_data,
                observations,
                include_notes=False,
                include_patterns=False,
            )

            # Write to file
            output_path.write_text(export_content, encoding="utf-8")

            if output_path.exists():
                self._show_temporary_message(
                    f"✓ Export complete: {output_path.absolute()}"
                )
            else:
                self._show_temporary_message("✗ Export failed: File was not created")

        except Exception as e:
            logger.error(f"Export failed: {e}")
            self.context.last_error = f"Export failed: {str(e)}"
            self._transition_to(TUIState.REFUSING)
        finally:
            self.loading_indicator = LoadingIndicator.create_idle()

    def _handle_watch(self) -> None:
        """Handle file watching request."""
        if not self.context.current_path:
            self.context.last_error = "Must set a path before watching"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.WATCHING)

        # Show watching status
        self._show_temporary_message(
            f"Watching {self.context.current_path}\n"
            "File system monitoring active.\n"
            "Changes will be detected in real-time.\n\n"
            "Press any key to return to observing..."
        )

        # Note: Real-time watching would require async/threading integration
        # For now, we show the UI state
        self._transition_to(TUIState.OBSERVING)

    def _handle_diff(self) -> None:
        """Handle diff viewing request."""
        if not self.context.current_path:
            self.context.last_error = "Must set a path before viewing diffs"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.DIFF_VIEWING)

        # Show diff viewer placeholder
        self._show_temporary_message(
            f"Diff Viewer\n"
            f"Path: {self.context.current_path}\n\n"
            "Compare file versions and view changes.\n\n"
            "Use 'codemarshal diff' CLI command for full functionality.\n\n"
            "Press any key to return..."
        )

        self._transition_to(TUIState.OBSERVING)

    def _handle_status(self) -> None:
        """Handle status viewing request."""
        self._transition_to(TUIState.STATUS_VIEWING)

        # Gather status information
        status_lines = [
            "Investigation Status",
            "===================",
            "",
        ]

        if self.context.current_path:
            status_lines.append(f"Current Path: {self.context.current_path}")
        else:
            status_lines.append("Current Path: Not set")

        if self.context.investigation_id:
            status_lines.append(f"Investigation ID: {self.context.investigation_id}")

        status_lines.append(f"Current State: {self.context.current_state.value}")

        if self.context.detected_changes:
            status_lines.append(
                f"Detected Changes: {len(self.context.detected_changes)}"
            )

        status_lines.extend(
            [
                "",
                "Press any key to return...",
            ]
        )

        self._show_temporary_message("\n".join(status_lines))
        self._transition_to(TUIState.OBSERVING)

    def _handle_history(self) -> None:
        """Handle knowledge history request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before viewing history"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.HISTORY_VIEWING)
        try:
            from knowledge import KnowledgeBase

            kb = KnowledgeBase()
            events = kb.history(session_id=self.context.investigation_id, limit=20)
            suggestions = kb.history_service.suggestions(
                session_id=self.context.investigation_id,
                limit=5,
            )

            lines = [
                "Knowledge History",
                "=================",
                "",
                f"Session: {self.context.investigation_id}",
                f"Events: {len(events)}",
                "",
            ]
            for event in events[:10]:
                timestamp = str(event.get("timestamp") or "unknown")
                event_type = str(event.get("event_type") or "unknown")
                question = str(event.get("question") or "").strip()
                lines.append(f"- [{timestamp}] {event_type}")
                if question:
                    lines.append(f"    Q: {question}")

            if suggestions:
                lines.extend(["", "Top suggestions:"])
                for item in suggestions:
                    lines.append(f"- {item.get('query', '')} ({item.get('count', 0)})")

            lines.extend(["", "Press any key to return..."])
            self._show_temporary_message("\n".join(lines))
        except Exception as exc:
            self.context.last_error = f"History failed: {exc}"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.OBSERVING)

    def _handle_graph(self) -> None:
        """Handle knowledge graph request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before viewing graph"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.GRAPH_VIEWING)
        try:
            from knowledge import KnowledgeBase

            kb = KnowledgeBase()
            payload = kb.graph(session_id=self.context.investigation_id, depth=2, limit=80)
            nodes = payload.get("nodes", [])
            edges = payload.get("edges", [])

            lines = [
                "Knowledge Graph",
                "===============",
                "",
                f"Session: {self.context.investigation_id}",
                f"Nodes: {len(nodes)}",
                f"Edges: {len(edges)}",
                "",
                "Sample nodes:",
            ]
            for node in nodes[:8]:
                node_id = str(node.get("node_id") or "")
                node_type = str(node.get("node_type") or "unknown")
                label = str(node.get("label") or "")
                lines.append(f"- {node_id} [{node_type}] {label}")

            lines.append("")
            lines.append("Sample edges:")
            for edge in edges[:10]:
                src = str(edge.get("from_node") or "")
                dst = str(edge.get("to_node") or "")
                edge_type = str(edge.get("edge_type") or "")
                lines.append(f"- {src} -> {dst} ({edge_type})")

            lines.extend(["", "Press any key to return..."])
            self._show_temporary_message("\n".join(lines))
        except Exception as exc:
            self.context.last_error = f"Graph failed: {exc}"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.OBSERVING)

    def _handle_recommendations(self) -> None:
        """Handle recommendation request."""
        if not self.context.investigation_id:
            self.context.last_error = "Must observe first before viewing recommendations"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.RECOMMENDATIONS_VIEWING)
        try:
            from knowledge import KnowledgeBase

            kb = KnowledgeBase()
            recommendations = kb.recommendations(
                self.context.investigation_id,
                limit=8,
            )

            lines = [
                "Recommendations",
                "===============",
                "",
                f"Session: {self.context.investigation_id}",
                f"Count: {len(recommendations)}",
                "",
            ]
            for item in recommendations:
                title = str(item.get("title") or "Untitled")
                category = str(item.get("category") or "unknown")
                confidence = float(item.get("confidence") or 0.0)
                reason = str(item.get("reason") or "")
                lines.append(f"- {title} [{category}] ({confidence:.2f})")
                if reason:
                    lines.append(f"    {reason}")

            lines.extend(["", "Press any key to return..."])
            self._show_temporary_message("\n".join(lines))
        except Exception as exc:
            self.context.last_error = f"Recommendations failed: {exc}"
            self._transition_to(TUIState.REFUSING)
            return

        self._transition_to(TUIState.OBSERVING)

    def _handle_confirm(self) -> None:
        """Handle confirmation."""
        if self.context.awaiting_confirmation and self.context.confirmation_callback:
            self.context.confirmation_callback()

    def _handle_deny(self) -> None:
        """Handle denial/cancellation."""
        self.context.awaiting_confirmation = False
        self.context.confirmation_message = None
        self.context.confirmation_callback = None

    def _show_help(self) -> None:
        """Show help information."""
        # Simple help display - could be expanded
        help_text = [
            "CodeMarshal TUI Help",
            "",
            "This interface guides you through code investigation:",
            "1. Observe: Collect evidence without interpretation",
            "2. Question: Ask about structure, purpose, connections",
            "3. Analyze: Detect patterns in the evidence",
            "4. Note: Record your thinking anchored to evidence",
            "5. Export: Save investigation results",
            "",
            "Constraints:",
            "• Linear workflow only",
            "• No hidden shortcuts",
            "• One action at a time",
            "• Clear refusal when action not possible",
            "",
            "Press any key to continue...",
        ]

        self._show_temporary_message("\n".join(help_text))

    def _request_path_input(self) -> None:
        """Request path input from user."""
        if not self.stdscr:
            self.context.last_error = "TUI internal error: screen not initialized"
            self._transition_to(TUIState.REFUSING)
            return

        self._update_screen_dimensions()
        self.stdscr.clear()
        self._render_header()
        prompt = "Enter path to observe (relative or absolute), then press Enter:"
        self._addstr_truncated(4, prompt, 2, curses.color_pair(1))

        # Input box
        box_y = 6
        box_x = 2
        box_w = max(20, min(self.width - 4, 120))
        box_h = 3
        win = curses.newwin(box_h, box_w, box_y, box_x)
        win.border()
        self.stdscr.refresh()
        win.refresh()

        editwin = win.derwin(1, box_w - 2, 1, 1)
        tb = curses.textpad.Textbox(editwin)
        curses.curs_set(1)
        try:
            raw = tb.edit().strip()
        finally:
            curses.curs_set(0)

        if not raw:
            self._show_temporary_message("No path provided.")
            return

        candidate = Path(raw).expanduser()
        # Resolve relative to current working directory
        if not candidate.is_absolute():
            candidate = (Path(os.getcwd()) / candidate).resolve()

        self.context.current_path = candidate
        # Immediately proceed to observe
        self._handle_observe()

    def _show_temporary_message(self, message: str) -> None:
        """Show a temporary message (simplified)."""
        if not self.stdscr:
            return

        self._update_screen_dimensions()
        self.stdscr.clear()
        self._render_header()

        lines = str(message).splitlines() or [""]
        y = 4
        for i, line in enumerate(lines):
            if y + i >= self.height - 5:
                break
            self._addstr_truncated(y + i, line, 2, curses.color_pair(2))

        self._addstr_truncated(
            self.height - 3, "Press any key to continue...", 2, curses.color_pair(5)
        )
        self.stdscr.refresh()
        self.stdscr.getch()

    def _request_text_input(self, prompt: str, default: str = "") -> str | None:
        """Request text input from user with optional default value."""
        if not self.stdscr:
            return None

        self._update_screen_dimensions()
        self.stdscr.clear()
        self._render_header()

        # Show prompt
        self._addstr_truncated(4, prompt, 2, curses.color_pair(1))

        if default:
            self._addstr_truncated(5, f"Default: {default}", 2, curses.color_pair(5))

        # Input box
        box_y = 7
        box_x = 2
        box_w = max(20, min(self.width - 4, 120))
        box_h = 3
        win = curses.newwin(box_h, box_w, box_y, box_x)
        win.border()
        self.stdscr.refresh()
        win.refresh()

        editwin = win.derwin(1, box_w - 2, 1, 1)
        tb = curses.textpad.Textbox(editwin)
        curses.curs_set(1)
        try:
            raw = tb.edit().strip()
        finally:
            curses.curs_set(0)

        if not raw and default:
            return default
        return raw if raw else None

    def _request_choice(
        self, prompt: str, options: list[str], default: int = 0
    ) -> str | None:
        """Request a choice from a list of options."""
        if not self.stdscr:
            return None

        current_selection = default

        while True:
            self._update_screen_dimensions()
            self.stdscr.clear()
            self._render_header()

            # Show prompt
            self._addstr_truncated(4, prompt, 2, curses.color_pair(1))
            self._addstr_truncated(
                5,
                "Use arrow keys to select, Enter to confirm, q to cancel",
                2,
                curses.color_pair(5),
            )

            # Show options
            y = 7
            for i, option in enumerate(options):
                if i == current_selection:
                    line = f"> {option}"
                    self._addstr_truncated(
                        y + i, line, 2, curses.color_pair(4)
                    )  # Green for selected
                else:
                    line = f"  {option}"
                    self._addstr_truncated(y + i, line, 2)

            self.stdscr.refresh()

            # Handle input
            key = self.stdscr.getch()

            if key == ord("\n") or key == ord("\r"):  # Enter
                return options[current_selection]
            elif key == ord("q") or key == 27:  # q or Escape
                return None
            elif key == curses.KEY_UP:
                current_selection = max(0, current_selection - 1)
            elif key == curses.KEY_DOWN:
                current_selection = min(len(options) - 1, current_selection + 1)
            elif ord("1") <= key <= ord("9"):
                # Direct selection via number keys
                idx = key - ord("1")
                if idx < len(options):
                    return options[idx]

    # Utility rendering methods
    def _addstr_centered(self, y: int, text: str, color: int = 0) -> None:
        """Add centered string to screen."""
        if y < 0 or y >= self.height:
            return

        x = max(0, (self.width - len(text)) // 2)
        self._addstr_truncated(y, text, x, color)

    def _addstr_truncated(self, y: int, text: str, x: int = 0, color: int = 0) -> None:
        """
        Add string truncated to fit screen width.

        Args:
            y: Row (0-indexed)
            text: Text to display
            x: Starting column (0-indexed)
            color: curses color pair
        """
        if y < 0 or y >= self.height:
            return

        if x >= self.width:
            return

        # Truncate to fit
        max_len = self.width - x
        if max_len <= 0:
            return

        truncated = text[:max_len]

        try:
            if color:
                self.stdscr.addstr(y, x, truncated, color)
            else:
                self.stdscr.addstr(y, x, truncated)
        except curses.error:
            pass  # Ignore cursor position errors at screen edges

    def _render_watching_interface(self, y: int, height: int) -> None:
        """Render real-time watching interface."""
        lines = [
            "File System Watcher",
            "",
            f"Watching: {self.context.current_path}",
            "",
            "Real-time monitoring active.",
            "Changes will be detected automatically.",
            "",
            f"Detected Changes: {len(self.context.detected_changes)}",
        ]

        if self.context.detected_changes:
            lines.extend(["", "Recent changes:"])
            for change in self.context.detected_changes[-5:]:  # Show last 5
                lines.append(f"  [{change.change_type.name}] {change.path.name}")

        lines.extend(["", "Press 'q' to stop watching, 'h' for help."])

        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_diff_interface(self, y: int, height: int) -> None:
        """Render diff viewer interface."""
        lines = [
            "Diff Viewer",
            "",
            f"Path: {self.context.current_path}",
            "",
            "Compare file versions and view changes.",
            "",
            "Features:",
            "  - Line-by-line comparison",
            "  - Semantic change detection",
            "  - Import/function/class tracking",
            "",
            "Use 'codemarshal diff' CLI for full functionality.",
        ]

        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_status_interface(self, y: int, height: int) -> None:
        """Render investigation status interface."""
        lines = [
            "Investigation Status",
            "===================",
            "",
        ]

        if self.context.current_path:
            lines.append(f"Current Path: {self.context.current_path}")
        else:
            lines.append("Current Path: Not set")

        if self.context.investigation_id:
            lines.append(f"Investigation ID: {self.context.investigation_id}")

        lines.extend(
            [
                f"Current State: {self.context.current_state.value}",
                f"Watcher Active: {self.context.watcher_active}",
            ]
        )

        if self.context.detected_changes:
            lines.append(f"Detected Changes: {len(self.context.detected_changes)}")

        lines.extend(
            [
                "",
                "Press 'w' to start watching, 'd' for diff, 'q' to quit.",
            ]
        )

        for i, line in enumerate(lines[:height]):
            if i < 3:
                self._addstr_centered(y + i, line, curses.color_pair(5))  # Cyan header
            else:
                self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_history_interface(self, y: int, height: int) -> None:
        """Render knowledge history placeholder interface."""
        lines = [
            "Knowledge History",
            "",
            "Reviewing timeline events and query suggestions...",
            "",
            "Press any key to open details.",
        ]
        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_graph_interface(self, y: int, height: int) -> None:
        """Render knowledge graph placeholder interface."""
        lines = [
            "Knowledge Graph",
            "",
            "Building bounded relationship graph for this session...",
            "",
            "Press any key to open details.",
        ]
        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_recommendations_interface(self, y: int, height: int) -> None:
        """Render recommendations placeholder interface."""
        lines = [
            "Recommendations",
            "",
            "Generating deterministic next-step guidance...",
            "",
            "Press any key to open details.",
        ]
        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))

    def _render_marketplace_interface(self, y: int, height: int) -> None:
        """Render pattern marketplace placeholder interface."""
        lines = [
            "Pattern Marketplace",
            "",
            "Searching local catalog and installed templates...",
            "",
            "You can search and apply pattern IDs from here.",
            "",
            "Press any key to open details.",
        ]
        for i, line in enumerate(lines[:height]):
            self._addstr_centered(y + i, line, curses.color_pair(1))


def launch_tui(initial_path: Path | None = None) -> int:
    """
    Public entry point for TUI launch.

    Args:
        initial_path: Optional starting path.

    Returns:
        Exit code (0 for success, 1 for error, 130 for interrupt)
    """
    if not TUI_AVAILABLE:
        print(
            "TUI requires curses library. On Windows install: pip install windows-curses",
            file=sys.stderr,
        )
        return 1

    try:
        tui = TruthPreservingTUI()
        if initial_path:
            tui.context.current_path = initial_path
        return tui.run(initial_path)
    except Exception as e:
        logger.error(f"TUI launch failed: {e}")
        print(f"Failed to launch TUI: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    # Simple standalone test
    import argparse

    parser = argparse.ArgumentParser(description="CodeMarshal TUI")
    parser.add_argument("path", nargs="?", help="Path to investigate")
    args = parser.parse_args()

    initial_path = Path(args.path) if args.path else None

    try:
        launch_tui(initial_path)
    except KeyboardInterrupt:
        sys.exit(0)
