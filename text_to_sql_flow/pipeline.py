"""Pipeline controller — wires together the LLM client, prompts, parser, and writer.

Orchestrates the end-to-end flow:
1. Build prompts from business description
2. Call LLM (with API-level retry in ``client.py``)
3. Parse and validate JSON (with format-level retry up to MAX_RETRIES)
4. Write validated Flow to JSON file
"""

import logging
from pathlib import Path
from typing import Optional

from text_to_sql_flow.llm.client import call_llm
from text_to_sql_flow.llm.prompts import build_generation_prompt
from text_to_sql_flow.parsers.flow_parser import parse_flow_response, extract_validation_error
from text_to_sql_flow.output.json_writer import write_flow_json
from text_to_sql_flow.types import Flow

logger = logging.getLogger(__name__)
MAX_RETRIES = 3


def run_generation(description: str, output_dir: Path) -> Path:
    """Execute the full generation pipeline.

    Args:
        description: Business description of the Spark SQL ETL flow.
        output_dir: Directory to write the output JSON file.

    Returns:
        Path to the generated JSON file.

    Raises:
        RuntimeError: If generation fails after all retries.
    """
    system_prompt, user_prompt = build_generation_prompt(description)
    last_error: Optional[str] = None

    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("Generation attempt %d/%d", attempt, MAX_RETRIES)

        # Step 1: Call LLM
        try:
            response_text = call_llm(system_prompt, user_prompt)
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
        return output_path

    raise RuntimeError(
        f"Generation failed after {MAX_RETRIES} retries. Last error: {last_error}"
    )
