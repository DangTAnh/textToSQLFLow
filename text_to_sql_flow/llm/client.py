"""OpenAI API client with retry logic.

Manages the connection to OpenAI's API, reads the key from environment,
and retries on transient failures with exponential backoff.
"""

import os
import time
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)


def _get_client() -> OpenAI:
    """Create an OpenAI client, reading the API key from the environment."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY environment variable is not set. "
            "Set it to your OpenAI API key before running this tool."
        )
    return OpenAI(api_key=api_key)


def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI gpt-4o with system and user prompts.

    Retries up to 3 times on API errors (rate limit 429, server 500, etc.)
    using exponential backoff with jitter.

    Returns the response text content.
    """
    client = _get_client()
    max_retries = 3
    last_error: Exception | None = None

    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )
            return response.choices[0].message.content or ""

        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                wait = (2**attempt) + (time.time() % 1)  # exponential backoff + jitter
                logger.warning(
                    "LLM call failed (attempt %d/%d): %s. Retrying in %.1fs",
                    attempt + 1,
                    max_retries,
                    e,
                    wait,
                )
                time.sleep(wait)

    raise RuntimeError(
        f"LLM call failed after {max_retries} retries: {last_error}"
    )
