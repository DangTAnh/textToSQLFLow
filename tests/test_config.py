"""Tests for .env loading and API key resolution.

Phase 4: Config Foundation (CFG-01, CFG-02).
"""

import os
import pytest
from pathlib import Path

from text_to_sql_flow.config import (
    _parse_dotenv,
    load_dotenv,
    resolve_api_key,
    AppConfig,
)


class TestParseDotenv:
    def test_parses_simple_key_value(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("FOO=bar\nBAZ=qux")
        parsed = _parse_dotenv(env)
        assert parsed == {"FOO": "bar", "BAZ": "qux"}

    def test_skips_comments_and_blank_lines(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("# this is a comment\n\nKEY=val\n\n# another comment\nFOO=bar")
        parsed = _parse_dotenv(env)
        assert parsed == {"KEY": "val", "FOO": "bar"}

    def test_strips_whitespace(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("  KEY  =  val  ")
        parsed = _parse_dotenv(env)
        assert parsed == {"KEY": "val"}

    def test_handles_quoted_values(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text('KEY="val ue"\nFOO=\'bar baz\'')
        parsed = _parse_dotenv(env)
        assert parsed == {"KEY": "val ue", "FOO": "bar baz"}

    def test_returns_empty_for_missing_file(self, tmp_path):
        parsed = _parse_dotenv(tmp_path / ".nonexistent")
        assert parsed == {}

    def test_handles_equals_in_value(self, tmp_path):
        env = tmp_path / ".env"
        env.write_text("KEY=val=ue")
        parsed = _parse_dotenv(env)
        assert parsed == {"KEY": "val=ue"}


class TestResolveApiKey:
    def test_priority_dotenv_over_env_var(self, tmp_path, monkeypatch):
        """.env value takes priority over system env var."""
        env = tmp_path / ".env"
        env.write_text("OPENAI_API_KEY=from-dotenv")
        monkeypatch.setenv("OPENAI_API_KEY", "from-env")

        # Force reload .env from tmp_path
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("text_to_sql_flow.config._dotenv_values", _parse_dotenv(env))
            mp.setattr("text_to_sql_flow.config._dotenv_loaded", True)
            key = resolve_api_key("openai")
            assert key == "from-dotenv"

    def test_priority_env_over_config(self, monkeypatch):
        """System env var takes priority over config.api_key."""
        monkeypatch.setenv("OPENAI_API_KEY", "from-env")
        config = AppConfig(api_key="from-config")
        # Force empty .env
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("text_to_sql_flow.config._dotenv_values", {})
            mp.setattr("text_to_sql_flow.config._dotenv_loaded", True)
            key = resolve_api_key("openai", config)
            assert key == "from-env"

    def test_priority_config_as_last_fallback(self, monkeypatch):
        """config.api_key is used when .env and env var are absent."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        config = AppConfig(api_key="from-config")
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("text_to_sql_flow.config._dotenv_values", {})
            mp.setattr("text_to_sql_flow.config._dotenv_loaded", True)
            key = resolve_api_key("openai", config)
            assert key == "from-config"

    def test_raises_error_when_no_key_found(self, monkeypatch):
        """ValueError raised when no key is found anywhere."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("text_to_sql_flow.config._dotenv_values", {})
            mp.setattr("text_to_sql_flow.config._dotenv_loaded", True)
            with pytest.raises(ValueError, match="OPENAI_API_KEY"):
                resolve_api_key("openai")

    def test_raises_error_for_unknown_provider(self, monkeypatch):
        """ValueError raised for unknown provider name."""
        with pytest.raises(ValueError, match="Unknown provider"):
            resolve_api_key("nonexistent_provider")


class TestDefaultProvider:
    def test_default_provider_is_opencode(self):
        """Default AppConfig provider is opencode (CFG-02)."""
        config = AppConfig()
        assert config.provider == "opencode"

    def test_opencode_requires_key_like_all_others(self, monkeypatch):
        """opencode raises ValueError when no key is found (needs API key)."""
        monkeypatch.delenv("OPENCODE_API_KEY", raising=False)
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("text_to_sql_flow.config._dotenv_values", {})
            mp.setattr("text_to_sql_flow.config._dotenv_loaded", True)
            with pytest.raises(ValueError, match="OPENCODE_API_KEY"):
                resolve_api_key("opencode")
