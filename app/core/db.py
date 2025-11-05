# app/core/db.py
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg

DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> Optional[asyncpg.Pool]:
    global _pool
    if _pool is None and DATABASE_URL:
        _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    return _pool


@asynccontextmanager
async def db():
    pool = await get_pool()
    if pool is None:
        raise RuntimeError("DATABASE_URL is not set")
    async with pool.acquire() as conn:
        yield conn
