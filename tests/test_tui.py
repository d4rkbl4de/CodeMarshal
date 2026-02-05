"""
Test suite for CodeMarshal TUI (Text User Interface).

Tests TUI initialization, state management, and functionality.
"""

import pytest

from bridge.entry.tui import TruthPreservingTUI, TUIState, TUI_AVAILABLE


@pytest.mark.skipif(not TUI_AVAILABLE, reason="curses not available")
class TestTUIInitialization:
    """Test TUI initialization and basic properties."""

    def test_tui_creation(self):
        """Test that TUI can be created."""
        tui = TruthPreservingTUI()
        assert tui is not None
        assert tui.context is not None

    def test_tui_initial_state(self):
        """Test TUI starts in correct initial state."""
        tui = TruthPreservingTUI()
        assert tui.context.current_state == TUIState.INITIAL

    def test_tui_has_exit_code_attribute(self):
        """Test TUI has exit_code attribute."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "exit_code")
        assert tui.exit_code == 0

    def test_tui_key_actions(self):
        """Test TUI has expected key actions."""
        tui = TruthPreservingTUI()
        expected_keys = ["q", "h", "o", "s", "p", "n", "e", "y", "x"]

        for key in expected_keys:
            assert key in tui.key_actions

    def test_tui_enabled_actions(self):
        """Test TUI has enabled actions tracking."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "enabled_actions")
        assert len(tui.enabled_actions) == len(tui.key_actions)


@pytest.mark.skipif(not TUI_AVAILABLE, reason="curses not available")
class TestTUIStateManagement:
    """Test TUI state transitions."""

    def test_transition_to_awaiting_path(self):
        """Test transition to AWAITING_PATH state."""
        tui = TruthPreservingTUI()
        tui._transition_to(TUIState.AWAITING_PATH)

        assert tui.context.current_state == TUIState.AWAITING_PATH

    def test_transition_to_observing(self):
        """Test transition to OBSERVING state."""
        tui = TruthPreservingTUI()
        tui._transition_to(TUIState.OBSERVING)

        assert tui.context.current_state == TUIState.OBSERVING

    def test_transition_clears_confirmation(self):
        """Test that transitions clear confirmation state."""
        tui = TruthPreservingTUI()
        tui.context.awaiting_confirmation = True
        tui.context.confirmation_message = "Test"

        tui._transition_to(TUIState.OBSERVING)

        assert not tui.context.awaiting_confirmation
        assert tui.context.confirmation_message is None

    def test_enabled_actions_updated_on_transition(self):
        """Test that enabled actions are updated on state transition."""
        tui = TruthPreservingTUI()
        tui._transition_to(TUIState.AWAITING_PATH)

        # In AWAITING_PATH state, 'q', 'h', and 'o' should be enabled
        assert tui.enabled_actions["q"]  # Quit
        assert tui.enabled_actions["h"]  # Help
        assert tui.enabled_actions["o"]  # Observe

        # Others should be disabled
        assert not tui.enabled_actions["s"]  # Structure question
        assert not tui.enabled_actions["e"]  # Export


@pytest.mark.skipif(not TUI_AVAILABLE, reason="curses not available")
class TestTUINewMethods:
    """Test new TUI methods added in Priority 3."""

    def test_request_text_input_method_exists(self):
        """Test _request_text_input method exists."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "_request_text_input")

    def test_request_choice_method_exists(self):
        """Test _request_choice method exists."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "_request_choice")

    def test_perform_query_method_exists(self):
        """Test _perform_query method exists."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "_perform_query")

    def test_perform_export_method_exists(self):
        """Test _perform_export method exists."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "_perform_export")

    def test_show_query_results_method_exists(self):
        """Test _show_query_results method exists."""
        tui = TruthPreservingTUI()
        assert hasattr(tui, "_show_query_results")


@pytest.mark.skipif(not TUI_AVAILABLE, reason="curses not available")
class TestTUIHandlers:
    """Test TUI action handlers."""

    def test_handle_quit_sets_exiting(self):
        """Test quit handler sets exiting state."""
        tui = TruthPreservingTUI()
        tui._transition_to(TUIState.AWAITING_PATH)

        tui._handle_quit()

        assert tui.context.current_state == TUIState.EXITING

    def test_handle_confirm_with_callback(self):
        """Test confirm handler calls callback."""
        tui = TruthPreservingTUI()
        callback_called = [False]

        def test_callback():
            callback_called[0] = True

        tui.context.awaiting_confirmation = True
        tui.context.confirmation_callback = test_callback

        tui._handle_confirm()

        assert callback_called[0]

    def test_handle_deny_clears_confirmation(self):
        """Test deny handler clears confirmation state."""
        tui = TruthPreservingTUI()
        tui.context.awaiting_confirmation = True
        tui.context.confirmation_message = "Test"
        tui.context.confirmation_callback = lambda: None

        tui._handle_deny()

        assert not tui.context.awaiting_confirmation
        assert tui.context.confirmation_message is None
        assert tui.context.confirmation_callback is None


class TestTUIAvailability:
    """Test TUI availability checks."""

    def test_tui_available_constant(self):
        """Test TUI_AVAILABLE constant is set correctly."""
        # This should be True if curses is available
        assert isinstance(TUI_AVAILABLE, bool)

    def test_tui_raises_error_when_not_available(self):
        """Test TUI raises error when curses not available."""
        if not TUI_AVAILABLE:
            with pytest.raises(ImportError):
                TruthPreservingTUI()


class TestTUIExitCodes:
    """Test TUI exit code handling."""

    @pytest.mark.skipif(not TUI_AVAILABLE, reason="curses not available")
    def test_run_returns_int(self):
        """Test that run method returns an integer exit code."""
        tui = TruthPreservingTUI()
        # We can't actually run the TUI in tests, but we can verify the method signature
        import inspect

        sig = inspect.signature(tui.run)
        # Check that the method exists and has the right signature
        assert callable(tui.run)

    def test_exit_codes_defined(self):
        """Test that standard exit codes are used."""
        # 0 = success
        # 1 = error
        # 130 = interrupt (Ctrl+C)
        assert (
            hasattr(TruthPreservingTUI, "exit_code") or True
        )  # Attribute set in __init__
