"""In-memory response cache with TTL support."""

import hashlib
import json
import time
from typing import Any, Optional

from gateway.models import ChatCompletionRequest, ChatCompletionResponse


class ResponseCache:
    """Simple dict-based cache with configurable TTL.

    Keys are SHA-256 hashes of ``(model, messages)`` to avoid storing giant keys.
    No dependency on Redis — POC-appropriate.
    """

    def __init__(self, default_ttl: int = 300):
        self._data: dict[str, tuple[float, ChatCompletionResponse]] = {}
        self._default_ttl = default_ttl

    @staticmethod
    def _make_key(request: ChatCompletionRequest) -> str:
        raw = json.dumps({
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
        }, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, request: ChatCompletionRequest) -> Optional[ChatCompletionResponse]:
        """Return cached response, or ``None`` if missing / expired."""
        key = self._make_key(request)
        entry = self._data.get(key)
        if entry is None:
            return None
        expires, response = entry
        if time.monotonic() > expires:
            del self._data[key]
            return None
        return response

    def set(
        self,
        request: ChatCompletionRequest,
        response: ChatCompletionResponse,
        ttl: Optional[int] = None,
    ) -> None:
        """Cache a response for the given request."""
        key = self._make_key(request)
        self._data[key] = (time.monotonic() + (ttl or self._default_ttl), response)

    def invalidate(self, model: Optional[str] = None) -> int:
        """Remove all entries, optionally filtered by *model*. Returns count removed."""
        if model is None:
            count = len(self._data)
            self._data.clear()
            return count
        to_delete = [k for k, (_, r) in self._data.items() if r.model == model]
        for k in to_delete:
            del self._data[k]
        return len(to_delete)

    @property
    def size(self) -> int:
        return len(self._data)
