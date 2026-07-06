# Phase 9: AI GATEWAY — Context

**Gathered:** 2026-07-06
**Status:** Ready for planning
**Mode:** Standard

<domain>
## Phase Boundary

Standalone FastAPI service acting as LLM proxy: routing, fallback, cost tracking, rate limiting, caching, audit logging, RBAC. CLI tool calls gateway instead of LLM directly when `--gateway-url` is set.

Requirements: GW-01 → GW-10

</domain>

<decisions>
## Implementation Decisions

### Location
- `gateway/` directory at repo root (standalone FastAPI service)
- Can import shared types from `text_to_sql_flow` if needed

### Tech Stack
- FastAPI + uvicorn (add to pyproject.toml)
- OpenAI-compatible `/v1/chat/completions` endpoint
- httpx for outbound LLM calls

### Endpoints
- `POST /v1/chat/completions` — main proxy endpoint
- `GET /health` — health check
- `GET /v1/models` — list available models (from config)

### Config (`gateway.yaml`)
- routing: list of pattern → provider/model rules
- fallback: secondary providers per primary
- rate_limit: RPM per provider
- cache: TTL in seconds
- audit: enable/disable + log path
- rbac: API keys → allowed providers

### Key Components
1. Config loader — Pydantic models for gateway.yaml
2. In-memory cache — dict + TTL, no Redis dependency for POC
3. Token bucket rate limiter — per-provider RPM
4. Router — regex match on prompt description → provider
5. Handler — route → primary LLM call (httpx) → fallback on failure → cost log
6. Auth — simple API key check via header (X-API-Key or Authorization: Bearer)

### CLI Integration (GW-10)
- `--gateway-url http://localhost:8000` flag on generate/batch
- When set, provider.py calls gateway endpoint instead of LLM directly
- Falls back to direct LLM call if gateway unreachable (with warning)

### Deferred (POC scope)
- No streaming support
- No Redis (in-memory cache only)
- No persistent audit DB (file-based audit log)
- No HTTPS (reverse proxy handles TLS)
</decisions>
