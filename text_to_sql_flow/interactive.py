"""Interactive REPL mode for TextToSQLFlow.

Provides a rich-based interactive session where users can:
- Enter business descriptions one after another (GUI-01)
- Select a provider from a rich table (GUI-02)
- Enter API key inline if missing (GUI-03)
- REPL loop: generate → "Generate another?" (GUI-04)
- View session summary on exit
"""

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
from rich import box

from text_to_sql_flow.config import AppConfig, resolve_api_key, PROVIDER_ENV_MAP
from text_to_sql_flow.pipeline import run_evaluation_loop
from text_to_sql_flow.evaluator import THRESHOLD as DEFAULT_THRESHOLD

logger = logging.getLogger(__name__)

# ── Session model ───────────────────────────────────────────────────────

_PROVIDER_DESCRIPTIONS: dict[str, str] = {
    "opencode": "Free tier — deepseek-v4-flash-free, cần OpenCode API key",
    "openai": "GPT-4o — best overall quality, requires API key",
    "claude": "Claude Sonnet 4 — strong at complex SQL logic, requires key",
    "deepseek": "Deepseek Chat — cost-effective, good for simple flows",
    "nvidia": "NVIDIA Nemotron 340B — specialized reasoning, requires key",
    "openrouter": "OpenRouter — unified API for many models, requires key",
}

_PROVIDER_LIST = list(_PROVIDER_DESCRIPTIONS.keys())


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
    """Run an interactive REPL session for generating Spark SQL flows.

    1. Show welcome message
    2. Loop:
       a. Get description via prompt
       b. Select provider from rich table
       c. Ensure API key (prompt inline if missing)
       d. Generate flow with status spinner
       e. Show result
       f. Ask "Generate another?"
    3. Show session summary table
    """
    console = Console()
    session_flows: list[SessionFlow] = []

    console.print()
    console.print(Panel.fit(
        "[bold cyan]TextToSQLFlow — Interactive Mode[/]\n"
        "[dim]Generate Spark SQL ETL flows from business descriptions[/]\n"
        "Powered by opencode/deepseek-v4-flash-free by default",
        border_style="cyan",
    ))
    console.print()

    while True:
        # 1. Get description
        console.print("[bold]Step 1:[/] Describe the Spark SQL ETL flow")
        description = Prompt.ask("[bold]Description[/]", default="")
        if not description.strip():
            console.print("[yellow]Empty description, skipping.[/]")
            if not _ask_continue(console):
                break
            continue

        # 2. Select provider
        console.print()
        console.print("[bold]Step 2:[/] Choose an LLM provider")
        provider = _select_provider(console)

        # 3. Ensure API key
        config = _ensure_api_key(console, provider)

        # 4. Adjust threshold
        console.print()
        console.print("[bold]Step 3:[/] Set evaluation threshold")
        threshold = _set_threshold(console)

        # 5. Generate with evaluation loop
        console.print()
        flow_id = f"flow-{uuid.uuid4().hex[:8]}"
        output_dir = Path(f"./output/{flow_id}")
        console.print(f"[bold green]▸[/] Generating with [bold]{provider}[/] (threshold [bold]{threshold}/10[/])...")

        try:
            result_path = run_evaluation_loop(
                description=description,
                output_dir=output_dir,
                auto=True,
                provider=provider,
                html=True,
                config=config,
                threshold=threshold,
            )
            status = "success"
            session_flows.append(SessionFlow(
                id=flow_id,
                description=description,
                provider=provider,
                status=status,
                path=result_path,
            ))
            # Save API key to .env if user entered it interactively
            if config and config.api_key:
                _save_key_to_dotenv(provider, config.api_key, console)
            console.print()
            console.print(Panel(
                f"[green]✓[/] Flow generated successfully\n[dim]{result_path}[/]",
                border_style="green",
            ))
        except Exception as e:
            status = "failed"
            session_flows.append(SessionFlow(
                id=flow_id,
                description=description,
                provider=provider,
                status=status,
            ))
            console.print()
            console.print(Panel(
                f"[red]✗[/] Generation failed: {e}",
                border_style="red",
            ))

        # 5. Ask to continue
        console.print()
        if not _ask_continue(console):
            break

    # Show summary
    _show_summary(console, session_flows)

    # Re-generate step
    _re_generate(console, session_flows)


