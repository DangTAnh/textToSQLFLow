# Milestone Summary: TextToSQLFlow v1.1 — CLI GUI & UX Improvements

**Generated:** 2026-07-06
**Milestone:** v1.1
**Status:** ✅ Complete (all 3 phases, 9/9 requirements)
**Previous Milestone:** v1.0 ✅ (Phases 1-3, 19/19 requirements)

---

## 1. Overview

**TextToSQLFlow** là CLI tool giúp data engineer sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM (6 providers). Milestone **v1.1** tập trung cải thiện UX: .env config, interactive REPL mode, batch processing, và rich CLI interface.

### Core Value

Data engineer đưa mô tả nghiệp vụ → nhận luồng SQL Spark sẵn sàng chạy, không cần tự viết từng câu SQL.

### Key Numbers

| Metric | Value |
|--------|-------|
| Requirements | 9 (v1.1) + 19 (v1.0) = **28 total** |
| Phases | 3 (Phases 4-6) |
| Plans executed | 4 plans |
| Test count | **82 tests** |
| LLM Providers | **6** (OpenAI, Claude, DeepSeek, NVIDIA NIM, OpenRouter, OpenCode) |
| CLI Modes | **3** (generate, interactive, batch) |
| Default provider | opencode/deepseek-v4-flash-free (free tier) |

---

## 2. Architecture

```
User Input (CLI / Interactive / Batch file)
         │
         ▼
┌─────────────────────────────────────────────┐
│              CLI Layer (Typer)                │
│  generate      interactive       batch       │
└──────────┬──────────────────────┬────────────┘
           │                      │
           ▼                      ▼
┌─────────────────────┐  ┌────────────────────┐
│  Pipeline Controller │  │  Interactive REPL   │
│  gen → eval → loop   │  │  (Rich TUI)         │
└──────────┬───────────┘  └──────────┬─────────┘
           │                         │
           ▼                         ▼
┌─────────────────────────────────────────────┐
│           LLM Abstraction (litellm)          │
│  openai  claude  deepseek  nvidia  openrouter│
└──────────┬──────────────────────┬────────────┘
           │                      │
           ▼                      ▼
┌─────────────────────┐  ┌────────────────────┐
│  Output Layer        │  │  Evaluation Engine  │
│  JSON + HTML report  │  │  5-dim rubric       │
└─────────────────────┘  └────────────────────┘
```

### Data Flow

```
Description → Prompt Builder → LLM Call (retry×3) → Parse JSON
  → Pydantic Validate → [Evaluator → score ≥ 7? → loop max 5×]
  → JSON Writer + HTML Renderer → output/
```

### Key Architectural Decisions

| Decision | Rationale |
|----------|-----------|
| **3 CLI modes** (`generate`, `interactive`, `batch`) | Phân tách rõ use case: single-shot, REPL, file batch |
| **Rich-based TUI** (không web framework) | Terminal-native, 0 web dependencies |
| **litellm unified interface** | 6 providers qua 1 API, dễ mở rộng |
| **.env > env var > config YAML priority** | API key resolution chain rõ ràng |
| **Pydantic validation** | Schema enforcement cho JSON flow output |
| **Double retry** (API × format) | API failure + malformed JSON handled riêng |

---

## 3. Phases

### ✅ Milestone v1.0 (Completed)

#### Phase 1: Core Pipeline
- **Requirements:** CLI-01, CLI-02, CLI-05, GEN-01 → GEN-05, OUT-01 (9 reqs)
- **Deliverables:** Typer CLI, Pydantic types, LLM client (OpenAI), JSON parser, pipeline controller, JSON writer
- **Walking Skeleton:** CLI nhận mô tả → LLM gen flow → parse/validate → JSON output
- **Patterns:** Lazy CLI import, type-first development, flexible JSON parsing (3 formats)

#### Phase 2: Evaluate & Tune
- **Requirements:** CLI-06, EVAL-01 → EVAL-06 (6 reqs)
- **Deliverables:** Evaluator module (5-dim rubric), pipeline eval loop, `--auto`/`--interactive` flags
- **Tests:** 16 tests added (total: 49)
- **Threshold:** 7.0/10, max 5 iterations

