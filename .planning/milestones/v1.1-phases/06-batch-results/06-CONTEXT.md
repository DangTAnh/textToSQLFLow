# Phase 6: Batch & Results — Context

**Milestone:** v1.1 CLI GUI & UX Improvements
**Requirements:** GUI-05, GUI-06, GUI-07
**Depends on:** Phase 5 (Interactive Mode) ✅
**Status:** Planned → In Progress

## Current State

- Interactive mode has `_show_summary()` + SessionFlow tracking
- No batch mode (process multiple descriptions from file)
- No re-generate flow (re-run with different provider)
- No description persistence in output directories

## Target State

1. **Save description to output** — each output dir has `description.txt`
2. **Batch command** — `text-to-sql-flow batch` reads `.txt` file → gen all → summary
3. **Re-generate** — interactive mode offers "Re-generate?" after main loop

## Files

| File | Change |
|------|--------|
| `text_to_sql_flow/batch.py` | **NEW** — batch processing module |
| `text_to_sql_flow/cli.py` | + `batch` command |
| `text_to_sql_flow/pipeline.py` | + save description.txt alongside output |
| `text_to_sql_flow/interactive.py` | + re-generate step after main loop |
| `tests/test_batch.py` | **NEW** — batch tests |
| `tests/test_interactive.py` | + re-generate tests |
