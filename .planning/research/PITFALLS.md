# Pitfalls Research

**Domain:** Spark SQL ETL Flow Generation using LLM
**Researched:** 2026-07-01
**Confidence:** HIGH

## Critical Pitfalls

### Pitfall 1: LLM trả về JSON malformed

**What goes wrong:**
LLM trả về JSON không đúng format — thiếu field, sai syntax, hoặc thêm text ngoài JSON block.

**Why it happens:**
LLM được train để hội thoại, không phải để trả JSON chính xác mỗi lần. Đặc biệt với SQL dài có nhiều escape characters.

**How to avoid:**
- Parse JSON linh hoạt: regex extract JSON block, fallback parsing
- Retry với prompt yêu cầu sửa format
- Pydantic validate + error message cụ thể

**Warning signs:**
- json.loads() throw SyntaxError thường xuyên
- Pydantic validation error >50% responses

**Phase to address:**
Phase 1 (Core Pipeline)

---

### Pitfall 2: Evaluate loop không hội tụ

**What goes wrong:**
LLM evaluator không bao giờ đánh giá "passed", loop chạy đến max iterations mà không có kết quả tốt.

**Why it happens:**
Evaluation rubric không clear, LLM quá khắt khe hoặc không có tiêu chí cụ thể.

**How to avoid:**
- Rubric rõ ràng, có thể đo đếm (ví dụ: "đúng format", "đủ steps", "SQL syntax đúng")
- Max iterations cứng (3-5 lần)
- Accept best effort sau max iterations
- Tự động giảm threshold sau mỗi iteration

**Warning signs:**
- Loop luôn chạy đến max iterations
- Score không cải thiện giữa các iteration

**Phase to address:**
Phase 2 (Evaluate & Tune Loop)

---

### Pitfall 3: Khác biệt giữa các LLM provider

**What goes wrong:**
Cùng prompt nhưng provider khác nhau cho output khác nhau — format, quality, consistency.

**Why it happens:**
Mỗi model có instruction-following capability khác nhau, context window khác nhau.

**How to avoid:**
- Prompt tuning riêng cho từng provider
- Test với tất cả provider trước khi release
- Model-specific template overrides

**Warning signs:**
- Output format khác nhau giữa các provider
- Provider A luôn pass eval, provider B luôn fail

**Phase to address:**
Phase 3 (Multi-Provider Support)

---

### Pitfall 4: SQL injection / prompt injection

**What goes wrong:**
Business description chứa text độc hại khiến LLM gen SQL không an toàn.

**Why it happens:**
Tool đưa user input trực tiếp vào prompt mà không sanitize.

**How to avoid:**
- System prompt isolation (user input trong user message, không trong system)
- Validate output SQL không chứa destructive operations (DROP, TRUNCATE...)
- POC scope nên low risk, nhưng cần awareness

**Warning signs:**
- Output SQL chứa DDL commands không mong muốn
- LLM trả về nội dung không liên quan đến schema

**Phase to address:**
Phase 1 (Core Pipeline)

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Hardcode provider config | Dev nhanh | Khó maintain khi thêm provider | POC iteration 1 |
| Không test | Ship nhanh | Bug khó detect | Không, luôn test pipeline |
| Sync HTTP | Đơn giản | Chậm khi có nhiều request | POC là đủ |
| Không type hints | Code nhanh hơn | Khó refactor, IDE kém support | Không, Python 3.11 có type hint dễ |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| OpenAI | Không handle rate limit (429) | Retry with exponential backoff |
| Claude | Không handle overloaded (529) | Retry with backoff, respect Retry-After header |
| NVIDIA NIM | Assume URL format giống OpenAI | Verify API endpoint format |
| Deepseek | Assume model name tồn tại ở all regions | Kiểm tra region availability |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Retry không backoff | Rate limit → fail ngay | Exponential backoff + jitter | 5+ concurrent requests |
| Load toàn bộ output vào memory | OOM với SQL flow lớn | Stream JSON writer | SQL >100 steps |
| Không cache LLM response | Gọi lại cùng prompt trả $ | Simple LRU cache | >10 calls với cùng input |

## "Looks Done But Isn't" Checklist

- [ ] **JSON validation:** Nếu parse fail, tool có fallback không? Hay crash?
- [ ] **Retry logic:** LLM API fail (429, 500) → tool có retry không?
- [ ] **Max iterations:** Loop có infinite guard không?
- [ ] **Error message:** User có biết tại sao fail không? (vs silent fail)
- [ ] **Config validation:** API key config sai → error message clear?
- [ ] **File overwrite:** Output file exists → có hỏi overwrite không?

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| JSON malformed | Phase 1 | Test với LLM response mock |
| Loop không hội tụ | Phase 2 | Test với evaluation mock |
| Provider khác biệt | Phase 3 | Test mỗi provider output format |
| Prompt injection | Phase 1 | Test với malicious input |

---
*Pitfalls research for: TextToSQLFlow*
*Researched: 2026-07-01*
