"""LLM-based evaluator for Spark SQL ETL flow quality.

Uses the same LLM provider as generation to score a generated flow
against a 5-dimension rubric: correctness, completeness, Spark best
practices, dependency correctness, and code quality.

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

THRESHOLD = 7.0
"""Score threshold for passing evaluation (per EVAL-02)."""

MAX_ITERATIONS = 5
"""Maximum iterations for evaluate-tune loop (per EVAL-04)."""

# ── Prompt ────────────────────────────────────────────────────────────────

EVALUATOR_SYSTEM_PROMPT = """You are a senior data engineer evaluating a Spark SQL ETL flow definition.

Evaluate the flow JSON on these 7 dimensions, each scored 1-10:

1. **correctness** — SQL syntax correctness, proper Spark SQL functions,
   no logical errors or column mismatches.

2. **completeness** — All required steps from the business description
   are covered, intermediate transformations exist.

3. **granularity** — ETL is decomposed into multiple granular steps
   (e.g. LOAD → FILTER → AGGREGATE → SAVE) rather than one monolithic
   step. Each logical operation has its own node in the DAG. Penalize
   single-step flows heavily.

4. **data_quality** — NULL-safe aggregations (COALESCE/IFNULL or explicit
   filters), WHERE clauses exclude NULLs on critical columns (dates, measures,
   join keys) so no downstream logic receives NULL input.

4. **spark_best_practices** — Uses `DATE_TRUNC`/`DATE_FORMAT` (not `TRUNC`),
   `${TABLE_VAR}` for table names (not hardcoded), broadcast hints for
   small tables, avoids UDFs where built-in functions suffice, proper
   partitioning, uses temp views appropriately.

5. **dependency_correctness** — Step parents list matches actual
   table/view dependencies, execution order is correct (parallel steps
   have same order number). Each step declares proper parent references
   forming a valid DAG — no orphan steps, no circular dependencies.

6. **code_quality** — SQL is readable, uses consistent naming with verb
   prefixes (`LOAD_*`, `FILTER_*`, `AGGREGATE_*`, `SAVE_*`), descriptions
   are meaningful, diagram positions are reasonable.

Respond with ONLY valid JSON in this exact shape (no extra text):

{
    "score": 7.5,
    "dimensions": {
        "correctness": 8,
        "completeness": 7,
        "granularity": 6,
        "data_quality": 7,
        "spark_best_practices": 6,
        "dependency_correctness": 8,
        "code_quality": 7
    },
    "feedback": "The flow covers the main requirements but ..."
}
"""

# ── Models ────────────────────────────────────────────────────────────────


class EvaluationResult(BaseModel):
    """Result of evaluating a generated Spark SQL ETL flow.

    Attributes:
        score: Overall quality score 0-10.
        feedback: Detailed feedback text from the LLM evaluator.
        dimensions: Per-dimension scores (correctness, completeness, …).
        passed: True when score >= THRESHOLD.
    """

    score: float
    feedback: str
    dimensions: dict[str, float]
    passed: bool


# ── Public API ────────────────────────────────────────────────────────────


def build_evaluation_prompt(flow_dict: dict) -> tuple[str, str]:
    """Build (system_prompt, user_prompt) pair for the evaluator LLM call.

    Args:
        flow_dict: The generated flow as a plain dict (from Flow.to_serializable_dict).

    Returns:
        A tuple of (system_prompt, user_prompt) strings.
    """
    user_prompt = (
        "Evaluate the following Spark SQL ETL flow:\n\n"
        f"```json\n{json.dumps(flow_dict, indent=2)}\n```"
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
        raise ValueError("No JSON object found in evaluator response")

    try:
        data: dict = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse evaluator JSON response: {e}")

    score = data.get("score")
    feedback = data.get("feedback")

    if score is None:
        raise ValueError("Evaluator response missing 'score' field")
    if feedback is None:
        raise ValueError("Evaluator response missing 'feedback' field")

    dimensions = data.get("dimensions", {})
    passed = float(score) >= threshold

    return EvaluationResult(
        score=float(score),
        feedback=str(feedback),
        dimensions=dimensions,
        passed=passed,
    )


def evaluate_flow(
    flow_path: Path,
    provider: str = "opencode",
    config: Optional[AppConfig] = None,
    threshold: float = THRESHOLD,
) -> EvaluationResult:
    """Evaluate a generated flow JSON file using the LLM evaluator.

    Args:
        flow_path: Path to the generated flow JSON file.
        provider: LLM provider name (defaults to "openai").
        config: Optional AppConfig for model/temperature overrides.
        threshold: Score threshold for passing (defaults to THRESHOLD constant).

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

    system_prompt, user_prompt = build_evaluation_prompt(flow_dict)
    response_text = call_llm(system_prompt, user_prompt, provider=provider, config=config)
    return parse_evaluation_response(response_text, threshold=threshold)
