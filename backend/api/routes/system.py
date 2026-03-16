from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from gremlin_python.driver.client import Client

from integrations.azure.blob_client import (
    create_blob_service_client,
    get_blob_container_name,
    get_container_client as get_blob_container_client,
    is_blob_configured,
)
from integrations.cosmos.cosmos_client import (
    create_cosmos_client,
    get_container_client as get_cosmos_container_client,
    get_cosmos_container_name,
)
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


def _dependency_status(
    *,
    required: bool,
    status: str,
    detail: str,
    **extra: Any,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "required": required,
        "status": status,
        "detail": detail,
    }
    payload.update(extra)
    return payload


async def _probe_openai_dependency(request: Request) -> dict[str, Any]:
    openai_client = getattr(request.app.state, "openai_client", None)
    if openai_client is None:
        return _dependency_status(
            required=True,
            status="not_ready",
            detail="Azure AI Foundry client is not configured",
        )

    return _dependency_status(
        required=True,
        status="ready",
        detail="Azure AI Foundry client initialized",
    )


def _probe_blob_dependency_sync() -> dict[str, Any]:
    container_name = get_blob_container_name()
    if not is_blob_configured():
        return _dependency_status(
            required=True,
            status="not_ready",
            detail="Blob storage env vars are missing",
            container=container_name,
        )

    blob_service_client = create_blob_service_client()
    if blob_service_client is None:
        return _dependency_status(
            required=True,
            status="not_ready",
            detail="Blob service client could not be created",
            container=container_name,
        )

    container_client = get_blob_container_client(blob_service_client, container_name)
    container_client.get_container_properties()
    return _dependency_status(
        required=True,
        status="ready",
        detail="Blob container reachable",
        container=container_name,
    )


async def _probe_blob_dependency() -> dict[str, Any]:
    try:
        return await run_in_threadpool(_probe_blob_dependency_sync)
    except Exception as exc:
        return _dependency_status(
            required=True,
            status="not_ready",
            detail=f"Blob container probe failed: {exc}",
            container=get_blob_container_name(),
        )


def _probe_cosmos_dependency_sync() -> dict[str, Any]:
    container_name = get_cosmos_container_name()
    cosmos_client = create_cosmos_client()
    if cosmos_client is None:
        return _dependency_status(
            required=True,
            status="not_ready",
            detail="Cosmos DB env vars are missing",
            container=container_name,
        )

    container_client = get_cosmos_container_client(cosmos_client, container_name)
    container_client.read()
    return _dependency_status(
        required=True,
        status="ready",
        detail="Cosmos container reachable",
        container=container_name,
    )


async def _probe_cosmos_dependency() -> dict[str, Any]:
    try:
        return await run_in_threadpool(_probe_cosmos_dependency_sync)
    except Exception as exc:
        return _dependency_status(
            required=True,
            status="not_ready",
            detail=f"Cosmos container probe failed: {exc}",
            container=get_cosmos_container_name(),
        )


async def _probe_gremlin_dependency(request: Request) -> dict[str, Any]:
    if not is_gremlin_configured():
        return _dependency_status(
            required=False,
            status="skipped",
            detail="Gremlin is optional and not configured",
            database=GREMLIN_DATABASE,
            graph=GREMLIN_GRAPH,
        )

    try:
        result = await _run_query(request, "g.V().limit(1).count()")
    except Exception as exc:
        return _dependency_status(
            required=False,
            status="not_ready",
            detail=f"Gremlin probe failed: {exc}",
            database=GREMLIN_DATABASE,
            graph=GREMLIN_GRAPH,
        )

    return _dependency_status(
        required=False,
        status="ready",
        detail="Gremlin graph reachable",
        database=GREMLIN_DATABASE,
        graph=GREMLIN_GRAPH,
        vertex_count_probe=result,
    )


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "ivy backend is running"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ivy-backend"}


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "live", "service": "ivy-backend"}


@router.get("/health/ready")
async def readiness(request: Request) -> dict[str, Any]:
    checks = {
        "openai": await _probe_openai_dependency(request),
        "blob": await _probe_blob_dependency(),
        "cosmos": await _probe_cosmos_dependency(),
        "gremlin": await _probe_gremlin_dependency(request),
    }
    blocking_checks = [
        name
        for name, check in checks.items()
        if check["required"] and check["status"] != "ready"
    ]
    payload = {
        "status": "ready" if not blocking_checks else "not_ready",
        "service": "ivy-backend",
        "checks": checks,
    }
    if blocking_checks:
        payload["blocking_checks"] = blocking_checks
        return JSONResponse(status_code=503, content=payload)
    return payload
