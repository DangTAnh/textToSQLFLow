# TextToSQLFlow

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM.

Data engineer đưa mô tả nghiệp vụ + thông tin bảng → nhận luồng SQL Spark tối ưu song song, sẵn sàng chạy.

## Quick Start

```bash
pip install -e .
# hoặc
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
| **3 CLI modes** | `generate`, `interactive` (REPL), `batch` (file) |
| **6 LLM providers** | OpenAI, Claude, DeepSeek, NVIDIA NIM, OpenRouter, OpenCode |
| **Auto evaluation** | 5-dim rubric, score ≥ 7.0 (default), tuning loop (max 5 lần) |
| **Table Metadata** | Cung cấp schema JSON hoặc DDL → LLM sinh flow chính xác hơn |
| **DAG Optimizer** | Tự động tối ưu thứ tự chạy cho parallel execution tối đa |
| **AI GATEWAY** | Standalone proxy service: routing, fallback, rate limit, cache, audit, RBAC |
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

### AI GATEWAY (v1.2)

```bash
# 1. Start gateway
python -m gateway.main

# 2. Trong terminal khác, dùng CLI với gateway
python -m text_to_sql_flow generate "Mô tả" --gateway-url http://localhost:8000

# Hoặc dùng Docker Compose
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
├── evaluator.py          # 5-dim quality evaluation
├── config.py             # .env + YAML config
├── types.py              # Pydantic models
├── interactive.py        # REPL mode
├── batch.py              # Batch mode
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
pytest tests/ -v    # 141+ tests
```

## Tech stack

Python 3.11+, Typer, Pydantic, litellm, Jinja2, Rich, FastAPI, uvicorn

*Không dùng LangChain*
