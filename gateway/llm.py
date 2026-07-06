"""LLM provider calling — routing, fallback, cost estimation."""

import logging
import re
import time
from typing import Optional

import httpx

from gateway.config import GatewayConfig
from gateway.models import ChatCompletionRequest, Message

logger = logging.getLogger(__name__)


# ── Routing ──────────────────────────────────────────────────────────


def route_request(
    config: GatewayConfig,
    request: ChatCompletionRequest,
) -> tuple[str, str]:
    """Match the request against routing rules.

    Uses the first user message's content for pattern matching.
    Falls back to the first configured provider + model if no rule matches.

    Returns:
        ``(provider_name, model_name)``
    """
    prompt_text = ""
    for msg in request.messages:
        if msg.role == "user":
            prompt_text = msg.content
            break

    for rule in config.routing:
        if re.search(rule.pattern, prompt_text, re.IGNORECASE):
            logger.debug("Routed to %s/%s (pattern=%s)", rule.provider, rule.model, rule.pattern)
            return rule.provider, rule.model

    # Default: first configured provider
    default_provider = next(iter(config.providers.keys()), "opencode")
    default_model = request.model
    logger.debug("No routing match, using default %s/%s", default_provider, default_model)
    return default_provider, default_model


# ── LLM calling ──────────────────────────────────────────────────────


def _build_headers(api_key: str) -> dict:
    if api_key.startswith("Bearer "):
        return {"Authorization": api_key}
    return {"Authorization": f"Bearer {api_key}"}


def _call_upstream(
    api_key: str,
    base_url: str,
    model: str,
    messages: list[Message],
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> dict:
    """Call an OpenAI-compatible upstream LLM API.

    Returns the raw JSON response dict.
    """
    url = f"{base_url.rstrip('/')}/chat/completions"
    body = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    resp = httpx.post(
        url,
        headers=_build_headers(api_key),
        json=body,
        timeout=120.0,
    )
    resp.raise_for_status()
    return resp.json()


def _estimate_cost(response_json: dict, model: str = "") -> float:
    """Rough cost estimate in USD based on token counts and model.

    Uses approximate rates per-1K tokens. Returns 0.0 if unknown.
    """
    usage = response_json.get("usage", {})
    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    # Approximate rates (input / output per 1K tokens)
    RATES = {
        "gpt-4o": (0.0025, 0.01),
        "gpt-4o-mini": (0.00015, 0.0006),
        "claude-sonnet-4": (0.003, 0.015),
        "claude-haiku-4": (0.00025, 0.00125),
        "deepseek-chat": (0.00027, 0.0011),
    }
    rate = RATES.get(model, (0.001, 0.002))
    return (prompt_tokens / 1000 * rate[0]) + (completion_tokens / 1000 * rate[1])


# ── Call with fallback ───────────────────────────────────────────────


class LLMResult:
    """Result of an LLM call through the gateway."""
    def __init__(self, response_json: dict, provider: str, model: str, cost: float):
        self.response_json = response_json
        self.provider = provider
        self.model = model
        self.cost = cost


def call_llm_with_fallback(
    config: GatewayConfig,
    provider: str,
    model: str,
    request: ChatCompletionRequest,
) -> LLMResult:
    """Call an LLM provider with automatic fallback on failure.

    Tries the primary provider first. If it fails, tries each secondary
    in order. Raises the last error if all fail.
    """
    provider_config = config.providers.get(provider, {})
    api_key = provider_config.get("api_key", "")
    base_url = provider_config.get("base_url", "https://api.openai.com/v1")

    def _attempt(prov: str, mdl: str) -> LLMResult:
        cfg = config.providers.get(prov, {})
        resp = _call_upstream(
            api_key=cfg.get("api_key", api_key),
            base_url=cfg.get("base_url", "https://api.openai.com/v1"),
            model=mdl,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        cost = _estimate_cost(resp, model=mdl)
        return LLMResult(resp, prov, mdl, cost)

    # Primary
    try:
        return _attempt(provider, model)
    except Exception as exc:
        logger.warning("Primary provider %s failed: %s", provider, exc)

    # Fallback chain
    fallback = config.fallback.get(provider)
    if fallback and fallback.secondary:
        for fb in fallback.secondary:
            try:
                logger.info("Falling back to %s", fb)
                fb_cfg = config.providers.get(fb, {})
                fb_model = fb_cfg.get("model", model)
                return _attempt(fb, fb_model)
            except Exception as fb_exc:
                logger.warning("Fallback %s also failed: %s", fb, fb_exc)
                continue

    raise RuntimeError(
        f"All providers failed for routing target {provider}/{model}"
    )
