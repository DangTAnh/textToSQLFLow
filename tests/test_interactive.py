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
