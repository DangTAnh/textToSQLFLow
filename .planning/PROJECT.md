# TextToSQLFlow

## What This Is

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM. Người dùng cung cấp mô tả inline, tool gọi LLM (nhiều provider) để sinh cấu trúc luồng SQL ETL, đánh giá chất lượng, tuning nếu cần, và xuất kết quả dưới dạng file JSON + HTML report. Dành cho data engineer muốn tăng năng suất viết SQL ETL.

## Core Value

Data engineer có thể đưa mô tả nghiệp vụ và nhận luồng SQL Spark sẵn sàng chạy, không cần tự viết từng câu SQL.

## Current Milestone: v1.1 CLI GUI & UX Improvements

**Goal:** Cải thiện trải nghiệm CLI với giao diện tương tác, hỗ trợ nhập nhiều mô tả, provider mặc định tối ưu, và .env config.

**Target features:**
- CLI GUI (rich-based interactive interface) để nhập nhiều mô tả nghiệp vụ
- Đổi default provider thành `opencode/deepseek-v4-flash-free`
- Hỗ trợ `.env` file để load API key
- Provider switching UI + GUI nhập API key khi chưa có

## Requirements

### Validated ✅ (v1.0)

- **LLM-01**: Người dùng nhập mô tả nghiệp vụ dạng inline (CLI argument) — ✅
- **LLM-02**: Gọi LLM sinh luồng SQL dạng JSON dựa trên mô tả — ✅
- **LLM-03**: Hỗ trợ nhiều LLM provider: OpenAI, Claude, Deepseek, NVIDIA NIM, OpenRouter, OpenCode — ✅
- **LLM-04**: Cấu hình provider qua CLI flag hoặc config file — ✅
- **EVAL-01**: Đánh giá luồng SQL bằng LLM (chất lượng, đúng nghiệp vụ) — ✅
- **EVAL-02**: Tuning luồng dựa trên kết quả đánh giá — ✅
- **EVAL-03**: Loop: nếu chưa OK thì quay lại bước đánh giá — ✅
- **EVAL-04**: Hỗ trợ mode --auto và --interactive — ✅
- **OUT-01**: Xuất kết quả ra file JSON chứa cấu trúc luồng — ✅
- **OUT-02**: Xuất HTML report có sơ đồ luồng và bảng đánh giá — ✅

### Active

- [ ] **GUI-01**: CLI interactive mode cho phép nhập nhiều mô tả nghiệp vụ
- [ ] **GUI-02**: Giao diện chọn provider (danh sách tương tác)
- [ ] **GUI-03**: Form nhập API key inline nếu provider chưa có key
- [ ] **CFG-01**: Load API key từ `.env` file
- [ ] **CFG-02**: Default provider = opencode/deepseek-v4-flash-free

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
*Last updated: 2026-07-01 after milestone v1.1 initialization*
