# TextToSQLFlow

## What This Is

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM. Người dùng cung cấp mô tả inline, tool gọi LLM (nhiều provider) để sinh cấu trúc luồng SQL ETL, đánh giá chất lượng, tuning nếu cần, và xuất kết quả dưới dạng file JSON + HTML report. Dành cho data engineer muốn tăng năng suất viết SQL ETL.

## Core Value

Data engineer có thể đưa mô tả nghiệp vụ và nhận luồng SQL Spark sẵn sàng chạy, không cần tự viết từng câu SQL.

## Current Milestone: v1.3 — Cải tiến GUI (Terminal UI)

**Goal:** Data engineer có thể quản lý cấu hình và tương tác với tool qua terminal UI trực quan, không cần nhớ CLI flags.

**Target features:**
- Interactive Config Manager: menu-driven TUI để quản lý provider, API key, gateway, preferences
- Enhanced Interactive REPL: multi-description input, provider search, progress visualization, session history
- Lưu cấu hình qua YAML + .env files tự động

## Requirements

### Validated ✅ (v1.0 + v1.1 + v1.2)

Toàn bộ 41 requirements từ v1.0-v1.2 đã hoàn thành. Xem `.planning/REQUIREMENTS.md` và `.planning/ROADMAP.md`.

### Active

- [ ] **CFG-01 → CFG-07**: Interactive Config Manager (Phase 11)
- [ ] **REPL-01 → REPL-06**: Enhanced Interactive REPL (Phase 12)
- [ ] **POL-01 → POL-04**: Polish & Integration (Phase 13)

### Out of Scope

- Giao diện web — CLI + file output, không có web/dashboard
- Chạy trực tiếp SQL trên Spark — chỉ sinh luồng, không execute
- Real-time streaming — batch ETL thuần
- Hỗ trợ database khác ngoài Spark SQL

## Context

- Dự án POC, chưa yêu cầu production-ready
- Dùng Python với thư viện phổ biến (không LangChain/LangGraph)
- Input format mẫu dựa trên cấu trúc JSON tại sample.txt
- Môi trường Windows 11
- **v1.2 complete**: 145 tests, 22 requirements, 4 phases
- **v1.3 starting**: Terminal UI improvements — config manager (Phase 11) first

## Constraints

- **Tech Stack**: Python, CLI, không Web framework
- **LLM**: Hỗ trợ tối thiểu 4 provider (OpenAI, Claude, Deepseek, NVIDIA NIM, OpenRouter, OpenCode)
- **Scope**: POC, không yêu cầu high-availability / production deployment
- **Output**: File-based (JSON + HTML)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python + thư viện phổ biến | POC nhanh, tránh dependency nặng | — Pending |
| Multi LLM provider | Linh hoạt, không lock-in | — Pending |
| CLI + file output | Đơn giản, tập trung vào core logic | — Pending |
| --auto / --interactive flags | Phù hợp cả dev và review workflow | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-07-07 after milestone v1.3 initialization*
