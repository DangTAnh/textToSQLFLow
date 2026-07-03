"""CLI entry point for TextToSQLFlow.

Uses Typer for command-line parsing with automatic ``--help`` support.
"""

import typer
import click
from pathlib import Path
from typing import Optional
from rich.console import Console

app = typer.Typer(
    name="text-to-sql-flow",
    help="Generate Spark SQL ETL flows from business descriptions using LLM",
)

_PROVIDER_CHOICES = [
    "openai", "claude", "deepseek",
    "nvidia", "openrouter", "opencode",
]


@app.command()
def generate(
    description: str = typer.Argument(
        ...,
        help="Business description of the Spark SQL ETL flow",
    ),
    output: Path = typer.Option(
        "./output",
        "--output",
        "-o",
        help="Output directory for generated flow files",
        file_okay=False,
        dir_okay=True,
    ),
    provider: str = typer.Option(
        "opencode",
        "--provider",
        "-p",
        help="LLM provider to use for generation",
        click_type=click.Choice(_PROVIDER_CHOICES),
        case_sensitive=False,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to YAML config file (default: ./text-to-sql-flow.yaml)",
        exists=False,
        file_okay=True,
        dir_okay=False,
    ),
    html: bool = typer.Option(
        False,
        "--html",
        help="Generate HTML report alongside JSON output",
    ),
    auto: bool = typer.Option(
        False,
        "--auto",
        help="Run evaluation loop automatically without prompts (for CI/batch)",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        help="Pause at each evaluation iteration for user review",
    ),
):
    """Generate a Spark SQL flow from a business description.

    By default, generates the flow once and writes JSON output.
    Use --auto to enable the evaluate-tune loop (auto-retry until quality threshold met).
    Use --interactive to review each evaluation result and choose retry/abort/continue.
    """
    from text_to_sql_flow.pipeline import run_generation, run_evaluation_loop

    console = Console()

    if auto or interactive:
        with console.status("[bold cyan]Running evaluation loop...") as status:
            result_path = run_evaluation_loop(
                description=description,
                output_dir=output,
                auto=auto,
                interactive=interactive,
                provider=provider,
                config_path=config,
                html=html,
            )
        console.print(f"[green]Flow generated successfully:[/green] {result_path}")
    else:
        result_path = run_generation(
            description=description,
            output_dir=output,
            provider=provider,
            config_path=config,
            html=html,
        )
        console.print(f"[green]Flow generated successfully:[/green] {result_path}")


@app.command()
def interactive():
    """Run interactive REPL mode: input descriptions, choose providers, loop.

    No flags needed — everything is prompted interactively.
    Uses the evaluate-tune loop automatically for each generation.
    """
    from text_to_sql_flow.interactive import interactive_session
    interactive_session()


@app.command()
def batch(
    file: Path = typer.Argument(
        ...,
        help="Text file with one business description per line (blank/# lines skipped)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    output: Path = typer.Option(
        "./output",
        "--output",
        "-o",
        help="Root output directory (each flow gets a subdir)",
        file_okay=False,
        dir_okay=True,
    ),
    provider: str = typer.Option(
        "opencode",
        "--provider",
        "-p",
        help="LLM provider for all descriptions",
        click_type=click.Choice(_PROVIDER_CHOICES),
        case_sensitive=False,
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to YAML config file",
        exists=False,
        file_okay=True,
        dir_okay=False,
    ),
    html: bool = typer.Option(
        False,
        "--html",
        help="Generate HTML report alongside each JSON output",
    ),
):
    """Process multiple descriptions from a text file (GUI-05).

    Each line in the file is treated as one business description.
    Blank lines and lines starting with # are ignored.
    Generates all flows, then shows a batch summary table.
    """
    from text_to_sql_flow.batch import run_batch
    run_batch(
        file_path=file,
        output_dir=output,
        provider=provider,
        config_path=config,
        html=html,
    )
