import json

from db.redis import get_redis, job_status_key, JOB_TTL_SECONDS


async def set_job_status(
    job_id: str,
    *,
    status: str,
    current_agent: str | None,
    completed_agents: list[str],
    error: str | None = None,
) -> None:
    key = job_status_key(job_id)
    payload = {
        "status": status,
        "current_agent": current_agent or "",
        "completed_agents": json.dumps(completed_agents),
        "error": error or "",
    }
    client = get_redis()
    await client.hset(key, mapping=payload)
    await client.expire(key, JOB_TTL_SECONDS)


async def get_job_status(job_id: str) -> dict | None:
    key = job_status_key(job_id)
    client = get_redis()
    data = await client.hgetall(key)

    if not data:
        return None

    return {
        "job_id": job_id,
        "status": data.get("status"),
        "current_agent": data.get("current_agent") or None,
        "completed_agents": json.loads(data.get("completed_agents", "[]")),
        "error": data.get("error") or None,
    }
