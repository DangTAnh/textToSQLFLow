"""Tests for the DAG Optimizer (Phase 8)."""

from datetime import datetime
from text_to_sql_flow.types import Flow, Step, StepOutput, Diagram, CreatedDate
from rich.panel import Panel
from text_to_sql_flow.dag_optimizer.engine import (
    build_dag,
    build_reverse_dag,
    compute_optimal_orders,
    apply_optimization,
    suggest_intermediate_steps,
    render_ascii_dag,
    render_optimization_diff,
)

NOW = datetime(2026, 7, 6)
TS = CreatedDate(date=NOW)


def _step(name: str, order: int = 0, parents: list[str] | None = None) -> Step:
    """Quick helper to build a Step with minimal required fields."""
    return Step(
        name=name,
        order=order,
        parents=parents or [],
        sql=f"SELECT * FROM {name}",
        output=StepOutput(tempView=f"{name}_view"),
        diagram=Diagram(x=0, y=0),
        createdDate=TS,
    )


# ── Graph building ────────────────────────────────────────────────────


class TestBuildDag:
    def test_simple_chain(self):
        steps = [
            _step("a", order=0),
            _step("b", order=1, parents=["a"]),
            _step("c", order=2, parents=["b"]),
        ]
        dag = build_dag(steps)
        assert dag["a"] == {"b"}
        assert dag["b"] == {"c"}
        assert dag["c"] == set()

    def test_diamond(self):
        steps = [
            _step("root", order=0),
            _step("left", order=1, parents=["root"]),
            _step("right", order=1, parents=["root"]),
            _step("merge", order=2, parents=["left", "right"]),
        ]
        dag = build_dag(steps)
        assert dag["root"] == {"left", "right"}
        assert dag["right"] == {"merge"}
        assert dag["left"] == {"merge"}


class TestBuildReverseDag:
    def test_matches_parents(self):
        steps = [
            _step("a"),
            _step("b", parents=["a"]),
            _step("c", parents=["a", "b"]),
        ]
        rdag = build_reverse_dag(steps)
        assert rdag["a"] == set()
        assert rdag["b"] == {"a"}
        assert rdag["c"] == {"a", "b"}


# ── Optimization ──────────────────────────────────────────────────────


class TestComputeOptimalOrders:
    def test_simple_chain(self):
        steps = [
            _step("a", order=0),
            _step("b", order=1, parents=["a"]),
            _step("c", order=2, parents=["b"]),
            _step("d", order=3, parents=["c"]),
        ]
        orders = compute_optimal_orders(steps)
        assert orders["a"] == 0
        assert orders["b"] == 1
        assert orders["c"] == 2
        assert orders["d"] == 3

    def test_diamond_parallel(self):
        steps = [
            _step("root", order=0),
            _step("left", order=1, parents=["root"]),
            _step("right", order=1, parents=["root"]),
            _step("merge", order=2, parents=["left", "right"]),
        ]
        orders = compute_optimal_orders(steps)
        assert orders["root"] == 0
        assert orders["left"] == 1
        assert orders["right"] == 1  # same level = parallel
        assert orders["merge"] == 2

    def test_wide_fan_out(self):
        steps = [_step("src", order=0)] + [
            _step(f"child_{i}", order=1, parents=["src"]) for i in range(5)
        ]
        orders = compute_optimal_orders(steps)
        assert orders["src"] == 0
        for i in range(5):
            assert orders[f"child_{i}"] == 1  # all parallel

    def test_no_parents_all_roots(self):
        steps = [
            _step("a", order=0),
            _step("b", order=1),
            _step("c", order=2),
        ]
        orders = compute_optimal_orders(steps)
        # All roots → all order 0 (parallel)
        assert orders["a"] == 0
        assert orders["b"] == 0
        assert orders["c"] == 0

    def test_complex_graph(self):
        steps = [
            _step("a", order=0),
            _step("b", order=1, parents=["a"]),
            _step("c", order=1, parents=["a"]),
            _step("d", order=2, parents=["b"]),
            _step("e", order=2, parents=["c"]),
            _step("f", order=3, parents=["d", "e"]),
        ]
        orders = compute_optimal_orders(steps)
        assert orders["a"] == 0
        assert orders["b"] == 1
        assert orders["c"] == 1
        assert orders["d"] == 2
        assert orders["e"] == 2
        assert orders["f"] == 3


