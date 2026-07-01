# Research Summary

**Domain:** Spark SQL ETL Flow Generation using LLM
**Synthesized:** 2026-07-01

## Key Findings

### Stack

- **Python 3.11+** + **Typer** (CLI) + **Pydantic** (validation) + **httpx** (HTTP)
- **litellm** là unified interface cho tất cả LLM provider (OpenAI, Claude, Deepseek, NVIDIA NIM, OpenRouter)
- **Jinja2** cho HTML report, **Rich** cho terminal UX
- **Không dùng** LangChain (overhead), không web framework (CLI-only)

### Table Stakes

- CLI nhập mô tả → Gen luồng JSON → Validate output
- Multi-provider LLM support
- Config provider settings (YAML)
- Rich terminal output

### Differentiators

- Evaluate → tune loop tự động hoặc interactive
- HTML report output
- Auto / Interactive mode flags

### Architecture

- **Pipeline with feedback loop:** Prompt Builder → LLM Call → Parse → Validate → Evaluator → (loop if failed)
- **LLM Abstraction Layer:** Abstract base class strategy pattern
- **Structure:** CLI layer → Core Engine → LLM Abstraction → Output Layer

### Critical Pitfalls

| Pitfall | Prevention |
|---------|------------|
| JSON malformed từ LLM | Flexible parser + retry + Pydantic validation |
| Loop không hội tụ | Max iterations cứng (3-5) + score threshold |
| Provider khác biệt | Prompt tuning riêng + test từng provider |
| Prompt injection | User input isolation + output SQL validation |

## Build Order

1. **Phase 1 — Core Pipeline:** CLI + LLM gen flow + parse + validate + JSON output (single provider)
2. **Phase 2 — Evaluate & Tune:** LLM evaluation + feedback loop + auto/interactive mode
3. **Phase 3 — Multi-Provider & Polish:** Multi-LLM support + HTML report + config

---
*Research synthesized for: TextToSQLFlow*
*Date: 2026-07-01*
