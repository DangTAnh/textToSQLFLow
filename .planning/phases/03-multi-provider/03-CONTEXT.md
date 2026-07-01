# Phase 3: Multi-Provider & Polish - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Hỗ trợ nhiều LLM provider + HTML report + config file YAML.

Requirements: CLI-03, CLI-04, OUT-02

</domain>

<decisions>
## Implementation Decisions

### Multi-Provider Support
- **CLI-03**: Config file YAML để cấu hình provider, API key, model params. Path mặc định `./text-to-sql-flow.yaml`
- **CLI-04**: CLI flag `--provider` để chọn provider (openai, claude, deepseek, nvidia, openrouter, opencode)
- **Architecture**: Dùng `litellm` làm unified interface cho tất cả provider. LiteLLM handle authentication, retry, rate limiting cho từng provider.
- **Config merge priority**: CLI flag > config file > environment variable > default

### HTML Report
- **OUT-02**: HTML report với Jinja2 template (từ CLAUDE.md stack)
- Template: flow diagram (ASCII/text steps), steps table, evaluation results
- Output alongside JSON: `{flow_name}_report.html`
- `--html` flag optional, mặc định chỉ output JSON

### Module Structure
- `text_to_sql_flow/llm/provider.py` — LLM abstraction layer dùng litellm
- `text_to_sql_flow/config.py` — YAML config loader
- `text_to_sql_flow/output/html_renderer.py` — Jinja2 HTML report renderer
- Update `text_to_sql_flow/cli.py` — Thêm `--provider` và `--html` flag
- Update `text_to_sql_flow/pipeline.py` — Accept provider param, optional HTML output

### Claude's Discretion
- YAML config schema: exact fields, defaults
- HTML template design: layout, components, styling (inline CSS)
- LiteLLM model mapping cho từng provider
- Error handling khi provider không available
- Config file search path

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `text_to_sql_flow/llm/client.py` — Sẽ refactor thành abstraction layer
- `text_to_sql_flow/output/json_writer.py` — Writer pattern để reuse cho HTML
- Pydantic models từ types.py — Flow model data cho HTML report

### Established Patterns
- Lazy import pattern (cli.py imports pipeline inside function body)
- Retry + exponential backoff (client.py)
- Pipeline controller orchestration (pipeline.py)

</code_context>

<specifics>
## Specific Ideas

- litellm hoá ra chỉ cần thay `openai.OpenAI()` bằng `litellm.completion()`
- YAML config: provider, api_key, model_name, temperature, max_tokens
- HTML report: dark theme, inline CSS, steps diagram as ASCII flow
- `--provider` flag: `openai` (default), `claude`, `deepseek`, `nvidia`, `openrouter`, `opencode`
- `--html` flag: generate HTML report alongside JSON
</specifics>

<deferred>
## Deferred Ideas

- Multi-provider evaluation (dùng provider khác để evaluate) — future
- Config hot-reload — not needed for CLI tool
- Provider fallback chain — too complex for POC
</deferred>

---

*Phase: 03-multi-provider*
*Context gathered: 2026-07-01 via smart discuss*
