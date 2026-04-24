import os

import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JOB_TTL_SECONDS = 60 * 60

_client: redis.Redis | None = None


async def init_redis() -> redis.Redis:
    global _client
    if _client is not None:
        return _client

    _client = redis.from_url(REDIS_URL, decode_responses=True)
    await _client.ping()
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def get_redis() -> redis.Redis:
    if _client is None:
        raise RuntimeError("Redis client not initialized. Call init_redis() first.")
    return _client


def job_status_key(job_id: str) -> str:
    return f"job_status:{job_id}"
