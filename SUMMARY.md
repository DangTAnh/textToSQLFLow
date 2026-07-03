# TextToSQLFlow — Summary

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM.

**Core Value:** Data engineer đưa mô tả nghiệp vụ → nhận luồng SQL Spark sẵn sàng chạy.

---

## Cài đặt

```bash
pip install -e .
# hoặc
uv sync
```

Set API key trong `.env` (ưu tiên cao nhất), env var, hoặc config YAML:

```bash
# .env (ưu tiên cao nhất)
OPENAI_API_KEY="sk-..."
ANTHROPIC_API_KEY="sk-ant-..."
```

**Không cần key cho opencode** — free tier, dùng ngay.

---

## Cách dùng

### 1. Generate một flow

```bash
python -m text_to_sql_flow generate "Mô tả nghiệp vụ Spark SQL ETL" --output ./output
```

Mặc định dùng `opencode/deepseek-v4-flash-free` (free, không cần key).
Thêm `--provider openai` / `--provider claude` để đổi provider.

### 2. Interactive mode (khuyên dùng)

```bash
python -m text_to_sql_flow interactive
```

REPL loop:
1. Nhập mô tả nghiệp vụ
2. Chọn provider từ danh sách tương tác
3. Tool tự động gen + evaluate + tune
4. Hỏi "Generate another?" — tiếp tục hoặc thoát
5. Sau session: summary table + "Re-generate?" (chọn flow cũ gen lại với provider khác)

### 3. Batch mode

```bash
# descriptions.txt — mỗi dòng là một mô tả
python -m text_to_sql_flow batch descriptions.txt --output ./output
```

Bỏ qua dòng trống và dòng `# comment`. Mỗi flow gen độc lập, lỗi không ảnh hưởng flow khác. Cuối batch hiển thị summary table.

### 4. Auto evaluation loop

```bash
python -m text_to_sql_flow generate "Mô tả" --output ./output --auto
```

Quy trình:
1. **Generate** — LLM sinh flow JSON
2. **Evaluate** — LLM chấm điểm 5 tiêu chí (0–10)
3. **Score ≥ 7.0?** → Pass, xuất file
4. **Score < 7.0?** → Tune prompt với feedback → quay lại bước 1 (tối đa 5 lần)

### 5. HTML report

```bash
python -m text_to_sql_flow generate "Mô tả" --output ./output --html
```

### 6. Config file

```yaml
# text-to-sql-flow.yaml
provider: opencode
model_name: deepseek-v4-flash-free
temperature: 0.3
max_tokens: 4096
```

```bash
python -m text_to_sql_flow generate "Mô tả" --config text-to-sql-flow.yaml
```

---

## API Key Priority

`.env` file > Environment variable > Config YAML > Error prompt

1. `.env` trong thư mục hiện tại — `OPENAI_API_KEY=sk-...`
2. System env var — `export OPENAI_API_KEY=sk-...`
3. Config YAML — `api_key: sk-...` trong `text-to-sql-flow.yaml`
4. Nếu không có key → `ValueError` (riêng opencode không cần key)

---

## Providers hỗ trợ

| Provider | Flag | Model mặc định | Env var |
|----------|------|---------------|---------|
| OpenCode (mặc định) | `--provider opencode` | `deepseek-v4-flash-free` | `OPENCODE_API_KEY` |
| OpenAI | `--provider openai` | `gpt-4o` | `OPENAI_API_KEY` |
| Claude | `--provider claude` | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| DeepSeek | `--provider deepseek` | `deepseek-chat` | `DEEPSEEK_API_KEY` |
| NVIDIA | `--provider nvidia` | `nvidia/nemotron-4-340b-instruct` | `NVIDIA_API_KEY` |
| OpenRouter | `--provider openrouter` | `openrouter/auto` | `OPENROUTER_API_KEY` |

