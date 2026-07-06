"""Interactive review mode for DAG optimization.

Shows before/after DAG, highlights changes, and prompts user to accept,
reject, or customise the optimization.
"""

from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from text_to_sql_flow.types import Flow
from text_to_sql_flow.dag_optimizer.engine import (
    render_optimization_diff,
    OptimizationSuggestion,
)


def review_optimization(
    console: Console,
    original_flow: Flow,
    optimized_flow: Flow,
    suggestions: list[OptimizationSuggestion] | None = None,
) -> Flow:
    """Present the optimization diff and let the user decide.

    Returns the *Flow* the user chose (optimised or original).
    """
    # Detect if there were actual changes
    original_orders = {s.name: s.order for s in original_flow.steps}
    optimized_orders = {s.name: s.order for s in optimized_flow.steps}
    changes = {
        name for name, old in original_orders.items()
        if optimized_orders.get(name) != old
    }

    if not changes and not suggestions:
        console.print("[dim]No optimization changes needed — DAG already optimal.[/]")
        return original_flow

    console.print()
    console.print("[bold cyan]═══ DAG Optimization Review ═══[/]")
    console.print()
    console.print(render_optimization_diff(original_flow, optimized_flow))

    # Show suggestions
    if suggestions:
        console.print()
        console.print("[bold yellow]Suggestions for further improvement:[/]")
        for s in suggestions:
            console.print(f"  [yellow]⚡ {s.detail}[/]")

    console.print()
    console.print("[bold]Options:[/]")
    console.print("  [1] Apply optimization [green](recommended)[/]")
    console.print("  [2] Keep original (no changes)")
    console.print("  [3] Skip optimization for this flow")

    while True:
        choice = Prompt.ask(
            "Choose",
            choices=["1", "2", "3"],
            default="1",
        )
        if choice == "1":
            console.print("[green]✓ Optimization applied[/]")
            return optimized_flow
        elif choice == "2":
            console.print("[dim]Keeping original flow order.[/]")
            return original_flow
        elif choice == "3":
            console.print("[dim]Skipping optimization for this run.[/]")
            return original_flow
