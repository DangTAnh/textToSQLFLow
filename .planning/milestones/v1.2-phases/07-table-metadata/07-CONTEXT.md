# Phase 7: Table Metadata — Context

**Gathered:** 2026-07-06
**Status:** Ready for planning
**Mode:** Smart discuss (auto-optimized)

<domain>
## Phase Boundary

User can provide table schema info (JSON/DDL) alongside business description. Tool parses metadata and feeds it into the LLM prompt for more accurate SQL flow generation with correct column names, join keys, and table references.

Requirements: TBL-01, TBL-02, TBL-03, TBL-04

</domain>

<decisions>
## Implementation Decisions

### File Format & Detection
- Detect by extension (`.json` / `.sql` / `.ddl`). Unknown extension → try JSON first → fallback DDL.
- DDL parser: regex-based, basic CREATE TABLE (columns, types, constraints, PRIMARY KEY). Skip indexes, foreign keys, storage clauses.
- No SQL parser library dependency.

### Table Metadata Schema (JSON Input)
```json
{
  "tables": [
    {
      "name": "invoice",
      "description": "Bảng hóa đơn bán hàng",
      "columns": [
        {"name": "invoice_id", "type": "string", "description": "Mã hóa đơn", "nullable": false, "is_key": true},
        {"name": "amount", "type": "decimal(18,2)", "description": "Số tiền", "nullable": false}
      ],
      "partitioned_by": ["invoice_date"]
    }
  ]
}
```

### Prompt Injection
- Inject metadata as structured text into system prompt: available tables with columns/types.
- `--tables-include-ddl` flag to include full DDL text instead of summary.

### CLI Integration
- `--tables` / `-t` flag: single file path (JSON or DDL). Single file only.
- If multiple tables → combine into one JSON array file.

### Error Handling
- File not found → clear error with path.
- Parse fail → print error + line number. Per-table failure → skip that table, warn, continue.
</decisions>

<code_context>
## Existing Code Insights

### Files to Modify
- `text_to_sql_flow/cli.py` — add `--tables` flag to `generate` and `interactive` commands
- `text_to_sql_flow/pipeline.py` — pass table metadata through pipeline
- `text_to_sql_flow/llm/prompts.py` — update `build_generation_prompt()` to accept metadata

### New Files
- `text_to_sql_flow/table_metadata/__init__.py`
- `text_to_sql_flow/table_metadata/parser.py` — parse JSON + DDL into Pydantic models
- `text_to_sql_flow/table_metadata/models.py` — Pydantic models (TableMetadata, ColumnMetadata)
- `text_to_sql_flow/table_metadata/ddl_parser.py` — regex-based DDL parser
- `tests/test_table_metadata.py`

### Established Patterns
- Pydantic models for all data structures (types.py pattern)
- Lazy imports in CLI (cli.py pattern)
- Retry + error handling (pipeline.py pattern)
</code_context>

<specifics>
## Specific Ideas

- DDL parser supports: CREATE TABLE, column defs with types, PRIMARY KEY, PARTITIONED BY, comments
- Prompt enhancement: thêm section "Available Tables" với column info sau business description
- Interactive mode: có thể hỏi user có muốn cung cấp table metadata không, hoặc dùng `--tables`
</specifics>

<deferred>
## Deferred Ideas
- Multi-file / directory input — single file đủ cho POC
- JDBC/DB connection để auto-fetch schema — POC scope, manual file đủ
- Foreign key inference — user tự define relationship trong mô tả
</deferred>
