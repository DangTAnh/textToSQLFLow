# Requirements: TextToSQLFlow — Milestone v1.3

**Defined:** 2026-07-07
**Milestone:** Cải tiến GUI — Terminal UI Experience
**Core Value:** Data engineer có thể quản lý cấu hình và tương tác với tool qua terminal UI trực quan, không cần nhớ CLI flags.

## v1.3 Requirements

### Interactive Config Manager (CFG)

- [ ] **CFG-01**: CLI `config` command launches interactive Rich-based config manager TUI với menu-driven interface
- [ ] **CFG-02**: Provider management — xem danh sách providers (6 providers), set default, xem model info mỗi provider
- [ ] **CFG-03**: API key management — xem trạng thái key (có/thiếu) từng provider, set/update/delete keys, test connectivity (gọi LLM thử)
- [ ] **CFG-04**: Gateway configuration — set URL, RBAC key, enable/disable gateway mode, view current gateway status
- [ ] **CFG-05**: Evaluation preferences — default threshold (1.0–10.0), auto/interactive mode default, optimize on/off
- [ ] **CFG-06**: Config file I/O — đọc config từ YAML, write/save changes back to YAML, merge với existing config
- [ ] **CFG-07**: .env file management — xem, thêm, sửa, xoá API keys trong .env qua interactive forms, validation

### Enhanced Interactive REPL (REPL)

- [ ] **REPL-01**: Multi-description bulk input — paste hoặc edit nhiều mô tả cùng lúc trong REPL, generate hàng loạt
- [ ] **REPL-02**: Provider selector nâng cấp — search/filter provider list (type to filter), preview model details, latency info
- [ ] **REPL-03**: Configuration-aware REPL — tự động dùng config từ config manager (default provider, threshold, flags)
- [ ] **REPL-04**: Progress visualization — hiển thị step-by-step progress bars (LLM call → parse → evaluate → optimize) với thời gian ước tính
- [ ] **REPL-05**: Session history persistence — lưu session history ra file JSON, hiển thị lịch sử các session trước, resume lại
- [ ] **REPL-06**: Error display — Rich tracebacks format đẹp, error panels với actionable suggestions (kiểm tra API key, network, config)

### Polish & Integration (POL)

- [ ] **POL-01**: Unit tests cho config manager — CRUD provider, API key, gateway config, file I/O
- [ ] **POL-02**: Unit tests cho enhanced REPL — multi-description, session persistence, config-aware behavior
- [ ] **POL-03**: Documentation — README update với v1.3 features, config manager usage guide, enhanced REPL guide
- [ ] **POL-04**: Edge case handling — empty/missing config, no .env file, provider unavailable, network timeout display

## Out of Scope

| Feature | Reason |
|---------|--------|
| Web UI / Dashboard | CLI-first, web UI deploy riêng nếu cần |
| GUI cho Gateway config | Gateway config qua YAML là đủ, không cần TUI |
| Multi-user support | POC scope, single user |
| Plugin/themes system | Overkill cho terminal UI POC |
| Mobile/remote UI | CLI tool local, không cần remote access |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CFG-01 | Phase 1 | 📝 Planned |
| CFG-02 | Phase 1 | 📝 Planned |
| CFG-03 | Phase 1 | 📝 Planned |
| CFG-04 | Phase 1 | 📝 Planned |
| CFG-05 | Phase 1 | 📝 Planned |
| CFG-06 | Phase 1 | 📝 Planned |
| CFG-07 | Phase 1 | 📝 Planned |
| REPL-01 | Phase 2 | 📝 Planned |
| REPL-02 | Phase 2 | 📝 Planned |
| REPL-03 | Phase 2 | 📝 Planned |
| REPL-04 | Phase 2 | 📝 Planned |
| REPL-05 | Phase 2 | 📝 Planned |
| REPL-06 | Phase 2 | 📝 Planned |
| POL-01 | Phase 3 | 📝 Planned |
| POL-02 | Phase 3 | 📝 Planned |
| POL-03 | Phase 3 | 📝 Planned |
| POL-04 | Phase 3 | 📝 Planned |

**Coverage:**
- v1.3 requirements: 17 total
- Mapped to phases: 17
- Unmapped: 0 ✓

---
*Last updated: 2026-07-07 during v1.3 initialization*
