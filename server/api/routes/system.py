from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

router = APIRouter(tags=["system"])


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


@router.get("/")
async def root() -> dict[str, str]:
    return {"message": "ivy server is running"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ivy-server"}


@router.get("/health/live")
async def liveness() -> dict[str, str]:
    return {"status": "live", "service": "ivy-server"}


@router.get("/health/ready")
async def readiness() -> dict[str, Any]:
    return {
        "status": "ready",
        "service": "ivy-server",
        "checks": {},
    }
