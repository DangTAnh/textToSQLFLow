# Requirements: TextToSQLFlow

**Defined:** 2026-07-01
**Core Value:** Data engineer có thể đưa mô tả nghiệp vụ và nhận luồng SQL Spark sẵn sàng chạy.

## v1 Requirements

### CLI & Configuration

- [ ] **CLI-01**: Tool chạy được qua `python -m text_to_sql_flow` và CLI entry point
- [ ] **CLI-02**: Command `generate` nhận mô tả nghiệp vụ dạng inline argument
- [ ] **CLI-03**: Config file YAML để cấu hình LLM provider, API key, model params
- [ ] **CLI-04**: CLI flag `--provider` để chọn LLM provider (openai, claude, deepseek, nvidia, openrouter, opencode)
- [ ] **CLI-05**: CLI flag `--output` để chỉ định thư mục output

### LLM Generation

- [ ] **GEN-01**: Gọi LLM sinh luồng SQL JSON từ mô tả nghiệp vụ
- [ ] **GEN-02**: System prompt template cho SQL generation
- [ ] **GEN-03**: Parse JSON từ LLM response (flexible: regex extract, fallback)
- [ ] **GEN-04**: Validate JSON output với Pydantic schema (Flow → Steps → Output)
- [ ] **GEN-05**: Retry nếu LLM trả JSON malformed (tối đa 3 lần)
- [ ] **GEN-06**: Progress bar / status output trong terminal

### Evaluation & Loop

- [ ] **EVAL-01**: Đánh giá chất lượng luồng SQL bằng LLM với rubric
- [ ] **EVAL-02**: Score threshold để quyết định pass/fail
- [ ] **EVAL-03**: Tune prompt với feedback từ evaluation
- [ ] **EVAL-04**: Loop: generate → evaluate → tune → re-evaluate (tối đa 5 iterations)
- [ ] **EVAL-05**: CLI flag `--auto` (tự động loop đến khi pass)
- [ ] **EVAL-06**: CLI flag `--interactive` (dừng ở mỗi iteration để review)

### Output

- [ ] **OUT-01**: Xuất JSON chứa cấu trúc luồng (steps, dependencies, output)
- [ ] **OUT-02**: Xuất HTML report có bảng đánh giá

## v2 Requirements

### Multi-Provider

- **MLT-01**: Hỗ trợ OpenAI (GPT-4o)
- **MLT-02**: Hỗ trợ Claude (Sonnet/Opus)
- **MLT-03**: Hỗ trợ Deepseek
- **MLT-04**: Hỗ trợ NVIDIA NIM
- **MLT-05**: Hỗ trợ OpenRouter
- **MLT-06**: Hỗ trợ OpenCode Zen

## Out of Scope

| Feature | Reason |
|---------|--------|
| Chạy SQL trên Spark | POC chỉ sinh luồng, không execute |
| Web UI / Dashboard | CLI-first, HTML report là đủ |
| LangChain / LangGraph | Overhead cho use case này |
| Real-time streaming | Batch ETL thuần |
| Database khác ngoài Spark SQL | Scope hẹp, Spark SQL focus |
| CI/CD pipeline | POC chưa cần |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CLI-01 | Phase 1 | Pending |
| CLI-02 | Phase 1 | Pending |
| CLI-03 | Phase 3 | Pending |
| CLI-04 | Phase 3 | Pending |
| CLI-05 | Phase 1 | Pending |
| GEN-01 | Phase 1 | Pending |
| GEN-02 | Phase 1 | Pending |
| GEN-03 | Phase 1 | Pending |
| GEN-04 | Phase 1 | Pending |
| GEN-05 | Phase 1 | Pending |
| GEN-06 | Phase 2 | Pending |
| EVAL-01 | Phase 2 | Pending |
| EVAL-02 | Phase 2 | Pending |
| EVAL-03 | Phase 2 | Pending |
| EVAL-04 | Phase 2 | Pending |
| EVAL-05 | Phase 2 | Pending |
| EVAL-06 | Phase 2 | Pending |
| OUT-01 | Phase 1 | Pending |
| OUT-02 | Phase 3 | Pending |

**Coverage:**
- v1 requirements: 19 total
- Mapped to phases: 19
- Unmapped: 0 ✓

---
*Requirements defined: 2026-07-01*
*Last updated: 2026-07-01 after initial definition*
