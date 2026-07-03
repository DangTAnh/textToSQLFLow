# Phase 5: Interactive Mode — Context

**Milestone:** v1.1 CLI GUI & UX Improvements
**Requirements:** GUI-01, GUI-02, GUI-03, GUI-04
**Depends on:** Phase 4 (Config Foundation) ✅
**Status:** Planned → In Progress

## Current State

- CLI only supports `generate` command with flags (--provider, --config, etc.)
- No interactive REPL session
- Provider selection requires knowing provider name strings
- API key resolution raises ValueError if missing

## Target State

- New `interactive` CLI command
- Rich.table provider selection with descriptions
- Inline API key input when missing
- REPL loop: generate → evaluate → continue prompt
- Session summary on exit

## Files

| File | Change |
|------|--------|
| `text_to_sql_flow/interactive.py` | **NEW** — main interactive session logic |
| `text_to_sql_flow/cli.py` | + `interactive` command |
| `text_to_sql_flow/pipeline.py` | + optional `config` override param |
