# Plan 03-01: Config & Multi-Provider — Summary

**Phase:** 03-multi-provider
**Plan:** 01
**Status:** ✅ Complete
**Date:** 2026-07-01

## Deliverables

- `text_to_sql_flow/config.py` — YAML config loader with Pydantic validation
- `text_to_sql_flow/llm/provider.py` — litellm-based multi-provider abstraction
- Updated `text_to_sql_flow/llm/__init__.py` — exports `call_llm` from provider
- Updated `pyproject.toml` — added litellm, PyYAML, Jinja2

## Features

- Config merge: CLI flag > config file > env var > default
- 6 providers mapped: openai, claude, deepseek, nvidia, openrouter, opencode
- API key resolution with env var fallback
- Retry with exponential backoff (matching existing client.py pattern)
