import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from api import router
from db import init_pool, close_pool, init_redis, close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await init_pool()
    yield
    await close_redis()
    await close_pool()


def create_app() -> FastAPI:
    app = FastAPI(title="ivy", lifespan=lifespan)
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
