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


_TRUNCATION_HINT = (
    " The response appears to be incomplete (truncated). "
    "This usually means the model hit the max_tokens limit. "
    "Go to Configuration (2) -> Gateway (3) -> '4 Set max_tokens' "
    "to increase it, or edit text-to-sql-flow.yaml directly."
)


def _looks_truncated(raw: str) -> bool:
    """Guess if the response was cut off mid-JSON (max_tokens too low)."""
    stripped = raw.strip()
    if not stripped:
        return False
    # Starts with JSON but doesn't close the top-level array+object
    first = stripped.find("{")
    if first == -1:
        return False
    # Normalise: keep what looks like the JSON block
    last = stripped.rfind("}")
    if last == -1 or last < first:
        return True  # Opening brace, no closing brace anywhere
    # Closing brace exists but the block before it
    # doesn't end with a valid JSON close pattern
    block = stripped[first:last + 1]
    if not block.endswith("]"):
        # JSON object must end with ]} for steps array, or at least }}
        return not block.endswith("}")
    return False


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
        hint = ""
        if raw_text and not raw_text.isspace():
            hint = _TRUNCATION_HINT if _looks_truncated(raw_text) else ""
        raise ValueError("No JSON object found in LLM response" + hint)

    try:
        data: dict[str, Any] = json.loads(json_str)
    except json.JSONDecodeError as e:
        hint = _TRUNCATION_HINT if _looks_truncated(raw_text) else ""
        raise ValueError(f"Failed to parse JSON from LLM response: {e}" + hint)

    try:
        return Flow.model_validate(data)
    except Exception as e:
        raise ValueError(f"Flow validation failed: {e}")


def extract_validation_error(error: Exception) -> str:
    """Extract a human-readable validation error message for retry feedback."""
    return str(error)
