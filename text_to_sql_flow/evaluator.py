"""LLM-based evaluator for Spark SQL ETL flow quality.

Uses the same LLM provider as generation to score a generated flow
against an 8-dimension rubric: correctness, completeness, granularity,
data_quality, spark_execution_efficiency, spark_coding_best_practices,
dependency_correctness, and code_quality.

Pass requires: overall >= 8.5 AND correctness >= 8 AND
spark_execution_efficiency >= 8 AND dependency_correctness >= 8.

Usage::
    result = evaluate_flow(Path("output/flow.json"), provider="opencode")
    if result.passed:
        print(f"Score: {result.score}/10")
"""

import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from text_to_sql_flow.llm.provider import call_llm
from text_to_sql_flow.config import AppConfig

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────

THRESHOLD = 8.5
"""Minimum overall score for an evaluation to pass."""

MAX_ITERATIONS = 5
"""Maximum iterations for evaluate-tune loop (per EVAL-04)."""

PASS_MINIMUMS: dict[str, float] = {
    "correctness": 8.0,
    "spark_execution_efficiency": 8.0,
    "dependency_correctness": 8.0,
}
"""Per-dimension minimum scores required for pass (in addition to overall threshold)."""

# ── Prompt ────────────────────────────────────────────────────────────────

EVALUATOR_SYSTEM_PROMPT = """You are a senior data engineer evaluating a Spark SQL ETL flow definition.

Evaluate the generated Spark SQL ETL flow strictly against the original
business description. Do not assume missing information. Only award high
scores when the optimization or correctness is explicitly present in the flow.

Evaluate on these 8 dimensions, each scored 1-10:

1. **correctness** — SQL syntax, business logic correctness,
   Spark SQL semantics, and column lineage.

2. **completeness** — All required steps from the business description
   are covered, intermediate transformations exist.

3. **granularity** — ETL is decomposed into meaningful stages, not
   monolithic. Each logical operation has its own node. Penalize
   single-step flows. Do NOT penalize combining a trivial filter or
   dedup into LOAD when it improves readability.

4. **data_quality** — NULL-safe aggregations (COALESCE/IFNULL or explicit
   filters), WHERE clauses exclude NULLs on critical columns (dates, measures,
   join keys) so no downstream logic receives NULL input.

5. **spark_execution_efficiency** — Predicate pushdown (filter early),
   projection pruning (no SELECT *), join strategy (SEMI/ANTI before
   LEFT JOIN, dedup keys before joining), broadcast only for known-small
   tables, early aggregation, minimize shuffle, avoid redundant filters.

6. **spark_coding_best_practices** — Uses `DATE_TRUNC`/`DATE_FORMAT`
   (not `TRUNC`), `${TABLE_VAR}` for table names (not hardcoded), temp
   views used correctly, column aliases, uppercase keywords, one column
   per line.

7. **dependency_correctness** — Step parents list matches actual
   table/view dependencies, execution order is correct (parallel steps
   have same order number). Each step declares proper parent references
   forming a valid DAG — no orphan steps, no circular dependencies.

8. **code_quality** — SQL is readable, uses consistent naming with verb
   prefixes (`LOAD_*`, `FILTER_*`, `AGGREGATE_*`, `SAVE_*`), descriptions
   are meaningful.

Respond with ONLY valid JSON in this exact shape (no extra text):

{
    "score": 8.6,
    "dimensions": {
        "correctness": 9,
        "completeness": 8,
        "granularity": 7,
        "data_quality": 8,
        "spark_execution_efficiency": 8,
        "spark_coding_best_practices": 7,
        "dependency_correctness": 9,
        "code_quality": 8
    },
    "critical_issues": [
        "column 'revenue' is missing from upstream view before aggregation"
    ],
    "feedback": "The flow covers the main requirements but ..."
}

List any blocking defect in **critical_issues** — a SQL syntax error, a missing
column, a wrong join key, a circular dependency, an unsupported Spark function,
or a business logic contradiction (e.g. business says "inactive 180 days" but
flow uses 90 days). Leave the list empty when no blocking issues exist.

Pass gate: overall >= 8.5 AND correctness >= 8 AND
spark_execution_efficiency >= 8 AND dependency_correctness >= 8
AND no critical_issues.
"""

# ── Models ────────────────────────────────────────────────────────────────


class EvaluationResult(BaseModel):
    """Result of evaluating a generated Spark SQL ETL flow.

    Attributes:
        score: Overall quality score 0-10.
        passed: True when score >= THRESHOLD AND per-dimension minimums met.
        dimensions: Per-dimension scores (correctness, completeness, …).
        critical_issues: List of blocking issues (from LLM).
        feedback: Detailed feedback text from the LLM evaluator.
    """

    score: float
    feedback: str
    dimensions: dict[str, float]
    passed: bool
    critical_issues: list[str] = []


