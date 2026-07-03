# TextToSQLFlow

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM.

Data engineer đưa mô tả nghiệp vụ → nhận luồng SQL Spark sẵn sàng chạy.

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
| **Auto evaluation** | 5-dim rubric, score ≥ 7.0, tuning loop (max 5 lần) |
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

## Output

```
./output/flow-xxxxxx/
├── flow.json         # Flow definition (MongoDB-compatible)
├── description.txt   # Mô tả gốc
└── report.html       # HTML report (nếu --html)
```

## Cấu trúc source

```
text_to_sql_flow/
├── __main__.py      # Entry point
├── cli.py           # Typer CLI (3 commands)
├── pipeline.py      # Pipeline controller
├── evaluator.py     # 5-dim quality evaluation
├── config.py        # .env + YAML config
├── types.py         # Pydantic models
├── interactive.py   # REPL mode
├── batch.py         # Batch mode
├── llm/
│   ├── provider.py  # litellm multi-provider
│   └── prompts.py   # System/user prompts
├── parsers/
│   └── flow_parser.py
└── output/
    ├── json_writer.py
    └── html_renderer.py
```

## Tests

```bash
pytest tests/ -v    # 82 tests
```

## Tech stack

Python 3.11+, Typer, Pydantic, litellm, Jinja2, Rich

*Không dùng LangChain, không Web framework*
