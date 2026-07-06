# Requirements: TextToSQLFlow — Milestone v1.2

**Defined:** 2026-07-06
**Core Value:** Data engineer có thể đưa mô tả nghiệp vụ + thông tin bảng và nhận luồng SQL Spark tối ưu song song, sẵn sàng chạy.

## v1.2 Requirements

### Table Metadata (TBL)

- [x] **TBL-01**: CLI flag `--tables` / `-t` nhận path đến file JSON chứa table metadata (tên bảng, cột, kiểu, mô tả, khóa, partitions)
- [x] **TBL-02**: CLI flag `--tables` cũng support file DDL (CREATE TABLE statements), tự detect JSON hay DDL dựa trên extension / nội dung
- [x] **TBL-03**: Module `table_metadata/` parse metadata thành Pydantic model (TableMetadata, ColumnMetadata)
- [x] **TBL-04**: Prompt builder kết hợp business description + table metadata để LLM sinh flow chính xác hơn (biết table nào có column gì, join key nào)

### DAG Optimizer (DAG)

- [x] **DAG-01**: Module `dag_optimizer/` phân tích flow DAG, detect các steps có thể chạy song song dựa trên dependency graph
- [x] **DAG-02**: Optimizer tự động điều chỉnh `steps.order` để tối đa parallel execution
- [x] **DAG-03**: Optimizer có thể đề xuất thêm intermediate steps để tận dụng parallelism
- [x] **DAG-04**: CLI flag `--optimize` / `--no-optimize` (mặc định bật)
- [x] **DAG-05**: User có thể review optimization result trước khi accept (interactive mode + batch có flag `--auto`)

### AI GATEWAY (GW)

- [x] **GW-01**: Standalone FastAPI service với endpoint `/v1/chat/completions` (openai-compatible)
- [x] **GW-02**: Routing rules: config map `description_pattern → provider/model`, match bằng regex
- [x] **GW-03**: Provider fallback: nếu primary provider fail, tự động chuyển sang secondary
- [x] **GW-04**: Cost tracking: log số tokens, cost estimate per request, per provider
- [x] **GW-05**: Rate limiting: configurable requests-per-minute per provider
- [x] **GW-06**: Response caching: cache identical prompts, TTL configurable
- [x] **GW-07**: Audit logging: log request/response metadata (không log payload) cho compliance
- [x] **GW-08**: RBAC: API key mapping → allowed providers, rate limit profile
- [x] **GW-09**: Gateway config: YAML file (`gateway.yaml`) với sections: routing, fallback, rate_limit, cache, audit, rbac
- [x] **GW-10**: CLI tool integration: `--gateway-url` flag trỏ đến gateway, tool gọi gateway thay vì LLM trực tiếp

### Integration & Polish (INT)

- [x] **INT-01**: Integration tests: CLI + Optimizer + Gateway end-to-end
- [x] **INT-02**: Docker Compose cho dev (CLI dev + Gateway service)
- [x] **INT-03**: Documentation: README update với v1.2 features, Gateway setup guide

## Out of Scope

| Feature | Reason |
|---------|--------|
| SQLWF integration | Deferred — chờ spec từ team |
| Web UI cho Gateway | CLI + API-first, web UI deploy riêng nếu cần |
| Multi-node Gateway cluster | POC scope, single instance đủ |
| Streaming response | Thêm complexity, batch ETL gen không cần real-time |
| Prompt template customization | v1.1 không có, v1.2 cũng chưa cần |
| Async batch processing | Sync batch đủ cho POC |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TBL-01 | Phase 7 | ✅ Complete |
| TBL-02 | Phase 7 | ✅ Complete |
| TBL-03 | Phase 7 | ✅ Complete |
| TBL-04 | Phase 7 | ✅ Complete |
| DAG-01 | Phase 8 | ✅ Complete |
| DAG-02 | Phase 8 | ✅ Complete |
| DAG-03 | Phase 8 | ✅ Complete |
| DAG-04 | Phase 8 | ✅ Complete |
| DAG-05 | Phase 8 | ✅ Complete |
| GW-01 | Phase 9 | ✅ Complete |
| GW-02 | Phase 9 | ✅ Complete |
| GW-03 | Phase 9 | ✅ Complete |
| GW-04 | Phase 9 | ✅ Complete |
| GW-05 | Phase 9 | ✅ Complete |
| GW-06 | Phase 9 | ✅ Complete |
| GW-07 | Phase 9 | ✅ Complete |
| GW-08 | Phase 9 | ✅ Complete |
| GW-09 | Phase 9 | ✅ Complete |
| GW-10 | Phase 9 | ✅ Complete |
| INT-01 | Phase 10 | ✅ Complete |
| INT-02 | Phase 10 | ✅ Complete |
| INT-03 | Phase 10 | ✅ Complete |

**Coverage:**
- v1.2 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Last updated: 2026-07-06 during v1.2 initialization*
