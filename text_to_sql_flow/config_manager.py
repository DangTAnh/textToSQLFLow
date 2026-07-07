"""Interactive Config Manager -- Rich-based TUI for managing TextToSQLFlow settings.

Features:
- Provider management: view, set default, model info (CFG-02)
- API key management: CRUD, test connectivity (CFG-03)
- Gateway configuration: URL, RBAC key, enable/disable (CFG-04)
- Evaluation preferences: threshold, auto/interactive, optimize (CFG-05)
- Config file I/O: view, save, load YAML (CFG-06)
- .env file management: view, add/edit/delete keys (CFG-07)

Usage:
    text-to-sql-flow config
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from text_to_sql_flow.config import (
    AppConfig,
    load_config,
    write_config,
    write_dotenv_key,
    get_config_status,
    load_dotenv,
    PROVIDER_ENV_MAP,
    DEFAULT_CONFIG_PATH,
    DEFAULT_DOTENV_PATH,
)
from text_to_sql_flow.llm.provider import PROVIDER_MODEL_MAP

logger = logging.getLogger(__name__)

PROVIDER_DESCRIPTIONS: dict[str, str] = {
    "opencode": "Free tier -- deepseek-v4-flash-free",
    "openai": "GPT-4o -- best overall quality",
    "claude": "Claude Sonnet 4 -- strong at complex SQL",
    "deepseek": "DeepSeek Chat -- cost-effective",
    "nvidia": "NVIDIA Nemotron 340B -- specialized",
    "openrouter": "OpenRouter -- unified API for many models",
}

_PROVIDER_LIST = list(PROVIDER_ENV_MAP.keys())


class ConfigManagerApp:
    """Rich-based interactive config manager."""

    def __init__(self) -> None:
        self.console = Console()
        self.config: AppConfig = load_config()
        self._dirty = False  # track if changes were made

    # -- Main loop ----------------------------------------------------------

    def run(self) -> None:
        """Main menu loop."""
        while True:
            self.console.clear()
            self._render_header()
            choice = self._main_menu()

            if choice == "0":
                break
            elif choice == "1":
                self._provider_menu()
            elif choice == "2":
                self._api_key_menu()
            elif choice == "3":
                self._gateway_menu()
            elif choice == "4":
                self._preferences_menu()
            elif choice == "5":
                self._config_file_menu()
            elif choice == "6":
                self._dotenv_menu()

        if self._dirty:
            self.console.print("[green][x] Configuration updated.[/]")
        self.console.print("[dim]Exiting config manager.[/]")

    # -- Header -------------------------------------------------------------

    def _render_header(self) -> None:
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]TextToSQLFlow -- Configuration Manager[/]\n"
            "[dim]Manage providers, API keys, gateway, and preferences[/]",
            border_style="cyan",
        ))
        self.console.print()

    # -- Main menu ----------------------------------------------------------

    def _main_menu(self) -> str:
        table = Table(box=box.ROUNDED, show_header=False)
        table.add_column("Option", style="bold", width=4)
        table.add_column("Section", style="bold", width=20)
        table.add_column("Description")

        status = get_config_status(self.config)
        default_prov = status["provider"]
        key_count = sum(1 for v in status["keys"].values() if v)
        total_keys = len(status["keys"])

        table.add_row("1", "Providers", f"Default: [bold]{default_prov}[/] -- {key_count}/{total_keys} keys set")
        table.add_row("2", "API Keys", "View status, set/update/delete, test connectivity")
        table.add_row("3", "Gateway", f"{'[green][x] Configured[/]' if status['gateway_url'] else '[yellow]Not set[/]'}")
        table.add_row("4", "Preferences", "Threshold, auto/interactive mode, optimize flag")
        table.add_row("5", "Config File", f"View, save, load from {DEFAULT_CONFIG_PATH.name}")
        table.add_row("6", ".env File", f"View, add/edit/delete keys in {DEFAULT_DOTENV_PATH.name}")
        table.add_row("0", "Exit", "Save and quit")

        self.console.print(table)
        self.console.print()
        return Prompt.ask("[bold]Select option[/]", choices=["0", "1", "2", "3", "4", "5", "6"], default="0")

    # -- Provider menu ------------------------------------------------------

    def _provider_menu(self) -> None:
        while True:
            self.console.clear()
            self.console.print(Panel("[bold]Provider Management[/]", border_style="cyan"))
            self.console.print()

            t = Table(title="Available Providers", box=box.ROUNDED, header_style="bold cyan")
            t.add_column("#", width=3)
            t.add_column("Provider", width=14)
            t.add_column("Model", width=32)
            t.add_column("Status", width=10)
            t.add_column("Description")

            status = get_config_status(self.config)
            for i, name in enumerate(_PROVIDER_LIST, 1):
                model = PROVIDER_MODEL_MAP.get(name, "?")
                key_ok = status["keys"].get(name, False)
                is_default = "* default" if name == self.config.provider else ""
                desc = PROVIDER_DESCRIPTIONS.get(name, "")
                t.add_row(
                    str(i), name, model,
                    "[green][x] key[/]" if key_ok else "[red][ ] no key[/]",
                    f"{is_default} {desc}".strip(),
                )
            self.console.print(t)
            self.console.print()

            self.console.print("[bold]Options:[/]")
            self.console.print("  [dim]1-6[/] Set as default provider")
            self.console.print("  [dim]0[/] Back to main menu")
            choice = Prompt.ask(
                "Select provider to set as default (or 0 to go back)",
                choices=[str(i) for i in range(len(_PROVIDER_LIST) + 1)],
                default="0",
            )
            if choice == "0":
                break
            idx = int(choice) - 1
            if 0 <= idx < len(_PROVIDER_LIST):
                new_provider = _PROVIDER_LIST[idx]
                if new_provider != self.config.provider:
                    self.config.provider = new_provider
                    self._dirty = True
                    self.console.print(f"[green][x] Default provider set to {new_provider}[/]")
                    Prompt.ask("[dim]Press Enter to continue[/]", default="")
                else:
                    self.console.print(f"[yellow]{new_provider} is already the default[/]")
                    Prompt.ask("[dim]Press Enter to continue[/]", default="")

    # -- API key menu -------------------------------------------------------

    def _api_key_menu(self) -> None:
        while True:
            self.console.clear()
            self.console.print(Panel("[bold]API Key Management[/]", border_style="cyan"))
            self.console.print()

            status = get_config_status(self.config)
            t = Table(box=box.ROUNDED, header_style="bold cyan")
            t.add_column("#", width=3)
            t.add_column("Provider", width=14)
            t.add_column("Env Var", width=20)
            t.add_column("Status", width=16)
            for i, name in enumerate(_PROVIDER_LIST, 1):
                env_var = PROVIDER_ENV_MAP.get(name, "?")
                key_ok = status["keys"].get(name, False)
                t.add_row(
                    str(i), name, env_var,
                    "[green][x] Key set[/]" if key_ok else "[red][ ] Missing[/]",
                )
            self.console.print(t)
            self.console.print()

            self.console.print("[bold]Options:[/]")
            self.console.print("  [dim]1-6[/] Set/update API key for a provider")
            self.console.print("  [dim]t[/] Test API key connectivity")
            self.console.print("  [dim]0[/] Back to main menu")
            choice = Prompt.ask(
                "Select option",
                choices=[str(i) for i in range(len(_PROVIDER_LIST) + 1)] + ["t", "T", "0"],
                default="0",
            )
            if choice == "0":
                break
            if choice.lower() == "t":
                self._test_key_connectivity()
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(_PROVIDER_LIST):
                provider = _PROVIDER_LIST[idx]
                self._set_api_key(provider)

    def _set_api_key(self, provider: str) -> None:
        env_var = PROVIDER_ENV_MAP.get(provider, "?")
        self.console.print(f"\nSetting API key for [bold]{provider}[/] ({env_var}):")
        self.console.print("  [dim]Enter the key, or leave blank to delete/keep as-is.[/]")
        key = Prompt.ask("API key", password=True)
        if not key.strip():
            return
        # Save to .env
        write_dotenv_key(provider, key.strip())
        self.console.print(f"[green][x] {env_var} saved to {DEFAULT_DOTENV_PATH.name}[/]")
        self._dirty = True
        Prompt.ask("[dim]Press Enter to continue[/]", default="")

    def _test_key_connectivity(self) -> None:
        """Test a provider's API key by making a minimal LLM call."""
        self.console.print()
        self.console.print("[bold]Test API Key Connectivity[/]")
        self.console.print("Select a provider to test:")
        for i, name in enumerate(_PROVIDER_LIST, 1):
            self.console.print(f"  [dim]{i}[/] {name}")
        choice = Prompt.ask(
            "Select provider",
            choices=[str(i) for i in range(1, len(_PROVIDER_LIST) + 1)],
        )
        provider = _PROVIDER_LIST[int(choice) - 1]

        from text_to_sql_flow.llm.provider import call_llm
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
            transient=True,
        ) as progress:
            progress.add_task(description=f"Testing {provider} connectivity...", total=None)
            try:
                response = call_llm(
                    system_prompt="You are a test bot. Reply 'OK' only.",
                    user_prompt="Reply 'OK' to confirm connectivity.",
                    provider=provider,
                    max_tokens=10,
                )
                self.console.print(f"[green][x][/] [bold]{provider}[/] responded: [dim]{response[:100]}[/]")
            except Exception as e:
                self.console.print(f"[red][ ][/] [bold]{provider}[/] failed: {e}")
        Prompt.ask("[dim]Press Enter to continue[/]", default="")

    # -- Gateway menu -------------------------------------------------------

    def _gateway_menu(self) -> None:
        while True:
            self.console.clear()
            self.console.print(Panel("[bold]Gateway Configuration[/]", border_style="cyan"))
            self.console.print()

            current_url = self.config.gateway_url if hasattr(self.config, "gateway_url") else None
            if current_url is None:
                current_url = get_config_status(self.config).get("gateway_url")

            t = Table(box=box.ROUNDED, show_header=False)
            t.add_column("Setting", style="bold", width=20)
            t.add_column("Value")
            t.add_row("Gateway URL", current_url or "[yellow]Not set[/]")
            t.add_row("Mode", "[green]Enabled[/]" if current_url else "[dim]Disabled (direct LLM calls)[/]")
            self.console.print(t)
            self.console.print()

            self.console.print("[bold]Options:[/]")
            self.console.print("  [dim]1[/] Set gateway URL")
            self.console.print("  [dim]2[/] Clear gateway URL (disable gateway mode)")
            self.console.print("  [dim]0[/] Back to main menu")
            choice = Prompt.ask("Select option", choices=["0", "1", "2"], default="0")
            if choice == "0":
                break
            elif choice == "1":
                url = Prompt.ask("Gateway URL", default="http://localhost:8000")
                if url.strip():
                    self.config.gateway_url = url.strip()
                    self._dirty = True
                    self.console.print(f"[green][x] Gateway URL set to {url}[/]")
                    Prompt.ask("[dim]Press Enter to continue[/]", default="")
            elif choice == "2":
                if hasattr(self.config, "gateway_url"):
                    delattr(self.config, "gateway_url")
                self._dirty = True
                self.console.print("[green][x] Gateway URL cleared[/]")
                Prompt.ask("[dim]Press Enter to continue[/]", default="")

    # -- Preferences menu ---------------------------------------------------

    def _preferences_menu(self) -> None:
        while True:
            self.console.clear()
            self.console.print(Panel("[bold]Evaluation Preferences[/]", border_style="cyan"))
            self.console.print()

            from text_to_sql_flow.evaluator import THRESHOLD as DEFAULT_THRESHOLD
            threshold = getattr(self.config, "threshold", None) or DEFAULT_THRESHOLD
            auto_mode = True if getattr(self.config, "auto", None) is None else self.config.auto
            optimize = True if getattr(self.config, "optimize", None) is None else self.config.optimize

            t = Table(box=box.ROUNDED, show_header=False)
            t.add_column("Preference", style="bold", width=20)
            t.add_column("Value")
            t.add_row("Threshold", f"{threshold}/10")
            t.add_row("Evaluation Mode", "Auto" if auto_mode else "Interactive")
            t.add_row("DAG Optimizer", "[green]Enabled[/]" if optimize else "[yellow]Disabled[/]")
            self.console.print(t)
            self.console.print()

            self.console.print("[bold]Options:[/]")
            self.console.print("  [dim]1[/] Set evaluation threshold")
            self.console.print("  [dim]2[/] Toggle auto/interactive mode")
            self.console.print("  [dim]3[/] Toggle DAG optimizer")
            self.console.print("  [dim]0[/] Back to main menu")
            choice = Prompt.ask("Select option", choices=["0", "1", "2", "3"], default="0")
            if choice == "0":
                break
            elif choice == "1":
                raw = Prompt.ask("Threshold (1.0-10.0)", default=str(threshold))
                try:
                    val = float(raw)
                    if 1.0 <= val <= 10.0:
                        self.config.threshold = val
                        self._dirty = True
                        self.console.print(f"[green][x] Threshold set to {val}/10[/]")
                    else:
                        self.console.print("[yellow]Must be between 1.0 and 10.0[/]")
                except ValueError:
                    self.console.print("[yellow]Invalid number[/]")
                Prompt.ask("[dim]Press Enter to continue[/]", default="")
            elif choice == "2":
                current = getattr(self.config, "auto", None)
                if current is None:
                    current = True
                self.config.auto = not current
                self._dirty = True
                mode = "Auto" if self.config.auto else "Interactive"
                self.console.print(f"[green][x] Evaluation mode set to {mode}[/]")
                Prompt.ask("[dim]Press Enter to continue[/]", default="")
            elif choice == "3":
                current = getattr(self.config, "optimize", None)
                if current is None:
                    current = True
                self.config.optimize = not current
                self._dirty = True
                self.console.print(f"[green][x] DAG Optimizer {'enabled' if self.config.optimize else 'disabled'}[/]")
                Prompt.ask("[dim]Press Enter to continue[/]", default="")

    # -- Config file menu ---------------------------------------------------

    def _config_file_menu(self) -> None:
        while True:
            self.console.clear()
            self.console.print(Panel("[bold]Config File Management[/]", border_style="cyan"))
            self.console.print()

            config_path = DEFAULT_CONFIG_PATH
            exists = config_path.exists()

            t = Table(box=box.ROUNDED, show_header=False)
            t.add_column("Setting", style="bold", width=20)
            t.add_column("Value")
            t.add_row("Config File", str(config_path))
            t.add_row("Status", "[green]Exists[/]" if exists else "[yellow]Not found[/]")
            self.console.print(t)
            self.console.print()

            if exists:
                content = config_path.read_text(encoding="utf-8")
                self.console.print(Panel(content, title="Current Config", border_style="dim"))
                self.console.print()

            self.console.print("[bold]Options:[/]")
            self.console.print("  [dim]1[/] Save current settings to config file")
            self.console.print("  [dim]2[/] Reload config from file (discard unsaved changes)")
            self.console.print("  [dim]0[/] Back to main menu")
            choice = Prompt.ask("Select option", choices=["0", "1", "2"], default="0")
            if choice == "0":
                break
            elif choice == "1":
                write_config(self.config)
                self._dirty = False
                self.console.print(f"[green][x] Config saved to {config_path}[/]")
                Prompt.ask("[dim]Press Enter to continue[/]", default="")
            elif choice == "2":
                try:
                    self.config = load_config()
                    self._dirty = False
                    self.console.print("[green][x] Config reloaded from file[/]")
                except Exception as e:
                    self.console.print(f"[red]Failed to load config: {e}[/]")
                Prompt.ask("[dim]Press Enter to continue[/]", default="")

    # -- .env menu ----------------------------------------------------------

    def _dotenv_menu(self) -> None:
        while True:
            self.console.clear()
            self.console.print(Panel("[bold].env File Management[/]", border_style="cyan"))
            self.console.print()

            env_path = DEFAULT_DOTENV_PATH
            exists = env_path.exists()
            dotenv = load_dotenv()

            t = Table(box=box.ROUNDED, header_style="bold cyan")
            t.add_column("#", width=3)
            t.add_column("Env Var", width=22)
            t.add_column("Status", width=12)
            t.add_column("Value")
            for i, name in enumerate(_PROVIDER_LIST, 1):
                env_var = PROVIDER_ENV_MAP.get(name, "?")
                val = dotenv.get(env_var, "")
                masked = val[:8] + "..." + val[-4:] if len(val) > 16 else (val[:4] + "..." if val else "")
                status_str = "[green][x] Set[/]" if val else "[red]Missing[/]"
                t.add_row(str(i), env_var, status_str, masked if val else "[dim]--[/]")
            self.console.print(t)
            self.console.print()

            self.console.print("[bold]Options:[/]")
            self.console.print("  [dim]1-6[/] Add/edit API key in .env")
            self.console.print("  [dim]d[/] Delete an API key from .env")
            self.console.print("  [dim]0[/] Back to main menu")
            choices = [str(i) for i in range(len(_PROVIDER_LIST) + 1)] + ["d", "D", "0"]
            choice = Prompt.ask("Select option", choices=choices, default="0")
            if choice == "0":
                break
            if choice.lower() == "d":
                self._dotenv_delete_key()
                continue
            idx = int(choice) - 1
            if 0 <= idx < len(_PROVIDER_LIST):
                provider = _PROVIDER_LIST[idx]
                env_var = PROVIDER_ENV_MAP.get(provider, "?")
                self.console.print(f"\nEnter API key for [bold]{provider}[/] ({env_var}):")
                key = Prompt.ask("API key", password=True)
                if key.strip():
                    write_dotenv_key(provider, key.strip())
                    self.console.print(f"[green][x] {env_var} saved[/]")
                    self._dirty = True
                    Prompt.ask("[dim]Press Enter to continue[/]", default="")

    def _dotenv_delete_key(self) -> None:
        self.console.print()
        self.console.print("[bold]Delete API Key[/]")
        for i, name in enumerate(_PROVIDER_LIST, 1):
            self.console.print(f"  [dim]{i}[/] {name}")
        choice = Prompt.ask(
            "Select provider key to delete",
            choices=[str(i) for i in range(1, len(_PROVIDER_LIST) + 1)],
        )
        provider = _PROVIDER_LIST[int(choice) - 1]
        if Confirm.ask(f"Delete API key for [bold]{provider}[/]?", default=False):
            write_dotenv_key(provider, "")
            self.console.print(f"[green][x] API key for {provider} deleted[/]")
            self._dirty = True
        Prompt.ask("[dim]Press Enter to continue[/]", default="")


def run_config_manager() -> None:
    """Entry point -- launched by ``text-to-sql-flow config``."""
    app = ConfigManagerApp()
    app.run()
