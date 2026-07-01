<!-- GSD:project-start source:PROJECT.md -->
## Project

**TextToSQLFlow**

CLI tool sinh luồng Spark SQL dạng JSON từ mô tả nghiệp vụ bằng LLM. Người dùng cung cấp mô tả inline, tool gọi LLM (nhiều provider) để sinh cấu trúc luồng SQL ETL, đánh giá chất lượng, tuning nếu cần, và xuất kết quả dưới dạng file JSON + HTML report. Dành cho data engineer muốn tăng năng suất viết SQL ETL.

**Core Value:** Data engineer có thể đưa mô tả nghiệp vụ và nhận luồng SQL Spark sẵn sàng chạy, không cần tự viết từng câu SQL.

### Constraints

- **Tech Stack**: Python, CLI, không Web framework
- **LLM**: Hỗ trợ tối thiểu 4 provider (OpenAI, Claude, Deepseek, NVIDIA NIM, OpenRouter, OpenCode)
- **Scope**: POC, không yêu cầu high-availability / production deployment
- **Output**: File-based (JSON + HTML)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
# Core
# LLM
# Dev
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
- Dùng litellm để support multiple provider nhanh
- Bỏ qua async, dùng sync httpx
- Không cần dependency injection pattern
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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
