"""Configuration loader with YAML + .env file support.

Loads application settings from a YAML config file with fallback
to .env file, then environment variables for API keys.

Config merge priority (highest to lowest):
1. CLI flags (set by caller, passed to pipeline)
2. .env file values
3. Environment variables
4. Config file (YAML) values
5. Hard-coded defaults

API key resolution priority (highest to lowest):
1. .env file
2. Environment variable
3. Config YAML ``api_key`` field
4. ValueError
"""

import os
import re
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
DEFAULT_DOTENV_PATH = Path("./.env")

# Module-level .env cache — populated once on first access
_dotenv_values: dict[str, str] = {}
_dotenv_loaded: bool = False


def _parse_dotenv(path: Path) -> dict[str, str]:
    """Parse a ``.env`` file and return ``{KEY: VALUE}``.

    Handles:
    - ``KEY=VALUE`` and ``KEY="VALUE"`` / ``KEY='VALUE'``
    - ``#`` comment lines (full-line only)
    - Blank lines
    - Trimming whitespace around key and value
    - Quoted value stripping (surrounding ``"`` / ``'``)

    Does NOT handle:
    - Multiline values (``VALUE="line1\\nline2"``)
    - ``export KEY=VALUE`` syntax
    - Variable interpolation (``KEY=$OTHER``)
    """
    result: dict[str, str] = {}
    if not path.exists():
        return result

    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # Split on first =
        eq = line.find("=")
        if eq == -1:
            continue

        key = line[:eq].strip()
        value = line[eq + 1:].strip()

        # Strip surrounding quotes
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]

        if key:
            result[key] = value

    return result


def load_dotenv(path: Optional[Path] = None) -> dict[str, str]:
    """Load ``.env`` file and return ``{KEY: VALUE}``.

    If *path* is ``None``, defaults to ``./.env`` in the current working
    directory.  The result is cached module-wide so the file is read only
    once per process.
    """
    global _dotenv_values, _dotenv_loaded
    if not _dotenv_loaded:
        _dotenv_values = _parse_dotenv(path or DEFAULT_DOTENV_PATH)
        _dotenv_loaded = True
        count = len(_dotenv_values)
        logger.debug("Loaded %d variable(s) from .env", count)
    return _dotenv_values


class AppConfig(BaseModel):
    """Application configuration loaded from YAML with env var fallback.

    Attributes:
        provider: LLM provider name (e.g. "opencode", "openai").
        api_key: API key — if set, overrides env var lookup.
        model_name: Model override (None = use provider default).
        temperature: LLM temperature (0.0–2.0).
        max_tokens: Max tokens in response (None = provider default).
    """

    provider: str = "opencode"
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

    Priority (highest first):
    1. ``.env`` file (in current working directory)
    2. System environment variable (e.g. ``OPENAI_API_KEY``)
    3. ``config.api_key`` from YAML config
    4. :class:`ValueError`

    Args:
        provider: Provider name (must be in PROVIDER_ENV_MAP).
        config: Optional AppConfig whose ``api_key`` field is checked last.

    Returns:
        The resolved API key string.

    Raises:
        ValueError: If no key is found in any location.
    """
    env_var = PROVIDER_ENV_MAP.get(provider)
    if not env_var:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: {', '.join(PROVIDER_ENV_MAP)}"
        )

    # 1. .env file
    dotenv = load_dotenv()
    key = dotenv.get(env_var)
    if key:
        logger.debug("Resolved %s from .env file", env_var)
        return key

    # 2. System environment variable
    key = os.environ.get(env_var)
    if key:
        logger.debug("Resolved %s from environment variable", env_var)
        return key

    # 3. Config YAML api_key field
    if config and config.api_key:
        logger.debug("Resolved API key from config file")
        return config.api_key

    # 4. Error
    raise ValueError(
        f"No API key found for provider '{provider}'. "
        f"Set {env_var} in your .env file, "
        f"or set the {env_var} environment variable, "
        f"or add api_key to your config file."
    )
