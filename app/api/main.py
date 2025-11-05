# app/api/main.py

from fastapi import FastAPI
from loguru import logger

app = FastAPI(title="Telegram Chat Summarizer Bot")

@app.get("/healthz")
async def health_check():
    """Проверка состояния сервиса"""
    logger.info("Health check OK")
    return {"status": "ok"}

@app.post("/tg-webhook")
async def telegram_webhook():
    """Заглушка для вебхука Telegram (пока что пустая)"""
    logger.info("Received webhook request")
    return {"ok": True}

