"""Multi-provider LLM abstraction layer using litellm.

Replaces the hardcoded ``openai.OpenAI()`` client with a unified interface
for all 6 supported providers. Relies on litellm to handle routing,
authentication, and response parsing per provider.

Usage::

    from text_to_sql_flow.llm.provider import call_llm
    text = call_llm("system prompt", "user prompt", provider="claude")
"""

import logging
import time
from typing import Optional

import httpx
import litellm

from text_to_sql_flow.config import AppConfig, resolve_api_key

logger = logging.getLogger(__name__)

# ── Provider → default model ────────────────────────────────────────────

PROVIDER_MODEL_MAP: dict[str, str] = {
    "openai": "gpt-4o",
    "claude": "claude-sonnet-4-20250514",
    "deepseek": "deepseek-chat",
    "nvidia": "nvidia/nemotron-4-340b-instruct",
    "openrouter": "openrouter/auto",
    "opencode": "deepseek-v4-flash-free",
}

MAX_RETRIES = 3


# ── Gateway support (Phase 9) ─────────────────────────────────────────


def call_llm_via_gateway(
    gateway_url: str,
    system_prompt: str,
    user_prompt: str,
    provider: str = "opencode",
    config: Optional[AppConfig] = None,
) -> str:
    """Call the AI GATEWAY instead of LLM directly.

    Args:
        gateway_url: Base URL of the gateway (e.g. ``http://localhost:8000``).
        system_prompt: System-level instruction for the model.
        user_prompt: User message / task description.
        provider: Provider hint (used to choose route on gateway).
        config: Optional AppConfig for temperature/max_tokens overrides.

    Returns:
        The response text content.
    """
    url = f"{gateway_url.rstrip('/')}/v1/chat/completions"
    model_name = PROVIDER_MODEL_MAP.get(provider, provider)
    body = {
        "model": provider,
        "model_name": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.temperature if config else 0.3,
    }
    if config and config.max_tokens:
        body["max_tokens"] = config.max_tokens

    # Forward API key to gateway so it doesn't need its own env copy
    headers = {}
    if config and config.api_key:
        headers["X-API-Key"] = config.api_key
    else:
        try:
            key = resolve_api_key(provider, config)
            if key:
                headers["X-API-Key"] = key
        except ValueError:
            pass

    last_error: Optional[Exception] = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.post(url, json=body, headers=headers, timeout=120.0)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait = (2**attempt) + (time.time() % 1)
                logger.warning(
                    "Gateway call failed (attempt %d/%d): %s. Retrying in %.1fs",
                    attempt + 1, MAX_RETRIES, e, wait,
                )
                time.sleep(wait)

    raise RuntimeError(
        f"Gateway call failed after {MAX_RETRIES} retries: {last_error}"
    )


def call_llm(
    system_prompt: str,
    user_prompt: str,
    provider: str = "opencode",
    config: Optional[AppConfig] = None,
    gateway_url: Optional[str] = None,
) -> str:
    """Call an LLM via litellm with retry and exponential backoff.

    Args:
        system_prompt: System-level instruction for the model.
        user_prompt: User message / task description.
        provider: One of the keys in PROVIDER_MODEL_MAP.
        config: Optional AppConfig for model/temperature overrides.

    Returns:
        The response text content.

    Raises:
        RuntimeError: If all retries are exhausted.
    """
    # Gateway mode: bypass litellm, route through gateway
    if gateway_url:
        return call_llm_via_gateway(
            gateway_url, system_prompt, user_prompt,
            provider=provider, config=config,
        )

    model = PROVIDER_MODEL_MAP.get(provider)
    if not model:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: {', '.join(PROVIDER_MODEL_MAP)}"
        )

    # Config override: model_name takes precedence
    if config and config.model_name:
        model = config.model_name

    # Resolve API key
    api_key = resolve_api_key(provider, config)

    # Build litellm kwargs
    kwargs = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": config.temperature if config else 0.3,
    }
    if api_key:
        kwargs["api_key"] = api_key
    if config and config.max_tokens:
        kwargs["max_tokens"] = config.max_tokens

    # OpenCode Zen uses a custom OpenAI-compatible endpoint
    if provider == "opencode":
        kwargs["model"] = f"openai/{kwargs['model']}"
        kwargs["api_base"] = "https://opencode.ai/zen/v1"

    last_error: Optional[Exception] = None

    for attempt in range(MAX_RETRIES):
        try:
            logger.info(
                "LLM call: provider=%s model=%s attempt=%d/%d",
                provider, model, attempt + 1, MAX_RETRIES,
            )
            response = litellm.completion(**kwargs)
            return response.choices[0].message.content or ""

        except Exception as e:
            last_error = e
            if attempt < MAX_RETRIES - 1:
                wait = (2**attempt) + (time.time() % 1)
                logger.warning(
                    "LLM call failed (attempt %d/%d, provider=%s): %s. "
                    "Retrying in %.1fs",
                    attempt + 1, MAX_RETRIES, provider, e, wait,
                )
                time.sleep(wait)

    raise RuntimeError(
        f"LLM call failed after {MAX_RETRIES} retries "
        f"(provider={provider}, model={model}): {last_error}"
    )
