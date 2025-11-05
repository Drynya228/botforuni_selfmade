# app/bot_runtime.py
import os
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message, Update
from app.bot.handlers import router_ingest, router_owner
from app.bot.admin import router as router_admin

BOT_TOKEN = (os.environ.get("BOT_TOKEN") or "").strip()
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# ВАЖНО: сначала роутер индексации (во всех чатах, без ответов),
# потом роутер для владельца (отвечает только в ЛС владельцу).
dp.include_router(router_ingest)
dp.include_router(router_admin)
dp.include_router(router_owner)

# (Опционально) эхо в ЛС владельца на всякий случай:
@dp.message(F.chat.type == "private")
async def _noop_private(m: Message):
    # Ничего не делать, если не владелец — молчим
    pass

async def process_update(data: dict):
    upd = Update.model_validate(data)
    await dp.feed_update(bot=bot, update=upd)
