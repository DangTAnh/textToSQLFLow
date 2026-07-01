# Architecture Research

**Domain:** Spark SQL ETL Flow Generation using LLM
**Researched:** 2026-07-01
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLI Layer (Typer)                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  text_to_sql │  │    config    │  │    evaluate / tune       │  │
│  │   command    │  │   command    │  │       commands           │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────────┘  │
├─────────┴─────────────────┴──────────────────────┴─────────────────┤
│                          Core Engine                                 │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                  Pipeline Controller                            │  │
│  │  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │ │
│  │  │ Prompt  │→ │ LLM Call │→ │  Parse   │→ │   Validate   │ │ │
│  │  │ Builder │  │  (retry) │  │ Response │  │  (Pydantic)  │ │ │
│  │  └────┬────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │ │
│  │       │            │             │               │         │ │
│  │  ┌────┴────┐       │      ┌──────┴──────┐        │         │ │
│  │  │ Template│       │      │ JSON Parser  │        │         │ │
│  │  │ (Jinja2)│       │      └─────────────┘        │         │ │
│  │  └─────────┘       └───────────────────────────┘ │         │ │
│  └──────────────────────────────────────────────────┘──────────┘ │
├────────────────────────────────────────────────────────────────────┤
│                       LLM Abstraction Layer                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌────────────┐  │  │
│  │  │ OpenAI  │  │  Claude  │  │ Deepseek  │  │  litellm   │  │  │
│  │  │ Adapter │  │  Adapter │  │  Adapter  │  │  (unified) │  │  │
│  │  └─────────┘  └──────────┘  └───────────┘  └────────────┘  │  │
│  └──────────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────────┤
│                         Output Layer                                 │
│  ┌──────────────┐          ┌──────────────────────────────────┐   │
│  │ JSON Writer  │          │        HTML Report (Jinja2)      │   │
│  └──────────────┘          └──────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| CLI Layer | Parse args, route commands | Typer commands |
| Pipeline Controller | Orchestrate flow: prompt → LLM → parse → validate → evaluate → loop | Python class with state machine |
| Prompt Builder | Build system/user prompt từ business description + schema | Jinja2 template |
| LLM Client | Gọi LLM API với retry | litellm / direct SDK |
| Response Parser | Parse JSON từ LLM response | regex + json.loads |
| Validator | Validate JSON format với schema | Pydantic model |
| Evaluator | Gọi LLM để evaluate quality | LLM prompt với rubric |
| JSON Writer | Ghi output ra file | json.dump |
| HTML Renderer | Render report từ template | Jinja2 |

## Recommended Project Structure

```
text_to_sql_flow/
├── text_to_sql_flow/       # Main package
│   ├── __init__.py
│   ├── __main__.py         # python -m entry
│   ├── cli.py              # Typer CLI definition
│   ├── config.py           # Config loader
│   ├── pipeline.py         # Pipeline controller (gen → eval → loop)
│   ├── types.py            # Pydantic models (Flow, Step, Output, etc.)
│   │
│   ├── llm/                # LLM abstraction
│   │   ├── __init__.py
│   │   ├── client.py       # Abstract base + litellm wrapper
│   │   └── prompts.py      # Prompt templates for gen + eval
│   │
│   ├── parsers/            # Response parsers
│   │   ├── __init__.py
│   │   └── flow_parser.py  # Parse JSON flow from LLM response
│   │
│   └── output/             # Output formatters
│       ├── __init__.py
│       ├── json_writer.py  # JSON file writer
│       └── html_renderer.py# HTML report renderer
│
├── config.yaml             # Default config
├── pyproject.toml          # Project metadata + deps
├── tests/
│   ├── test_pipeline.py
│   ├── test_parser.py
│   └── test_types.py
└── README.md
```

### Structure Rationale

- **CLI tách biệt khỏi core logic:** Dễ test, dễ thêm command mới
- **LLM abstraction layer:** Multi-provider support mà không sửa core logic
- **Pydantic models:** Validation tự động, IDE autocomplete, type safety
- **Parsers tách riêng:** Xử lý LLM output format khác nhau giữa các provider

