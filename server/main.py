import logging
import logging.config
import uvicorn
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)

logging.config.dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
            "datefmt": "%H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    # keep uvicorn's own loggers quiet (they already have their own format)
    "loggers": {
        "uvicorn": {"propagate": False},
        "uvicorn.error": {"propagate": False},
        "uvicorn.access": {"propagate": False},
    },
})

from db import init_pool, close_pool, init_redis, close_redis
from api import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_redis()
    await init_pool()
    yield
    await close_redis()
    await close_pool()


def create_app() -> FastAPI:
    app = FastAPI(title="ivy", lifespan=lifespan)
    app.include_router(router, prefix="/api")
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
