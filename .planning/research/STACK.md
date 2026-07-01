# Stack Research

**Domain:** Spark SQL ETL Flow Generation using LLM
**Researched:** 2026-07-01
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Runtime | Standard for data/AI tooling, rich ecosystem |
| Typer | 0.12+ | CLI framework | Modern, intuitive, auto --help, built on Click |
| Pydantic | 2.5+ | Data validation | Schema validation cho JSON flow definition |
| httpx | 0.27+ | HTTP client | Async HTTP cho LLM API calls, retry support |

### LLM SDKs

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| openai | 1.0+ | OpenAI API client | Gọi GPT-4o, Deepseek, NVIDIA NIM |
| anthropic | 0.30+ | Claude API | Gọi Claude Sonnet/Opus |
| litellm | 1.40+ | Unified LLM interface | Gọi tất cả provider qua 1 API (OpenAI, Claude, Deepseek, etc.) |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Jinja2 | 3.1+ | HTML report template | Render HTML report từ template |
| rich | 13.0+ | Terminal UI | Progress bars, color output cho CLI |
| PyYAML | 6.0+ | Config file format | Config file provider settings |
| pytest | 8.0+ | Testing | Unit test cho generator logic |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| rye/uv | Python package manager | Fast alternative to pip/poetry |
| ruff | Linter/formatter | Fast Python linter, thay thế flake8 + isort |

## Installation

```bash
# Core
pip install typer pydantic httpx jinja2 rich pyyaml

# LLM
pip install openai anthropic litellm

# Dev
pip install pytest ruff mypy
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Typer | Click (manual) | Click khi cần control cực kỳ fine-grained |
| litellm | Viết provider adapter thủ công | Khi chỉ dùng 1 provider duy nhất |
| Pydantic | dataclasses | Khi không cần validation phức tạp |
| Jinja2 | Mako | Khi cần template logic phức tạp hơn |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| LangChain | Overhead lớn cho use case đơn giản, prompt engineering phức tạp hơn cần thiết | litellm + tự quản lý prompt |
| Django/Flask | Web framework không cần thiết cho CLI tool | Typer |
| aiohttp | Thấp hơn httpx về ergonomics, không cần async mạnh | httpx |
| streamlit | Overkill cho CLI, thêm dependency web không cần | Rich terminal output |

## Stack Patterns by Variant

**If POC scope nhỏ (single developer):**
- Dùng litellm để support multiple provider nhanh
- Bỏ qua async, dùng sync httpx
- Không cần dependency injection pattern

**If muốn production-ready:**
- Dùng Abstract Factory pattern cho LLM providers
- Thêm retry + rate limiting layer
- Cấu hình qua YAML config file

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| openai >=1.0 | Python 3.8+ | Breaking change từ v0.x |
| anthropic >=0.30 | Python 3.7+ | Streaming support |
| litellm >=1.40 | Python 3.8+ | Proxy mode available |
| typer >=0.12 | click 8.0+ | Built on Click |

---
*Stack research for: TextToSQLFlow*
*Researched: 2026-07-01*
