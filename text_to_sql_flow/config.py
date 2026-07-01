"""YAML configuration loader with Pydantic validation.

Loads application settings from a YAML config file with fallback
to environment variables for API keys.

Config merge priority (highest to lowest):
1. CLI flags (set by caller, passed to pipeline)
2. Config file values
3. Environment variables
4. Hard-coded defaults
"""

import os
import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# ── Provider → env var mapping ──────────────────────────────────────────

PROVIDER_ENV_MAP: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "nvidia": "NVIDIA_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "opencode": "OPENCODE_API_KEY",
}

DEFAULT_CONFIG_PATH = Path("./text-to-sql-flow.yaml")


class AppConfig(BaseModel):
    """Application configuration loaded from YAML with env var fallback.

    Attributes:
        provider: LLM provider name (e.g. "openai", "claude").
        api_key: API key — if set, overrides env var lookup.
        model_name: Model override (None = use provider default).
        temperature: LLM temperature (0.0–2.0).
        max_tokens: Max tokens in response (None = provider default).
    """

    provider: str = "openai"
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    temperature: float = Field(default=0.3, ge=0.0, le=2.0)
    max_tokens: Optional[int] = None


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load config from a YAML file, returning defaults if file doesn't exist.

    Args:
        config_path: Path to YAML config. Defaults to ./text-to-sql-flow.yaml.

    Returns:
        Validated AppConfig with values merged from the YAML file (if it
        exists and is readable) over defaults.

    Raises:
        ValueError: If the config file exists but is malformed YAML.
    """
    path = config_path or DEFAULT_CONFIG_PATH

    if not path.exists():
        logger.info("No config file at %s, using defaults", path)
        return AppConfig()

    logger.info("Loading config from %s", path)
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Malformed YAML config file {path}: {e}")

    if not isinstance(data, dict):
        raise ValueError(f"Config file {path} must contain a YAML mapping (dict)")

    return AppConfig(**data)


def resolve_api_key(provider: str, config: Optional[AppConfig] = None) -> str:
    """Resolve the API key for *provider*.

    Priority:
    1. ``config.api_key`` if set (applies to any provider — overrides env).
    2. Provider-specific environment variable (e.g. OPENAI_API_KEY).

    Args:
        provider: Provider name (must be in PROVIDER_ENV_MAP).
        config: Optional AppConfig whose ``api_key`` field is checked first.

    Returns:
        The resolved API key string.

    Raises:
        ValueError: If no key is found in either location.
    """
    if config and config.api_key:
        return config.api_key

    env_var = PROVIDER_ENV_MAP.get(provider)
    if env_var:
        key = os.environ.get(env_var)
        if key:
            return key

    # Give a helpful error listing both possible locations
    env_var_name = PROVIDER_ENV_MAP.get(provider, "<unknown>")
    raise ValueError(
        f"No API key found for provider '{provider}'. "
        f"Set the {env_var_name} environment variable, "
        f"or add api_key to your config file."
    )
