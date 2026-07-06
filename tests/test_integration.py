"""Integration tests: CLI + Table Metadata + DAG Optimizer + Gateway (Phase 10).

These tests verify the full chain works end-to-end with mocked LLM calls.
"""

from pathlib import Path
from unittest.mock import patch

from text_to_sql_flow.pipeline import run_generation
from text_to_sql_flow.dag_optimizer.engine import apply_optimization
from text_to_sql_flow.llm.provider import call_llm_via_gateway

SAMPLE_DDL = """CREATE TABLE orders (
    order_id STRING NOT NULL COMMENT 'Order ID',
    customer_id STRING NOT NULL COMMENT 'Customer ID',
    amount DECIMAL(18,2) NOT NULL,
    order_date DATE NOT NULL,
    PRIMARY KEY (order_id)
) PARTITIONED BY (order_date);
"""

VALID_FLOW_JSON = """
{
  "name": "integration_test",
  "description": "Integration test flow",
  "steps": [
    {
      "name": "step1",
      "parents": [],
      "order": 0,
      "sql": "SELECT order_id, customer_id, amount FROM orders",
      "output": {"tempView": "V_ORDERS", "table": "", "appendType": "REPLACE", "kafkaGroup": ""},
      "description": "Load orders",
      "diagram": {"x": 80, "y": 40},
      "active": true,
      "createdDate": {"$date": "2026-07-06T00:00:00.000Z"}
    },
    {
      "name": "step2",
      "parents": ["step1"],
      "order": 1,
      "sql": "SELECT customer_id, SUM(amount) as total FROM V_ORDERS GROUP BY customer_id",
      "output": {"tempView": "V_SUMMARY", "table": "", "appendType": "REPLACE", "kafkaGroup": ""},
      "description": "Summarize by customer",
      "diagram": {"x": 80, "y": 120},
      "active": true,
      "createdDate": {"$date": "2026-07-06T00:00:00.000Z"}
    }
  ]
}
"""


class TestIntegration:
    def test_table_metadata_to_prompt_to_optimizer(self, tmp_path):
        """Full chain: DDL file -> parse -> prompt -> parse flow -> optimize."""
        ddl_file = tmp_path / "schema.ddl"
        ddl_file.write_text(SAMPLE_DDL, encoding="utf-8")

        with patch("text_to_sql_flow.pipeline.call_llm", return_value=VALID_FLOW_JSON):
            result_path = run_generation(
                description="Test integration",
                output_dir=tmp_path / "output",
                tables_path=ddl_file,
                optimize=True,
            )
        assert result_path.exists()
        assert result_path.suffix == ".json"

        import json
        flow = json.loads(result_path.read_text(encoding="utf-8"))
        assert flow["name"] == "integration_test"
        assert len(flow["steps"]) == 2

        # Verify DAG optimization preserved structure
        orders = {s["order"] for s in flow["steps"]}
        assert 0 in orders
        assert 1 in orders

    def test_no_optimize_flag_passthrough(self, tmp_path):
        """--no-optimize should skip optimizer, flow unchanged."""
        with patch("text_to_sql_flow.pipeline.call_llm", return_value=VALID_FLOW_JSON):
            result_path = run_generation(
                description="Test no-optimize",
                output_dir=tmp_path / "output",
                optimize=False,
            )
        assert result_path.exists()

    def test_gateway_provider_routing(self, tmp_path):
        """Gateway route_request function should route correctly."""
        from gateway.config import GatewayConfig, RoutingRule
        from gateway.llm import route_request
        from gateway.models import ChatCompletionRequest, Message

        config = GatewayConfig(
            routing=[RoutingRule(pattern="order", provider="openai", model="gpt-4o")],
            providers={"openai": {"api_key": "sk-test"}},
        )
        req = ChatCompletionRequest(messages=[
            Message(role="user", content="Generate order summary flow"),
        ])
        provider, model = route_request(config, req)
        assert provider == "openai"
        assert model == "gpt-4o"

    def test_gateway_url_passthrough(self, tmp_path):
        """When gateway_url is set but gateway is down, the CLI should fail with connection error."""
        with patch("text_to_sql_flow.llm.provider.call_llm_via_gateway") as mock_gw:
            mock_gw.side_effect = RuntimeError("Gateway unreachable")
            import pytest
            with pytest.raises(RuntimeError, match="Gateway unreachable"):
                run_generation(
                    description="Test gateway failure",
                    output_dir=tmp_path / "output",
                    gateway_url="http://localhost:19999",
                )
