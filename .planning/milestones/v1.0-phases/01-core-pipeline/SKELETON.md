# Walking Skeleton: TextToSQLFlow Phase 1

**Date:** 2026-07-01
**Mode:** MVP — Walking Skeleton (thinnest end-to-end stack)

---

## Architecture

### System Diagram

```
User: text-to-sql-flow generate "business description" --output ./out
         │
         ▼
  ┌──────────────────┐
  │   CLI (Typer)     │  text_to_sql_flow/cli.py
  │  generate command │  text_to_sql_flow/__main__.py
  └────────┬─────────┘
           │
           ▼
  ┌──────────────────┐
  │ Pipeline Ctrl    │  text_to_sql_flow/pipeline.py
  │ run_generation() │
  └──┬───┬───┬───┬──┘
     │   │   │   │
     ▼   ▼   ▼   ▼
  ┌──┐ ┌──┐ ┌──┐ ┌──┐
  │P │ │LL│ │Pa│ │Wr│
  │ro│ │M │ │rs│ │it│
  │mp│ │Cl│ │er│ │er│
  │t │ │nt│ │  │ │  │
  └──┘ └──┘ └──┘ └──┘
  llm/  llm/  parsers/ output/
  prompts  client  flow_parsr  json_writer
```

### Data Flow

```
Description (str)
  → build_generation_prompt() → (system_prompt, user_prompt)
  → call_llm() → raw response (str)
  → parse_flow_response() → Flow (Pydantic model)
  → write_flow_json() → output.json (file)
```

### Retry Layers

| Layer | Scope | Mechanism | Max Retries |
|-------|-------|-----------|-------------|
| Inner (client.py) | API failure (429, 500) | Exponential backoff + jitter | 3 |
| Outer (pipeline.py) | Malformed JSON | Prompt enhancement with validation error | 3 |

---

## Tech Stack Decisions

| Component | Decision | Rationale |
|-----------|----------|-----------|
| Runtime | Python 3.11+ | Per CLAUDE.md recommendation |
| CLI | Typer 0.12+ | Auto --help, type validation, built on Click |
| Validation | Pydantic v2 | Model schema validation, alias support for `$date` |
| HTTP | httpx 0.27+ | HTTP for LLM API (sync mode for Phase 1) |
| LLM SDK | openai >=1.0 | Direct SDK for single-provider (gpt-4o) |
| Testing | pytest 8.0+ | Standard Python testing |

---

## Directory Layout

```
text_to_sql_flow/
├── __init__.py              # Package marker
├── __main__.py              # python -m entry -> cli.py
├── cli.py                   # Typer CLI (app, generate command)
├── pipeline.py              # Pipeline controller (run_generation)
├── types.py                 # Pydantic models (Flow, Step, StepOutput, Diagram, CreatedDate)
├── llm/
│   ├── __init__.py
│   ├── client.py            # OpenAI client with retry
│   └── prompts.py           # Prompt templates (SYSTEM_PROMPT, build_generation_prompt)
├── parsers/
│   ├── __init__.py
│   └── flow_parser.py       # Flexible JSON extraction from LLM response
└── output/
    ├── __init__.py
    └── json_writer.py       # Write Flow to JSON file
tests/
├── __init__.py
├── test_types.py
├── test_parser.py
├── test_writer.py
└── test_pipeline.py
```

---

## Key Patterns

### Type-First Development
All interfaces are defined as Pydantic models in `types.py` first. Every other module imports from here.

### Lazy CLI Import
The `generate` command imports `pipeline.run_generation` inside the function body, not at module level. This allows the CLI to be importable before the pipeline module exists (important for incremental development).

### Flexible Parsing (Pitfall Prevention)
The parser handles three LLM output formats:
1. Pure JSON (no extra text)
2. JSON wrapped in ```json code blocks
3. JSON with leading/trailing explanatory text

### Double Retry (Pitfall Prevention)
Two independent retry mechanisms:
1. **API retry** in `client.py` — for HTTP/network failures with exponential backoff
2. **Format retry** in `pipeline.py` — for malformed JSON with prompt enhancement feedback

---

## Decisions Made (for Walking Skeleton)

| Decision | Value |
|----------|-------|
| LLM Provider | OpenAI (gpt-4o) only |
| API Key Source | `OPENAI_API_KEY` environment variable |
| LLM Temperature | 0.3 (low for deterministic JSON output) |
| Output File Name | `{flow_name}_flow.json` |
| Output File Format | Pretty-printed JSON (indent=2) |
| Max Generation Retries | 3 |
| Max API Retries | 3 (inside client.py) |
| Default Output Dir | `./output` |

## Decisions Deferred (to later phases)

| Decision | Deferred To | Reason |
|----------|-------------|--------|
| Multi-provider abstraction | Phase 3 | Single provider is simpler for POC |
| Config file (YAML) | Phase 3 | Not needed with single hardcoded provider |
| HTML report | Phase 3 | Jinja2 template not needed yet |
| Evaluation loop | Phase 2 | Separate feature, depends on core pipeline |
| Rich/color terminal output | Phase 2 | Per GEN-06, mapped to Phase 2 |
| Progress bars | Phase 2 | Rich library integration |

---

## Security Constraints

- **API key**: provided via environment variable, never logged or written to output files
- **User input**: separated into `user` message role (not injected into `system` prompt)
- **Output validation**: all LLM output is validated against Pydantic models before writing
- **No SQL execution**: tool generates SQL text only, does not execute on any database

---

*Skeleton established: 2026-07-01*
*Next: Execute Plans 01-03 sequentially, then verify end-to-end.*
