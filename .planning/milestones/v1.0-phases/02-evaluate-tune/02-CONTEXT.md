# Phase 2: Evaluate & Tune - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Thêm evaluation loop: LLM đánh giá chất lượng flow với rubric → score < threshold → tune prompt với feedback → re-generate. Auto/interactive mode flags. Progress bar cho CLI.

Requirements: CLI-06, EVAL-01, EVAL-02, EVAL-03, EVAL-04, EVAL-05, EVAL-06

</domain>

<decisions>
## Implementation Decisions

### Evaluation Strategy
- **EVAL-01**: Dùng LLM (OpenAI gpt-4o) để đánh giá flow đầu ra. Evaluator prompt mô tả rubric: correctness, completeness, Spark SQL best practices, dependency correctness.
- **EVAL-02**: Score threshold = 7/10. Score < 7 → tune + regenerate.
- **EVAL-03**: Prompt tuning: append evaluator feedback vào user prompt, yêu cầu LLM sửa lỗi.
- **EVAL-04**: Loop tối đa 5 iterations. Pipeline: generate → evaluate → (if score < threshold) tune prompt → regenerate → evaluate → ...

### CLI & UX
- **CLI-05 (progress bar)**: Dùng thư viện `rich` cho progress bar trong terminal.
- **EVAL-05 (`--auto`)**: Tự động loop đến khi pass. Không cần confirm.
- **EVAL-06 (`--interactive`)**: Dừng ở mỗi iteration, show score + feedback, hỏi user continue/retry/abort.

### Module Structure
- `text_to_sql_flow/evaluator.py` — Evaluation logic: gọi LLM evaluator, parse score + feedback
- Update `text_to_sql_flow/pipeline.py` — Thêm evaluate loop trong `run_generation()`
- Update `text_to_sql_flow/cli.py` — Thêm `--auto` và `--interactive` flags

### Claude's Discretion
- Rubric chi tiết trong evaluator prompt
- Response format: JSON với score + feedback fields
- Progress bar style (Rich progress bar)
- Interactive mode UX: what info to show, what prompts to ask

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `text_to_sql_flow/llm/client.py` — Reuse `call_llm()` cho evaluator calls
- `text_to_sql_flow/pipeline.py` — `run_generation()` kết quả đầu vào cho evaluator
- Pydantic models từ types.py — Flow model để evaluator đánh giá

### Established Patterns
- LLM client pattern: system + user message roles, temperature=0.3, retry 3 lần
- Pipeline controller pattern: function orchestrator với retry logic
- Lazy import pattern cho optional dependencies

</code_context>

<specifics>
## Specific Ideas

- Evaluator prompt đánh giá trên thang 1-10 với 5 dimensions
- Loop dừng khi score >= 7 hoặc max 5 iterations
- --interactive: show score per dimension + LLM feedback text
- Rich progress bar: "Generating... [Evaluating...] [Score: 8/10 ✓]" 
- --auto dùng cho CI / batch mode
</specifics>

<deferred>
## Deferred Ideas

- HTML report có bảng đánh giá → Phase 3
- Multi-provider evaluator → Phase 3
</deferred>

---

*Phase: 02-evaluate-tune*
*Context gathered: 2026-07-01 via smart discuss*
