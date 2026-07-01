"""Unit tests for the flow JSON parser (parse_flow_response)."""

import pytest

from text_to_sql_flow.parsers.flow_parser import parse_flow_response

# A minimal valid flow JSON for use across test cases
MINIMAL_FLOW_JSON = """{
    "name": "TEST_PARSER",
    "description": "parser test",
    "steps": [
        {
            "name": "STEP_1",
            "parents": [],
            "order": 1,
            "sql": "SELECT 1",
            "output": {"tempView": "V_T1", "table": ""},
            "description": "",
            "diagram": {"x": 80, "y": 160},
            "active": true,
            "createdDate": {"$date": "2026-05-15T01:44:25.911Z"}
        }
    ]
}"""


class TestParsePureJson:
    def test_parse_pure_json(self):
        """Pure JSON string parses correctly."""
        flow = parse_flow_response(MINIMAL_FLOW_JSON)
        assert flow.name == "TEST_PARSER"
        assert len(flow.steps) == 1
        assert flow.steps[0].name == "STEP_1"

    def test_parse_preserves_field_values(self):
        flow = parse_flow_response(MINIMAL_FLOW_JSON)
        step = flow.steps[0]
        assert step.order == 1
        assert step.sql == "SELECT 1"
        assert step.diagram.x == 80
        assert step.diagram.y == 160


class TestParseMarkdown:
    def test_parse_markdown_block(self):
        """JSON wrapped in ```json ... ``` parses correctly."""
        wrapped = f"```json\n{MINIMAL_FLOW_JSON}\n```"
        flow = parse_flow_response(wrapped)
        assert flow.name == "TEST_PARSER"

    def test_parse_markdown_without_lang(self):
        """JSON wrapped in plain ``` ... ``` (no language tag) parses correctly."""
        wrapped = f"```\n{MINIMAL_FLOW_JSON}\n```"
        flow = parse_flow_response(wrapped)
        assert flow.name == "TEST_PARSER"

    def test_parse_markdown_with_extra_text(self):
        """JSON inside ```json with explanatory text before/after the block."""
        text = f"Here is the generated flow:\n\n```json\n{MINIMAL_FLOW_JSON}\n```\n\nLet me know if you need changes."
        flow = parse_flow_response(text)
        assert flow.name == "TEST_PARSER"


class TestParseWithExtraText:
    def test_extra_text_before_and_after(self):
        """Explanatory text around raw JSON (no code block)."""
        text = f"Sure! Here is the flow you requested:\n{MINIMAL_FLOW_JSON}\nI hope this helps!"
        flow = parse_flow_response(text)
        assert flow.name == "TEST_PARSER"

    def test_extra_whitespace_and_newlines(self):
        """JSON with lots of surrounding whitespace."""
        text = f"\n\n  \n{MINIMAL_FLOW_JSON}\n  \n\n"
        flow = parse_flow_response(text)
        assert flow.name == "TEST_PARSER"

    def test_leading_text_no_markdown(self):
        """Only leading text, no trailing, no markdown markers."""
        text = f"The flow is:\n{MINIMAL_FLOW_JSON}"
        flow = parse_flow_response(text)
        assert flow.name == "TEST_PARSER"


class TestParseErrors:
    def test_no_json_at_all(self):
        """String with no JSON raises ValueError."""
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_flow_response("This is not a JSON response at all")

    def test_malformed_json(self):
        """Malformed JSON with syntax error raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse JSON"):
            parse_flow_response('{"name": "broken", steps: [}')

    def test_empty_string(self):
        """Empty string raises ValueError."""
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_flow_response("")

    def test_valid_json_but_wrong_structure(self):
        """Valid JSON that doesn't match Flow schema raises ValueError."""
        with pytest.raises(ValueError, match="Flow validation failed"):
            parse_flow_response('{"not": "a flow"}')
