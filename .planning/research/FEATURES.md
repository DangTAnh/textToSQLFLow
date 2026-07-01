# Feature Research

**Domain:** Spark SQL ETL Flow Generation using LLM
**Researched:** 2026-07-01
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| CLI nhập mô tả nghiệp vụ | Cần input để gen luồng | LOW | Argument positional hoặc --description |
| Gen luồng SQL dạng JSON | Output cốt lõi của tool | MEDIUM | Parser JSON từ LLM response |
| Validate cấu trúc JSON đầu ra | Đảm bảo đúng format flow | MEDIUM | Pydantic schema validation |
| Multi-provider LLM support | Không muốn lock-in 1 provider | MEDIUM | Abstraction layer qua litellm |
| Config provider settings | API key, model name, params | LOW | YAML config file |
| Rich terminal output | UX cho data engineer | LOW | Progress bar, color output |

### Differentiators (Competitive Advantage)

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Evaluate → tune loop | Quality improvement qua iteration | HIGH | LLM gọi lại để self-evaluate |
| HTML report | Visual review cho non-technical stakeholders | MEDIUM | Jinja2 template |
| --auto mode chạy tự động | Không cần can thiệp tay | MEDIUM | Loop controller logic |
| --interactive mode | Review từng bước, manual control | MEDIUM | Confirm prompts |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Execute SQL trên Spark | "Muốn chạy luôn" | POC scope, thêm dependency nặng, Spark setup | Export file, user tự chạy |
| Web UI dashboard | "Nhìn cho trực quan" | Overhead frontend, maintain 2 codebase | HTML report đơn giản |
| Auto-deploy pipeline | "Production-ready" | POC chưa cần CI/CD | Commit file là đủ |

## Feature Dependencies

```
Mô tả nghiệp vụ
    └──requires──> LLM Provider Config
                       └──requires──> API Key / Config file

Gen luồng JSON
    └──requires──> Multi-Provider LLM Client
                       └──requires──> HTTP Client (httpx)

Validate Output
    └──requires──> Pydantic Schema

Đánh giá chất lượng (Evaluate)
    └──requires──> Gen luồng JSON (có output để đánh giá)

Tune loop
    └──requires──> Đánh giá chất lượng + Gen luồng

Auto mode
    └──requires──> Tune loop (gọi lại tự động)

HTML Report
    └──requires──> Output JSON (có data để render)
```

### Dependency Notes

- **Gen luồng cần LLM client:** Không thể gen nếu chưa có provider config
- **Evaluate cần gen luồng:** Phải có output trước khi đánh giá
- **Auto mode cần tune loop:** Loop là core logic, auto mode là wrapper
- **HTML report độc lập:** Có thể phát triển song song với core logic

## MVP Definition

### Launch With (v1)

- [x] CLI nhập mô tả nghiệp vụ
- [x] LLM gen luồng SQL JSON (single provider trước)
- [x] Validate output format
- [x] Evaluate quality (LLM)
- [x] Tune loop
- [x] Output JSON
- [x] Multi-provider (expand từ single)
- [x] Rich terminal output

### Add After Validation (v1.1)

- [ ] HTML report
- [ ] Auto mode
- [ ] Interactive mode

### Future Consideration (v2+)

- [ ] Config hot-reload
- [ ] Prompt templates tùy chỉnh
- [ ] Batch processing nhiều mô tả

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| CLI nhập mô tả | HIGH | LOW | P1 |
| Gen luồng JSON | HIGH | MEDIUM | P1 |
| Validate output | HIGH | MEDIUM | P1 |
| Evaluate quality | HIGH | HIGH | P1 |
| Tune loop | HIGH | HIGH | P1 |
| Output JSON | HIGH | LOW | P1 |
| Multi-provider LLM | MEDIUM | MEDIUM | P1 |
| Rich terminal | MEDIUM | LOW | P2 |
| HTML report | MEDIUM | MEDIUM | P2 |
| Auto mode | MEDIUM | LOW | P2 |
| Interactive mode | MEDIUM | LOW | P2 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---
*Feature research for: TextToSQLFlow*
*Researched: 2026-07-01*
