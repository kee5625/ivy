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


def job_manifest_key(job_id: str) -> str:
    return f"job_manifest:{job_id}"


async def set_job_manifest(job_id: str, object_key: str) -> None:
    client = get_redis()
    await client.set(job_manifest_key(job_id), object_key, ex=JOB_TTL_SECONDS)


async def get_job_manifest(job_id: str) -> str | None:
    client = get_redis()
    return await client.get(job_manifest_key(job_id))