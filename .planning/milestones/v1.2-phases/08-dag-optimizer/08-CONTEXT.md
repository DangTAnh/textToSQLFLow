# Phase 8: DAG Optimizer — Context

**Gathered:** 2026-07-06
**Status:** Ready for planning
**Mode:** Smart discuss (auto-optimized)

<domain>
## Phase Boundary

Optimize generated flow's DAG for maximum parallel execution. Hybrid approach: LLM generates initial DAG with order values, Optimizer fine-tunes to maximize same-order parallelism.

Requirements: DAG-01, DAG-02, DAG-03, DAG-04, DAG-05

</domain>

<decisions>
## Implementation Decisions

### DAG Representation
- Build from `Step.parents` (existing field in `types.py`).
- Root steps (no parents) → order 0.
- Each child step → `order = max(parent_orders) + 1`.
- Same order value → parallel execution (existing semantics).

### Optimization Algorithm
- Topological sort with level assignment.
- Preserve relative order within same level (stable sort).
- No external graph library — pure Python dict/set operations.

### Intermediate Step Suggestions
- Detect steps with fan-out > N children → suggest split into separate intermediate temp views.
- Simple heuristic based on children count, configurable threshold.

### ASCII Visualization
- Render using Rich Tree / Panel in terminal.
- Show "before → after" side-by-side or sequential diff.
- Color-coded: green = parallel group, yellow = sequential dependency.

### CLI Integration
- `--optimize` / `--no-optimize` flag (default: `--optimize`).
- In interactive mode, show optimization diff and ask accept/override.
- In batch `--auto` mode, apply silently.
- `--no-optimize` → pass through raw LLM output unchanged.

### User Review (DAG-05)
- Interactive mode: show before/after DAG, highlight order changes.
- User can: accept all, reject specific changes, or reject all.
- Batch auto mode: apply with summary log.

### Module Structure
- `dag_optimizer/engine.py` — DAG building, optimization, ASCII render
- `dag_optimizer/review.py` — interactive review UI
</decisions>
