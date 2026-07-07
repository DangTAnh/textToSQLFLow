# TextToSQLFlow

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM.

Data engineer đưa mô tả nghiệp vụ + thông tin bảng → nhận luồng SQL Spark tối ưu song song, sẵn sàng chạy.

## Quick Start

```bash
# Cài dependencies
pip install -r requirements.txt

# Cài local package
pip install -e .

# hoặc dùng uv
uv sync

# Gen một flow (mặc định dùng OpenCode - model free, cần OPENCODE_API_KEY)
python -m text_to_sql_flow generate "Mô tả nghiệp vụ Spark SQL ETL" --output ./output --provider opencode

# Interactive mode (khuyên dùng)
python -m text_to_sql_flow interactive

# Batch mode
python -m text_to_sql_flow batch descriptions.txt
```

## Tính năng

| Tính năng | Mô tả |
|-----------|-------|
| **4 CLI modes** | `generate`, `interactive` (REPL), `batch` (file), `config` (TUI) |
| **6 LLM providers** | OpenAI, Claude, DeepSeek, NVIDIA NIM, OpenRouter, OpenCode |
| **Auto evaluation** | 8-dim rubric, score ≥ 8.5 (default), per-dimension minimums, tuning loop (max 5 lần) |
| **Table Metadata** | Cung cấp schema JSON hoặc DDL → LLM sinh flow chính xác hơn |
| **DAG Optimizer** | Tự động tối ưu thứ tự chạy cho parallel execution tối đa |
| **AI GATEWAY** | Standalone proxy service: routing, fallback, rate limit, cache, audit, RBAC |
| **Config Manager** | Interactive TUI: quản lý provider, API key, gateway, preferences (v1.3) |
| **Enhanced REPL** | Multi-description input, provider search, progress viz, session history (v1.3) |
| **HTML report** | Jinja2 template, dark theme |
| **Pydantic validation** | Schema validation cho flow JSON |
| **OpenCode default** | Model free, cần OPENCODE\_API\_KEY |

## LLM Providers

| Provider | Flag | Model mặc định | Cần key? |
|----------|------|---------------|----------|
| OpenCode (default) | `--provider opencode` | deepseek-v4-flash-free | OPENCODE\_API\_KEY |
| OpenAI | `--provider openai` | GPT-4o | OPENAI\_API\_KEY |
| Claude | `--provider claude` | claude-sonnet-4-20250514 | ANTHROPIC\_API\_KEY |
| DeepSeek | `--provider deepseek` | deepseek-chat | DEEPSEEK\_API\_KEY |
| NVIDIA NIM | `--provider nvidia` | nemotron-4-340b-instruct | NVIDIA\_API\_KEY |
| OpenRouter | `--provider openrouter` | openrouter/auto | OPENROUTER\_API\_KEY |

## Usage nâng cao

### Table Metadata (v1.2)

```bash
# JSON format
python -m text_to_sql_flow generate "Mô tả" --tables schema.json

# DDL format (auto-detect)
python -m text_to_sql_flow generate "Mô tả" --tables schema.ddl --tables-include-ddl
```

### DAG Optimizer (v1.2)

```bash
# Optimizer tự động bật (mặc định)
python -m text_to_sql_flow generate "Mô tả" --optimize

# Tắt optimizer (passthrough raw LLM output)
python -m text_to_sql_flow generate "Mô tả" --no-optimize
```

### Config Manager (v1.3)

```bash
# Launch interactive config manager TUI
text-to-sql-flow config

# Menu sections:
# 1. Providers  — xem, set default provider, sửa model name từng provider
# 2. API Keys   — CRUD API keys, test connectivity
# 3. Gateway    — cấu hình URL, enable/disable gateway mode
# 4. Preferences — threshold, auto/interactive, optimize flag
# 5. Config File — save/load YAML config
# 6. .env File  — view, add/edit/delete API keys in .env
```

### Enhanced Interactive REPL (v1.3)

```bash
# Interactive mode với đầy đủ tính năng
text-to-sql-flow interactive

# Tính năng mới:
# - Multi-description: nhập nhiều mô tả cùng lúc
# - Provider search: gõ để lọc provider
# - Config-aware: tự động dùng config từ config manager
# - Progress bars: hiển thị từng bước generation
# - Session history: tự động lưu vào ~/.text-to-sql-flow/history/
# - Error suggestions: gợi ý khắc phục lỗi (API key, network, gateway)
```

### AI GATEWAY (v1.2)

```bash
# 1. Start gateway (direct)
python -m gateway.main

# hoặc dùng uv
uv run python -m gateway.main

# 2. Trong terminal khác, dùng CLI với gateway
python -m text_to_sql_flow generate "Mô tả" --gateway-url http://localhost:8000

# hoặc dùng uv
uv run python -m text_to_sql_flow generate "Mô tả" --gateway-url http://localhost:8000

# 3. Hoặc dùng Docker Compose
docker compose up gateway -d
python -m text_to_sql_flow generate "Mô tả" --gateway-url http://localhost:8000
```

## Output

```
./output/flow-xxxxxx/
├── flow.json         # Flow definition (MongoDB-compatible)
├── description.txt   # Mô tả gốc
└── report.html       # HTML report (nếu --html)
```

## AI GATEWAY

Standalone FastAPI service, OpenAI-compatible endpoint, config qua `gateway.yaml`.

### Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/health` | GET | Health check |
| `/v1/models` | GET | Danh sách model (từ routing rules) |
| `/v1/chat/completions` | POST | Proxy LLM call (OpenAI-compatible) |

### Tính năng Gateway

| Tính năng | Config | Mô tả |
|-----------|--------|-------|
| Routing | `routing` | Regex pattern → provider/model |
| Fallback | `fallback` | Tự động chuyển provider khi fail |
| Rate limit | `rate_limit` | Token bucket, configurable RPM |
| Caching | `cache_ttl` | In-memory, TTL configurable |
| Audit log | `audit_log_path` | Ghi metadata request (không payload) |
| RBAC | `rbac` | API key → allowed providers |

### Docker

```bash
# Gateway service
docker compose up gateway -d

# CLI one-shot command
docker compose run cli --help
```

## Cấu trúc source

```
text_to_sql_flow/          # CLI tool
├── cli.py                # Typer CLI (3 commands)
├── pipeline.py           # Pipeline controller
├── evaluator.py          # 8-dim quality evaluation + tuning loop
├── config.py             # .env + YAML config
├── types.py              # Pydantic models
├── interactive.py        # REPL mode (enhanced v1.3)
├── batch.py              # Batch mode
├── config_manager.py     # Rich TUI config manager (v1.3)
├── dag_optimizer/        # DAG optimization (v1.2)
│   ├── engine.py
│   └── review.py
├── table_metadata/        # Table metadata parsing (v1.2)
│   ├── models.py
│   ├── parser.py
│   └── ddl_parser.py
├── llm/
│   ├── provider.py       # litellm multi-provider + gateway support
│   └── prompts.py        # System/user prompts
├── parsers/
│   └── flow_parser.py
└── output/
    ├── json_writer.py
    └── html_renderer.py

gateway/                   # AI GATEWAY service (v1.2)
├── main.py               # FastAPI app
├── config.py             # gateway.yaml loader
├── models.py             # Request/response models
├── llm.py                # Routing, fallback, cost tracking
├── cache.py              # Response cache
└── rate_limiter.py       # Token bucket rate limiter
```

## Tests

```bash
pytest tests/ -v    # 168+ tests
```

## Tech stack

Python 3.11+, Typer, Pydantic, litellm, Jinja2, Rich, FastAPI, uvicorn

*Không dùng LangChain*
