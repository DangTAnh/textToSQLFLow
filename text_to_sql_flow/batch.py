"""Batch mode — process multiple business descriptions from a text file.

GUI-05: Read a .txt file with one description per line, generate flows
for all descriptions, show a summary table at the end.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from text_to_sql_flow.pipeline import run_evaluation_loop

logger = logging.getLogger(__name__)

MAX_BATCH = 100


@dataclass
class BatchItem:
    """Result of processing one description in a batch."""
    index: int
    description: str
    provider: str
    status: str  # "success" | "failed"
    flow_id: str = ""
    path: Optional[Path] = None
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def run_batch(
    file_path: Path,
    output_dir: Path = Path("./output"),
    provider: str = "opencode",
    config_path: Optional[Path] = None,
    html: bool = False,
    tables_path: Optional[Path] = None,
    tables_include_ddl: bool = False,
    optimize: bool = True,
) -> list[BatchItem]:
    """Run batch generation from a text file.

    Args:
        file_path: Path to .txt file with one description per line.
        output_dir: Root output directory (each flow gets a subdir).
        provider: LLM provider for all descriptions.
        config_path: Optional YAML config file path.
        html: If True, generate HTML report alongside JSON.
        tables_path: Optional path to table metadata file (JSON or DDL).
        tables_include_ddl: If True, inject full DDL text instead of summary.

    Returns:
        List of BatchItem results.
    """
    descriptions = _read_descriptions(file_path)
    if not descriptions:
        logger.warning("No descriptions found in %s", file_path)
        return []

    if len(descriptions) > MAX_BATCH:
        logger.warning(
            "File contains %d descriptions, capping to %d",
            len(descriptions), MAX_BATCH,
        )
        descriptions = descriptions[:MAX_BATCH]

    console = Console()
    results: list[BatchItem] = []

    console.print(f"[bold cyan]Batch mode:[/] {len(descriptions)} description(s)")
    console.print(f"[dim]Provider:[/] {provider}")
    console.print()

    for i, desc in enumerate(descriptions, 1):
        flow_id = f"flow-{uuid.uuid4().hex[:8]}"
        item_output = output_dir / flow_id
        console.print(
            f"  [{i}/{len(descriptions)}] "
            f"[bold]{desc[:60]}{'...' if len(desc) > 60 else ''}[/]"
        )

        with console.status(f"  Generating...", spinner="dots"):
            try:
                result_path = run_evaluation_loop(
                    description=desc,
                    output_dir=item_output,
                    auto=True,
                    provider=provider,
                    config_path=config_path,
                    html=html,
                    tables_path=tables_path,
                    tables_include_ddl=tables_include_ddl,
                    optimize=optimize,
                )
                results.append(BatchItem(
                    index=i,
                    description=desc,
                    provider=provider,
                    status="success",
                    flow_id=flow_id,
                    path=result_path,
                ))
                console.print(f"  [green]✓[/] → {result_path}")
            except Exception as e:
                results.append(BatchItem(
                    index=i,
                    description=desc,
                    provider=provider,
                    status="failed",
                    flow_id=flow_id,
                    error=str(e),
                ))
                console.print(f"  [red]✗[/] {e}")

    _show_batch_summary(console, results)
    return results


def _read_descriptions(file_path: Path) -> list[str]:
    """Read descriptions from a text file.

    Skips blank lines and lines starting with ``#``.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Description file not found: {file_path}")

    lines = file_path.read_text(encoding="utf-8").splitlines()
    descriptions: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            descriptions.append(stripped)
    return descriptions


def _show_batch_summary(console: Console, results: list[BatchItem]) -> None:
    """Display batch summary table."""
    console.print()
    success = sum(1 for r in results if r.status == "success")

    table = Table(
        title=f"Batch Summary — {success}/{len(results)} successful",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Flow ID", width=14)
    table.add_column("Description", width=40, overflow="fold")
    table.add_column("Status", width=10)
    table.add_column("Output")

    for r in results:
        status_style = "green" if r.status == "success" else "red"
        status_text = r.status
        if r.status == "failed" and r.error:
            status_text = f"failed: {r.error[:30]}"

        short_desc = r.description[:50] + "..." if len(r.description) > 50 else r.description
        output_str = str(r.path) if r.path else "—"

        table.add_row(
            str(r.index),
            r.flow_id,
            short_desc,
            f"[{status_style}]{status_text}[/]",
            f"[dim]{output_str}[/]",
        )

    console.print(table)
    console.print()
