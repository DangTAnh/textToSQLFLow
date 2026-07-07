"""Gateway configuration — loads ``gateway.yaml`` into Pydantic models.

Resolves ``${VAR}`` and ``$VAR`` environment variable placeholders
in YAML string values automatically.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_VAR_RE = re.compile(r"\$\{(\w+)\}|\$(\w+)")


def _resolve_env(value: Any) -> Any:
    """Recursively resolve ``${VAR}`` placeholders in strings."""
    if isinstance(value, str):
        def _repl(m: re.Match) -> str:
            key = m.group(1) or m.group(2)
            resolved = os.environ.get(key, "")
            if not resolved:
                logger.warning("Environment variable %s is not set", key)
            return resolved
        return _VAR_RE.sub(_repl, value)
    if isinstance(value, dict):
        return {k: _resolve_env(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env(v) for v in value]
    return value


class RoutingRule(BaseModel):
    """A routing rule: regex *pattern* maps to *provider/model*."""
    pattern: str
    provider: str
    model: str


class FallbackEntry(BaseModel):
    """Fallback providers for a given primary provider."""
    primary: str
    secondary: list[str]


class RateLimitConfig(BaseModel):
    """Rate limiter settings."""
    enabled: bool = True
    default_rpm: int = 60
    overrides: dict[str, int] = Field(default_factory=dict)


class GatewayConfig(BaseModel):
    """Complete gateway configuration from ``gateway.yaml``."""
    host: str = "0.0.0.0"
    port: int = 8000
    routing: list[RoutingRule] = Field(default_factory=list)
    fallback: dict[str, FallbackEntry] = Field(default_factory=dict)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    cache_ttl: int = 300
    audit_log_path: str = ""
    rbac: dict[str, list[str]] = Field(default_factory=dict)
    providers: dict[str, dict] = Field(default_factory=dict)


def load_gateway_config(path: Optional[Path] = None) -> GatewayConfig:
    """Load gateway configuration from a YAML file.

    All ``${VAR}`` / ``$VAR`` placeholders in string values are resolved
    from environment variables.

    Args:
        path: Path to ``gateway.yaml``. Defaults to ``./gateway.yaml``.

    Returns:
        A validated :class:`GatewayConfig`.
    """
    resolved = path or Path("gateway.yaml")
    if not resolved.exists():
        return GatewayConfig()

    raw = yaml.safe_load(resolved.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return GatewayConfig()

    raw = _resolve_env(raw)
    return GatewayConfig(**raw)
