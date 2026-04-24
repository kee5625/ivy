import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api import router
from db import init_pool, close_pool
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
JOB_TTL_SECONDS = 60 * 60

redis_client: redis.Redis | None = None

def job_status_key(job_id: str) -> str:
    return f"job_status:{job_id}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global redis_client
    redis_client = redis.from_url(
        REDIS_URL,
        decode_response=True,
    )
    await redis_client.ping()
    await init_pool()
    yield
    # Shutdown
    await redis_client.close()
    await close_pool()


def create_app() -> FastAPI:
    app = FastAPI(title="ivy", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
