"""Flexible JSON extraction and validation from LLM response text.

Handles the three common LLM response formats:
1. Pure JSON (no extra text)
2. JSON wrapped in ```json ... ``` code blocks
3. JSON with leading/trailing explanatory text
"""

import re
import json
import logging
from typing import Any

from text_to_sql_flow.types import Flow

logger = logging.getLogger(__name__)


def parse_flow_response(response_text: str) -> Flow:
    """Parse and validate Spark SQL flow JSON from LLM response text.

    Handles pure JSON, ```json code blocks, and extra text around JSON.
    Returns a validated ``Flow`` Pydantic model.

    Raises
        ValueError: If no valid JSON block can be extracted or validated.
    """
    raw_text = response_text.strip()

    # Case 2: Extract from markdown code block
    json_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?```", raw_text)
    if json_match:
        json_str = json_match.group(1).strip()
    else:
        json_str = raw_text

    # Case 3: Find first { and last } if extra text exists
    first_brace = json_str.find("{")
    last_brace = json_str.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_str = json_str[first_brace : last_brace + 1]
    else:
        raise ValueError("No JSON object found in LLM response")

    try:
        data: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from LLM response: {e}")

    try:
        return Flow.model_validate(data)
    except Exception as e:
        raise ValueError(f"Flow validation failed: {e}")


def extract_validation_error(error: Exception) -> str:
    """Extract a human-readable validation error message for retry feedback."""
    return str(error)
