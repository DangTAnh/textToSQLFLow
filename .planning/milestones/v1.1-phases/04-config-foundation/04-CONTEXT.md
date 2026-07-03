# Phase 4: Config Foundation — Context

**Milestone:** v1.1 CLI GUI & UX Improvements
**Requirements:** CFG-01, CFG-02
**Depends on:** Phase 3 (Multi-Provider & Polish)
**Status:** Planned → In Progress

## Current State

- `config.py` has YAML loader + `resolve_api_key()` but NO `.env` support
- Default provider = `"openai"` across 5 files (config, cli, pipeline, evaluator, provider)
- `resolve_api_key()` priority: config.api_key > env var
- No `python-dotenv` dependency (manual parse chosen)
- `PROVIDER_ENV_MAP` maps providers to env var names

## Target State

1. `.env` file loader (manual parse) with priority: `.env` > env var > config YAML > error
2. Default provider = `"opencode"` (maps to `deepseek-v4-flash-free` which is free, no key needed)
3. All default provider strings updated across codebase

## Key Decisions

- Manual `.env` parsing (no python-dotenv dependency) — confirmed by user
- Priority chain: `.env` > os.environ > config.api_key > error
- Default provider: `opencode` (deepseek-v4-flash-free, free tier)

## Files to Modify

| File | Changes |
|------|---------|
| `config.py` | + `load_dotenv()`, `_parse_dotenv()`, update `resolve_api_key()` priority |
| `cli.py` | Default provider → `opencode` |
| `pipeline.py` | Default provider → `opencode` (2 funcs) |
| `llm/provider.py` | Default provider → `opencode` |
| `evaluator.py` | Default provider → `opencode` |
| `tests/test_config.py` | New test file for `.env` loading |

## Risks

- Manual parse misses edge cases (quoted values with `#`, multiline) — acceptable for POC
- Default provider change may break existing tests that assume "openai" — check and fix