class TestApplyOptimization:
    def test_preserves_fields(self):
        steps = [_step("a", order=0), _step("b", order=5, parents=["a"])]
        flow = Flow(name="test", steps=steps)
        optimized = apply_optimization(flow)
        assert optimized.name == "test"
        assert optimized.steps[0].name == "a"
        assert optimized.steps[1].name == "b"
        # b's order gets fixed from 5 to 1
        assert optimized.steps[0].order == 0
        assert optimized.steps[1].order == 1
        # Non-order fields preserved
        assert optimized.steps[1].sql == steps[1].sql
        assert optimized.steps[1].output.tempView == "b_view"

    def test_no_change_if_already_optimal(self):
        steps = [
            _step("a", order=0),
            _step("b", order=1, parents=["a"]),
            _step("c", order=2, parents=["b"]),
        ]
        flow = Flow(name="test", steps=steps)
        optimized = apply_optimization(flow)
        for s in optimized.steps:
            assert s.order == next(orig.order for orig in steps if orig.name == s.name)

    def test_reduces_parallel_levels(self):
        # Steps with gaps in order should be compacted
        steps = [
            _step("a", order=0),
            _step("b", order=10, parents=["a"]),
            _step("c", order=20, parents=["a"]),
        ]
        flow = Flow(name="test", steps=steps)
        optimized = apply_optimization(flow)
        orders = {s.name: s.order for s in optimized.steps}
        assert orders["a"] == 0
        assert orders["b"] == 1
        assert orders["c"] == 1


# ── Suggestions ───────────────────────────────────────────────────────


class TestSuggestIntermediateSteps:
    def test_no_suggestion_low_fanout(self):
        steps = [
            _step("src"),
            _step("a", parents=["src"]),
            _step("b", parents=["src"]),
        ]
        flow = Flow(name="test", steps=steps)
        suggestions = suggest_intermediate_steps(flow, threshold=3)
        assert len(suggestions) == 0

    def test_suggests_high_fanout(self):
        steps = [_step("src")] + [
            _step(f"c{i}", parents=["src"]) for i in range(5)
        ]
        flow = Flow(name="test", steps=steps)
        suggestions = suggest_intermediate_steps(flow, threshold=3)
        assert any(s.step_name == "src" for s in suggestions)
        assert suggestions[0].children_count == 5

    def test_custom_threshold(self):
        steps = [_step("src")] + [
            _step(f"c{i}", parents=["src"]) for i in range(3)
        ]
        flow = Flow(name="test", steps=steps)
        suggestions = suggest_intermediate_steps(flow, threshold=2)
        assert len(suggestions) == 1


# ── ASCII Rendering ───────────────────────────────────────────────────


class TestRenderAsciiDag:
    def test_returns_panel(self):
        steps = [_step("a", order=0), _step("b", order=1, parents=["a"])]
        panel = render_ascii_dag(steps, title="Test")
        assert isinstance(panel, Panel)

    def test_highlight_shows_changes(self):
        optimized = [
            _step("a", order=0),
            _step("b", order=1, parents=["a"]),
        ]
        highlight = {"b": 5}
        panel = render_ascii_dag(optimized, highlight=highlight)
        assert isinstance(panel, Panel)


class TestRenderOptimizationDiff:
    def test_returns_panel(self):
        orig = Flow(name="test", steps=[
            _step("a", order=0),
            _step("b", order=5, parents=["a"]),
        ])
        opt = Flow(name="test", steps=[
            _step("a", order=0),
            _step("b", order=1, parents=["a"]),
        ])
        panel = render_optimization_diff(orig, opt)
        assert panel is not None
