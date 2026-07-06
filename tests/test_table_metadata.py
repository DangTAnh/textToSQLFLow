"""Tests for table metadata parsing (JSON + DDL) and prompt integration."""

import json
from pathlib import Path

import pytest

from text_to_sql_flow.table_metadata.models import (
    TableMetadata, ColumnMetadata, TableMetadataFile,
    format_metadata_summary, format_ddl_text,
)
from text_to_sql_flow.table_metadata.parser import (
    parse_table_metadata_file, _detect_format, _parse_json,
)
from text_to_sql_flow.table_metadata.ddl_parser import parse_ddl
from text_to_sql_flow.llm.prompts import build_generation_prompt

FIXTURES = Path(__file__).parent / "fixtures"


# ── Model tests ──────────────────────────────────────────────────────


def test_column_metadata_defaults():
    c = ColumnMetadata(name="col1", type="string")
    assert c.name == "col1"
    assert c.type == "string"
    assert c.description == ""
    assert c.nullable is True
    assert c.is_key is False
    assert c.partition_column is False


def test_table_metadata_with_columns():
    t = TableMetadata(
        name="test",
        columns=[
            ColumnMetadata(name="id", type="int", is_key=True, nullable=False),
            ColumnMetadata(name="val", type="string"),
        ],
        partitioned_by=["dt"],
    )
    assert len(t.columns) == 2
    assert t.columns[0].is_key is True
    assert t.partitioned_by == ["dt"]


# ── JSON parsing ─────────────────────────────────────────────────────


def test_parse_json_object_with_tables():
    raw = json.dumps({
        "tables": [{
            "name": "t1",
            "columns": [{"name": "c1", "type": "int"}],
        }]
    })
    tables = _parse_json(raw)
    assert len(tables) == 1
    assert tables[0].name == "t1"
    assert tables[0].columns[0].name == "c1"


def test_parse_json_array():
    raw = json.dumps([
        {"name": "t1", "columns": [{"name": "c1", "type": "int"}]}
    ])
    tables = _parse_json(raw)
    assert len(tables) == 1


def test_parse_json_missing_tables_key():
    with pytest.raises(ValueError, match="'tables' key"):
        _parse_json('{"foo": "bar"}')


def test_parse_json_invalid():
    with pytest.raises(ValueError, match="Invalid JSON"):
        _parse_json("not json")


# ── DDL parsing ──────────────────────────────────────────────────────


def test_parse_ddl_basic():
    ddl = """CREATE TABLE invoice (
        invoice_id STRING NOT NULL COMMENT 'Ma hoa don',
        amount DECIMAL(18,2) NOT NULL,
        PRIMARY KEY (invoice_id)
    ) PARTITIONED BY (invoice_date)
    """
    tables = parse_ddl(ddl)
    assert len(tables) == 1
    t = tables[0]
    assert t.name == "invoice"
    assert len(t.columns) == 2
    assert t.columns[0].name == "invoice_id"
    assert t.columns[0].is_key is True
    assert t.columns[0].nullable is False
    assert t.partitioned_by == ["invoice_date"]


def test_parse_ddl_multiple_tables():
    ddl = """CREATE TABLE a (id INT); CREATE TABLE b (val STRING);"""
    tables = parse_ddl(ddl)
    assert len(tables) == 2


def test_parse_ddl_backtick_names():
    ddl = "CREATE TABLE `schema`.`table` (id INT)"
    tables = parse_ddl(ddl)
    assert len(tables) == 1
    assert tables[0].name == "table"


def test_parse_ddl_skip_indexes():
    ddl = """CREATE TABLE t (id INT, INDEX idx (id) USING GLOBAL)")
    )"""
    tables = parse_ddl(ddl)
    assert len(tables) == 1
    assert len(tables[0].columns) == 1  # only id, not the index line


# ── File detection ───────────────────────────────────────────────────


def test_detect_json_ext():
    assert _detect_format(Path("x.json")) == "json"


def test_detect_ddl_ext():
    assert _detect_format(Path("x.sql")) == "ddl"
    assert _detect_format(Path("x.ddl")) == "ddl"


def test_detect_unknown():
    assert _detect_format(Path("x.txt")) == "unknown"


# ── File parsing ─────────────────────────────────────────────────────


def test_parse_json_file():
    tables = parse_table_metadata_file(FIXTURES / "sample_schema.json")
    assert len(tables) == 2
    assert tables[0].name == "invoice"
    assert len(tables[0].columns) == 5
    assert tables[0].columns[0].is_key is True
    assert tables[0].partitioned_by == ["invoice_date"]


def test_parse_ddl_file():
    tables = parse_table_metadata_file(FIXTURES / "sample_schema.ddl")
    assert len(tables) == 2
    invoice = next(t for t in tables if t.name == "invoice")
    assert invoice.columns[0].is_key is True
    assert invoice.partitioned_by == ["invoice_date"]
    assert invoice.columns[2].type == "DECIMAL(18,2)"


def test_parse_file_not_found():
    with pytest.raises(FileNotFoundError):
        parse_table_metadata_file(Path("nonexistent.json"))


# ── Format helpers ───────────────────────────────────────────────────


def test_format_metadata_summary():
    tables = [TableMetadata(name="t", columns=[
        ColumnMetadata(name="id", type="int", is_key=True),
        ColumnMetadata(name="val", type="string"),
    ])]
    result = format_metadata_summary(tables)
    assert "t" in result
    assert "id int PK" in result
    assert "val string" in result


def test_format_ddl_text():
    tables = [TableMetadata(
        name="t",
        columns=[ColumnMetadata(name="id", type="int", is_key=True, nullable=False)],
        partitioned_by=["dt"],
    )]
    result = format_ddl_text(tables)
    assert "CREATE TABLE t" in result
    assert "PRIMARY KEY (id)" in result
    assert "PARTITIONED BY (dt)" in result


# ── Prompt integration ───────────────────────────────────────────────


def test_prompt_without_metadata():
    sys_p, user_p = build_generation_prompt("test desc")
    assert "test desc" in user_p
    assert "Available Tables" not in user_p


def test_prompt_with_metadata():
    tables = [TableMetadata(name="t1", columns=[
        ColumnMetadata(name="id", type="int", is_key=True),
    ])]
    sys_p, user_p = build_generation_prompt("test desc", table_metadata=tables)
    assert "t1" in user_p
    assert "id int PK" in user_p


def test_prompt_with_ddl():
    tables = [TableMetadata(name="t1", columns=[
        ColumnMetadata(name="id", type="int", is_key=True, nullable=False),
    ])]
    sys_p, user_p = build_generation_prompt("test desc", table_metadata=tables, include_ddl=True)
    assert "CREATE TABLE t1" in user_p
    assert "NOT NULL" in user_p
