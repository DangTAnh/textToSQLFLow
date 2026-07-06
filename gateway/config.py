"""Gateway configuration — loads ``gateway.yaml`` into Pydantic models."""

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


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
    return GatewayConfig(**raw)
