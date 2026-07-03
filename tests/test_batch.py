"""Tests for batch mode (GUI-05) and batch internals."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from text_to_sql_flow.batch import _read_descriptions, MAX_BATCH, BatchItem


class TestReadDescriptions:
    def test_reads_lines_from_file(self, tmp_path):
        f = tmp_path / "descriptions.txt"
        f.write_text("first flow\nthe second flow\nthird flow")
        assert _read_descriptions(f) == ["first flow", "the second flow", "third flow"]

    def test_skips_blank_and_comment_lines(self, tmp_path):
        f = tmp_path / "descriptions.txt"
        f.write_text("# this is a comment\n\nflow one\n\n# another comment\nflow two")
        assert _read_descriptions(f) == ["flow one", "flow two"]

    def test_strips_whitespace(self, tmp_path):
        f = tmp_path / "descriptions.txt"
        f.write_text("  flow one  \n  flow two  ")
        assert _read_descriptions(f) == ["flow one", "flow two"]

    def test_raises_on_missing_file(self):
        with pytest.raises(FileNotFoundError):
            _read_descriptions(Path("/nonexistent/file.txt"))

    def test_returns_empty_when_all_lines_skipped(self, tmp_path):
        f = tmp_path / "descriptions.txt"
        f.write_text("# comment only\n\n  \n")
        assert _read_descriptions(f) == []


class TestBatchItem:
    def test_batch_item_defaults(self):
        item = BatchItem(index=1, description="test", provider="opencode", status="success")
        assert item.index == 1
        assert item.path is None
        assert item.error is None
        assert item.timestamp is not None


class TestBatchMax:
    def test_max_batch_limit(self):
        """MAX_BATCH is defined and reasonable."""
        assert 0 < MAX_BATCH <= 1000