#### Phase 3: Multi-Provider & Polish
- **Requirements:** CLI-03, CLI-04, OUT-02 (3 reqs)
- **Deliverables:** litellm provider abstraction (6 providers), YAML config, Jinja2 HTML report (dark theme)
- **CLI flags:** `--provider`, `--config`, `--html`

### ✅ Milestone v1.1 (This Summary)

#### Phase 4: Config Foundation ✅
- **Requirements:** CFG-01, CFG-02
- **Deliverables:** Manual `.env` parser (no python-dotenv), `resolve_api_key()` priority update, default provider → `opencode`
- **Files:** Modified 5 files, created `tests/test_config.py`
- **Key decision:** Manual .env parsing (0 dependencies, POC-acceptable)

#### Phase 5: Interactive Mode ✅
- **Requirements:** GUI-01, GUI-02, GUI-03, GUI-04
- **Deliverables:** `text_to_sql_flow/interactive.py`, `interactive` CLI command, Rich provider selection table, inline API key input, REPL loop
- **UX Features:** Provider list với descriptions, inline API key form (nếu thiếu), continue/exit prompt sau mỗi flow

#### Phase 6: Batch & Results ✅
- **Requirements:** GUI-05, GUI-06, GUI-07
- **Deliverables:** `text_to_sql_flow/batch.py`, `batch` CLI command, result summary table, re-generate flow từ session history
- **Features:** Batch từ .txt file (1 description/line), session summary hiển thị tất cả flows (ID, description, provider, status, timestamp)

---

## 4. Decisions Made

| Decision | Value | Phase | Rationale |
|----------|-------|-------|-----------|
| Default provider | opencode/deepseek-v4-flash-free | 4 | Free tier, no key needed for basic usage |
| .env parser | Manual (no python-dotenv) | 4 | 0 extra deps, POC scope |
| Session persistence | Memory-only | 5 | No file persistence until proven needed |
| TUI framework | Rich (not web) | 5 | Terminal-native, matches CLI-first strategy |
| API key priority | .env > env var > YAML > error | 4 | User expectation alignment |
| Generator retry | 3× API + 3× format | 1 | Double retry for API failure + malformed JSON |
| Evaluation threshold | 7.0 / 10 | 2 | Pass with margin, adjustable via flag |
| Max eval iterations | 5 | 2 | Cost guard, best-effort after limit |
| Eval provider | Same as generator (gpt-4o) | 2 | Simpler than cross-provider eval |
| No LangChain | Avoided entirely | 1 | Overhead > benefit for this use case |

---

## 5. Requirements Coverage

| Req | Description | Phase | Status |
|-----|-------------|-------|--------|
| CLI-01 | CLI entry point `text-to-sql-flow` | 1 | ✅ |
| CLI-02 | `generate` command với description positional arg | 1 | ✅ |
| CLI-03 | Config file support (YAML) | 3 | ✅ |
| CLI-04 | `--provider` flag | 3 | ✅ |
| CLI-05 | `--output` flag | 1 | ✅ |
| CLI-06 | `--auto` / `--interactive` flags | 2 | ✅ |
| GEN-01 | LLM gọi để gen Spark SQL flow | 1 | ✅ |
| GEN-02 | Prompt template cho gen flow | 1 | ✅ |
| GEN-03 | Flexible JSON parser (pure JSON / code block / text) | 1 | ✅ |
| GEN-04 | Pydantic validation (Flow, Step, StepOutput, Diagram) | 1 | ✅ |
| GEN-05 | Retry: API failure (3×) + malformed JSON (3×) | 1 | ✅ |
| EVAL-01 | LLM evaluator với rubric (5 dimensions) | 2 | ✅ |
| EVAL-02 | Score threshold + regenerate nếu fail | 2 | ✅ |
| EVAL-03 | Loop max 5 iterations | 2 | ✅ |
| EVAL-04 | Prompt tuning với feedback | 2 | ✅ |
| EVAL-05 | `--auto` mode (không cần confirm) | 2 | ✅ |
| EVAL-06 | `--interactive` mode (stop per iteration) | 2 | ✅ |
| OUT-01 | JSON output file (`{flow_name}_flow.json`) | 1 | ✅ |
| OUT-02 | HTML report (Jinja2, dark theme) | 3 | ✅ |
| CFG-01 | .env file loading (manual parse) | 4 | ✅ |
| CFG-02 | Default provider = opencode | 4 | ✅ |
| GUI-01 | Interactive mode (nhiều mô tả trong 1 session) | 5 | ✅ |
| GUI-02 | Provider selection UI (Rich table) | 5 | ✅ |
| GUI-03 | Inline API key input khi thiếu | 5 | ✅ |
| GUI-04 | REPL loop (generate → continue/exit) | 5 | ✅ |
| GUI-05 | Batch mode (file → gen all → summary) | 6 | ✅ |
| GUI-06 | Result summary table | 6 | ✅ |
| GUI-07 | Re-generate flow cũ với provider khác | 6 | ✅ |

