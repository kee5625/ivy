from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from gremlin_python.driver.client import Client

from config import GREMLIN_DATABASE, GREMLIN_GRAPH, is_gremlin_configured


router = APIRouter(tags=["system"])


def _run_query_sync(gremlin_client: Client, query: str) -> list[Any]:
    result_set = gremlin_client.submit(query)
    return result_set.all().result()


async def _run_query(request: Request, query: str) -> list[Any]:
    gremlin_client: Client | None = getattr(request.app.state, "gremlin_client", None)
    if gremlin_client is None:
        raise HTTPException(status_code=503, detail="Gremlin client is not configured")
    return await run_in_threadpool(_run_query_sync, gremlin_client, query)


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "ivy backend is running"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(request: Request) -> dict[str, Any]:
    if not is_gremlin_configured():
        raise HTTPException(
            status_code=503,
            detail="Gremlin env vars missing (GREMLIN_ENDPOINT, GREMLIN_KEY)",
        )

    try:
        result = await _run_query(request, "g.V().limit(1).count()")
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Gremlin not ready: {exc}") from exc

    return {
        "status": "ready",
        "database": GREMLIN_DATABASE,
        "graph": GREMLIN_GRAPH,
        "vertex_count_probe": result,
    }
