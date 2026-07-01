# Plan 02-02: Pipeline + CLI Evaluation Loop — Summary

**Phase:** 02-evaluate-tune
**Plan:** 02
**Status:** 🛑 Blocked (awaiting user verification)
**Date:** 2026-07-01

## Deliverables

- Updated `text_to_sql_flow/pipeline.py` — `run_evaluation_loop()` added
- Updated `text_to_sql_flow/cli.py` — `--auto`/`--interactive` flags + Rich console
- Updated `pyproject.toml` — `rich>=13.0` dependency

## Changes

1. **pipeline.py**: Added `run_evaluation_loop()` with generate → evaluate → tune cycle, helpers `_tune_prompt()`, `_show_interactive_prompt()`, `_get_interactive_action()`
2. **cli.py**: Added `--auto` and `--interactive` flags, Rich console.status() spinner, backward-compatible single-generation path
3. **pyproject.toml**: Added `rich>=13.0`

## Verification

- `run_generation()` still importable (backward compatible): ✅
- `run_evaluation_loop()` importable: ✅
- CLI help shows `--auto` and `--interactive`: ✅
- All imports work: ✅

## Blocking Checkpoint

Requires human verification of interactive/auto mode. See below.
