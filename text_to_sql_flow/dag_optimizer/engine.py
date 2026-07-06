"""DAG engine — build dependency graph, compute parallel levels, optimize execution order.

Provides:
- Topological sort with level assignment (same level = parallel)
- Fan-out detection for intermediate step suggestions
- ASCII DAG render for terminal display
"""

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from rich.tree import Tree
from rich.panel import Panel
from rich.table import Table
from rich.console import Group
from rich.text import Text
from rich import box

from text_to_sql_flow.types import Flow, Step


# ── Graph building ────────────────────────────────────────────────────


def build_dag(steps: list[Step]) -> dict[str, set[str]]:
    """Build a parent→children adjacency map from a list of steps."""
    dag: dict[str, set[str]] = {s.name: set() for s in steps}
    names = {s.name for s in steps}
    for s in steps:
        for p in s.parents:
            if p in names:
                dag[p].add(s.name)
    return dag


def build_reverse_dag(steps: list[Step]) -> dict[str, set[str]]:
    """Build a step→parents adjacency map (mirrors ``Step.parents``)."""
    return {s.name: set(s.parents) for s in steps}


# ── Optimization ──────────────────────────────────────────────────────


def compute_optimal_orders(steps: list[Step]) -> dict[str, int]:
    """Assign optimal parallel levels via BFS topological sort.

    Returns a dict ``{step_name: order}`` where steps with the same
    ``order`` value can execute in parallel.
    """
    parents = build_reverse_dag(steps)
    children = build_dag(steps)
    orders: dict[str, int] = {}
    q: deque[str] = deque()

    # Roots first
    for name, ps in parents.items():
        if not ps:
            orders[name] = 0
            q.append(name)

    # BFS level by level
    while q:
        node = q.popleft()
        for child in children.get(node, []):
            if child not in orders:
                child_parents = parents[child]
                if all(p in orders for p in child_parents):
                    orders[child] = max(orders[p] for p in child_parents) + 1
                    q.append(child)

    # Residual (cycles / disconnected)
    max_order = max(orders.values()) if orders else 0
    for s in steps:
        if s.name not in orders:
            max_order += 1
            orders[s.name] = max_order

    return orders


def apply_optimization(flow: Flow) -> Flow:
    """Return a new *Flow* with optimised ``Step.order`` values.

    Preserves all other fields (name, description, steps, SQL, parents,
    diagram positions, etc.).
    """
    optimal = compute_optimal_orders(flow.steps)
    # Map name → original index for stable sort
    orig_index = {s.name: i for i, s in enumerate(flow.steps)}
    new_steps = []
    for s in flow.steps:
        new_steps.append(s.model_copy(update={"order": optimal[s.name]}))
    # Sort by new order then original index for stable output
    new_steps.sort(key=lambda s: (s.order, orig_index[s.name]))
    return flow.model_copy(update={"steps": new_steps})


# ── Suggestions ───────────────────────────────────────────────────────


@dataclass
class OptimizationSuggestion:
    """A suggestion from the optimizer for further parallelism."""

    step_name: str
    kind: str  # "fan_out"
    detail: str
    children_count: int = 0


def suggest_intermediate_steps(
    flow: Flow,
    threshold: int = 3,
) -> list[OptimizationSuggestion]:
    """Detect steps that may benefit from intermediate temp views.

    A step with more than *threshold* direct children is flagged as
    a potential candidate for splitting into intermediate views.
    """
    dag = build_dag(flow.steps)
    suggestions: list[OptimizationSuggestion] = []
    for parent, kids in dag.items():
        if len(kids) > threshold:
            suggestions.append(OptimizationSuggestion(
                step_name=parent,
                kind="fan_out",
                detail=(
                    f"Step '{parent}' feeds {len(kids)} downstream steps. "
                    f"Consider splitting into intermediate temp views to "
                    f"enable more parallel execution of dependent branches."
                ),
                children_count=len(kids),
            ))
    return suggestions


# ── ASCII Rendering ───────────────────────────────────────────────────


def render_ascii_dag(
    steps: list[Step],
    title: str = "DAG",
    highlight: Optional[dict[str, int]] = None,
) -> Panel:
    """Render a DAG level-grouped ASCII view using Rich.

    *highlight*, if provided, is a ``{step_name: old_order}`` dict;
    steps whose order differs from their original highlight get a
    ``changed`` style.
    """
    by_order: dict[int, list[Step]] = defaultdict(list)
    for s in steps:
        by_order[s.order].append(s)

    tree = Tree(f"[bold]{title}[/]")
    for level in sorted(by_order):
        branch = tree.add(f"[cyan]Order {level}[/]")
        for s in sorted(by_order[level], key=lambda x: x.name):
            old = highlight.get(s.name) if highlight else None
            changed = old is not None and old != s.order
            label = s.name
            if s.parents:
                label += f"  [dim]← {', '.join(sorted(s.parents))}[/]"
            if changed:
                label += f"  [yellow](was {old})[/]"
            style = "green" if changed else "default"
            branch.add(Text(label, style=style))

    return Panel(
        Group(tree),
        title=f"[bold]{title}[/]",
        border_style="dim",
    )


def render_optimization_diff(
    original: Flow,
    optimized: Flow,
) -> Panel:
    """Render a before/after diff of the DAG optimization."""
    original_orders = {s.name: s.order for s in original.steps}
    before = render_ascii_dag(
        original.steps, title="Before",
    )
    after = render_ascii_dag(
        optimized.steps, title="After",
        highlight=original_orders,
    )

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("Before")
    table.add_column("After")
    table.add_row(before, after)
    return Panel(table, title="[bold]DAG Optimization Diff[/]", border_style="cyan")
