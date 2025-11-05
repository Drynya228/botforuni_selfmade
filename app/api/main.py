# app/api/main.py
from fastapi import FastAPI, Request
from loguru import logger
from app.bot_runtime import process_update
from app.core.init_db import ensure_schema

app = FastAPI(title="Telegram Chat Summarizer Bot")

@app.on_event("startup")
async def _startup():
    await ensure_schema()
    logger.info("DB schema ensured")

@app.get("/")
async def root():
    return {"status": "ok", "service": "bot"}

@app.get("/healthz")
async def health_check():
    return {"status": "ok"}

@app.post("/tg-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    await process_update(data)
    return {"ok": True}
