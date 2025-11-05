# app/bot_runtime.py
import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, Update
from loguru import logger
from app.bot.handlers import router as handlers_router

BOT_TOKEN = (os.environ.get("BOT_TOKEN") or "").strip()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
dp.include_router(handlers_router)

@dp.message(F.text == "/start")
async def on_start(m: Message):
    await m.answer("Привет! Готов к сводкам. Пример: /summary сегодня")

async def process_update(data: dict):
    upd = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=upd)
