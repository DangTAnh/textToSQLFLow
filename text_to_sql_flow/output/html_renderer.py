"""Jinja2-based HTML report renderer for Spark SQL ETL flow definitions.

Produces a dark-themed, self-contained HTML report with:
- Flow name + description header
- Steps table with collapsible SQL
- ASCII/text dependency diagram
- Evaluation results section (placeholder ready for Phase 2 data)
- Generation timestamp footer

No external CSS/fonts — everything is inline.
"""

import logging
from pathlib import Path
from typing import Optional

from jinja2 import Template

from text_to_sql_flow.types import Flow

logger = logging.getLogger(__name__)

# ── Embedded Jinja2 template ─────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ flow_name }} — Flow Report</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { background: #1a1a2e; color: #e0e0e0; font-family: -apple-system, 'Segoe UI', Arial, sans-serif; padding: 2rem; line-height: 1.6; }
  h1 { color: #4fc3f7; font-size: 1.8rem; margin-bottom: 0.3rem; }
  h2 { color: #4fc3f7; font-size: 1.3rem; margin: 1.5rem 0 0.8rem; border-bottom: 1px solid #333; padding-bottom: 0.3rem; }
  .description { color: #aaa; margin-bottom: 1.5rem; font-size: 0.95rem; }
  table { width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; }
  th, td { padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid #333; }
  th { background: #16213e; color: #4fc3f7; font-weight: 600; }
  tr:nth-child(even) { background: #1e1e3a; }
  tr:hover { background: #252550; }
  .sql-preview { color: #b0b0b0; font-family: 'Courier New', monospace; font-size: 0.85rem; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sql-full { background: #111; color: #4fc3f7; padding: 0.8rem; border-radius: 4px; font-family: 'Courier New', monospace; font-size: 0.85rem; white-space: pre-wrap; margin-top: 0.3rem; }
  details { cursor: pointer; }
  details summary { color: #4fc3f7; font-size: 0.85rem; }
  .diagram { background: #111; padding: 1rem; border-radius: 6px; font-family: 'Courier New', monospace; font-size: 0.9rem; line-height: 1.7; white-space: pre; overflow-x: auto; margin-bottom: 1.5rem; }
  .diagram .step-link { color: #4fc3f7; }
  .diagram .step-name { color: #ffd54f; }
  .eval-box { background: #16213e; border-left: 4px solid #4fc3f7; padding: 1rem; border-radius: 4px; margin-bottom: 1.5rem; }
  .eval-box .score { font-size: 1.5rem; font-weight: bold; color: #4fc3f7; }
  .eval-placeholder { color: #666; font-style: italic; }
  .footer { margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #333; font-size: 0.8rem; color: #666; }
  .badge { display: inline-block; background: #333; color: #ccc; padding: 0.15rem 0.5rem; border-radius: 3px; font-size: 0.75rem; margin-right: 0.3rem; }
  .badge-parent { background: #1a3a4a; color: #4fc3f7; }
</style>
</head>
<body>

<h1>Flow: {{ flow_name }}</h1>
<div class="description">{{ flow_description }}</div>

<h2>Flow Diagram</h2>
<div class="diagram">{{ diagram_text }}</div>

<h2>Steps</h2>
<table>
<thead><tr>
  <th>#</th><th>Name</th><th>Order</th><th>Parents</th><th>Description</th><th>SQL</th>
</tr></thead>
<tbody>
{% for step in steps %}
<tr>
  <td>{{ loop.index }}</td>
  <td><strong>{{ step.name }}</strong></td>
  <td><span class="badge">{{ step.order }}</span></td>
  <td>{% for p in step.parents %}<span class="badge badge-parent">{{ p }}</span> {% endfor %}</td>
  <td>{{ step.description or "—" }}</td>
  <td>
    <div class="sql-preview">{{ step.sql[:120] }}{% if step.sql|length > 120 %}...{% endif %}</div>
    {% if step.sql|length > 120 %}
    <details><summary>Show full SQL</summary><div class="sql-full">{{ step.sql }}</div></details>
    {% endif %}
  </td>
</tr>
{% endfor %}
</tbody>
</table>

{% if eval_results %}
<h2>Evaluation Results</h2>
<div class="eval-box">
  <div>Score: <span class="score">{{ eval_results.score }}/10</span></div>
  {% if eval_results.iterations %}<div>Iterations: {{ eval_results.iterations }}</div>{% endif %}
  <div style="margin-top:0.5rem">{{ eval_results.feedback }}</div>
</div>
{% else %}
<h2>Evaluation</h2>
<div class="eval-placeholder">No evaluation data available.</div>
{% endif %}

<div class="footer">
  Generated: {{ generation_time }}<br>
  Tool: TextToSQLFlow
</div>

</body>
</html>"""


def render_html_report(
    flow: Flow,
    output_dir: Path,
    eval_results: Optional[dict] = None,
) -> Path:
    """Render a Flow model to a dark-themed HTML report.

    Args:
        flow: Validated Flow model to render.
        output_dir: Directory to write the HTML file.
        eval_results: Optional dict with evaluation data:
            ``{"score": float, "feedback": str, "iterations": int}``

    Returns:
        Absolute path to the generated HTML file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Sort steps by order then name
    sorted_steps = sorted(flow.steps, key=lambda s: (s.order, s.name))

    # Build ASCII flow diagram
    diagram_text = _build_diagram(sorted_steps)

    # Render template
    from datetime import datetime, timezone

    template = Template(HTML_TEMPLATE)
    html = template.render(
        flow_name=flow.name,
        flow_description=flow.description or "(no description)",
        steps=[
            {
                "name": s.name,
                "order": s.order,
                "parents": s.parents or [],
                "description": s.description or "",
                "sql": s.sql,
            }
            for s in sorted_steps
        ],
        diagram_text=diagram_text,
        eval_results=eval_results,
        generation_time=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    # Write file
    safe_name = flow.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
    filename = f"{safe_name}_report.html"
    output_path = output_dir / filename
    output_path.write_text(html, encoding="utf-8")

    logger.info("HTML report written: %s", output_path.resolve())
    return output_path.resolve()


def _build_diagram(steps: list) -> str:
    """Build a text-based dependency diagram from sorted steps.

    Renders each step with its order in brackets and indented to show
    parent → child relationships::

        [1] STEP_ONE
          [2] STEP_TWO  (depends on: STEP_ONE)
    """
    if not steps:
        return "(no steps)"

    # Build a name→step lookup
    step_map = {s.name: s for s in steps}

    lines: list[str] = []
    for s in steps:
        indent = "  " if s.parents else ""
        deps = f"(depends on: {', '.join(s.parents)})" if s.parents else ""
        lines.append(f"{indent}[{s.order}] {s.name} {deps}")

    return "\n".join(lines)
