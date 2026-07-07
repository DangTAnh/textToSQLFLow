"""Tests for the interactive Config Manager module (Phase 11 / v1.3).

CFG-01 through CFG-07 are tested through unit tests of the
ConfigManagerApp and its helper functions.
"""

from unittest.mock import MagicMock, patch, PropertyMock

from text_to_sql_flow.config_manager import (
    ConfigManagerApp,
    run_config_manager,
    _BUILTIN_PROVIDERS,
    PROVIDER_DESCRIPTIONS,
)


class TestConfigManagerApp:
    def test_init_creates_console_and_config(self):
        """ConfigManagerApp initialises with console and loaded config."""
        app = ConfigManagerApp()
        assert app.console is not None
        assert app.config is not None
        assert app._dirty is False

    def test_run_config_manager_calls_app_run(self):
        """run_config_manager() creates an app and calls run()."""
        with patch.object(ConfigManagerApp, "run") as mock_run:
            run_config_manager()
            mock_run.assert_called_once()

    def test_provider_list_all_six(self):
        """All 6 standard providers are in the list."""
        expected = {"openai", "claude", "deepseek", "nvidia", "openrouter", "opencode"}
        assert set(_BUILTIN_PROVIDERS) == expected

    def test_every_provider_has_description(self):
        """Every provider in _BUILTIN_PROVIDERS has a description."""
        assert set(_BUILTIN_PROVIDERS) == set(PROVIDER_DESCRIPTIONS.keys())

    def test_main_menu_renders_without_error(self):
        """Main menu renders and returns a valid choice."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            result = app._main_menu()
        assert result == "0"

    def test_provider_menu_returns_to_main(self):
        """Provider menu exits to main menu on '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app._provider_menu()  # should complete without error

    def test_api_key_menu_returns_to_main(self):
        """API key menu exits to main on '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app._api_key_menu()

    def test_gateway_menu_returns_to_main(self):
        """Gateway menu exits to main on '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app._gateway_menu()

    def test_preferences_menu_returns_to_main(self):
        """Preferences menu exits to main on '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app._preferences_menu()

    def test_config_file_menu_returns_to_main(self):
        """Config file menu exits to main on '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app._config_file_menu()

    def test_dotenv_menu_returns_to_main(self):
        """.env menu exits to main on '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app._dotenv_menu()

    def test_run_exits_cleanly(self):
        """run() exits without error when main menu returns '0'."""
        app = ConfigManagerApp()
        app.console = MagicMock()
        with patch("text_to_sql_flow.config_manager.Prompt.ask", return_value="0"):
            app.run()
