"""Pipeline controller — wires together the LLM provider, prompts, parser, and writer.

Orchestrates the end-to-end flow:
1. Build prompts from business description
2. Call LLM (with API-level retry in ``provider.py``)
3. Parse and validate JSON (with format-level retry up to MAX_RETRIES)
4. Write validated Flow to JSON file
5. Optionally generate HTML report (--html flag)
6. Optionally run evaluate-tune loop (--auto/--interactive flags)
"""

import logging
import shutil
from pathlib import Path
from typing import Optional

import typer

from text_to_sql_flow.llm.provider import call_llm
from text_to_sql_flow.llm.prompts import build_generation_prompt
from text_to_sql_flow.parsers.flow_parser import parse_flow_response, extract_validation_error
from text_to_sql_flow.output.json_writer import write_flow_json
from text_to_sql_flow.types import Flow
from text_to_sql_flow.evaluator import evaluate_flow, EvaluationResult, THRESHOLD, MAX_ITERATIONS
from text_to_sql_flow.config import AppConfig, load_config

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


def run_generation(
    description: str,
    output_dir: Path,
    provider: str = "opencode",
    config_path: Optional[Path] = None,
    html: bool = False,
    config: Optional[AppConfig] = None,
    tables_path: Optional[Path] = None,
    tables_include_ddl: bool = False,
) -> Path:
    """Execute the full generation pipeline.

    Args:
        description: Business description of the Spark SQL ETL flow.
        output_dir: Directory to write the output JSON file.
        provider: LLM provider name (one of PROVIDER_MODEL_MAP keys).
        config_path: Optional path to YAML config file.
        html: If True, generate HTML report alongside JSON.
        config: Pre-built AppConfig override (takes precedence over config_path).
        tables_path: Optional path to table metadata file (JSON or DDL).
        tables_include_ddl: If True, inject full DDL text instead of summary.

    Returns:
        Path to the generated JSON file.

    Raises:
        RuntimeError: If generation fails after all retries.
    """
    config = config or load_config(config_path)
    active_provider = provider if provider != "opencode" else config.provider

    table_metadata = None
    if tables_path:
        from text_to_sql_flow.table_metadata.parser import parse_table_metadata_file
        table_metadata = parse_table_metadata_file(tables_path)

    system_prompt, user_prompt = build_generation_prompt(
        description,
        table_metadata=table_metadata,
        include_ddl=tables_include_ddl,
    )
    last_error: Optional[str] = None

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info(
            "Generation attempt %d/%d (provider=%s)",
            attempt, MAX_RETRIES, active_provider,
        )

        # Step 1: Call LLM
        try:
            response_text = call_llm(
                system_prompt, user_prompt,
                provider=active_provider,
                config=config,
            )
        except Exception as e:
            last_error = str(e)
            logger.error("LLM call failed: %s", e)
            if attempt == MAX_RETRIES:
                raise RuntimeError(
                    f"Generation failed after {MAX_RETRIES} retries: {last_error}"
                )
            continue

        # Step 2: Parse and validate
        try:
            flow = parse_flow_response(response_text)
        except ValueError as e:
            last_error = str(e)
            logger.warning(
                "Parse/validation failed (attempt %d/%d): %s",
                attempt,
                MAX_RETRIES,
                e,
            )
            if attempt < MAX_RETRIES:
                error_feedback = extract_validation_error(e)
                user_prompt = (
                    f"{user_prompt}\n\n---\n"
                    f"The previous response had validation errors. "
                    f"Please fix these issues and output ONLY valid JSON:\n"
                    f"{error_feedback}"
                )
            continue

        # Step 3: Write output
        output_path = write_flow_json(flow, output_dir)
        logger.info("Flow generated successfully: %s", output_path)

        # Save original description alongside output (for re-generate)
        (output_dir / "description.txt").write_text(description, encoding="utf-8")

        # Step 4: Optional HTML report
        if html:
            from text_to_sql_flow.output.html_renderer import render_html_report
            html_path = render_html_report(flow, output_dir)
            logger.info("HTML report generated: %s", html_path)

        return output_path

    raise RuntimeError(
        f"Generation failed after {MAX_RETRIES} retries. Last error: {last_error}"
    )


# ── Evaluation Loop (Phase 2) ────────────────────────────────────────────


