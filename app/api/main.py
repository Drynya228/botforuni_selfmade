from fastapi import FastAPI, Request
from loguru import logger
from app.bot_runtime import process_update

app = FastAPI(title="Telegram Chat Summarizer Bot")

@app.get("/")
async def root():
    return {"status": "ok", "service": "bot"}

@app.get("/healthz")
async def health_check():
    logger.info("Health check OK")
    return {"status": "ok"}

@app.post("/tg-webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    await process_update(data)
    return {"ok": True}
