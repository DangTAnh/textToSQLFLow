"""Unit tests for the JSON file writer (write_flow_json)."""

import json
import pytest
from pathlib import Path
from datetime import datetime

from text_to_sql_flow.types import Flow, Step, StepOutput, Diagram, CreatedDate
from text_to_sql_flow.output.json_writer import write_flow_json


def _make_test_flow(name: str = "TEST_WRITER") -> Flow:
    """Helper to create a minimal Flow for writer tests."""
    return Flow(
        name=name,
        description="writer test",
        steps=[
            Step(
                name="S1",
                parents=[],
                order=1,
                sql="SELECT 1",
                output=StepOutput(tempView="V_S1"),
                description="",
                diagram=Diagram(x=0, y=0),
                active=True,
                createdDate=CreatedDate(date=datetime(2026, 1, 1)),
            )
        ],
    )


class TestWriteFlowJson:
    def test_write_flow_json(self, tmp_path):
        """Writing a flow creates the expected file."""
        flow = _make_test_flow()
        result = write_flow_json(flow, tmp_path)
        assert result.exists()
        assert result.name == "TEST_WRITER_flow.json"

    def test_write_creates_directory(self, tmp_path):
        """Writer creates intermediate directories."""
        nested = tmp_path / "sub" / "dir"
        flow = _make_test_flow()
        result = write_flow_json(flow, nested)
        assert result.exists()
        assert nested.exists()

    def test_written_file_is_valid_json(self, tmp_path):
        """Written file can be parsed as JSON with expected keys."""
        flow = _make_test_flow()
        result = write_flow_json(flow, tmp_path)
        with open(result) as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert "name" in data
        assert "steps" in data

    def test_output_path_is_absolute(self, tmp_path):
        """Returned path is absolute and points to an existing file."""
        flow = _make_test_flow()
        result = write_flow_json(flow, tmp_path)
        assert result.is_absolute()
        assert result.exists()
