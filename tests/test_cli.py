"""Tests for CLI flag parsing and help output.

Uses subprocess to invoke the CLI (since CliRunner has compat issues
with Typer 0.20.x). Evaluator/pipeline functions are tested in their
own test files.
"""

import subprocess
import sys
from pathlib import Path


class TestGenerateHelp:
    def test_generate_help_shows_new_flags(self):
        """--help output includes --auto and --interactive."""
        result = subprocess.run(
            [sys.executable, "-m", "text_to_sql_flow", "generate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--auto" in result.stdout
        assert "--interactive" in result.stdout


class TestCliImport:
    def test_cli_module_imports(self):
        """CLI module can be imported without error."""
        result = subprocess.run(
            [sys.executable, "-c", "from text_to_sql_flow.cli import app; print('OK')"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "OK" in result.stdout

    def test_cli_app_has_generate_command(self):
        """App has a generate command."""
        from text_to_sql_flow.cli import app

        # Verify the command is registered (name is None for auto-generated, check callback)
        assert any(
            cmd.callback and cmd.callback.__name__ == "generate"
            for cmd in app.registered_commands
        )

    def test_cli_app_has_interactive_command(self):
        """App has an interactive command."""
        from text_to_sql_flow.cli import app

        assert any(
            cmd.callback and cmd.callback.__name__ == "interactive"
            for cmd in app.registered_commands
        )

    def test_interactive_help_shows(self):
        """--help for interactive shows the command description."""
        import subprocess, sys

        result = subprocess.run(
            [sys.executable, "-m", "text_to_sql_flow", "interactive", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "interactive" in result.stdout.lower()

    def test_cli_app_has_batch_command(self):
        """App has a batch command."""
        from text_to_sql_flow.cli import app

        assert any(
            cmd.callback and cmd.callback.__name__ == "batch"
            for cmd in app.registered_commands
        )

    def test_batch_help_shows(self):
        """--help for batch shows the command description."""
        import subprocess, sys

        result = subprocess.run(
            [sys.executable, "-m", "text_to_sql_flow", "batch", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "batch" in result.stdout.lower()
