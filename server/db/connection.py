import os
import asyncpg
from contextlib import asynccontextmanager
from typing import AsyncGenerator

DATABASE_URL = os.getenv("DATABASE_URL")
_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Initialize the connection pool."""
    global _pool
    if _pool is not None:
        return _pool

    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    _pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=5,
        max_size=20,
        command_timeout=60,
        server_settings={
            "jit": "off",
        },
    )
    return _pool


async def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    """Get the current pool (raises if not initialized)."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized. Call init_pool() first.")
    return _pool


@asynccontextmanager
async def get_conn() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a connection from the pool."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


# Convenience query functions


async def fetch(query: str, *args) -> list[asyncpg.Record]:
    """Execute a SELECT query and return all rows."""
    async with get_conn() as conn:
        return await conn.fetch(query, *args)


async def fetchrow(query: str, *args) -> asyncpg.Record | None:
    """Execute a SELECT query and return a single row."""
    async with get_conn() as conn:
        return await conn.fetchrow(query, *args)


async def execute(query: str, *args) -> str:
    """Execute an INSERT/UPDATE/DELETE query."""
    async with get_conn() as conn:
        return await conn.execute(query, *args)


async def fetchval(query: str, *args):
    """Execute a query and return a single value."""
    async with get_conn() as conn:
        return await conn.fetchval(query, *args)
