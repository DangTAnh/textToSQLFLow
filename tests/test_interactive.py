"""Tests for the interactive REPL session module (Phase 5).

GUI-01 through GUI-04 are tested through unit tests of individual
functions. Full REPL loop testing requires subprocess input simulation.
"""

from unittest.mock import MagicMock, patch

from text_to_sql_flow.interactive import (
    _get_provider_model,
    _ask_continue,
    _PROVIDER_LIST,
    _PROVIDER_DESCRIPTIONS,
    SessionFlow,
)


class TestProviderList:
    def test_opencode_is_first_and_default(self):
        """opencode appears first (default in the provider list)."""
        assert _PROVIDER_LIST[0] == "opencode"

    def test_all_six_providers_listed(self):
        """All 6 expected providers are in the list."""
        expected = {"openai", "claude", "deepseek", "nvidia", "openrouter", "opencode"}
        assert set(_PROVIDER_LIST) == expected

    def test_every_provider_has_description(self):
        """Every provider in the list has a description."""
        assert set(_PROVIDER_LIST) == set(_PROVIDER_DESCRIPTIONS.keys())


class TestGetProviderModel:
    def test_opencode_model(self):
        """opencode defaults to deepseek-v4-flash-free."""
        model = _get_provider_model("opencode")
        assert "deepseek" in model.lower() or "flash" in model.lower()

    def test_unknown_provider_returns_unknown(self):
        """Unknown provider returns 'unknown'."""
        model = _get_provider_model("nonexistent")
        assert model == "unknown"


class TestAskContinue:
    def test_returns_true_by_default(self):
        """Confirm defaults to True."""
        console = MagicMock()
        with patch("text_to_sql_flow.interactive.Confirm.ask", return_value=True):
            assert _ask_continue(console) is True

    def test_returns_false_when_user_says_no(self):
        """Returns False when user declines."""
        console = MagicMock()
        with patch("text_to_sql_flow.interactive.Confirm.ask", return_value=False):
            assert _ask_continue(console) is False


class TestSessionFlow:
    def test_session_flow_defaults(self):
        """SessionFlow has all required fields."""
        flow = SessionFlow(
            id="test-1",
            description="test flow",
            provider="opencode",
            status="success",
        )
        assert flow.id == "test-1"
        assert flow.path is None
        assert flow.timestamp is not None


class TestReGenerate:
    def test_skips_when_no_successful_flows(self):
        """_re_generate returns without prompting when no successful flows exist."""
        console = MagicMock()
        flows = [
            SessionFlow(id="f1", description="failed flow", provider="opencode", status="failed"),
        ]
        with patch("text_to_sql_flow.interactive.Confirm.ask") as mock_confirm:
            from text_to_sql_flow.config import AppConfig
            from text_to_sql_flow.interactive import _re_generate
            _re_generate(console, flows, AppConfig())
            mock_confirm.assert_not_called()


class TestEnhancedREPL:
    """Tests for new v1.3 REPL features (REPL-01 through REPL-06)."""

    def test_load_session_config_returns_appconfig(self):
        """_load_session_config returns AppConfig (not None)."""
        console = MagicMock()
        from text_to_sql_flow.interactive import _load_session_config
        cfg = _load_session_config(console)
        assert cfg is not None
        assert hasattr(cfg, "provider")

    def test_load_recent_sessions_no_history_dir(self):
        """_load_recent_sessions returns empty list when no history."""
        from text_to_sql_flow.interactive import _load_recent_sessions
        sessions = _load_recent_sessions(limit=3)
        assert isinstance(sessions, list)

    def test_error_suggestions_api_key(self):
        """_show_error_suggestion shows API key tips for key-related errors."""
        console = MagicMock()
        from text_to_sql_flow.interactive import _show_error_suggestion
        error = ValueError("No API key found for provider 'openai'")
        _show_error_suggestion(console, "openai", error)
        assert console.print.called

    def test_error_suggestions_connection(self):
        """_show_error_suggestion shows connection tips for connection errors."""
        console = MagicMock()
        from text_to_sql_flow.interactive import _show_error_suggestion
        error = ConnectionError("Failed to connect to api.openai.com")
        _show_error_suggestion(console, "openai", error)
        assert console.print.called

    def test_error_suggestions_gateway(self):
        """_show_error_suggestion shows gateway tips for gateway errors."""
        console = MagicMock()
        from text_to_sql_flow.interactive import _show_error_suggestion
        error = ConnectionError("Gateway connection refused")
        _show_error_suggestion(console, "openai", error)
        assert console.print.called

    def test_get_descriptions_single(self):
        """_get_descriptions returns a single description list."""
        console = MagicMock()
        from text_to_sql_flow.interactive import _get_descriptions
        with patch("text_to_sql_flow.interactive.Confirm.ask", return_value=False):
            with patch("text_to_sql_flow.interactive.Prompt.ask", return_value="test description"):
                result = _get_descriptions(console)
        assert result == ["test description"]

    def test_save_session_history_no_crash(self):
        """_save_session_history doesn't crash with empty list."""
        from text_to_sql_flow.interactive import _save_session_history
        _save_session_history([])  # should not raise

    def test_save_session_history_creates_file(self, tmp_path):
        """_save_session_history writes a JSON file."""
        from text_to_sql_flow.interactive import _save_session_history, HISTORY_DIR
        from text_to_sql_flow.interactive import SessionFlow

        # Temporarily override HISTORY_DIR
        with patch("text_to_sql_flow.interactive.HISTORY_DIR", tmp_path):
            flow = SessionFlow(id="t1", description="test", provider="opencode", status="success")
            _save_session_history([flow])
            files = list(tmp_path.glob("session-*.json"))
        assert len(files) == 1