# ── Public API ────────────────────────────────────────────────────────────


def build_evaluation_prompt(flow_dict: dict, description: Optional[str] = None) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) pair for the evaluator LLM call.

    Args:
        flow_dict: The generated flow as a plain dict (from Flow.to_serializable_dict).
        description: Optional original business description to evaluate against.

    Returns:
        A tuple of (system_prompt, user_prompt) strings.
    """
    user_prompt = (
        f"Evaluate the following Spark SQL ETL flow:\n\n"
        f"```json\n{json.dumps(flow_dict, indent=2)}\n```"
    )
    if description:
        user_prompt += (
            f"\n\nOriginal business description (use to verify correctness and "
            f"completeness):\n\n{description}"
        )
    return EVALUATOR_SYSTEM_PROMPT, user_prompt


def parse_evaluation_response(response_text: str, threshold: float = THRESHOLD) -> EvaluationResult:
    """Parse the LLM evaluator's JSON response into an EvaluationResult.

    Handles pure JSON, ```json code blocks, and extra text around the JSON.

    Args:
        response_text: Raw text returned by the LLM evaluator.
        threshold: Score threshold for passing (defaults to THRESHOLD constant).

    Returns:
        A validated EvaluationResult.

    Raises:
        ValueError: If JSON cannot be extracted or the parsed result
            is missing required fields (score, feedback).
    """
    raw_text = response_text.strip()

    # Try to extract from markdown code block first
    import re
    json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", raw_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = raw_text

    # Find first { and last }
    first_brace = json_str.find("{")
    last_brace = json_str.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = json_str[first_brace: last_brace + 1]
    else:
        hint = ""
        if raw_text and not raw_text.isspace() and "{" in raw_text:
            hint = (
                " The response appears to be incomplete (truncated). "
                "This usually means the model hit the max_tokens limit."
            )
        raise ValueError("No JSON object found in evaluator response" + hint)

    try:
        data: dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        hint = ""
        if "{" in raw_text and not raw_text.rstrip().endswith("}"):
            hint = (
                " The response appears to be incomplete (truncated). "
                "This usually means the model hit the max_tokens limit."
            )
        raise ValueError(f"Failed to parse evaluator JSON response: {e}{hint}")

    score = data.get("score")
    feedback = data.get("feedback")

    if score is None:
        raise ValueError("Evaluator response missing 'score' field")
    if feedback is None:
        raise ValueError("Evaluator response missing 'feedback' field")

    dimensions = data.get("dimensions", {})
    critical_issues = data.get("critical_issues", [])

    # Validate that all required dimensions are present
    missing = [d for d in PASS_MINIMUMS if d not in dimensions]
    if missing:
        raise ValueError(
            f"Evaluator response missing required dimensions: {', '.join(missing)}"
        )
    passed = (
        float(score) >= threshold
        and len(critical_issues) == 0
        and all(
            dimensions[dim] >= min_score
            for dim, min_score in PASS_MINIMUMS.items()
        )
    )
    return EvaluationResult(
        score=float(score),
        feedback=str(feedback),
        dimensions=dimensions,
        passed=passed,
        critical_issues=critical_issues,
    )


def evaluate_flow(
    flow_path: Path,
    provider: str = "opencode",
    config: Optional[AppConfig] = None,
    threshold: float = THRESHOLD,
    description: Optional[str] = None,
) -> EvaluationResult:
    """Evaluate a generated flow JSON file using the LLM evaluator.

    Args:
        flow_path: Path to the generated flow JSON file.
        provider: LLM provider name (defaults to "openai").
        config: Optional AppConfig for model/temperature overrides.
        threshold: Score threshold for passing (defaults to THRESHOLD constant).
        description: Original business description for correctness check.

    Returns:
        An EvaluationResult with score, feedback, and pass/fail status.

    Raises:
        ValueError: If the flow file cannot be read or parsed.
        RuntimeError: If the LLM evaluator call fails after retries
            (propagated from call_llm).
    """
    if not flow_path.exists():
        raise ValueError(f"Flow file not found: {flow_path}")

    with open(flow_path, "r", encoding="utf-8") as f:
        flow_dict = json.load(f)

    system_prompt, user_prompt = build_evaluation_prompt(flow_dict, description=description)
    response_text = call_llm(system_prompt, user_prompt, provider=provider, config=config)
    return parse_evaluation_response(response_text, threshold=threshold)
