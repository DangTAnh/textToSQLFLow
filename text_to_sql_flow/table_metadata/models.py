"""Pydantic models for table metadata (schemas, columns, DDL parse results)."""

from pydantic import BaseModel, Field


class ColumnMetadata(BaseModel):
    """A single column in a database table."""

    name: str
    type: str
    description: str = ""
    nullable: bool = True
    is_key: bool = False
    partition_column: bool = False


class TableMetadata(BaseModel):
    """Metadata describing one database table / source."""

    name: str
    description: str = ""
    columns: list[ColumnMetadata] = Field(default_factory=list)
    partitioned_by: list[str] = Field(default_factory=list)


class TableMetadataFile(BaseModel):
    """Root model for a JSON file containing one or more table definitions."""

    tables: list[TableMetadata]


def format_metadata_summary(tables: list[TableMetadata]) -> str:
    """Render a human-readable summary of available tables for prompt injection."""
    lines = ["## Available Tables\n"]
    for t in tables:
        cols = ", ".join(
            f"{c.name} {c.type}{' PK' if c.is_key else ''}{' (partition)' if c.partition_column else ''}"
            for c in t.columns
        )
        desc = f" — {t.description}" if t.description else ""
        lines.append(f"- **{t.name}**{desc}: columns = {cols}")
    return "\n".join(lines)


def format_ddl_text(tables: list[TableMetadata]) -> str:
    """Render full DDL-style text for each table (for --tables-include-ddl)."""
    parts = []
    for t in tables:
        cols = []
        for c in t.columns:
            nullable = " NOT NULL" if not c.nullable else ""
            comment = f" COMMENT '{c.description}'" if c.description else ""
            cols.append(f"    {c.name} {c.type}{nullable}{comment}")
        pk_cols = [c.name for c in t.columns if c.is_key]
        if pk_cols:
            cols.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")

        ddl = f"CREATE TABLE {t.name} (\n" + ",\n".join(cols) + "\n)"
        if t.partitioned_by:
            ddl += f"\nPARTITIONED BY ({', '.join(t.partitioned_by)})"
        parts.append(ddl)
    return "\n\n".join(parts)
