import asyncio
import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.services.indexing import run_indexing_job

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


frontend_origin = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
PORT = os.getenv("PORT")

app = FastAPI(title="the search thing")

app.add_middleware(
    CORSMiddleware,  # type: ignore[ arg-type ]
    allow_origins=[frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _log_task_exception(task: "asyncio.Task[None]", job_id: str) -> None:
    try:
        task.result()
    except Exception:
        logger.exception("[job:%s] Indexing job failed", job_id)


if __name__ == "__main__":
    import uvicorn

    try:
        port_value = int(PORT) if PORT is not None else 8000
    except ValueError:
        port_value = 8000
    uvicorn.run(app, host="0.0.0.0", port=port_value)
