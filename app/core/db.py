# app/core/db.py
import asyncpg
from contextlib import asynccontextmanager
import os

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: asyncpg.Pool | None = None

async def get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set")
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool

@asynccontextmanager
async def db():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn
