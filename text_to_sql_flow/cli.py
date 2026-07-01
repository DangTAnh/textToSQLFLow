"""CLI entry point for TextToSQLFlow.

Uses Typer for command-line parsing with automatic ``--help`` support.
"""

import typer
from pathlib import Path

app = typer.Typer(
    name="text-to-sql-flow",
    help="Generate Spark SQL ETL flows from business descriptions using LLM",
)


@app.command()
def generate(
    description: str = typer.Argument(
        ...,
        help="Business description of the Spark SQL ETL flow",
    ),
    output: Path = typer.Option(
        "./output",
        "--output",
        "-o",
        help="Output directory for generated flow files",
        file_okay=False,
        dir_okay=True,
    ),
):
    """Generate a Spark SQL flow from a business description.

    Calls an LLM to analyze the description and produce a structured
    Spark SQL ETL flow definition, then writes the result as a JSON file.
    """
    # Lazy import — pipeline module is created in Plan 02
    from text_to_sql_flow.pipeline import run_generation

    result_path = run_generation(description=description, output_dir=output)
    typer.echo(f"Flow generated successfully: {result_path}")