**Total: 28/28 requirements covered ✅**

---

## 6. Tech Debt & Known Gaps

| Item | Severity | Notes | When to Address |
|------|----------|-------|-----------------|
| Manual .env parser (edge cases) | Low | Quoted `#` values, multiline not handled | v2.0 (if needed) |
| No session persistence | Low | History in memory only, lost on exit | v2.0 (if requested) |
| Eval provider = gen provider | Low | Cross-provider eval would be more objective | v2.0 |
| No async support | Low | Sync httpx, fine for single-user CLI | v2.0 (if latency matters) |
| No provider fallback chain | Low | Fail-fast if provider unavailable | v2.0 |
| No CI/CD pipeline | Low | POC scope, manual test run | v2.0 |
| No cache for LLM responses | Low | Same prompt → same cost each time | v2.0 (if iterating heavily) |

### Pitfalls Identified & Mitigated

| Pitfall | Mitigation | Phase |
|---------|------------|-------|
| JSON malformed from LLM | Flexible parser + Pydantic + retry×3 | 1 |
| Loop not converging | Max 5 iterations + best-effort return | 2 |
| Provider output differences | litellm abstraction, model-specific tuning | 3 |
| Prompt injection | User input in user message (not system), SQL output validation | 1 |

---

## 7. Getting Started

### Prerequisites

```bash
# Python 3.11+
pip install -e .
# hoặc
uv sync
```

### Basic Usage

```bash
# Single generation
python -m text_to_sql_flow generate "ETL xử lý sao kê ngân hàng" --output ./output

# Interactive mode (recommended)
python -m text_to_sql_flow interactive

# Batch mode
python -m text_to_sql_flow batch descriptions.txt

# With specific provider + HTML report
python -m text_to_sql_flow generate "..." --provider claude --html
```

### Project Structure

```
text_to_sql_flow/
├── __main__.py          # Entry point
├── cli.py               # Typer CLI (3 commands)
├── pipeline.py          # Pipeline controller
├── evaluator.py         # 5-dim quality evaluation
├── config.py            # .env + YAML config
├── types.py             # Pydantic models
├── interactive.py       # REPL mode (v1.1)
├── batch.py             # Batch mode (v1.1)
├── llm/
│   ├── provider.py      # litellm multi-provider
│   └── prompts.py       # System/user prompts
├── parsers/
│   └── flow_parser.py
└── output/
    ├── json_writer.py
    └── html_renderer.py
tests/                   # 82 tests total
```

### Key Files

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Project conventions, tech stack, workflow rules |
| `.planning/ROADMAP.md` | Full roadmap: 6 phases, 28 requirements |
| `.planning/STATE.md` | Current project state |
| `.planning/reports/MILESTONE_SUMMARY-v1.1.md` | This document |

---

## 8. Next Steps (Post-v1.1)

The project has completed both v1.0 and v1.1 milestones. Potential future directions:

1. **Session persistence** — save history to file for cross-session re-gen
2. **Cross-provider evaluation** — use different provider for eval vs gen
3. **LLM response caching** — avoid re-calling for identical prompts
4. **Provider fallback chain** — auto-failover when primary provider unavailable
5. **Async support** — parallel batch processing, non-blocking UX
6. **Prompt template customization** — user-defined templates per domain

---

*Milestone summary generated from: ROADMAP.md, PROJECT.md, REQUIREMENTS.md, STATE.md, phase CONTEXT files (6 phases), phase SUMMARY files (6 plans), research artifacts (5 files), README.md*
