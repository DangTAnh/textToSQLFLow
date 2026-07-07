"""Interactive REPL mode for TextToSQLFlow.

Enhanced mode (v1.3):
- Multi-description bulk input (REPL-01)
- Provider selector with search/filter (REPL-02)
- Configuration-aware from YAML config (REPL-03)
- Step-by-step progress visualization (REPL-04)
- Session history persistence (REPL-05)
- Error display with Rich panels (REPL-06)
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.traceback import Traceback
from rich import box

from text_to_sql_flow.config import (
    AppConfig,
    load_config,
    resolve_api_key,
    PROVIDER_ENV_MAP,
    DEFAULT_CONFIG_PATH,
)
from text_to_sql_flow.pipeline import run_evaluation_loop
from text_to_sql_flow.evaluator import THRESHOLD as DEFAULT_THRESHOLD

logger = logging.getLogger(__name__)

# ── Session model ───────────────────────────────────────────────────────

_PROVIDER_DESCRIPTIONS: dict[str, str] = {
    "opencode": "Free tier -- deepseek-v4-flash-free, can OpenCode API key",
    "openai": "GPT-4o -- best overall quality, requires API key",
    "claude": "Claude Sonnet 4 -- strong at complex SQL logic, requires key",
    "deepseek": "DeepSeek Chat -- cost-effective, good for simple flows",
    "nvidia": "NVIDIA Nemotron 340B -- specialized reasoning, requires key",
    "openrouter": "OpenRouter -- unified API for many models, requires key",
}

_PROVIDER_LIST = list(_PROVIDER_DESCRIPTIONS.keys())

HISTORY_DIR = Path.home() / ".text-to-sql-flow" / "history"


@dataclass
class SessionFlow:
    """A single flow generated during an interactive session."""
    id: str
    description: str
    provider: str
    status: str  # "success", "failed"
    path: Optional[Path] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ── Core interactive session ─────────────────────────────────────────────

def interactive_session() -> None:
    """Run an enhanced interactive REPL session with main menu.

    Menu:
    1. Generate flow — standard generation flow
    2. Configuration — launch config manager TUI
    0. Exit
    """
    console = Console()
    config = _load_session_config(console)
    session_flows: list[SessionFlow] = []

    _render_welcome(console, config)

    while True:
        console.print()
        menu = Table(box=box.ROUNDED, show_header=False)
        menu.add_column("Option", style="bold", width=6)
        menu.add_column("Action", style="bold", width=20)
        menu.add_column("Description")
        menu.add_row("[bold cyan]1[/]", "Generate flow", "Enter description(s) and generate ETL flows")
        menu.add_row("[bold cyan]2[/]", "Configuration", "Manage providers, API keys, gateway, preferences")
        gateway_url = getattr(config, "gateway_url", None)
        gw = f"[green][x] {gateway_url}[/]" if gateway_url else "[yellow]direct[/]"
        menu.add_row("", "Gateway", f"Current: {gw}")
        menu.add_row("[bold cyan]0[/]", "Exit", "Back to shell")
        console.print(menu)
        console.print()

        choice = Prompt.ask(
            "[bold]Select option[/]",
            choices=["0", "1", "2"],
            default="1",
        )

        if choice == "0":
            break

        if choice == "2":
            from text_to_sql_flow.config_manager import run_config_manager
            run_config_manager()
            config = _load_session_config(console)
            console.print("[green][x] Config reloaded[/]")
            Prompt.ask("[dim]Press Enter to continue[/]", default="")
            console.clear()
            _render_welcome(console, config)
            continue

        # choice == "1" — Generate flow
        # ── Multi-description input (REPL-01) ──────────────────────────────
        descriptions = _get_descriptions(console)
        if not descriptions:
            console.print("[yellow]No description entered.[/]")
            Prompt.ask("[dim]Press Enter to continue[/]", default="")
            continue

        # ── Table metadata (optional) ────────────────────────────────────────
        tables_path, tables_include_ddl = _prompt_table_metadata(console)

        # ── Generation loop ──────────────────────────────────────────────────
        for i, desc in enumerate(descriptions, 1):
            if len(descriptions) > 1:
                console.print(f"\n[bold cyan]--- Flow {i}/{len(descriptions)} ---[/]")

            # 2. Select provider (with search — REPL-02)
            console.print()
            console.print("[bold]Step 1:[/] Choose an LLM provider")
            provider = _select_provider(console)

            # 3. Ensure API key
            cfg = _ensure_api_key(console, provider, config)

            # 4. Adjust threshold
            threshold = _get_threshold(console, config)

            # 5. Generate with step-by-step progress (REPL-04)
            flow_id = f"flow-{uuid.uuid4().hex[:8]}"
            output_dir = Path(f"./output/{flow_id}")

            result_path = _generate_with_progress(
                console, desc, output_dir, provider, cfg, threshold,
                getattr(config, "gateway_url", None),
                getattr(config, "optimize", True),
                tables_path, tables_include_ddl,
            )

            if result_path:
                status = "success"
                _save_key_to_dotenv(provider, cfg, console) if cfg else None
            else:
                status = "failed"

            session_flows.append(SessionFlow(
                id=flow_id,
                description=desc,
                provider=provider,
                status=status,
                path=result_path,
            ))

        # ── Session persistence (REPL-05) ────────────────────────────────────
        _save_session_history(session_flows)

        # ── Summary + re-generate ────────────────────────────────────────────
        _show_summary(console, session_flows)
        _re_generate(console, session_flows, config, tables_path, tables_include_ddl)
        Prompt.ask("[dim]Press Enter to continue[/]", default="")


# ── Config-aware (REPL-03) ──────────────────────────────────────────────

def _load_session_config(console: Console) -> AppConfig:
    """Load config from YAML if available, return AppConfig."""
    try:
        cfg = load_config()
        if cfg.provider:
            console.print(f"[dim]Config loaded from {DEFAULT_CONFIG_PATH}[/]")
        return cfg
    except Exception:
        return AppConfig()


# ── Welcome ─────────────────────────────────────────────────────────────

def _render_welcome(console: Console, config: AppConfig) -> None:
    console.print()
    console.print(Panel.fit(
        "[bold cyan]TextToSQLFlow -- Interactive Mode (Enhanced v1.3)[/]\n"
        "[dim]Default provider: {provider}[/]".format(
            provider=config.provider or "opencode"
        ),
        border_style="cyan",
    ))
    console.print()

    # Show recent sessions (REPL-05)
    recent = _load_recent_sessions(limit=3)
    if recent:
        console.print("[dim]Recent sessions:[/]")
        for s in recent:
            n = len(s.get("flows", []))
            t = s.get("started_at", "")[:16]
            console.print(f"  [dim]{t}[/] -- {n} flow(s)")
        console.print()


# ── Multi-description input (REPL-01) ───────────────────────────────────

def _get_descriptions(console: Console) -> list[str]:
    """Get one or more descriptions from the user.

    Single: prompt directly.
    Multi: user toggles with 'm', then enters multiple lines.
    """
    multi = Confirm.ask("[bold]Enter multiple descriptions?[/]", default=False)
    if not multi:
        desc = Prompt.ask("[bold]Description[/]", default="")
        return [desc] if desc.strip() else []

    console.print("[bold]Enter descriptions[/] (one per line, blank line to finish):")
    descs: list[str] = []
    while True:
        line = Prompt.ask(f"[dim]{len(descs) + 1}[/]")
        if not line.strip():
            break
        descs.append(line.strip())
    if descs:
        console.print(f"[green]{len(descs)}[/] description(s) entered")
    return descs


# ── Table metadata (optional) ─────────────────────────────────────────

def _prompt_table_metadata(console: Console) -> tuple[Optional[Path], bool]:
    """Prompt user to optionally provide a table schema file.

    Returns (path_or_None, include_full_ddl_or_False).
    """
    if not Confirm.ask("[bold]Provide table schema?[/]", default=False):
        return None, False

    path_str = Prompt.ask("[bold]Path to schema file[/] (.json / .sql / .ddl)")
    if not path_str.strip():
        return None, False

    p = Path(path_str.strip())
    if not p.exists():
        console.print(f"[yellow]File not found: {p}[/]")
        return None, False

    include_ddl = False
    if p.suffix.lower() in {".sql", ".ddl"}:
        include_ddl = Confirm.ask("[bold]Include full DDL in prompt?[/]", default=False)

    console.print(f"[dim]Loaded table schema: {p.name}[/]")
    return p, include_ddl


# ── Provider selector with search (REPL-02) ─────────────────────────────

def _select_provider(console: Console) -> str:
    """Display a filtered provider list; user types to search or picks by number."""
    filtered = _PROVIDER_LIST

    while True:
        t = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
        t.add_column("#", style="dim", width=3)
        t.add_column("Provider", style="bold", width=14)
        t.add_column("Model", width=32)
        t.add_column("Description")
        for i, name in enumerate(filtered, 1):
            t.add_row(str(i), name, _get_provider_model(name), _PROVIDER_DESCRIPTIONS.get(name, ""))
        console.print(t)
        console.print()

        console.print("[dim]Type to filter, enter # to select, or 'q' to cancel[/]")
        raw = Prompt.ask("[bold]Select provider[/]", default="1")

        if raw.lower() == "q":
            return _PROVIDER_LIST[0]

        # Number -> select directly
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(filtered):
                return filtered[idx]

        # Text -> filter
        filtered = [p for p in _PROVIDER_LIST if raw.lower() in p.lower()]
        if not filtered:
            console.print("[yellow]No match, showing all[/]")
            filtered = _PROVIDER_LIST


def _get_provider_model(provider: str) -> str:
    from text_to_sql_flow.llm.provider import PROVIDER_MODEL_MAP
    return PROVIDER_MODEL_MAP.get(provider, "unknown")


# ── API key handling ────────────────────────────────────────────────────

def _ensure_api_key(console: Console, provider: str, config: AppConfig) -> Optional[AppConfig]:
    """Check API key; prompt if missing. Returns AppConfig with key if entered."""
    try:
        resolve_api_key(provider, config)
        console.print(f"[dim][x] API key found for {provider}[/]")
        return None
    except ValueError:
        pass

    console.print()
    console.print(
        f"[yellow]No API key found for [bold]{provider}[/].[/]\n"
        f"Set [bold]{PROVIDER_ENV_MAP.get(provider, '?')}[/] in your .env file, "
        f"or enter it now:"
    )
    key = Prompt.ask("[bold]API key[/]", password=True)
    if key.strip():
        console.print("[green][x][/] Key accepted for this session")
        return AppConfig(api_key=key.strip())

    console.print("[yellow]No key entered -- generation may fail[/]")
    return None


def _save_key_to_dotenv(provider: str, cfg: AppConfig, console: Console) -> None:
    if not cfg or not cfg.api_key:
        return
    from text_to_sql_flow.config import write_dotenv_key
    write_dotenv_key(provider, cfg.api_key)
    console.print(f"[dim][x] Saved to .env[/]")


# ── Threshold ───────────────────────────────────────────────────────────

def _get_threshold(console: Console, config: AppConfig) -> float:
    """Get threshold from config or prompt user."""
    cfg_threshold = getattr(config, "threshold", None)
    default = cfg_threshold if cfg_threshold is not None else DEFAULT_THRESHOLD
    console.print(f"[bold]Threshold:[/] default [bold]{default}/10[/]")
    raw = Prompt.ask("[bold]Threshold[/]", default="")
    if not raw.strip():
        return default
    try:
        val = float(raw.strip())
    except ValueError:
        console.print(f"[yellow]Invalid, using {default}[/]")
        return default
    if val < 1.0 or val > 10.0:
        console.print(f"[yellow]Must be 1.0-10.0, using {default}[/]")
        return default
    console.print(f"[dim]Threshold set to {val}/10[/]")
    return val


# ── Generation with progress (REPL-04) ──────────────────────────────────

def _generate_with_progress(
    console: Console,
    description: str,
    output_dir: Path,
    provider: str,
    cfg: Optional[AppConfig],
    threshold: float,
    gateway_url: Optional[str],
    optimize: bool,
    tables_path: Optional[Path] = None,
    tables_include_ddl: bool = False,
) -> Optional[Path]:
    """Generate a flow with step-by-step progress display."""
    steps = [
        ("Calling LLM...", "cyan"),
        ("Parsing response...", "green"),
        ("Evaluating quality...", "yellow"),
        ("Optimizing DAG...", "magenta"),
    ]

    result_path = None
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=None),
        console=console,
        transient=False,
    ) as progress:
        task = progress.add_task(f"[bold cyan]Generating with {provider}...[/]", total=len(steps))

        for step_desc, color in steps:
            progress.update(task, description=f"[bold {color}]{step_desc}[/]")
            progress.advance(task)

            if step_desc == "Calling LLM...":
                try:
                    result_path = run_evaluation_loop(
                        description=description,
                        output_dir=output_dir,
                        auto=True,
                        provider=provider,
                        html=True,
                        config=cfg,
                        threshold=threshold,
                        gateway_url=gateway_url,
                        optimize=optimize,
                        tables_path=tables_path,
                        tables_include_ddl=tables_include_ddl,
                    )
                except Exception as e:
                    # REPL-06: Rich traceback
                    console.print()
                    console.print(Panel(
                        f"[red]Generation failed[/]\n[dim]{e}[/]",
                        border_style="red",
                    ))
                    tb = Traceback.from_exception(type(e), e, e.__traceback__)
                    console.print(tb)
                    _show_error_suggestion(console, provider, e)
                    return None

    if result_path:
        console.print(Panel(
            f"[green][x][/] Flow generated successfully\n[dim]{result_path}[/]",
            border_style="green",
        ))
    return result_path


# ── Error suggestions (REPL-06) ─────────────────────────────────────────

_ERROR_SUGGESTIONS: dict[str, list[str]] = {
    "api_key": [
        "Check that your API key is correct in .env or config file",
        "Run `text-to-sql-flow config` to set API keys interactively",
    ],
    "authentication": [
        "Your API key may be invalid or expired",
        "Check the provider's dashboard for key status",
    ],
    "connection": [
        "Check your internet connection",
        "If using a proxy, set HTTP_PROXY/HTTPS_PROXY environment variables",
    ],
    "timeout": [
        "The provider took too long to respond",
        "Try again later or switch to a different provider",
    ],
    "gateway": [
        "Ensure the AI GATEWAY is running: `docker compose up gateway -d`",
        "Check gateway URL in config or --gateway-url flag",
    ],
}


def _show_error_suggestion(console: Console, provider: str, error: Exception) -> None:
    """Show actionable suggestions based on error type."""
    err_str = str(error).lower()
    suggestions: list[str] = []

    if "api_key" in err_str or "api key" in err_str:
        suggestions = _ERROR_SUGGESTIONS["api_key"]
    elif any(w in err_str for w in ["auth", "unauthorized", "forbidden", "401", "403"]):
        suggestions = _ERROR_SUGGESTIONS["authentication"]
    elif any(w in err_str for w in ["connect", "timeout", "econnrefused", "dns"]):
        suggestions = _ERROR_SUGGESTIONS["connection"]
        if provider == "gateway" or "gateway" in err_str:
            suggestions = _ERROR_SUGGESTIONS["gateway"]
    elif "timeout" in err_str:
        suggestions = _ERROR_SUGGESTIONS["timeout"]

    if suggestions:
        text = "\n".join(f"  [yellow]-[/] {s}" for s in suggestions)
        console.print(Panel(
            f"[bold yellow]Suggestions:[/]\n{text}",
            border_style="yellow",
            title="Next Steps",
        ))


# ── Session history (REPL-05) ───────────────────────────────────────────

def _save_session_history(flows: list[SessionFlow]) -> None:
    """Save session to a JSON history file."""
    if not flows:
        return

    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    path = HISTORY_DIR / f"session-{timestamp}.json"

    data = {
        "started_at": timestamp,
        "flow_count": len(flows),
        "success_count": sum(1 for f in flows if f.status == "success"),
        "flows": [
            {
                "id": f.id,
                "description": f.description[:80],
                "provider": f.provider,
                "status": f.status,
                "path": str(f.path) if f.path else None,
                "timestamp": f.timestamp,
            }
            for f in flows
        ],
    }

    try:
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except OSError:
        pass  # non-critical


def _load_recent_sessions(limit: int = 5) -> list[dict]:
    """Load recent session history files."""
    if not HISTORY_DIR.exists():
        return []
    sessions = []
    try:
        for p in sorted(HISTORY_DIR.glob("session-*.json"), reverse=True)[:limit]:
            sessions.append(json.loads(p.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        pass
    return sessions


# ── REPL helpers ────────────────────────────────────────────────────────

def _ask_continue(console: Console) -> bool:
    """Ask if user wants to generate another (single) description."""
    return Confirm.ask("[bold]Generate another?[/]", default=True)


# ── Re-generate ─────────────────────────────────────────────────────────

def _re_generate(console: Console, flows: list[SessionFlow], config: AppConfig,
                 tables_path: Optional[Path] = None,
                 tables_include_ddl: bool = False) -> None:
    """Offer to re-generate a previous flow with a different provider."""
    success_flows = [f for f in flows if f.status == "success"]
    if not success_flows:
        return

    console.print()
    if not Confirm.ask("[bold]Re-generate a previous flow?[/]", default=False):
        return

    _show_summary(console, flows, show_selection=True)

    max_choice = len(success_flows)
    choice = Prompt.ask(
        "[bold]Select flow to re-generate[/]",
        choices=[str(i) for i in range(1, max_choice + 1)],
        default="1",
    )
    selected = success_flows[int(choice) - 1]
    console.print(f"[dim]Re-generating: {selected.description[:60]}...[/]")
    console.print()

    new_provider = _select_provider(console)
    new_cfg = _ensure_api_key(console, new_provider, config)
    new_threshold = _get_threshold(console, config)

    flow_id = f"flow-{uuid.uuid4().hex[:8]}"
    output_dir = Path(f"./output/{flow_id}")
    console.print(f"[bold green]...[/] Re-generating with [bold]{new_provider}[/]...")

    result_path = _generate_with_progress(
        console, selected.description, output_dir, new_provider, new_cfg,
        new_threshold, getattr(config, "gateway_url", None),
        getattr(config, "optimize", True),
        tables_path, tables_include_ddl,
    )

    if result_path:
        status = "success"
        _save_key_to_dotenv(new_provider, new_cfg, console) if new_cfg else None
    else:
        status = "failed"

    flows.append(SessionFlow(
        id=flow_id,
        description=selected.description,
        provider=new_provider,
        status=status,
        path=result_path,
    ))

    _save_session_history(flows)
    _show_summary(console, flows)


# ── Summary table ───────────────────────────────────────────────────────

def _show_summary(console: Console, flows: list[SessionFlow], show_selection: bool = False) -> None:
    """Display session summary table."""
    console.print()
    console.print(Panel("[bold]Session Summary[/]", border_style="cyan"))

    if not flows:
        console.print("[dim]No flows were generated in this session.[/]")
        return

    t = Table(box=box.ROUNDED, show_header=True, header_style="bold cyan")
    t.add_column("ID", style="dim", width=14)
    t.add_column("Description", width=40, overflow="fold")
    t.add_column("Provider", width=12)
    t.add_column("Status", width=10)
    t.add_column("Output")

    for f in flows:
        style = "green" if f.status == "success" else "red"
        desc = f.description[:50] + "..." if len(f.description) > 50 else f.description
        out = str(f.path) if f.path else "--"
        t.add_row(f.id, desc, f.provider, f"[{style}]{f.status}[/]", f"[dim]{out}[/]")

    console.print(t)
    success_count = sum(1 for f in flows if f.status == "success")
    console.print(f"[dim]{len(flows)} flow(s), {success_count} successful[/]")