## Architectural Patterns

### Pattern 1: Pipeline with Feedback Loop

**What:** Core architecture là pipeline có feedback loop. Gen → Eval → (if not OK) → tune prompt → Gen lại.
**When to use:** Mọi flow generation
**Trade-offs:** Simple, dễ debug, loop termination cần guard

**Example:**
```python
def run_pipeline(description: str, max_iterations: int = 3) -> FlowResult:
    for i in range(max_iterations):
        flow = generate_flow(description, previous_attempts)
        evaluation = evaluate_flow(flow, description)
        if evaluation.passed:
            return flow
        description = refine_prompt(description, evaluation.feedback)
    return flow  # best effort after max iterations
```

### Pattern 2: Strategy Pattern for LLM Providers

**What:** Abstract base class cho mỗi LLM provider
**When to use:** Multi-provider support
**Trade-offs:** Thêm abstraction layer, nhưng dễ thêm provider mới

### Pattern 3: Config as Code (YAML)

**What:** Cấu hình provider, model params, prompts trong YAML file
**When to use:** POC muốn flexible config mà không cần DB
**Trade-offs:** Không có hot-reload, cần restart để apply config mới

## Data Flow

### Request Flow

```
User input (CLI arg: "sao kê theo số tài khoản")
    ↓
CLI → Pipeline Controller
    ↓
Prompt Builder → (template + description + schema)
    ↓
LLM Call → raw text response
    ↓
Response Parser → dict
    ↓
Pydantic Validator → FlowModel
    ↓ (if valid)
Evaluator → call LLM với rubric → Score + Feedback
    ↓ (if score < threshold)
Refine prompt với feedback → loop lại LLM Call
    ↓ (if score >= threshold OR max iterations)
JSON Writer → output.json
HTML Renderer → report.html
    ↓
Done ✓
```

### Key Data Flows

1. **Generation:** Description → Prompt → LLM → Raw JSON → Validated FlowModel
2. **Evaluation:** FlowModel + Description → Eval Prompt → LLM → Score + Feedback
3. **Tuning:** Feedback → Enhanced prompt → LLM → Improved FlowModel
4. **Output:** FlowModel → JSON file + HTML report

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| POC (1 user) | Single CLI, sync calls, no state management |
| Team (5-10 users) | Add config profiles, shared prompt templates |
| Enterprise | API service, async queue, result DB |

### Scaling Priorities

1. **POC priority:** Core pipeline hoạt động, 1 provider, output ra file
2. **P1 priority:** Multi-provider support, config, evaluate loop

## Anti-Patterns

### Anti-Pattern 1: Over-abstract LLM từ đầu

**What people do:** Factory pattern, plugin system, dynamic loading cho provider ngay từ iteration 1
**Why it's wrong:** Waste effort, POC cần chạy trước, abstraction sau
**Do this instead:** Bắt đầu với 1 provider cụ thể, refactor ra abstraction khi thêm provider thứ 2

### Anti-Pattern 2: Infinite loop

**What people do:** Loop evaluate → tune không có max iteration guard
**Why it's wrong:** LLM never satisfied, chạy mãi, tốn tokens
**Do this instead:** Max iterations cứng + score threshold dừng sớm

### Anti-Pattern 3: Không validate JSON format

**What people do:** Assume LLM trả về đúng format
**Why it's wrong:** LLM thường trả format lỗi, parse fail → crash
**Do this instead:** Pydantic validate + retry với prompt fix format

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| OpenAI API | REST API (openai SDK) | API key env/config |
| Claude API | REST API (anthropic SDK) | API key env/config |
| Deepseek API | OpenAI-compatible API | Dùng openai SDK với custom base_url |
| NVIDIA NIM | OpenAI-compatible API | Dùng openai SDK với custom base_url |
| OpenRouter | OpenAI-compatible API | Dùng openai SDK với custom base_url |

---
*Architecture research for: TextToSQLFlow*
*Researched: 2026-07-01*
