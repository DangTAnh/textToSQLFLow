"""Prompt templates for Spark SQL flow generation.

The system prompt instructs the LLM to produce a structured JSON
representation of a Spark SQL ETL flow based on the user's business
description.
"""

SYSTEM_PROMPT = """You are a Spark SQL ETL flow designer. Your task is to analyze a business
description and produce a structured JSON representation of the Spark SQL ETL
flow that implements it.

## Output Format

Respond with ONLY valid JSON. No explanations, no markdown outside the JSON.
The JSON must conform to this schema:

{
    "name": "<flow identifier>",
    "description": "<business description>",
    "steps": [
        {
            "name": "<unique step name>",
            "parents": ["<names of upstream steps this step depends on>"],
            "order": <integer — execution order; same order = parallel>,
            "sql": "<Spark SQL statement>",
            "output": {
                "tempView": "<spark temp view name, data cached on storage>",
                "table": "<parquet table on HDFS, empty string if not persisted>",
                "appendType": "REPLACE",
                "kafkaGroup": ""
            },
            "description": "<business description of this step>",
            "diagram": {
                "x": <integer — horizontal position>,
                "y": <integer — vertical position>
            },
            "active": true,
            "createdDate": {
                "$date": "<ISO 8601 timestamp, e.g. 2026-05-15T01:44:25.911Z>"
            }
        }
    ]
}

## Rules

1. **steps.name** — must be unique within the flow. Use UPPER_SNAKE_CASE.
2. **steps.parents** — list names of steps whose temp views or tables this step reads.
   Leave empty for the first step(s).
3. **steps.order** — execution order, ascending. Steps with the same order
   execute in parallel.
4. **steps.sql** — the Spark SQL statement. Use ${table_var} for table variables
   and $[param_var] for parameters supplied at runtime. UDFs are already
   optimized and available.
5. **steps.output.tempView** — name of the Spark temp view caching the result.
6. **steps.output.table** — target HDFS table in parquet format. Empty string
   means the result is only a temp view.
7. **steps.active** — true for enabled steps, false for disabled.
8. **Output ONLY valid JSON** — no extra text before or after.
"""


def build_generation_prompt(description: str) -> tuple[str, str]:
    """Build the (system_prompt, user_prompt) pair for flow generation.

    The system_prompt is the fixed instruction template above.
    The user_prompt wraps the user's business description.
    """
    user_prompt = (
        f"Generate a Spark SQL ETL flow for the following business requirement:\n\n"
        f"{description}\n\n"
        f"Respond with ONLY the JSON flow definition. No extra text."
    )
    return SYSTEM_PROMPT, user_prompt
