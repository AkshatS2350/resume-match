"""In-process token-bucket rate limiting for protected API operations."""

from dataclasses import dataclass
from time import monotonic

from fastapi import Request

from resumematch.core.errors import RateLimitedError


@dataclass
class _Bucket:
    tokens: float
    updated_at: float


class TokenBucketLimiter:
    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self._capacity = capacity
        self._refill_per_second = refill_per_second
        self._buckets: dict[str, _Bucket] = {}

    def allow(self, key: str) -> tuple[bool, int]:
        now = monotonic()
        bucket = self._buckets.setdefault(key, _Bucket(float(self._capacity), now))
        bucket.tokens = min(
            float(self._capacity),
            bucket.tokens + (now - bucket.updated_at) * self._refill_per_second,
        )
        bucket.updated_at = now
        if bucket.tokens >= 1:
            bucket.tokens -= 1
            return True, 0
        return False, max(1, int(1 / self._refill_per_second))


def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency for endpoints permitted to reach external systems."""

    token = request.headers.get("X-Session-Token", "")
    client = request.client.host if request.client is not None else "unknown"
    allowed, retry_after = request.app.state.rate_limiter.allow(f"{client}:{token}")
    if not allowed:
        raise RateLimitedError("Request rate limit exceeded", context={"retry_after": retry_after})
