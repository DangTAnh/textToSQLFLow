"""AI GATEWAY — FastAPI application entry point.

Run with::

    python -m gateway.main
    # or
    uvicorn gateway.main:app --reload
"""

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from gateway.cache import ResponseCache
from gateway.config import load_gateway_config, GatewayConfig
from gateway.llm import route_request, call_llm_with_fallback
from gateway.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    Choice,
    Message,
    Usage,
)
from gateway.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# ── Application state ────────────────────────────────────────────────


class AppState:
    """Shared state for the gateway application."""

    def __init__(self):
        self.config: GatewayConfig = GatewayConfig()
        self.cache: ResponseCache = ResponseCache()
        self.rate_limiter: RateLimiter = RateLimiter()
        self._audit_file: Optional[Path] = None


state = AppState()


# ── Lifespan ─────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: load config, initialise cache, rate limiter, audit log."""
    config_path = Path(os.environ.get("GATEWAY_CONFIG", "gateway.yaml"))
    state.config = load_gateway_config(config_path)
    state.cache = ResponseCache(default_ttl=state.config.cache_ttl)
    state.rate_limiter = RateLimiter(
        default_rpm=state.config.rate_limit.default_rpm,
        overrides=state.config.rate_limit.overrides,
    )
    if state.config.audit_log_path:
        audit = Path(state.config.audit_log_path)
        audit.parent.mkdir(parents=True, exist_ok=True)
        audit.touch(exist_ok=True)
        state._audit_file = audit

    logger.info(
        "Gateway started — %d provider(s), %d routing rule(s), cache TTL=%ds",
        len(state.config.providers),
        len(state.config.routing),
        state.config.cache_ttl,
    )
    yield
    logger.info("Gateway shutting down")


app = FastAPI(
    title="TextToSQLFlow AI GATEWAY",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Helpers ──────────────────────────────────────────────────────────


def _audit_log(request: Request, provider: str, model: str, status: str, cost: float) -> None:
    """Write an audit log line (metadata only — no prompt content)."""
    if not state._audit_file:
        return
    entry = (
        f"{datetime.now(timezone.utc).isoformat()} "
        f"| {request.client.host if request.client else '-'} "
        f"| {provider}/{model} "
        f"| {status} "
        f"| cost=${cost:.6f}\n"
    )
    try:
        state._audit_file.write_text(entry, encoding="utf-8")
    except Exception:
        pass  # fire-and-forget; audit failure shouldn't block


def _check_rbac(request: Request) -> Optional[str]:
    """Check RBAC. Returns the authenticated provider or ``None``.

    Reads ``Authorization: Bearer <key>`` or ``X-API-Key`` header.
    """
    auth = request.headers.get("Authorization", "")
    api_key = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else ""
    if not api_key:
        api_key = request.headers.get("X-API-Key", "")

    if state.config.rbac:
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API key")
        allowed = state.config.rbac.get(api_key, [])
        if not allowed:
            raise HTTPException(status_code=403, detail="Invalid API key")
    return None


# ── Endpoints ────────────────────────────────────────────────────────


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "providers": len(state.config.providers),
        "cache_size": state.cache.size,
        "uptime": "running",
    }


@app.get("/v1/models")
async def list_models():
    """List available models (from routing rules + configured providers)."""
    models: list[dict] = []
    seen: set[str] = set()
    for rule in state.config.routing:
        model_id = f"{rule.provider}/{rule.model}"
        if model_id not in seen:
            seen.add(model_id)
            models.append({"id": model_id, "object": "model", "provider": rule.provider})
    if not models:
        for prov, cfg in state.config.providers.items():
            mid = cfg.get("model", "gpt-4o")
            model_id = f"{prov}/{mid}"
            if model_id not in seen:
                seen.add(model_id)
                models.append({"id": model_id, "object": "model", "provider": prov})
    return {"object": "list", "data": models}


@app.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    request: Request,
):
    """OpenAI-compatible chat completion endpoint."""
    # 1. RBAC
    _check_rbac(request)

    # 2. Cache check
    if not body.stream:
        cached = state.cache.get(body)
        if cached is not None:
            logger.debug("Cache hit")
            return cached.model_dump()

    # 3. Extract forwarded API key (opencode client → gateway → upstream)
    upstream_key = request.headers.get("X-API-Key", "").strip()

    # 4. Route
    provider, model = route_request(state.config, body)

    # 5. Rate limit
    if state.config.rate_limit.enabled:
        allowed, retry_after = state.rate_limiter.check(provider)
        if not allowed:
            headers = {"Retry-After": str(int(retry_after))}
            return JSONResponse(
                status_code=429,
                content={"error": "rate_limit_exceeded", "retry_after": retry_after},
                headers=headers,
            )

    # 6. Call LLM (with fallback)
    try:
        result = call_llm_with_fallback(state.config, provider, model, body, upstream_api_key=upstream_key)
    except RuntimeError as e:
        _audit_log(request, provider, model, "failed", 0.0)
        raise HTTPException(status_code=502, detail=str(e))

    # 6. Build response
    choice = result.response_json["choices"][0]
    usage_raw = result.response_json.get("usage", {})
    response = ChatCompletionResponse(
        id=f"chatcmpl-{uuid.uuid4().hex[:12]}",
        created=int(time.time()),
        model=f"{result.provider}/{result.model}",
        choices=[
            Choice(
                index=0,
                message=Message(
                    role=choice["message"]["role"],
                    content=choice["message"]["content"],
                ),
                finish_reason=choice.get("finish_reason", "stop"),
            )
        ],
        usage=Usage(
            prompt_tokens=usage_raw.get("prompt_tokens", 0),
            completion_tokens=usage_raw.get("completion_tokens", 0),
            total_tokens=usage_raw.get("total_tokens", 0),
        ),
    )

    # 7. Cache
    if not body.stream:
        state.cache.set(body, response)

    # 8. Audit
    _audit_log(request, result.provider, result.model, "success", result.cost)

    logger.info(
        "provider=%s model=%s prompt=%d completion=%d cost=$%.6f",
        result.provider,
        result.model,
        response.usage.prompt_tokens,
        response.usage.completion_tokens,
        result.cost,
    )
    return response.model_dump()


# ── CLI entry point ──────────────────────────────────────────────────


def main():
    """Run the gateway server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    import uvicorn
    uvicorn.run(
        "gateway.main:app",
        host=state.config.host,
        port=state.config.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()
