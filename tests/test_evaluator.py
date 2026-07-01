"""Unit tests for the evaluator module (parse_evaluation_response, evaluate_flow)."""

import json
import pytest
from unittest.mock import patch
from pathlib import Path

from text_to_sql_flow.evaluator import (
    evaluate_flow,
    parse_evaluation_response,
    EvaluationResult,
    THRESHOLD,
)

SAMPLE_EVALUATION_RESPONSE = json.dumps({
    "score": 8.5,
    "dimensions": {
        "correctness": 9,
        "completeness": 8,
        "spark_best_practices": 8,
        "dependency_correctness": 9,
        "code_quality": 8,
    },
    "feedback": "The flow is well-structured. All dependencies are correctly specified.",
})

SAMPLE_FLOW_JSON = json.dumps({
    "name": "TEST_FLOW",
    "description": "test",
    "steps": [
        {
            "name": "S1",
            "parents": [],
            "order": 1,
            "sql": "SELECT 1",
            "output": {"tempView": "V_S1", "table": ""},
            "description": "",
            "diagram": {"x": 80, "y": 160},
            "active": True,
            "createdDate": {"$date": "2026-05-15T01:44:25.911Z"},
        }
    ],
})


class TestParseEvaluationResponse:
    def test_parse_valid_evaluation_response(self):
        """Valid JSON parses to EvaluationResult with passed=True."""
        result = parse_evaluation_response(SAMPLE_EVALUATION_RESPONSE)
        assert result.score == 8.5
        assert result.passed is True
        assert "well-structured" in result.feedback
        assert result.dimensions["correctness"] == 9

    def test_parse_below_threshold_response(self):
        """Score below threshold sets passed=False."""
        low_score = json.dumps({"score": 5.0, "feedback": "Needs improvement", "dimensions": {"correctness": 5}})
        result = parse_evaluation_response(low_score)
        assert result.score == 5.0
        assert result.passed is False

    def test_parse_markdown_block_response(self):
        """JSON wrapped in ```json block is parsed correctly."""
        wrapped = f"```json\n{SAMPLE_EVALUATION_RESPONSE}\n```"
        result = parse_evaluation_response(wrapped)
        assert result.score == 8.5
        assert result.passed is True

    def test_parse_invalid_response_raises_error(self):
        """Non-JSON string raises ValueError."""
        with pytest.raises(ValueError, match="No JSON object found"):
            parse_evaluation_response("This is not JSON at all")

    def test_parse_missing_fields_handled(self):
        """Missing 'dimensions' defaults to empty dict, score/feedback required."""
        # Missing dimensions is OK
        resp = json.dumps({"score": 7.5, "feedback": "Good"})
        result = parse_evaluation_response(resp)
        assert result.score == 7.5
        assert result.dimensions == {}

        # Missing score raises error
        with pytest.raises(ValueError, match="score"):
            parse_evaluation_response(json.dumps({"feedback": "No score"}))

        # Missing feedback raises error
        with pytest.raises(ValueError, match="feedback"):
            parse_evaluation_response(json.dumps({"score": 8.0}))


class TestEvaluateFlow:
    def test_evaluate_flow_with_mock_llm(self, tmp_path):
        """evaluate_flow returns EvaluationResult with mocked LLM."""
        flow_file = tmp_path / "flow.json"
        flow_file.write_text(SAMPLE_FLOW_JSON)

        with patch("text_to_sql_flow.evaluator.call_llm", return_value=SAMPLE_EVALUATION_RESPONSE):
            result = evaluate_flow(flow_file)
            assert isinstance(result, EvaluationResult)
            assert result.score == 8.5
            assert result.passed is True

    def test_evaluate_flow_handles_llm_error(self, tmp_path):
        """Exception from call_llm propagates to caller."""
        flow_file = tmp_path / "flow.json"
        flow_file.write_text(SAMPLE_FLOW_JSON)

        with patch("text_to_sql_flow.evaluator.call_llm", side_effect=RuntimeError("API error")):
            with pytest.raises(RuntimeError, match="API error"):
                evaluate_flow(flow_file)

    def test_evaluate_flow_file_not_found(self):
        """Missing file raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            evaluate_flow(Path("/nonexistent/flow.json"))


class TestConstants:
    def test_threshold_constant(self):
        assert THRESHOLD == 7.0
