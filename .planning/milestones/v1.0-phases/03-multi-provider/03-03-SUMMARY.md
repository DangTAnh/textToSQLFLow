# Plan 03-03: Wire CLI & Pipeline — Summary

**Phase:** 03-multi-provider
**Plan:** 03
**Status:** ✅ Complete
**Date:** 2026-07-01

## Deliverables

- Updated `text_to_sql_flow/cli.py` — --provider, --config, --html flags
- Updated `text_to_sql_flow/pipeline.py` — multi-provider call_llm, optional HTML

## Flags Added

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| --provider / -p | choice | openai | openai, claude, deepseek, nvidia, openrouter, opencode |
| --config / -c | path | None | YAML config file path |
| --html | flag | False | Generate HTML report alongside JSON |
