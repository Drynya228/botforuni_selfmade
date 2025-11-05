import os
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, Update

# Инициализируем бота и диспетчер
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

router = Router()
dp.include_router(router)

@router.message(F.text == "/start")
async def on_start(m: Message):
    await m.answer("Привет! Я живу на Render и готов к работе.\nПопробуй: /summary сегодня")

@router.message(F.text.startswith("/summary"))
async def on_summary(m: Message):
    # Простейшая заглушка сводки
    period = m.text.replace("/summary", "").strip() or "сегодня"
    await m.answer(f"Сводка за период «{period}»: (пока заглушка)")

@router.message(F.text)
async def echo(m: Message):
    # Эхо для проверки
    if not m.text.startswith("/"):
        await m.answer(f"Эхо: {m.text[:300]}")

# Обработчик апдейта из FastAPI
async def process_update(data: dict):
    upd = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=upd)
