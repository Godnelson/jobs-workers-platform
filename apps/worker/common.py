from __future__ import annotations

import time
from contextlib import contextmanager

from redis import Redis


@contextmanager
def redis_lock(redis: Redis, key: str, ttl_seconds: int = 120):
    # Simple lock: SET key value NX EX ttl
    token = str(time.time())
    acquired = redis.set(key, token, nx=True, ex=ttl_seconds)
    try:
        yield bool(acquired)
    finally:
        # Best-effort unlock: only delete if still ours (basic check)
        try:
            current = redis.get(key)
            if current == token:
                redis.delete(key)
        except Exception:
            pass
