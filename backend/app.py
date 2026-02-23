import logging
import os
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from gremlin_python.driver.client import Client
from gremlin_python.driver.serializer import GraphSONSerializersV2d0

from parse.parse import parse_pdf_bytes

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


load_dotenv()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
GREMLIN_ENDPOINT = os.getenv("GREMLIN_ENDPOINT", "")
GREMLIN_DATABASE = os.getenv("GREMLIN_DATABASE", "ivy-db")
GREMLIN_GRAPH = os.getenv("GREMLIN_GRAPH", "storygraph")
GREMLIN_KEY = os.getenv("GREMLIN_KEY", "")
PORT = os.getenv("PORT", "8000")


def _get_gremlin_username(database: str, graph: str) -> str:
    return f"/dbs/{database}/colls/{graph}"


app = FastAPI(title="ivy")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _is_gremlin_configured() -> bool:
    return bool(GREMLIN_ENDPOINT and GREMLIN_KEY)


def _build_gremlin_client() -> Client:
    return Client(
        GREMLIN_ENDPOINT,
        "g",
        username=_get_gremlin_username(GREMLIN_DATABASE, GREMLIN_GRAPH),
        password=GREMLIN_KEY,
        message_serializer=GraphSONSerializersV2d0(),
    )


@app.on_event("startup")
async def startup_gremlin_client() -> None:
    if not _is_gremlin_configured():
        logger.warning("Gremlin not configured. Set GREMLIN_ENDPOINT and GREMLIN_KEY.")
        app.state.gremlin_client = None
        return

    app.state.gremlin_client = _build_gremlin_client()
    logger.info(
        "Gremlin client initialized for db=%s graph=%s", GREMLIN_DATABASE, GREMLIN_GRAPH
    )


@app.on_event("shutdown")
async def shutdown_gremlin_client() -> None:
    gremlin_client: Client | None = getattr(app.state, "gremlin_client", None)
    if gremlin_client is not None:
        gremlin_client.close()
        logger.info("Closed Gremlin client connection")


def _run_query_sync(gremlin_client: Client, query: str) -> list[Any]:
    result_set = gremlin_client.submit(query)
    return result_set.all().result()


async def run_query(query: str) -> list[Any]:
    gremlin_client: Client | None = getattr(app.state, "gremlin_client", None)
    if gremlin_client is None:
        raise HTTPException(status_code=503, detail="Gremlin client is not configured")
    return await run_in_threadpool(_run_query_sync, gremlin_client, query)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def readiness() -> dict[str, Any]:
    if not _is_gremlin_configured():
        raise HTTPException(
            status_code=503,
            detail="Gremlin env vars missing (GREMLIN_ENDPOINT, GREMLIN_KEY)",
        )

    try:
        result = await run_query("g.V().limit(1).count()")
    except Exception as exc:
        raise HTTPException(
            status_code=503, detail=f"Gremlin not ready: {exc}"
        ) from exc

    return {
        "status": "ready",
        "database": GREMLIN_DATABASE,
        "graph": GREMLIN_GRAPH,
        "vertex_count_probe": result,
    }


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "ivy backend is running"}


@app.post("/pdf/parse")
async def parse_pdf(file: UploadFile = File(...)) -> dict[str, object]:
    return {
        "status": "ok",
        "data": parsed,
    }


if __name__ == "__main__":
    import uvicorn

    try:
        port_value = int(PORT)
    except ValueError:
        port_value = 8000
    uvicorn.run(app, host="0.0.0.0", port=port_value)
