from fastapi import FastAPI
from loguru import logger

app = FastAPI(title="Telegram Chat Summarizer Bot")

@app.get("/")
async def root():
    return {"status": "ok", "service": "bot"}

@app.get("/healthz")
async def health_check():
    logger.info("Health check OK")
    return {"status": "ok"}

# Заглушка под вебхук (позже подключим aiogram)
@app.post("/tg-webhook")
async def telegram_webhook():
    logger.info("Webhook hit")
    return {"ok": True}
