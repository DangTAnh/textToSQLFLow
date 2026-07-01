"""Unit tests for Pydantic types (Flow, Step, StepOutput, etc.)."""

from datetime import datetime
from pydantic import ValidationError
import pytest

from text_to_sql_flow.types import Flow, Step, StepOutput, Diagram, CreatedDate

# Reference structure matching sample.txt — a 4-step flow
SAMPLE_FLOW_DICT = {
    "name": "TEST_FLOW",
    "description": "Test flow for unit tests",
    "steps": [
        {
            "name": "STEP_1",
            "parents": [],
            "order": 1,
            "sql": "SELECT * FROM ${TABLE}",
            "output": {"tempView": "V_STEP1", "table": ""},
            "description": "First step",
            "diagram": {"x": 80, "y": 160},
            "active": True,
            "createdDate": {"$date": "2026-05-15T01:44:25.911Z"},
        },
        {
            "name": "STEP_2",
            "parents": ["STEP_1"],
            "order": 2,
            "sql": "SELECT * FROM V_STEP1",
            "output": {"tempView": "V_STEP2", "table": "T_STEP2"},
            "description": "",
            "diagram": {"x": 240, "y": 120},
            "active": True,
            "createdDate": {"$date": "2026-05-15T01:44:25.937Z"},
        },
        {
            "name": "STEP_3",
            "parents": ["STEP_1"],
            "order": 2,
            "sql": "SELECT * FROM V_STEP1 WHERE x = 1",
            "output": {"tempView": "V_STEP3", "table": ""},
            "description": "",
            "diagram": {"x": 240, "y": 200},
            "active": True,
            "createdDate": {"$date": "2026-05-15T01:44:25.937Z"},
        },
        {
            "name": "STEP_OUTPUT",
            "parents": ["STEP_2", "STEP_3"],
            "order": 3,
            "sql": "SELECT * FROM V_STEP2 JOIN V_STEP3",
            "output": {"tempView": "V_OUTPUT", "table": "T_OUTPUT"},
            "description": "Final output step",
            "diagram": {"x": 400, "y": 160},
            "active": True,
            "createdDate": {"$date": "2026-05-15T01:44:25.955Z"},
        },
    ],
}


class TestFlow:
    def test_flow_from_sample_dict(self):
        """Create a Flow from a dict matching sample.txt structure."""
        flow = Flow.model_validate(SAMPLE_FLOW_DICT)
        assert flow.name == "TEST_FLOW"
        assert flow.description == "Test flow for unit tests"
        assert len(flow.steps) == 4

    def test_step_names_match(self):
        flow = Flow.model_validate(SAMPLE_FLOW_DICT)
        names = [s.name for s in flow.steps]
        assert names == ["STEP_1", "STEP_2", "STEP_3", "STEP_OUTPUT"]

    def test_step_parents(self):
        flow = Flow.model_validate(SAMPLE_FLOW_DICT)
        assert flow.steps[0].parents == []
        assert flow.steps[1].parents == ["STEP_1"]
        assert flow.steps[3].parents == ["STEP_2", "STEP_3"]


class TestStep:
    def test_minimal_step(self):
        """Create a Step with only required fields."""
        step = Step(
            name="MINIMAL",
            order=1,
            sql="SELECT 1",
            output=StepOutput(tempView="V_MIN"),
            diagram=Diagram(x=0, y=0),
            createdDate=CreatedDate(date=datetime(2026, 1, 1)),
        )
        assert step.name == "MINIMAL"
        assert step.parents == []  # default
        assert step.description == ""  # default
        assert step.active is True  # default

    def test_step_output_defaults(self):
        """StepOutput has correct defaults."""
        out = StepOutput(tempView="V_TEST", table="")
        assert out.appendType == "REPLACE"
        assert out.kafkaGroup == ""


class TestCreatedDate:
    def test_alias_parsing(self):
        """CreatedDate accepts $date alias."""
        cd = CreatedDate.model_validate({"$date": "2026-05-15T01:44:25.911Z"})
        assert isinstance(cd.date, datetime)
        assert cd.date.year == 2026
        assert cd.date.month == 5

    def test_direct_construction(self):
        """CreatedDate can be constructed directly with a datetime."""
        dt = datetime(2026, 6, 1, 12, 0, 0)
        cd = CreatedDate(date=dt)
        assert cd.date == dt

    def test_serialization_uses_alias(self):
        """model_dump with by_alias outputs $date key."""
        cd = CreatedDate.model_validate({"$date": "2026-05-15T01:44:25.911Z"})
        dumped = cd.model_dump(by_alias=True)
        assert "$date" in dumped
        assert "date" not in dumped


class TestFlowSerialization:
    def test_flow_to_serializable_dict(self):
        flow = Flow.model_validate(SAMPLE_FLOW_DICT)
        data = flow.to_serializable_dict()
        assert data["name"] == "TEST_FLOW"
        assert "$date" in data["steps"][0]["createdDate"]

    def test_model_dump_by_alias(self):
        flow = Flow.model_validate(SAMPLE_FLOW_DICT)
        data = flow.model_dump(by_alias=True, mode="json")
        assert data["steps"][0]["createdDate"]["$date"].startswith("2026")


class TestValidation:
    def test_invalid_flow_missing_name(self):
        with pytest.raises(ValidationError):
            Flow.model_validate({"steps": []})

    def test_invalid_step_missing_sql(self):
        with pytest.raises(ValidationError):
            Step.model_validate({"name": "BAD"})  # missing order, sql, output
