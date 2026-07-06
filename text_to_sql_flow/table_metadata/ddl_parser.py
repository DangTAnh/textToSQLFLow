"""Regex-based DDL parser for CREATE TABLE statements.

Parses basic Spark SQL DDL: column definitions, types, PRIMARY KEY,
PARTITIONED BY, COMMENT, NOT NULL. Skips indexes, storage clauses.
"""

import re
import logging
from text_to_sql_flow.table_metadata.models import TableMetadata, ColumnMetadata

logger = logging.getLogger(__name__)

# Regex: CREATE TABLE [IF NOT EXISTS] <name>
RE_CREATE_TABLE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?"
    r"(?:`([^`]+)`(?:\.`([^`]+)`)?|(\w+)(?:\.(\w+))?)",
    re.IGNORECASE,
)

# Regex: column line — <name> <type> [COMMENT '...'] [NOT NULL] [other constraints]
RE_COLUMN = re.compile(
    r"^\s*(?:`([^`]+)`|(\w+))\s+"
    r"([A-Za-z]\w*(?:\s*\(\s*\d+\s*(?:,\s*\d+\s*)?\))?)"
    r"(.*?)$",
    re.IGNORECASE,
)

# Extract COMMENT from column suffix
RE_COMMENT = re.compile(r"COMMENT\s+'((?:[^']|'')*)'", re.IGNORECASE)

# Extract NOT NULL
RE_NOT_NULL = re.compile(r"\bNOT\s+NULL\b", re.IGNORECASE)

# Extract PRIMARY KEY from inline or table-level constraint
RE_PRIMARY_KEY = re.compile(
    r"PRIMARY\s+KEY\s*\(([^)]+)\)", re.IGNORECASE
)

# Extract PARTITIONED BY
RE_PARTITIONED_BY = re.compile(
    r"PARTITIONED\s+BY\s*\(([^)]+)\)", re.IGNORECASE
)


def _clean_table_name(m: re.Match) -> str:
    """Extract table name from a ``CREATE TABLE`` match (handles backtick + ``schema.table``)."""
    # Groups: (backtick_schema, backtick_table, plain_schema, plain_table)
    return next(g for g in reversed(m.groups()) if g is not None)


def _clean_col_name(m: re.Match) -> str:
    """Extract column name from a column definition match."""
    # Groups: (backtick_name, plain_name, type, suffix)
    return next(g for g in m.groups()[:2] if g is not None)


def parse_ddl(text: str) -> list[TableMetadata]:
    """Parse one or more CREATE TABLE statements from *text*.

    Returns a list of :class:`TableMetadata`.
    Unparseable statements are logged and skipped.
    """
    tables: list[TableMetadata] = []
    blocks = re.split(r"(?=CREATE\s+TABLE)", text, flags=re.IGNORECASE)

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        try:
            table = _parse_single_table(block)
            if table:
                tables.append(table)
        except Exception as e:
            logger.warning("Skipping unparseable DDL block: %s", e)

    return tables


def _parse_single_table(block: str) -> TableMetadata | None:
    """Parse a single CREATE TABLE statement."""
    m = RE_CREATE_TABLE.search(block)
    if not m:
        return None
    table_name = _clean_table_name(m)

    # Extract body between outermost parentheses
    body_start = block.find("(")
    if body_start == -1:
        logger.warning("No column definition body found for table %s", table_name)
        return None

    depth, body_end = 1, body_start + 1
    while depth > 0 and body_end < len(block):
        if block[body_end] == "(":
            depth += 1
        elif block[body_end] == ")":
            depth -= 1
        body_end += 1
    body = block[body_start + 1 : body_end - 1]

    columns: list[ColumnMetadata] = []
    pk_columns: set[str] = set()
    partitioned_by: list[str] = []

    # Table-level PRIMARY KEY
    for pm in RE_PRIMARY_KEY.finditer(body):
        for name in pm.group(1).split(","):
            pk_columns.add(name.strip().strip("`"))

    # PARTITIONED BY
    pbm = RE_PARTITIONED_BY.search(block)
    if pbm:
        partitioned_by = [c.strip().strip("`") for c in pbm.group(1).split(",")]

    # Parse each column line
    for line in body.splitlines():
        line = line.strip()
        if not line or line.upper().startswith(("PRIMARY", "UNIQUE", "INDEX", "KEY", "CONSTRAINT", "FOREIGN")):
            continue

        cm = RE_COLUMN.match(line)
        if not cm:
            continue

        col_name = _clean_col_name(cm)
        col_type = cm.group(3).strip()
        suffix = cm.group(4)

        comment = ""
        cmt = RE_COMMENT.search(suffix)
        if cmt:
            comment = cmt.group(1)

        not_null = bool(RE_NOT_NULL.search(suffix))
        is_key = col_name in pk_columns

        columns.append(ColumnMetadata(
            name=col_name,
            type=col_type,
            description=comment,
            nullable=not not_null,
            is_key=is_key,
            partition_column=col_name in partitioned_by,
        ))

    return TableMetadata(
        name=table_name,
        columns=columns,
        partitioned_by=partitioned_by,
    )
