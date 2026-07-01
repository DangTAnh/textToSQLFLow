# Phase 1: Core Pipeline - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the core pipeline: CLI entry point that takes business description → calls LLM to generate Spark SQL flow JSON → parses/validates the JSON → writes output to file. Single provider (OpenAI) for now.

Requirements: CLI-01, CLI-02, CLI-05, GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, OUT-01

</domain>

<decisions>
## Implementation Decisions

### CLI & Entry Point
- Typer framework cho CLI (auto --help, type validation)
- `python -m text_to_sql_flow` entry point
- Command: `generate` với argument positional cho mô tả
- Flag `--output` cho thư mục output (mặc định ./output)

### LLM Integration
- OpenAI SDK (openai >=1.0) — single provider trước
- API key từ environment variable OPENAI_API_KEY
- Model: gpt-4o
- Retry với exponential backoff (tối đa 3 lần)

### Project Structure
- Package: `text_to_sql_flow/`
- Modules: cli.py, pipeline.py, types.py, llm/client.py, llm/prompts.py, parsers/flow_parser.py, output/json_writer.py

### JSON Schema & Validation
- Pydantic model: Flow, Step, StepOutput, Diagram
- Schema dựa trên sample.txt structure
- Flexible JSON parser: extract JSON block từ LLM response, fallback nếu có text thừa

### Claude's Discretion
- Prompt template chi tiết
- Error handling cụ thể
- Logging level và format
- Output file naming convention

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- sample.txt chứa mẫu JSON structure của Spark SQL flow

### Established Patterns
- New project — no established patterns yet

### Integration Points
- N/A — Phase 1 là nền tảng

</code_context>

<specifics>
## Specific Ideas

- Mô tả nghiệp vụ nhập dạng CLI argument (positional)
- JSON output format theo chuẩn từ sample.txt

</specifics>

<deferred>
## Deferred Ideas

- Multi-provider support → Phase 3
- HTML report → Phase 3
- Evaluate & tune loop → Phase 2

</deferred>
