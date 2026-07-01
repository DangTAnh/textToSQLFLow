# Requirements: TextToSQLFlow — Milestone v1.1

**Defined:** 2026-07-01
**Core Value:** Data engineer có thể đưa mô tả nghiệp vụ và nhận luồng SQL Spark sẵn sàng chạy.

## v1.1 Requirements

### Interactive GUI (GUI)

- [ ] **GUI-01**: CLI interactive mode (rich-based) cho phép nhập nhiều mô tả nghiệp vụ trong 1 session
- [ ] **GUI-02**: Giao diện chọn provider từ danh sách (dùng rich.table / prompt), không cần nhớ --provider flag
- [ ] **GUI-03**: Form nhập API key inline nếu provider chưa có key (.env, env var, config file đều không có)
- [ ] **GUI-04**: REPL loop — sau mỗi lần gen, hỏi user có muốn nhập tiếp hay thoát
- [ ] **GUI-05**: Batch mode — đọc danh sách mô tả từ file text, gen batch tất cả
- [ ] **GUI-06**: Result summary — hiển thị bảng tổng hợp tất cả flow đã gen trong session
- [ ] **GUI-07**: Re-generate — chọn 1 flow cũ để gen lại với provider/config khác

### Configuration (CFG)

- [ ] **CFG-01**: Load API key từ `.env` file, priority: `.env` > environment variable > config YAML
- [ ] **CFG-02**: Đổi default provider thành `opencode/deepseek-v4-flash-free`

## Out of Scope

| Feature | Reason |
|---------|--------|
| Chạy SQL trên Spark | POC chỉ sinh luồng, không execute |
| Web UI / Dashboard | CLI-first, HTML report là đủ |
| LangChain / LangGraph | Overhead cho use case này |
| Real-time streaming | Batch ETL thuần |
| Database khác ngoài Spark SQL | Scope hẹp, Spark SQL focus |
| CI/CD pipeline | POC chưa cần |
| Lưu session history vào file | Đủ dùng trong memory cho POC |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| GUI-01 | Phase 5 | Pending |
| GUI-02 | Phase 5 | Pending |
| GUI-03 | Phase 5 | Pending |
| GUI-04 | Phase 5 | Pending |
| GUI-05 | Phase 6 | Pending |
| GUI-06 | Phase 6 | Pending |
| GUI-07 | Phase 6 | Pending |
| CFG-01 | Phase 4 | Pending |
| CFG-02 | Phase 4 | Pending |

**Coverage:**
- v1.1 requirements: 9 total
- Mapped to phases: 9
- Unmapped: 0 ✓

---
*Last updated: 2026-07-01 after roadmap creation*
