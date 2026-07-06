"""Tests for the AI GATEWAY service (Phase 9)."""

from pathlib import Path

import pytest
import yaml

from gateway.config import load_gateway_config, GatewayConfig, RoutingRule
from gateway.cache import ResponseCache
from gateway.rate_limiter import RateLimiter
from gateway.llm import route_request
from gateway.models import ChatCompletionRequest, Message


# ── Config ───────────────────────────────────────────────────────────


class TestConfigLoading:
    def test_default_on_missing_file(self):
        config = load_gateway_config(Path("nonexistent.yaml"))
        assert isinstance(config, GatewayConfig)
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert config.routing == []

    def test_load_from_dict(self):
        raw = {
            "host": "127.0.0.1",
            "port": 9000,
            "routing": [
                {"pattern": "test", "provider": "openai", "model": "gpt-4o"}
            ],
            "providers": {"openai": {"api_key": "sk-test"}},
        }
        config = GatewayConfig(**raw)
        assert config.host == "127.0.0.1"
        assert len(config.routing) == 1
        assert config.routing[0].pattern == "test"

    def test_roundtrip_yaml(self, tmp_path):
        cfg_path = tmp_path / "gateway.yaml"
        data = {
            "host": "0.0.0.0",
            "port": 8000,
            "routing": [{"pattern": "sales", "provider": "openai", "model": "gpt-4o"}],
            "providers": {"openai": {"api_key": "sk-test"}},
        }
        cfg_path.write_text(yaml.dump(data), encoding="utf-8")
        config = load_gateway_config(cfg_path)
        assert len(config.routing) == 1
        assert config.routing[0].provider == "openai"


# ── Cache ────────────────────────────────────────────────────────────


class TestResponseCache:
    def test_miss_on_empty(self):
        cache = ResponseCache()
        req = ChatCompletionRequest(messages=[Message(role="user", content="hi")])
        assert cache.get(req) is None

    def test_set_and_get(self):
        cache = ResponseCache(default_ttl=300)
        req = ChatCompletionRequest(messages=[Message(role="user", content="hi")])
        resp = _fake_response()
        cache.set(req, resp)
        cached = cache.get(req)
        assert cached is not None
        assert cached.model == resp.model

    def test_ttl_expiry(self):
        cache = ResponseCache(default_ttl=0)  # 0 TTL = expire immediately
        req = ChatCompletionRequest(messages=[Message(role="user", content="hi")])
        cache.set(req, _fake_response())
        assert cache.get(req) is None

    def test_invalidate_all(self):
        cache = ResponseCache()
        req = ChatCompletionRequest(messages=[Message(role="user", content="hi")])
        cache.set(req, _fake_response())
        assert cache.size == 1
        cache.invalidate()
        assert cache.size == 0

    def test_different_requests_different_keys(self):
        cache = ResponseCache()
        req1 = ChatCompletionRequest(messages=[Message(role="user", content="hello")])
        req2 = ChatCompletionRequest(messages=[Message(role="user", content="world")])
        cache.set(req1, _fake_response())
        assert cache.get(req2) is None


# ── Rate Limiter ─────────────────────────────────────────────────────


class TestRateLimiter:
    def test_allows_first_request(self):
        limiter = RateLimiter(default_rpm=10)
        ok, wait = limiter.check("test")
        assert ok is True
        assert wait == 0.0

    def test_blocks_excess(self):
        limiter = RateLimiter(default_rpm=1)
        ok, _ = limiter.check("test")
        assert ok is True
        ok, wait = limiter.check("test")
        assert ok is False
        assert wait > 0

    def test_per_provider_isolation(self):
        limiter = RateLimiter(default_rpm=1, overrides={"slow": 0})
        ok, _ = limiter.check("slow")
        assert ok is False  # 0 RPM = always blocked
        ok, _ = limiter.check("fast")
        assert ok is True


# ── Routing ──────────────────────────────────────────────────────────


class TestRouting:
    def _make_config(self, rules):
        return GatewayConfig(
            routing=[RoutingRule(**r) for r in rules],
            providers={"openai": {}, "opencode": {}},
        )

    def test_match_by_user_message(self):
        config = self._make_config([
            {"pattern": "invoice", "provider": "openai", "model": "gpt-4o"},
        ])
        req = ChatCompletionRequest(messages=[
            Message(role="user", content="Generate invoice summary flow"),
        ])
        provider, model = route_request(config, req)
        assert provider == "openai"
        assert model == "gpt-4o"

    def test_default_when_no_match(self):
        config = self._make_config([])
        req = ChatCompletionRequest(messages=[
            Message(role="user", content="whatever"),
        ])
        provider, _ = route_request(config, req)
        assert provider == "openai"  # first configured provider (dict insertion order)

    def test_first_rule_wins(self):
        config = self._make_config([
            {"pattern": "sales", "provider": "openai", "model": "gpt-4o"},
            {"pattern": ".*", "provider": "opencode", "model": "deepseek"},
        ])
        req = ChatCompletionRequest(messages=[
            Message(role="user", content="sales data pipeline"),
        ])
        provider, model = route_request(config, req)
        assert provider == "openai"

    def test_case_insensitive(self):
        config = self._make_config([
            {"pattern": "SALES", "provider": "openai", "model": "gpt-4o"},
        ])
        req = ChatCompletionRequest(messages=[
            Message(role="user", content="sales report"),
        ])
        provider, _ = route_request(config, req)
        assert provider == "openai"


# ── Helpers ──────────────────────────────────────────────────────────


def _fake_response():
    from gateway.models import ChatCompletionResponse, Choice, Message, Usage
    return ChatCompletionResponse(
        id="test",
        model="test-model",
        choices=[Choice(index=0, message=Message(role="assistant", content="OK"))],
        usage=Usage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
    )