**OpenCode free**: dùng model `deepseek-v4-flash-free` — không cần key. Endpoint: `https://opencode.ai/zen/v1`.

---

## Output format

Mỗi lần chạy sinh ra thư mục output chứa:

```
./output/flow-xxxxxx/
├── flow.json              # Flow definition (schema bên dưới)
├── description.txt        # Mô tả gốc — dùng cho re-generate
└── report.html            # HTML report (nếu --html)
```

Schema `flow.json`:

```json
{
    "name": "FLOW_NAME",
    "description": "Mô tả nghiệp vụ",
    "steps": [
        {
            "name": "STEP_NAME",
            "parents": ["STEP_DEPENDENCY"],
            "order": 1,
            "sql": "SELECT ... FROM ${table_var} WHERE ...",
            "output": {
                "tempView": "temp_view_name",
                "table": "output_table_name",
                "appendType": "REPLACE",
                "kafkaGroup": ""
            },
            "description": "Mô tả step",
            "diagram": { "x": 100, "y": 100 },
            "active": true,
            "createdDate": { "$date": "2026-..." }
        }
    ]
}
```

- **`${table_var}`** — table variable (bảng dữ liệu đầu vào)
- **`parents`** — dependency graph giữa các step
- **`order`** — thứ tự thực thi (cùng số = chạy song song)

---

## Kiến trúc

```
text_to_sql_flow/
├── __main__.py          # Entry point (python -m)
├── cli.py               # CLI với Typer (3 commands)
├── pipeline.py          # Pipeline controller (generation + eval loop)
├── evaluator.py         # Quality evaluation (5-dimension rubric)
├── config.py            # YAML config + .env loader + API key resolution
├── types.py             # Pydantic models (Flow, Step, Output, …)
├── interactive.py       # Interactive REPL mode
├── batch.py             # Batch mode (file → multiple flows)
├── llm/
│   ├── provider.py      # Multi-provider LLM abstraction (litellm)
│   └── prompts.py       # System/user prompts cho generation
├── parsers/
│   └── flow_parser.py   # Parse + validate LLM response → Flow
└── output/
    ├── json_writer.py   # Ghi JSON file
    └── html_renderer.py # HTML report (Jinja2, dark theme)
```

### Pipeline flow

```
Description → [Build Prompt] → [Call LLM] → [Parse JSON] → [Validate Pydantic]
                                                              ↓
                                          [Write JSON + description.txt] ← retry
                                                              ↓
                                              [Evaluate quality (--auto)]
                                                              ↓
                                          Score ≥ 7.0? → Xuất file
                                              ↓ (nếu < 7.0)
                                          Tune prompt → retry (max 5 lần)
```

---

## CLI Commands

| Command | Usage | Mô tả |
|---------|-------|-------|
| `generate` | `text-to-sql-flow generate "mô tả"` | Gen một flow từ mô tả |
| `interactive` | `text-to-sql-flow interactive` | REPL session tương tác |
| `batch` | `text-to-sql-flow batch file.txt` | Gen nhiều flow từ file |

### Flags (generate)

| Flag | Short | Mô tả |
|------|-------|-------|
| `--output` | `-o` | Thư mục output (default: `./output`) |
| `--provider` | `-p` | LLM provider (default: `opencode`) |
| `--config` | `-c` | File config YAML |
| `--html` | | Sinh HTML report |
| `--auto` | | Tự động evaluate-tune loop |
| `--interactive` | | Hỏi user mỗi iteration |

---

## Tests

```bash
pytest tests/ -v
```

**82 tests** — unit + integration, tất cả module.

---

## Dependencies chính

- **typer** — CLI framework
- **pydantic** — Schema validation
- **litellm** — Unified LLM interface (6 providers)
- **jinja2** — HTML report template
- **rich** — Terminal output, interactive UI
- **PyYAML** — Config file

*(Không dùng python-dotenv — tự parse .env bằng tay ~15 dòng)*
