"""End-to-end tests for the AI GATEWAY FastAPI endpoints."""

from fastapi.testclient import TestClient

from gateway.main import app
from gateway.models import Message, ChatCompletionRequest

client = TestClient(app)


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestModels:
    def test_list_models(self):
        resp = client.get("/v1/models")
        assert resp.status_code == 200
        data = resp.json()
        assert data["object"] == "list"
        assert isinstance(data["data"], list)


class TestChatCompletions:
    def test_rejects_invalid_body(self):
        resp = client.post("/v1/chat/completions", json={})
        assert resp.status_code == 422  # validation error

    def test_requires_messages(self):
        resp = client.post(
            "/v1/chat/completions",
            json={"model": "test", "messages": []},
        )
        # No user message + no upstream providers = 502 (gateway can't route/call)
        assert resp.status_code == 502

    def test_default_routing_with_no_providers(self):
        """Without configured providers, the gateway should return 502."""
        resp = client.post(
            "/v1/chat/completions",
            json={
                "model": "test",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
        # No upstream providers configured -> 502
        assert resp.status_code == 502
