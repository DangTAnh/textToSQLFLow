"""Table metadata parser — auto-detect JSON vs DDL, parse into TableMetadata models."""

import json
import logging
from pathlib import Path
from typing import Optional

from text_to_sql_flow.table_metadata.models import TableMetadata, TableMetadataFile
from text_to_sql_flow.table_metadata.ddl_parser import parse_ddl

logger = logging.getLogger(__name__)

_JSON_EXTENSIONS = {".json"}
_DDL_EXTENSIONS = {".sql", ".ddl", ".ddl.sql"}


def _detect_format(path: Path) -> str:
    """Detect file format by extension, with fallback to content sniffing."""
    ext = path.suffix.lower()
    if ext in _JSON_EXTENSIONS:
        return "json"
    if ext in _DDL_EXTENSIONS:
        return "ddl"
    # Unknown extension — try JSON first, then DDL
    return "unknown"


def parse_table_metadata_file(path: Path) -> list[TableMetadata]:
    """Parse a table metadata file (JSON schema or DDL) into ``TableMetadata`` list.

    Args:
        path: Path to a ``.json`` or ``.sql`` / ``.ddl`` file.

    Returns:
        List of :class:`TableMetadata` parsed from the file.

    Raises:
        FileNotFoundError: If *path* does not exist.
        ValueError: If the file format is unrecognised and both JSON and DDL parsing fail.
    """
    if not path.exists():
        raise FileNotFoundError(f"Table metadata file not found: {path}")

    fmt = _detect_format(path)
    raw = path.read_text(encoding="utf-8")

    if fmt == "json":
        return _parse_json(raw)
    elif fmt == "ddl":
        return parse_ddl(raw)
    else:
        # Try JSON first
        tables = _try_parse_json(raw)
        if tables is not None:
            return tables
        # Fallback DDL
        ddl_tables = parse_ddl(raw)
        if ddl_tables:
            return ddl_tables
        raise ValueError(
            f"Cannot parse '{path.name}': not valid JSON and no CREATE TABLE statements found. "
            f"Supported formats: .json (table schema), .sql / .ddl (DDL)."
        )


def _parse_json(raw: str) -> list[TableMetadata]:
    """Parse JSON string into list of TableMetadata."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    # Support both {"tables": [...]} and plain [...] array
    if isinstance(data, dict):
        if "tables" in data:
            return TableMetadataFile(**data).tables
        raise ValueError("JSON object must contain a 'tables' key with an array of table definitions")
    elif isinstance(data, list):
        return [TableMetadata(**t) for t in data]
    else:
        raise ValueError("JSON must be an object with 'tables' key or a plain array")


def _try_parse_json(raw: str) -> Optional[list[TableMetadata]]:
    """Attempt JSON parse without raising — returns None on failure."""
    try:
        return _parse_json(raw)
    except (ValueError, json.JSONDecodeError):
        return None
