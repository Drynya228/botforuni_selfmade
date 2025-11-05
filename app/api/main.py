# app/api/main.py
from fastapi import FastAPI, Request
from loguru import logger

from app.bot_runtime import process_update
from app.core.db import DATABASE_URL, get_pool
from app.core.init_db import ensure_schema

app = FastAPI(title="Telegram Chat Summarizer Bot")


@app.on_event("startup")
async def _startup():
    try:
        await ensure_schema()
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error(f"DB ensure error: {exc}")

@app.get("/")
async def root():
    return {"status": "ok", "service": "bot"}

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}


@app.get("/dbz")
async def db_probe():
    if not DATABASE_URL:
        return {"db": "not-configured"}
    try:
        pool = await get_pool()
        if pool is None:
            return {"db": "not-configured"}
        async with pool.acquire() as conn:
            version = await conn.fetchval("select version()")
        return {"db": "ok", "version": version}
    except Exception as exc:  # pragma: no cover - runtime diagnostics
        return {"db": "error", "error": str(exc)}


@app.post("/tg-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    await process_update(data)
    return {"ok": True}
