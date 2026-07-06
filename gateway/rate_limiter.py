"""Token-bucket rate limiter — per-provider requests-per-minute."""

import time


class _Bucket:
    """Token bucket for a single provider."""

    def __init__(self, rpm: int):
        self.capacity = float(rpm)
        self.tokens = float(rpm)
        self.refill_rate = rpm / 60.0  # tokens per second
        self.last_refill = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_consume(self) -> tuple[bool, float]:
        """Try to consume one token.

        Returns:
            ``(allowed, retry_after_seconds)``
        """
        if self.capacity <= 0:
            return False, float("inf")
        self._refill()
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True, 0.0
        wait = (1.0 - self.tokens) / self.refill_rate
        return False, wait


class RateLimiter:
    """Per-provider token bucket rate limiter.

    Usage::

        limiter = RateLimiter(default_rpm=60, overrides={"claude": 30})
        ok, wait = limiter.check("openai")
    """

    def __init__(self, default_rpm: int = 60, overrides: dict[str, int] | None = None):
        self._default_rpm = default_rpm
        self._overrides = overrides or {}
        self._buckets: dict[str, _Bucket] = {}

    def check(self, provider: str) -> tuple[bool, float]:
        """Check if a request for *provider* is allowed right now.

        Returns:
            ``(True, 0)`` if allowed, ``(False, retry_after_seconds)`` if rate-limited.
        """
        rpm = self._overrides.get(provider, self._default_rpm)
        if provider not in self._buckets:
            self._buckets[provider] = _Bucket(rpm)
        return self._buckets[provider].try_consume()