def run_evaluation_loop(
    description: str,
    output_dir: Path,
    auto: bool = False,
    interactive: bool = False,
    provider: str = "opencode",
    config_path: Optional[Path] = None,
    html: bool = False,
    config: Optional[AppConfig] = None,
    threshold: float = THRESHOLD,
    tables_path: Optional[Path] = None,
    tables_include_ddl: bool = False,
) -> Path:
    """Run generate-evaluate-tune loop.

    Generates a flow, evaluates it against the rubric, and if score < threshold,
    appends evaluator feedback to the description and regenerates.
    Loops until score >= THRESHOLD or MAX_ITERATIONS reached.

    Args:
        description: Business description of the Spark SQL ETL flow.
        output_dir: Directory to write output files.
        auto: If True, run without user prompts (for CI/batch).
        interactive: If True, pause at each iteration for user review.
        provider: LLM provider name.
        config_path: Optional path to YAML config file.
        html: If True, generate HTML report alongside JSON.
        config: Pre-built AppConfig override (takes precedence over config_path).
        threshold: Score threshold for passing (defaults to THRESHOLD constant).

    Returns:
        Path to the final generated JSON file.
    """
    current_description = description
    flow_path: Path | None = None

    # Load config once for the entire loop
    config = config or load_config(config_path)
    active_provider = provider if provider != "opencode" else config.provider

    # Track evaluated iterations for best-pick at the end
    scored: list[tuple[float, int, Path]] = []

    for iteration in range(1, MAX_ITERATIONS + 1):
        typer.echo("")
        typer.echo(f"── Iteration {iteration}/{MAX_ITERATIONS} ─{'─' * (20 + len(str(iteration)))}")

        # Step 1: Generate
        flow_path = run_generation(
            current_description,
            output_dir,
            provider=provider,
            config_path=config_path,
            html=html,
            config=config,
            tables_path=tables_path,
            tables_include_ddl=tables_include_ddl,
        )

        # Step 2: Evaluate
        try:
            result = evaluate_flow(flow_path, provider=active_provider, config=config, threshold=threshold)
        except Exception as e:
            logger.error("Evaluation failed: %s", e)
            if iteration == MAX_ITERATIONS:
                return flow_path
            continue

        scored.append((result.score, iteration, flow_path))

        # Step 3: Interactive mode — ask user
        if interactive:
            _show_interactive_prompt(result, iteration, threshold)
            action = _get_interactive_action()
            if action == "abort":
                logger.info("User aborted evaluation loop")
                return flow_path
            elif action == "continue":
                logger.info("User chose to continue with current output")
                return flow_path

        # Step 4: Check if passed
        if result.passed:
            typer.echo(f"✅ PASSED — score {result.score:.1f}/10 ≥ threshold {threshold}/10")
            return flow_path

        typer.echo(f"⏳ Score {result.score:.1f}/10 below threshold {threshold}/10 — tuning...")

        # Step 5: Tune prompt with feedback (per EVAL-03)
        if iteration < MAX_ITERATIONS:
            current_description = _tune_prompt(current_description, result.feedback, threshold)
            logger.info("Tuned prompt (iteration %d -> %d)", iteration, iteration + 1)

    # Max iterations exhausted — pick best scored (earliest iteration on tie)
    if scored:
        scored.sort(key=lambda x: (-x[0], x[1]))
        best = scored[0]
        typer.echo(f"⚠️ Max iterations ({MAX_ITERATIONS}) reached. Best: score {best[0]:.1f} (iteration {best[1]})")
        # Copy best flow to "best" file in output dir for easy reference
        best_path = output_dir / f"best_score_{best[0]:.1f}.json"
        shutil.copy2(best[2], best_path)
        return best[2]
    else:
        logger.warning("Max iterations (%d) reached. No evaluations succeeded.", MAX_ITERATIONS)
        return flow_path or output_dir / "last_output.json"


def _tune_prompt(description: str, feedback: str, threshold: float = THRESHOLD) -> str:
    """Append evaluator feedback to the description for the next iteration."""
    return (
        f"{description}\n\n"
        f"---\n"
        f"Feedback from previous evaluation (score < {threshold}/10):\n"
        f"{feedback}\n\n"
        f"Please address the feedback above and regenerate an improved Spark SQL flow."
    )


def _show_interactive_prompt(result: EvaluationResult, iteration: int, threshold: float = THRESHOLD) -> None:
    """Display evaluation result and prompt for user action."""
    typer.echo("")
    typer.echo("=" * 50)
    typer.echo(f"Iteration {iteration}/{MAX_ITERATIONS} — Evaluation Result")
    typer.echo("=" * 50)
    typer.echo(f"Overall Score: {result.score:.1f}/10 (threshold: {threshold}/10)")
    typer.echo("")
    typer.echo("Dimensions:")
    for dim, score in sorted(result.dimensions.items()):
        bar = "█" * int(score) + "░" * (10 - int(score))
        typer.echo(f"  {dim.replace('_', ' ').title():25s} {bar} {score:.0f}/10")
    typer.echo("")
    typer.echo("Feedback:")
    typer.echo(f"  {result.feedback}")
    typer.echo("")


def _get_interactive_action() -> str:
    """Prompt user for action in interactive mode.

    Returns:
        One of "retry", "abort", or "continue".
    """
    typer.echo("")
    typer.echo("Options:")
    typer.echo("  [1] Retry with feedback (auto-tune)")
    typer.echo("  [2] Abort (discard current output)")
    typer.echo("  [3] Continue (use as-is)")
    typer.echo("")
    while True:
        choice = typer.prompt("Choose (1-3)", default="1")
        if choice in ("1", "2", "3"):
            return {"1": "retry", "2": "abort", "3": "continue"}[choice]
        typer.echo("Invalid choice. Enter 1, 2, or 3.")