# ── Provider selection UI ────────────────────────────────────────────────


def _select_provider(console: Console) -> str:
    """Display a rich table of providers and let user pick by number.

    Returns:
        Provider name string (e.g. "opencode", "openai").
    """
    table = Table(
        title="Available Providers",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Provider", style="bold", width=14)
    table.add_column("Default Model", width=32)
    table.add_column("Description")

    for i, name in enumerate(_PROVIDER_LIST, 1):
        model = _get_provider_model(name)
        desc = _PROVIDER_DESCRIPTIONS.get(name, "")
        table.add_row(str(i), name, model, desc)

    console.print(table)
    console.print()

    choice = Prompt.ask(
        "[bold]Select provider[/]",
        choices=[str(i) for i in range(1, len(_PROVIDER_LIST) + 1)],
        default="1",
    )
    return _PROVIDER_LIST[int(choice) - 1]


def _get_provider_model(provider: str) -> str:
    """Get the default model name for a provider."""
    from text_to_sql_flow.llm.provider import PROVIDER_MODEL_MAP
    return PROVIDER_MODEL_MAP.get(provider, "unknown")


# ── API key handling ─────────────────────────────────────────────────────


def _ensure_api_key(console: Console, provider: str) -> Optional[AppConfig]:
    """Check API key availability; prompt user if missing.

    Returns:
        AppConfig with api_key set if user entered one, else None.
    """
    try:
        resolve_api_key(provider)
        console.print(f"[dim]✓ API key found for {provider}[/]")
        return None
    except ValueError:
        pass

    # No key found — prompt user
    console.print()
    console.print(
        f"[yellow]No API key found for [bold]{provider}[/].[/]\n"
        f"Set [bold]{PROVIDER_ENV_MAP.get(provider, '?')}[/] in your .env file,\n"
        f"or enter it now:"
    )
    key = Prompt.ask("[bold]API key[/]", password=True)
    if key.strip():
        console.print("[green]✓[/] Key accepted for this session")
        return AppConfig(api_key=key.strip())

    console.print("[yellow]No key entered — generation may fail if provider requires one[/]")
    return None


def _save_key_to_dotenv(provider: str, api_key: str, console: Console) -> None:
    """Write API key to .env file so it persists for future sessions.

    Creates .env if missing; updates existing entry for the provider's
    env var while preserving other entries.
    """
    env_var = PROVIDER_ENV_MAP.get(provider)
    if not env_var:
        return

    env_path = Path("./.env")
    lines = []
    found = False

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    with env_path.open("w", encoding="utf-8") as f:
        for line in lines:
            if line.strip().startswith(f"{env_var}="):
                f.write(f"{env_var}={api_key}\n")
                found = True
            else:
                f.write(line + "\n")
        if not found:
            f.write(f"{env_var}={api_key}\n")

    console.print(f"[dim]✓ Saved {env_var} to .env[/]")


# ── Threshold adjustment ────────────────────────────────────────────────


def _set_threshold(console: Console) -> float:
    """Prompt user to adjust evaluation threshold.

    Returns:
        Threshold value (1.0-10.0).
    """
    console.print(f"  Default: [bold]{DEFAULT_THRESHOLD}/10[/] (higher = stricter)")
    console.print("  Enter a new value, or leave blank to keep default.")
    raw = Prompt.ask("[bold]Threshold[/]", default="")
    if not raw.strip():
        return DEFAULT_THRESHOLD
    try:
        val = float(raw.strip())
    except ValueError:
        console.print(f"[yellow]Invalid number, using {DEFAULT_THRESHOLD}[/]")
        return DEFAULT_THRESHOLD
    if val < 1.0 or val > 10.0:
        console.print(f"[yellow]Must be between 1.0 and 10.0, using {DEFAULT_THRESHOLD}[/]")
        return DEFAULT_THRESHOLD
    console.print(f"[dim]Threshold set to {val}/10[/]")
    return val


# ── REPL helpers ─────────────────────────────────────────────────────────


def _ask_continue(console: Console) -> bool:
    """Ask user if they want to generate another flow.

    Returns:
        True if user wants to continue, False to exit.
    """
    return Confirm.ask("[bold]Generate another?[/]", default=True)


def _re_generate(console: Console, flows: list[SessionFlow]) -> None:
    """Offer to re-generate a previous flow with a different provider.

    GUI-07: User can select any previously generated flow from the
    summary and re-generate it with a different provider or config.
    """
    success_flows = [f for f in flows if f.status == "success"]
    if not success_flows:
        return

    console.print()
    if not Confirm.ask("[bold]Re-generate a previous flow?[/]", default=False):
        return

    # Show summary with numbers
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

    # Select new provider
    new_provider = _select_provider(console)

    # Ensure API key
    new_config = _ensure_api_key(console, new_provider)

    # Adjust threshold
    console.print()
    console.print("[bold]Threshold:[/] Set evaluation threshold")
    new_threshold = _set_threshold(console)

    # Re-generate
    flow_id = f"flow-{uuid.uuid4().hex[:8]}"
    output_dir = Path(f"./output/{flow_id}")
    console.print(f"[bold green]▸[/] Re-generating with [bold]{new_provider}[/]...")

    try:
        result_path = run_evaluation_loop(
            description=selected.description,
            output_dir=output_dir,
            auto=True,
            provider=new_provider,
            html=True,
            config=new_config,
            threshold=new_threshold,
        )
        flows.append(SessionFlow(
            id=flow_id,
            description=selected.description,
            provider=new_provider,
            status="success",
            path=result_path,
        ))
        # Save API key to .env if user entered it interactively
        if new_config and new_config.api_key:
            _save_key_to_dotenv(new_provider, new_config.api_key, console)
        console.print()
        console.print(Panel(
            f"[green]✓[/] Re-generated successfully\n[dim]{result_path}[/]",
            border_style="green",
        ))
    except Exception as e:
        flows.append(SessionFlow(
            id=flow_id,
            description=selected.description,
            provider=new_provider,
            status="failed",
        ))
        console.print(Panel(
            f"[red]✗[/] Re-generation failed: {e}",
            border_style="red",
        ))

    # Show updated summary
    _show_summary(console, flows)


def _show_summary(console: Console, flows: list[SessionFlow], show_selection: bool = False) -> None:
    """Display session summary table after interactive session ends."""
    console.print()
    console.print(Panel("[bold]Session Summary[/]", border_style="cyan"))

    if not flows:
        console.print("[dim]No flows were generated in this session.[/]")
        return

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("ID", style="dim", width=14)
    table.add_column("Description", width=40, overflow="fold")
    table.add_column("Provider", width=12)
    table.add_column("Status", width=10)
    table.add_column("Output")

    for f in flows:
        status_style = "green" if f.status == "success" else "red"
        desc_short = f.description[:50] + "..." if len(f.description) > 50 else f.description
        output_str = str(f.path) if f.path else "—"
        table.add_row(
            f.id,
            desc_short,
            f.provider,
            f"[{status_style}]{f.status}[/]",
            f"[dim]{output_str}[/]",
        )

    console.print(table)

    success_count = sum(1 for f in flows if f.status == "success")
    console.print(f"[dim]{len(flows)} flow(s), {success_count} successful[/]")
    console.print()
