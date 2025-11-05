import asyncpg
from contextlib import asynccontextmanager
from app.core.config import cfg

_pool: asyncpg.Pool | None = None

async def _pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(dsn=cfg.DATABASE_URL, min_size=1, max_size=10)
    return _pool

@asynccontextmanager
async def db():
    pool = await _pool()
    async with pool.acquire() as conn:
        yield conn